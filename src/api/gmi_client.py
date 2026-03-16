"""gmicloud Gemini 3.1 Flash Image API client.

This is a queue-based (async polling) API, not a streaming API.
Flow: submit request -> poll status -> download result image.
"""

import base64
import time
from collections.abc import Callable

import httpx

from src.utils import config
from src.utils.image_utils import get_mime_type, image_to_base64, pad_to_aspect_ratio

_BASE_URL = "https://console.gmicloud.ai"
_SUBMIT_ENDPOINT = "/api/v1/ie/requestqueue/apikey/requests"
_MODEL_ID = "gemini-3.1-flash-image-preview"

_POLL_INTERVAL = 2.0
_POLL_TIMEOUT = 300


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {config.get('gmi_api_key')}",
        "Content-Type": "application/json",
    }


def _build_payload(image_path: str, aspect_ratio: str, color_mode: str = "grayscale") -> dict:
    """Build gmicloud payload using Gemini-style inlineData."""
    from src.core.prompts import get_system_prompt, get_user_message

    b64 = image_to_base64(image_path)
    mime = get_mime_type(image_path)

    return {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": f"{get_system_prompt()}\n\n{get_user_message(color_mode)}"},
                    {
                        "inlineData": {
                            "mimeType": mime,
                            "data": b64,
                        }
                    },
                ],
            }
        ],
        "image_size": config.get("gmi_image_size") or "4K",
        "aspect_ratio": aspect_ratio,
    }


def _build_generate_payload(prompt: str, aspect_ratio: str, resolution: str) -> dict:
    return {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}],
            }
        ],
        "image_size": resolution,
        "aspect_ratio": aspect_ratio,
    }


def _download_image(url: str) -> str:
    """Download an image and return its base64 encoding."""
    resp = httpx.get(url, timeout=60)
    resp.raise_for_status()
    return base64.b64encode(resp.content).decode("utf-8")


def _poll_result(client: httpx.Client, request_id: str, on_text: Callable[[str], None], mode_name: str) -> dict:
    url = f"{_BASE_URL}{_SUBMIT_ENDPOINT}/{request_id}"
    elapsed = 0.0

    while elapsed < _POLL_TIMEOUT:
        resp = client.get(url)
        resp.raise_for_status()
        data = resp.json()
        status = data.get("status", "")

        if status == "success":
            on_text(f"\n✨ {mode_name}完成！耗时约 {elapsed:.0f} 秒\n")
            return data

        if status in ("failed", "cancelled"):
            on_text(f"\n❌ {mode_name}失败: {status}\n")
            raise RuntimeError(f"gmicloud {mode_name}失败，状态: {status}")

        on_text(".")
        time.sleep(_POLL_INTERVAL)
        elapsed += _POLL_INTERVAL

    on_text(f"\n⏱️ {mode_name}超时\n")
    raise RuntimeError(f"gmicloud {mode_name}超时（{_POLL_TIMEOUT}秒），请稍后重试")


def _extract_image_b64(result_data: dict, on_text: Callable[[str], None]) -> str:
    media_urls = result_data.get("outcome", {}).get("media_urls", [])
    if not media_urls:
        raise RuntimeError("gmicloud 返回结果中未找到图片 URL")

    image_url = media_urls[0].get("url", "")
    if not image_url:
        raise RuntimeError("gmicloud 返回的图片 URL 为空")

    on_text("📥 正在下载结果图片...\n")
    return _download_image(image_url)


def _submit_edit_request(
    client: httpx.Client,
    image_path: str,
    on_text: Callable[[str], None],
    color_mode: str = "grayscale",
) -> str:
    manual_ratio = config.get("gmi_aspect_ratio") or ""
    padded_path, aspect_ratio = pad_to_aspect_ratio(image_path, manual_ratio)
    if padded_path != image_path:
        on_text(f"📐 已自动调整图片比例为 {aspect_ratio}\n")
    else:
        on_text(f"📐 图片比例: {aspect_ratio}\n")

    body = {
        "model": _MODEL_ID,
        "payload": _build_payload(padded_path, aspect_ratio, color_mode=color_mode),
    }
    resp = client.post(f"{_BASE_URL}{_SUBMIT_ENDPOINT}", json=body)
    resp.raise_for_status()
    return resp.json()["request_id"]


def process_image(
    image_path: str,
    on_text: Callable[[str], None],
    color_mode: str = "grayscale",
) -> str:
    """Process an image via gmicloud queue API."""
    with httpx.Client(headers=_headers(), timeout=120) as client:
        on_text("🚀 正在提交处理请求...\n")
        request_id = _submit_edit_request(client, image_path, on_text, color_mode=color_mode)
        on_text("✅ 请求已提交\n")
        on_text(f"📏 目标尺寸: {config.get('gmi_image_size') or '4K'}\n")

        on_text("\n⏳ AI 正在处理中")
        result_data = _poll_result(client, request_id, on_text, "处理")
        b64_image = _extract_image_b64(result_data, on_text)

        try:
            import io
            from PIL import Image

            raw = base64.b64decode(b64_image)
            with Image.open(io.BytesIO(raw)) as img:
                on_text(f"🎉 下载完成！图片尺寸: {img.size[0]}x{img.size[1]}\n")
        except Exception:
            on_text("🎉 下载完成！\n")

        return b64_image


def generate_image(
    prompt: str,
    on_text: Callable[[str], None],
    resolution: str,
    aspect_ratio: str,
) -> str:
    """Generate an image via gmicloud queue API."""
    with httpx.Client(headers=_headers(), timeout=120) as client:
        on_text("🚀 正在提交生图请求...\n")
        body = {
            "model": _MODEL_ID,
            "payload": _build_generate_payload(prompt, aspect_ratio, resolution),
        }
        resp = client.post(f"{_BASE_URL}{_SUBMIT_ENDPOINT}", json=body)
        resp.raise_for_status()
        request_id = resp.json()["request_id"]

        on_text("✅ 请求已提交\n")
        on_text(f"📏 目标尺寸: {resolution}\n")
        on_text(f"📐 宽高比: {aspect_ratio}\n")

        on_text("\n⏳ AI 正在生图中")
        result_data = _poll_result(client, request_id, on_text, "生图")
        return _extract_image_b64(result_data, on_text)

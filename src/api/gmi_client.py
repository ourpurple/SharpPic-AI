"""gmicloud Gemini 3.1 Flash Image API client.

This is a queue-based (async polling) API, not a streaming API.
Flow: submit request → poll status → download result image.
"""

import base64
import json
import os
import time
from collections.abc import Callable

import httpx

from src.utils import config
from src.utils.image_utils import image_to_base64, get_mime_type, pad_to_aspect_ratio

_BASE_URL = "https://console.gmicloud.ai"
_SUBMIT_ENDPOINT = "/api/v1/ie/requestqueue/apikey/requests"
_MODEL_ID = "gemini-3.1-flash-image-preview"

# Polling settings
_POLL_INTERVAL = 2.0  # seconds between status checks
_POLL_TIMEOUT = 300   # max seconds to wait


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {config.get('gmi_api_key')}",
        "Content-Type": "application/json",
    }


def _build_payload(image_path: str, aspect_ratio: str) -> dict:
    """Build the gmicloud request payload using contents format for inline images.

    The `image` field only accepts HTTP URLs. For local files we must use
    the `contents` array with Gemini-style inlineData parts.
    Uses camelCase keys (inlineData, mimeType) following Google Gemini API format.
    """
    from src.core.prompts import get_system_prompt, get_user_message

    b64 = image_to_base64(image_path)
    mime = get_mime_type(image_path)

    payload: dict = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": f"{get_system_prompt()}\n\n{get_user_message()}"},
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

    return payload


def _submit_request(
    client: httpx.Client,
    image_path: str,
    on_text: Callable[[str], None],
) -> str:
    """Submit an image generation request. Returns the request_id."""
    # Pad image to closest supported aspect ratio
    manual_ratio = config.get("gmi_aspect_ratio") or ""
    padded_path, aspect_ratio = pad_to_aspect_ratio(image_path, manual_ratio)
    if padded_path != image_path:
        on_text(f"📐 已自动调整图片比例为 {aspect_ratio}\n")
    else:
        on_text(f"📐 图片比例: {aspect_ratio}\n")

    payload = _build_payload(padded_path, aspect_ratio)
    body = {
        "model": _MODEL_ID,
        "payload": payload,
    }

    resp = client.post(f"{_BASE_URL}{_SUBMIT_ENDPOINT}", json=body)

    resp.raise_for_status()
    data = resp.json()
    return data["request_id"]


def _download_image(url: str) -> str:
    """Download an image from URL and return base64-encoded data.

    Uses a plain client without auth headers — the result URLs are on
    Google Cloud Storage and reject foreign Authorization tokens.
    """
    resp = httpx.get(url, timeout=60)
    resp.raise_for_status()
    return base64.b64encode(resp.content).decode("utf-8")


def process_image(
    image_path: str,
    on_text: Callable[[str], None],
) -> str:
    """Process an image via gmicloud queue API.

    Calls on_text for status updates (not streaming text).
    Returns the base64-encoded result image.
    Raises RuntimeError on failure.
    """
    with httpx.Client(headers=_headers(), timeout=120) as client:
        # Step 1: Submit
        on_text("🚀 正在提交处理请求...\n")
        request_id = _submit_request(client, image_path, on_text)
        on_text(f"✅ 请求已提交\n")
        on_text(f"📏 目标尺寸: {config.get('gmi_image_size') or '4K'}\n")

        # Step 2: Poll
        on_text("\n⏳ AI 正在处理中")
        poll_count = 0
        url = f"{_BASE_URL}{_SUBMIT_ENDPOINT}/{request_id}"
        elapsed = 0.0
        result_data = None

        while elapsed < _POLL_TIMEOUT:
            resp = client.get(url)
            resp.raise_for_status()
            data = resp.json()
            status = data.get("status", "")

            if status == "success":
                result_data = data
                break
            if status in ("failed", "cancelled"):
                on_text(f"\n❌ 处理失败: {status}\n")
                raise RuntimeError(f"gmicloud 请求失败，状态: {status}")

            poll_count += 1
            on_text(".")
            time.sleep(_POLL_INTERVAL)
            elapsed += _POLL_INTERVAL

        if result_data is None:
            on_text(f"\n⏱️ 处理超时\n")
            raise RuntimeError(f"gmicloud 请求超时（{_POLL_TIMEOUT}秒），请稍后重试")

        on_text(f"\n✨ 处理完成！耗时约 {elapsed:.0f} 秒\n")

        # Step 3: Download result image
        media_urls = result_data.get("outcome", {}).get("media_urls", [])
        if not media_urls:
            raise RuntimeError("gmicloud 返回结果中未找到图片 URL")

        image_url = media_urls[0].get("url", "")
        if not image_url:
            raise RuntimeError("gmicloud 返回的图片 URL 为空")

        on_text(f"📥 正在下载结果图片...\n")
        b64_image = _download_image(image_url)
        
        # Get result image info
        try:
            import io
            from PIL import Image
            raw = base64.b64decode(b64_image)
            with Image.open(io.BytesIO(raw)) as img:
                on_text(f"🎉 下载完成！图片尺寸: {img.size[0]}x{img.size[1]}\n")
        except Exception:
            on_text(f"🎉 下载完成！\n")

        return b64_image

import base64
import re
from collections.abc import Callable

import httpx
from openai import OpenAI

from src.core.prompts import build_generate_prompt, get_system_prompt, get_user_message
from src.utils import config
from src.utils.image_utils import extract_base64_from_text, get_mime_type, image_to_base64

_TRAILING_URL_PUNCT = "'\"),.;:!?)]}>\n\r\t"


def _debug_enabled() -> bool:
    return bool(config.get("debug_enabled", False))


def _debug_emit(on_text: Callable[[str], None], message: str) -> None:
    if _debug_enabled():
        on_text(f"[DEBUG] {message}\n")


def _sanitize_url(raw_url: str) -> str:
    return raw_url.strip().rstrip(_TRAILING_URL_PUNCT)


def _looks_like_upstream_generation_error(text: str) -> bool:
    lowered = text.lower()
    error_markers = [
        "watermark processing failed",
        "failed to",
        "http 404",
        "http 5",
        "internal server error",
        "service unavailable",
        "timeout",
    ]
    return any(marker in lowered for marker in error_markers)


def _build_client() -> OpenAI:
    return OpenAI(
        api_key=config.get("api_key"),
        base_url=config.get("api_base_url"),
    )


def _build_messages(image_path: str, color_mode: str = "grayscale") -> list[dict]:
    b64_input = image_to_base64(image_path)
    mime = get_mime_type(image_path)
    user_text = get_user_message(color_mode)
    return [
        {
            "role": "system",
            "content": get_system_prompt(),
        },
        {
            "role": "user",
            "content": [
                {"type": "text", "text": user_text},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime};base64,{b64_input}",
                    },
                },
            ],
        },
    ]


def _extract_images_from_extra(model_extra: dict | None, on_text: Callable[[str], None] | None = None) -> list[str]:
    if not model_extra:
        return []
    images = model_extra.get("images")
    if not isinstance(images, list):
        return []

    results: list[str] = []
    for img in images:
        if not isinstance(img, dict):
            continue

        url = ""
        if img.get("type") == "image_url":
            url = (img.get("image_url") or {}).get("url", "")
        elif "url" in img:
            url = img["url"]
        elif "data" in img:
            data = img["data"]
            if isinstance(data, str):
                results.append(data)
            continue

        if url.startswith("data:"):
            results.append(url.split(",", 1)[1])
        elif url.startswith("http"):
            sanitized = _sanitize_url(url)
            if on_text:
                _debug_emit(on_text, f"Found image URL in model_extra (len={len(sanitized)}), downloading")
            image_b64 = _download_image_url(sanitized, on_text=on_text)
            if on_text:
                on_text("✅ 图片下载完成\n")
            results.append(image_b64)

    if on_text and images:
        _debug_emit(on_text, f"model_extra.images count={len(images)}, extracted={len(results)}")
    return results


def _extract_text_from_delta_content(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
        return "".join(parts)
    return ""


def _extract_image_from_text_or_raise(full_text: str, on_text: Callable[[str], None], error_prefix: str) -> str:
    image_b64 = extract_base64_from_text(full_text)
    if image_b64:
        _debug_emit(on_text, f"Extracted base64 image from text, len={len(image_b64)}")
        return image_b64

    url_match = re.search(r"https?://\S+", full_text)
    if url_match:
        url = _sanitize_url(url_match.group(0))
        _debug_emit(on_text, f"Found URL in text and sanitized: {url}")
        on_text("📥 正在下载结果图片...\n")
        try:
            image_b64 = _download_image_url(url, on_text=on_text)
            on_text("✅ 图片下载完成\n")
            return image_b64
        except Exception as exc:
            _debug_emit(on_text, f"Download from extracted URL failed: {exc}")
            raise RuntimeError(
                f"{error_prefix}检测到图片链接，但下载失败（可能为临时链接失效或服务端资源异常）。\n\n"
                f"链接: {url}\n"
                f"下载错误: {exc}\n\n"
                f"模型回复内容:\n{full_text}"
            ) from exc

    if _looks_like_upstream_generation_error(full_text):
        _debug_emit(on_text, "Detected upstream error markers from model text output")
        raise RuntimeError(
            f"{error_prefix}未返回可用图片数据，且上游服务报告了生成/后处理失败。\n\n"
            f"模型回复内容:\n{full_text}"
        )

    _debug_emit(on_text, "No base64, no URL, and no known upstream markers in text output")
    raise RuntimeError(
        f"{error_prefix}未找到图片数据。未识别到可下载链接或 base64 图片。\n"
        f"这更可能是本地解析路径未覆盖该返回格式，或当前模型/网关未按预期返回图片字段。\n\n"
        f"模型回复内容:\n{full_text}"
    )


def process_image_stream(
    image_path: str,
    on_text: Callable[[str], None],
    color_mode: str = "grayscale",
) -> str:
    provider = config.get("api_provider") or "openai"

    if provider == "gmicloud":
        from src.api.gmi_client import process_image as gmi_process

        return gmi_process(image_path, on_text, color_mode=color_mode)

    client = _build_client()
    messages = _build_messages(image_path, color_mode=color_mode)

    _debug_emit(on_text, f"Provider={provider}, model={config.get('model_name')}, stream=chat.completions")
    on_text("🚀 开始处理图片...\n")

    stream = client.chat.completions.create(
        model=config.get("model_name"),
        messages=messages,
        stream=True,
    )

    full_text = ""
    collected_images: list[str] = []
    chunk_count = 0

    for chunk in stream:
        chunk_count += 1
        if not chunk.choices:
            continue

        delta = chunk.choices[0].delta

        text_delta = _extract_text_from_delta_content(delta.content)
        if text_delta:
            full_text += text_delta
            on_text(text_delta)

        if hasattr(delta, "model_extra") and delta.model_extra:
            collected_images.extend(_extract_images_from_extra(delta.model_extra, on_text=on_text))

    _debug_emit(on_text, f"Stream finished: chunks={chunk_count}, text_len={len(full_text)}, images={len(collected_images)}")
    on_text("\n✨ 处理完成，正在整理结果图片...\n")

    if collected_images:
        on_text("✅ 结果图片已准备完成\n")
        return collected_images[0]

    return _extract_image_from_text_or_raise(full_text, on_text, "API 响应中")


def generate_image_stream(
    prompt: str,
    on_text: Callable[[str], None],
    color_mode: str,
    resolution: str,
    aspect_ratio: str,
    style: str,
    custom_style: str = "",
) -> str:
    provider = config.get("api_provider") or "openai"
    merged_prompt = build_generate_prompt(prompt, color_mode, resolution, aspect_ratio, style, custom_style)

    if provider == "gmicloud":
        from src.api.gmi_client import generate_image as gmi_generate

        return gmi_generate(
            prompt=merged_prompt,
            on_text=on_text,
            resolution=resolution,
            aspect_ratio=aspect_ratio,
        )

    client = _build_client()
    _debug_emit(on_text, f"Provider={provider}, model={config.get('model_name')}, stream=chat.completions")
    _debug_emit(on_text, f"Gen params: color={color_mode}, resolution={resolution}, aspect_ratio={aspect_ratio}, style={style}")
    on_text("🚀 正在提交生图请求...\n")

    messages = [{"role": "user", "content": merged_prompt}]
    stream = client.chat.completions.create(
        model=config.get("model_name"),
        messages=messages,
        stream=True,
    )

    full_text = ""
    collected_images: list[str] = []
    chunk_count = 0

    for chunk in stream:
        chunk_count += 1
        if not chunk.choices:
            continue

        delta = chunk.choices[0].delta

        text_delta = _extract_text_from_delta_content(delta.content)
        if text_delta:
            full_text += text_delta
            on_text(text_delta)

        if hasattr(delta, "model_extra") and delta.model_extra:
            collected_images.extend(_extract_images_from_extra(delta.model_extra, on_text=on_text))

    _debug_emit(on_text, f"Stream finished: chunks={chunk_count}, text_len={len(full_text)}, images={len(collected_images)}")
    on_text("\n✨ 生图完成，正在整理结果...\n")

    if collected_images:
        on_text("✅ 结果图片已准备完成\n")
        return collected_images[0]

    return _extract_image_from_text_or_raise(full_text, on_text, "生图响应中")


def _download_image_url(url: str, on_text: Callable[[str], None] | None = None) -> str:
    headers = {"User-Agent": "Mozilla/5.0 SharpPic-AI/1.0"}
    try:
        resp = httpx.get(url, timeout=60, follow_redirects=True, headers=headers)
    except Exception as exc:
        if "WRONG_VERSION_NUMBER" in str(exc) and url.startswith("https://"):
            fallback_url = "http://" + url[len("https://") :]
            if on_text:
                _debug_emit(on_text, f"TLS handshake failed, retrying with HTTP: {fallback_url}")
            resp = httpx.get(fallback_url, timeout=60, follow_redirects=True, headers=headers)
        else:
            raise

    resp.raise_for_status()
    content_type = resp.headers.get("content-type", "")
    if content_type and "image" not in content_type.lower():
        raise RuntimeError(f"下载到的资源不是图片（content-type={content_type}）")
    return base64.b64encode(resp.content).decode("utf-8")


def list_models() -> list[str]:
    client = _build_client()
    models = client.models.list()
    return sorted(m.id for m in models)


def test_connection() -> str:
    client = _build_client()
    response = client.chat.completions.create(
        model=config.get("model_name"),
        messages=[{"role": "user", "content": "Hi, reply with OK."}],
        max_tokens=10,
    )
    return response.choices[0].message.content or "OK"

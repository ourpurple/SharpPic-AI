import re
import base64
from collections.abc import Callable

import httpx
from openai import OpenAI

from src.utils import config
from src.utils.image_utils import image_to_base64, get_mime_type, extract_base64_from_text
from src.core.prompts import get_system_prompt, get_user_message


def _build_client() -> OpenAI:
    return OpenAI(
        api_key=config.get("api_key"),
        base_url=config.get("api_base_url"),
    )


def _build_messages(image_path: str) -> list[dict]:
    b64_input = image_to_base64(image_path)
    mime = get_mime_type(image_path)
    user_text = get_user_message()
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


def _extract_images_from_extra(model_extra: dict | None) -> list[str]:
    """Extract base64 image data from delta.model_extra['images'] field.

    Some OpenAI-compatible APIs (e.g. Qwen) return images in this extension field.
    Returns a list of base64 strings (without data URI prefix).
    """
    if not model_extra:
        return []
    images = model_extra.get("images")
    if not isinstance(images, list):
        return []
    results = []
    for img in images:
        if isinstance(img, dict):
            url = ""
            if img.get("type") == "image_url":
                url = (img.get("image_url") or {}).get("url", "")
            elif "url" in img:
                url = img["url"]
            elif "data" in img:
                results.append(img["data"])
                continue
            if url.startswith("data:"):
                results.append(url.split(",", 1)[1])
            elif url.startswith("http"):
                results.append(_download_image_url(url))
    return results


def _extract_text_from_delta_content(content: object) -> str:
    """Normalize streaming delta content into plain text."""
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


def _debug(on_text: Callable[[str], None], msg: str):
    # Debug messages are disabled for better user experience
    pass


def process_image_stream(
    image_path: str,
    on_text: Callable[[str], None],
) -> str:
    """Process an image with streaming. Calls on_text for each text delta.

    Routes to the correct backend based on config api_provider.
    Returns the base64-encoded result image.
    Raises RuntimeError if no image found.
    """
    provider = config.get("api_provider") or "openai"

    if provider == "gmicloud":
        from src.api.gmi_client import process_image as gmi_process

        return gmi_process(image_path, on_text)

    client = _build_client()
    messages = _build_messages(image_path)

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
            extras = _extract_images_from_extra(delta.model_extra)
            if extras:
                _debug(on_text, f"chunk[{chunk_count}]: found {len(extras)} image(s) in model_extra, b64 length={len(extras[0])}")
                collected_images.extend(extras)

    on_text("\n✅ 处理完成，正在生成结果图片...\n")

    if collected_images:
        return collected_images[0]

    image_b64 = extract_base64_from_text(full_text)
    if image_b64:
        return image_b64

    url_match = re.search(r"https?://\S+", full_text)
    if url_match:
        url = url_match.group(0).rstrip(")")
        on_text("📥 正在下载结果图片...\n")
        return _download_image_url(url)

    raise RuntimeError(
        "API 响应中未找到图片数据。模型可能不支持图片生成，请检查模型设置。\n\n"
        f"模型回复内容:\n{full_text}"
    )


def _download_image_url(url: str) -> str:
    """Download an image from a URL and return its base64 encoding."""
    resp = httpx.get(url, timeout=60)
    resp.raise_for_status()
    return base64.b64encode(resp.content).decode("utf-8")


def list_models() -> list[str]:
    """Fetch available model IDs from the API. Returns a sorted list."""
    client = _build_client()
    models = client.models.list()
    return sorted(m.id for m in models)


def test_connection() -> str:
    """Test the API connection. Returns a success message or raises on failure."""
    client = _build_client()
    response = client.chat.completions.create(
        model=config.get("model_name"),
        messages=[{"role": "user", "content": "Hi, reply with OK."}],
        max_tokens=10,
    )
    return response.choices[0].message.content or "OK"

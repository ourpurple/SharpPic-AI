import base64
import io
import math
import re
import tempfile
from pathlib import Path

from PIL import Image
from PyQt6.QtGui import QPixmap, QImage


# GMI API supported aspect ratios: (label, width, height)
_SUPPORTED_RATIOS = [
    ("1:1", 1, 1),
    ("3:2", 3, 2),
    ("2:3", 2, 3),
    ("3:4", 3, 4),
    ("4:3", 4, 3),
    ("4:5", 4, 5),
    ("5:4", 5, 4),
    ("9:16", 9, 16),
    ("16:9", 16, 9),
    ("21:9", 21, 9),
]


def image_to_base64(path: str) -> str:
    """Read an image file and return its base64-encoded string."""
    with open(path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode("utf-8")


def get_mime_type(path: str) -> str:
    """Return MIME type based on file extension."""
    ext = Path(path).suffix.lower()
    mime_map = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".bmp": "image/bmp",
    }
    return mime_map.get(ext, "image/png")


def base64_to_qpixmap(data: str) -> QPixmap:
    """Decode a base64 string into a QPixmap."""
    if "," in data and data.startswith("data:"):
        data = data.split(",", 1)[1]
    raw = base64.b64decode(data)
    qimage = QImage()
    qimage.loadFromData(raw)
    return QPixmap.fromImage(qimage)


def base64_to_pil(data: str) -> Image.Image:
    """Decode a base64 string into a PIL Image."""
    if "," in data and data.startswith("data:"):
        data = data.split(",", 1)[1]
    raw = base64.b64decode(data)
    return Image.open(io.BytesIO(raw))


def save_image(image: Image.Image, path: str) -> None:
    """Save a PIL Image to the given path, creating parent directories if needed."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def extract_base64_from_text(text: str) -> str | None:
    """Try to extract a base64-encoded image from text content."""
    match = re.search(r"data:image/[^;]+;base64,([A-Za-z0-9+/=]+)", text)
    if match:
        return match.group(1)

    match = re.search(r"([A-Za-z0-9+/=]{100,})", text)
    if match:
        candidate = match.group(1)
        try:
            raw = base64.b64decode(candidate)
            Image.open(io.BytesIO(raw))
            return candidate
        except Exception:
            pass
    return None


def find_closest_aspect_ratio(width: int, height: int) -> str:
    """Find the closest supported GMI aspect ratio for the given dimensions."""
    actual = width / height
    best_label = "1:1"
    best_diff = float("inf")
    for label, rw, rh in _SUPPORTED_RATIOS:
        target = rw / rh
        # Use log-ratio distance for proportional comparison.
        diff = abs(math.log(actual) - math.log(target))
        if diff < best_diff:
            best_diff = diff
            best_label = label
    return best_label


def pad_to_aspect_ratio(image_path: str, target_label: str = "") -> tuple[str, str]:
    """Pad image with white borders to match a supported aspect ratio.

    If target_label is given (e.g. "16:9"), pad to that exact ratio.
    If empty, auto-detect the closest supported ratio.
    Returns (padded_image_path, aspect_ratio_label).
    If the image already matches, returns the original path unchanged.
    """
    with Image.open(image_path) as img:
        w, h = img.size

        if target_label and ":" in target_label:
            ratio_label = target_label
        else:
            ratio_label = find_closest_aspect_ratio(w, h)

        tw, th = map(int, ratio_label.split(":"))
        target_ratio = tw / th
        actual_ratio = w / h

        # Already close enough; no padding needed.
        if abs(actual_ratio - target_ratio) / target_ratio < 0.01:
            return image_path, ratio_label

        # Calculate padded dimensions.
        if target_ratio > actual_ratio:
            # Need wider; pad left and right.
            new_w = round(h * target_ratio)
            new_h = h
        else:
            # Need taller; pad top and bottom.
            new_w = w
            new_h = round(w / target_ratio)

        canvas = Image.new("RGB", (new_w, new_h), (255, 255, 255))
        paste_x = (new_w - w) // 2
        paste_y = (new_h - h) // 2
        if img.mode == "RGBA":
            canvas.paste(img, (paste_x, paste_y), img)
        else:
            canvas.paste(img, (paste_x, paste_y))

        tmp_dir = Path(tempfile.gettempdir()) / "sharppic"
        tmp_dir.mkdir(exist_ok=True)
        tmp_path = tempfile.NamedTemporaryFile(
            prefix="padded_",
            suffix=".png",
            dir=tmp_dir,
            delete=False,
        ).name
        canvas.save(tmp_path, "PNG")

        return tmp_path, ratio_label

"""Image preparation for the two kinds of engines.

* Vision LLMs want the photo itself (colour helps them), just bounded in size.
* Tesseract wants a clean, deskewed, binarised page.
"""
from __future__ import annotations

import cv2
import numpy as np

MAX_VISION_SIDE = 1600


class InvalidImageError(ValueError):
    pass


def decode(image_bytes: bytes) -> np.ndarray:
    arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise InvalidImageError("Could not decode image. Upload a JPG or PNG photo.")
    return img


def _limit_size(img: np.ndarray, max_side: int) -> np.ndarray:
    h, w = img.shape[:2]
    scale = max_side / max(h, w)
    if scale >= 1:
        return img
    return cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)


def for_vision(image_bytes: bytes) -> tuple[bytes, str]:
    """Return JPEG bytes no larger than MAX_VISION_SIDE on the long edge."""
    img = _limit_size(decode(image_bytes), MAX_VISION_SIDE)
    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 90])
    if not ok:
        raise InvalidImageError("Could not re-encode image.")
    return buf.tobytes(), "image/jpeg"


def estimate_skew(gray: np.ndarray) -> float:
    """Skew angle in degrees from the minimum-area rectangle around dark pixels."""
    inv = cv2.bitwise_not(gray)
    _, thresh = cv2.threshold(inv, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    coords = np.column_stack(np.where(thresh > 0))
    if len(coords) < 50:
        return 0.0
    angle = cv2.minAreaRect(coords)[-1]
    # OpenCV >= 4.5 returns angles in [0, 90); map to a small signed correction.
    if angle > 45:
        angle -= 90
    return float(-angle) if abs(angle) <= 15 else 0.0


def for_ocr(image_bytes: bytes) -> np.ndarray:
    """Grayscale, upscale small photos, contrast-normalise, deskew, denoise, binarise."""
    img = decode(image_bytes)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    if max(h, w) < 1400:
        f = 1400 / max(h, w)
        gray = cv2.resize(gray, None, fx=f, fy=f, interpolation=cv2.INTER_CUBIC)
    gray = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gray)

    angle = estimate_skew(gray)
    if abs(angle) > 0.3:
        h, w = gray.shape
        m = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
        gray = cv2.warpAffine(gray, m, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

    gray = cv2.fastNlMeansDenoising(gray, None, h=12, templateWindowSize=7, searchWindowSize=21)
    return cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 15)

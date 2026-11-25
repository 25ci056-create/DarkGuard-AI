"""Image preprocessing with OpenCV."""
import base64
import io
from pathlib import Path

try:
    import cv2
    import numpy as np
    _CV2 = True
except ImportError:
    _CV2 = False

try:
    from PIL import Image, ImageOps, ExifTags
    _PIL = True
except ImportError:
    _PIL = False


def _fix_orientation(img_pil):
    """Auto-rotate based on EXIF orientation."""
    if not _PIL:
        return img_pil
    try:
        img_pil = ImageOps.exif_transpose(img_pil)
    except Exception:
        pass
    return img_pil


def preprocess_images(paths: dict) -> dict:
    """
    Returns {slot: {"path": str, "b64": str, "cv_img": ndarray or None, "pil_img": PIL.Image or None}}
    """
    results = {}
    for slot, path in paths.items():
        entry = {"path": path, "b64": None, "cv_img": None, "pil_img": None}
        try:
            if _PIL:
                pil = Image.open(path).convert("RGB")
                pil = _fix_orientation(pil)
                # Resize if too large (keep aspect, max 1600 wide)
                if pil.width > 1600:
                    ratio = 1600 / pil.width
                    pil = pil.resize((1600, int(pil.height * ratio)), Image.LANCZOS)
                entry["pil_img"] = pil
                buf = io.BytesIO()
                pil.save(buf, format="JPEG", quality=92)
                entry["b64"] = base64.b64encode(buf.getvalue()).decode()

            if _CV2:
                img = cv2.imdecode(np.frombuffer(Path(path).read_bytes(), np.uint8), cv2.IMREAD_COLOR)
                if img is not None:
                    # Denoise lightly
                    img = cv2.fastNlMeansDenoisingColored(img, None, 3, 3, 7, 21)
                    entry["cv_img"] = img

            # Fallback b64 from raw file
            if entry["b64"] is None:
                with open(path, "rb") as f:
                    entry["b64"] = base64.b64encode(f.read()).decode()

        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning("Preprocess failed for slot %s: %s", slot, exc)

        results[slot] = entry
    return results

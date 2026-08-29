import sys
import os
import shutil
import io
import subprocess
import pytesseract
from PIL import Image

_configured = False


def _get_base_dir():
    """Directory to resolve the bundled vendor/ folder from — the
    PyInstaller extraction dir when frozen, otherwise the project's
    src/ folder during development."""
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # .../src


def _find_bundled_tesseract():
    base = _get_base_dir()
    candidates = [
        os.path.join(base, "vendor", "tesseract-ocr", "tesseract.exe"),
        os.path.join(os.path.dirname(base), "vendor", "tesseract-ocr", "tesseract.exe"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None


def _configure_tesseract():
    global _configured
    if _configured:
        return
    _configured = True

    bundled = _find_bundled_tesseract()
    if bundled:
        pytesseract.pytesseract.tesseract_cmd = bundled
        tessdata_dir = os.path.join(os.path.dirname(bundled), "tessdata")
        if os.path.isdir(tessdata_dir):
            os.environ["TESSDATA_PREFIX"] = tessdata_dir
        return

    if shutil.which("tesseract"):
        return  # already on PATH (dev machine with a system install)

    if sys.platform == "win32":
        for p in (
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        ):
            if os.path.exists(p):
                pytesseract.pytesseract.tesseract_cmd = p
                return


def is_available() -> bool:
    return get_status()["available"]


def get_status() -> dict:
    _configure_tesseract()
    try:
        cmd = pytesseract.pytesseract.tesseract_cmd
        proc = subprocess.run(
            [cmd, "--version"],
            capture_output=True, text=True, timeout=5,
        )
        first_line = proc.stdout.splitlines()[0] if proc.stdout else "unknown version"
        return {"available": True, "version": first_line}
    except subprocess.TimeoutExpired:
        return {"available": False, "error": "Tesseract did not respond (timed out)"}
    except FileNotFoundError:
        return {"available": False, "error": "Tesseract not found on this system. Install from https://github.com/UB-Mannheim/tesseract/wiki"}
    except Exception as e:
        return {"available": False, "error": str(e)}


def ocr_page(pix, dpi=250, min_confidence=40):
    """
    pix: a fitz.Pixmap of the page rendered at `dpi`.
    Returns {"lines": [{bbox:[x0,y0,x1,y1] in PDF points, text, confidence,
    low_confidence}], "avg_confidence": float} grouped by Tesseract's own
    line/block/paragraph numbering.
    """
    _configure_tesseract()
    scale = 72 / dpi

    img = Image.open(io.BytesIO(pix.tobytes("png")))
    data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)

    groups = {}
    n = len(data["text"])
    for i in range(n):
        text = data["text"][i].strip()
        try:
            conf = int(float(data["conf"][i]))
        except (ValueError, TypeError):
            conf = -1
        if not text or conf < 0:
            continue
        key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
        x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
        entry = groups.setdefault(key, {"words": [], "confs": []})
        entry["words"].append({"text": text, "bbox": [x, y, x + w, y + h]})
        entry["confs"].append(conf)

    lines = []
    all_confs = []
    for entry in groups.values():
        words = entry["words"]
        if not words:
            continue
        x0 = min(w["bbox"][0] for w in words) * scale
        y0 = min(w["bbox"][1] for w in words) * scale
        x1 = max(w["bbox"][2] for w in words) * scale
        y1 = max(w["bbox"][3] for w in words) * scale
        avg_conf = sum(entry["confs"]) / len(entry["confs"])
        all_confs.append(avg_conf)
        lines.append({
            "bbox": [x0, y0, x1, y1],
            "text": " ".join(w["text"] for w in words),
            "confidence": round(avg_conf, 1),
            "low_confidence": avg_conf < min_confidence,
        })

    avg_page_conf = round(sum(all_confs) / len(all_confs), 1) if all_confs else 0.0
    return {"lines": lines, "avg_confidence": avg_page_conf}
import fitz  # PyMuPDF


def _color_to_rgb(color_int):
    """PyMuPDF span colors are packed ints; unpack to 0-255 RGB."""
    r = (color_int >> 16) & 255
    g = (color_int >> 8) & 255
    b = color_int & 255
    return [r, g, b]


def parse_pdf(path: str) -> dict:
    doc = fitz.open(path)
    pages_out = []

    for page_index in range(doc.page_count):
        page = doc[page_index]
        page_dict = page.get_text("dict")

        text_blocks = []
        char_count = 0
        for block in page_dict.get("blocks", []):
            if block.get("type") != 0:  # 0 = text block, 1 = image block
                continue
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span.get("text", "")
                    if not text.strip():
                        continue
                    char_count += len(text)
                    text_blocks.append({
                        "bbox": list(span["bbox"]),
                        "text": text,
                        "font": span.get("font", ""),
                        "size": round(span.get("size", 0), 2),
                        "color": _color_to_rgb(span.get("color", 0)),
                        "flags": span.get("flags", 0),
                    })

        images = []
        for img in page.get_images(full=True):
            xref = img[0]
            try:
                rects = page.get_image_rects(xref)
            except Exception:
                rects = []
            base_image = doc.extract_image(xref)
            for rect in rects:
                images.append({
                    "bbox": [rect.x0, rect.y0, rect.x1, rect.y1],
                    "xref": xref,
                    "ext": base_image.get("ext", "png"),
                    "width": base_image.get("width", 0),
                    "height": base_image.get("height", 0),
                })

        pages_out.append({
            "number": page_index + 1,
            "width": page.rect.width,
            "height": page.rect.height,
            "text_blocks": text_blocks,
            "images": images,
            "is_scanned": char_count < 20 and len(images) > 0,
        })

    result = {"page_count": doc.page_count, "pages": pages_out}
    doc.close()
    return result


def extract_image_bytes(path: str, xref: int) -> bytes:
    """Pull raw bytes for a specific embedded image (used by docx_builder later)."""
    doc = fitz.open(path)
    base_image = doc.extract_image(xref)
    doc.close()
    return base_image["image"]
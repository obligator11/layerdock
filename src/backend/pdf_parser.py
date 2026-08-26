import fitz  # PyMuPDF


def _color_to_rgb(color_int):
    r = (color_int >> 16) & 255
    g = (color_int >> 8) & 255
    b = color_int & 255
    return [r, g, b]


def _rects_overlap_ratio(a, b):
    """Fraction of rect b's area covered by rect a. a,b = [x0,y0,x1,y1]."""
    x0, y0 = max(a[0], b[0]), max(a[1], b[1])
    x1, y1 = min(a[2], b[2]), min(a[3], b[3])
    if x1 <= x0 or y1 <= y0:
        return 0.0
    inter = (x1 - x0) * (y1 - y0)
    area_b = (b[2] - b[0]) * (b[3] - b[1])
    return inter / area_b if area_b > 0 else 0.0


def _get_vector_regions(page, min_area=150, pad=4):
    """Cluster PDF vector drawing ops (how charts/diagrams are usually
    built) into bounding boxes so each cluster can be rasterized."""
    try:
        drawings = page.get_drawings()
    except Exception:
        return []

    rects = [d["rect"] for d in drawings if d.get("rect") and d["rect"].width > 0 and d["rect"].height > 0]
    if not rects:
        return []

    used = [False] * len(rects)
    clusters = []
    for i, r in enumerate(rects):
        if used[i]:
            continue
        cluster = fitz.Rect(r)
        used[i] = True
        changed = True
        while changed:
            changed = False
            expanded = fitz.Rect(cluster.x0 - pad, cluster.y0 - pad, cluster.x1 + pad, cluster.y1 + pad)
            for j, r2 in enumerate(rects):
                if used[j]:
                    continue
                if expanded.intersects(r2):
                    cluster |= r2
                    used[j] = True
                    changed = True
        if cluster.get_area() >= min_area:
            clusters.append(cluster)
    return clusters


def parse_pdf(path: str) -> dict:
    doc = fitz.open(path)
    pages_out = []

    for page_index in range(doc.page_count):
        page = doc[page_index]
        page_dict = page.get_text("dict")

        text_blocks = []
        images = []
        char_count = 0

        for block in page_dict.get("blocks", []):
            btype = block.get("type")

            if btype == 0:  # text block
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

            elif btype == 1:  # image block — bbox here is already correctly
                                # transformed/positioned, unlike xref-based lookup
                img_bytes = block.get("image")
                if not img_bytes:
                    continue
                images.append({
                    "bbox": list(block["bbox"]),
                    "kind": "raster",
                    "raw_bytes": img_bytes,
                    "width": block.get("width", 0),
                    "height": block.get("height", 0),
                })

        # Vector graphics (charts/diagrams not captured as image blocks above)
        for region in _get_vector_regions(page):
            rbbox = [region.x0, region.y0, region.x1, region.y1]
            if any(_rects_overlap_ratio(im["bbox"], rbbox) > 0.6 for im in images):
                continue  # already covered by an image block
            try:
                mat = fitz.Matrix(150 / 72, 150 / 72)  # render at 150dpi
                pix = page.get_pixmap(matrix=mat, clip=region)
                images.append({
                    "bbox": rbbox,
                    "kind": "vector",
                    "raw_bytes": pix.tobytes("png"),
                    "width": pix.width,
                    "height": pix.height,
                })
            except Exception:
                continue

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
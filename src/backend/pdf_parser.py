"""
PDF parsing engine.

Extracts positioned text runs plus rasterized regions for anything visual:
embedded images, and vector-drawn graphics (charts/diagrams) — but not
simple decorative shapes like full-page backgrounds or borders, which get
filtered out so they don't swallow real text underneath them.
"""
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


def _cluster_rects(rects, pad=4):
    """Merge overlapping/adjacent rects into clusters, tracking how many
    raw drawing ops fed each cluster (used to spot simple backgrounds)."""
    if not rects:
        return []
    used = [False] * len(rects)
    clusters = []
    for i, r in enumerate(rects):
        if used[i]:
            continue
        cluster = fitz.Rect(r)
        count = 1
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
                    count += 1
                    used[j] = True
                    changed = True
        clusters.append({"rect": cluster, "count": count})
    return clusters


def _get_vector_regions(page, min_area=150):
    """Return bounding boxes of real vector graphics (charts/diagrams),
    excluding simple full-page-ish shapes (backgrounds, borders, watermarks)
    that would otherwise swallow the text drawn on top of them."""
    try:
        drawings = page.get_drawings()
    except Exception:
        return []

    rects = [d["rect"] for d in drawings if d.get("rect") and d["rect"].width > 0 and d["rect"].height > 0]
    if not rects:
        return []

    page_area = page.rect.width * page.rect.height
    clusters = _cluster_rects(rects)

    regions = []
    for c in clusters:
        rect, count = c["rect"], c["count"]
        area = rect.get_area()
        if area < min_area:
            continue
        area_ratio = area / page_area if page_area > 0 else 0
        # A handful of drawing ops covering a large fraction of the page is
        # almost always a background fill, border, or watermark — not a
        # chart. Real charts/diagrams are built from many small ops.
        if count <= 3 and area_ratio > 0.2:
            continue
        if rect.width < 3 or rect.height < 3:
            continue  # hairline rule / underline, not a graphic
        regions.append(rect)
    return regions


def parse_pdf(path: str) -> dict:
    doc = fitz.open(path)
    pages_out = []

    for page_index in range(doc.page_count):
        page = doc[page_index]
        page_dict = page.get_text("dict")

        raw_text_spans = []
        image_block_rects = []  # real embedded photos only — used for text dedup

        for block in page_dict.get("blocks", []):
            btype = block.get("type")
            if btype == 0:
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text = span.get("text", "")
                        if not text.strip():
                            continue
                        raw_text_spans.append({
                            "bbox": list(span["bbox"]),
                            "text": text,
                            "font": span.get("font", ""),
                            "size": round(span.get("size", 0), 2),
                            "color": _color_to_rgb(span.get("color", 0)),
                            "flags": span.get("flags", 0),
                        })
            elif btype == 1:
                bbox = block.get("bbox")
                if bbox and (bbox[2] - bbox[0]) > 1 and (bbox[3] - bbox[1]) > 1:
                    image_block_rects.append(fitz.Rect(bbox))

        image_regions_for_render = [[r.x0, r.y0, r.x1, r.y1] for r in image_block_rects]

        for region in _get_vector_regions(page):
            rbbox = [region.x0, region.y0, region.x1, region.y1]
            if any(_rects_overlap_ratio(ib, rbbox) > 0.6 for ib in image_regions_for_render):
                continue
            image_regions_for_render.append(rbbox)

        images = []
        for rbbox in image_regions_for_render:
            try:
                clip = fitz.Rect(rbbox)
                mat = fitz.Matrix(150 / 72, 150 / 72)
                pix = page.get_pixmap(matrix=mat, clip=clip)
                images.append({
                    "bbox": rbbox,
                    "raw_bytes": pix.tobytes("png"),
                    "width": pix.width,
                    "height": pix.height,
                })
            except Exception:
                continue

        # Only drop text that sits inside a REAL embedded photo (not vector
        # regions) — avoids duplicate text on top of photos, without risking
        # nuking real page text under a decorative shape.
        image_block_bboxes = [[r.x0, r.y0, r.x1, r.y1] for r in image_block_rects]
        text_blocks = []
        char_count = 0
        for span in raw_text_spans:
            if any(_rects_overlap_ratio(ib, span["bbox"]) > 0.8 for ib in image_block_bboxes):
                continue
            char_count += len(span["text"])
            text_blocks.append(span)

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
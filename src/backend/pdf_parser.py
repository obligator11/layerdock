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


def _cluster_rects(rects, pad=2):
    """
    Connected-components clustering by PAIRWISE rect proximity — not by
    testing against an ever-growing cluster bounding box. Only merges
    rects that are actually close to a specific neighboring rect, so one
    cluster can't "reach" across the page toward unrelated shapes.
    """
    if not rects:
        return []
    n = len(rects)
    parent = list(range(n))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    expanded = [fitz.Rect(r.x0 - pad, r.y0 - pad, r.x1 + pad, r.y1 + pad) for r in rects]
    for i in range(n):
        for j in range(i + 1, n):
            if expanded[i].intersects(rects[j]):
                union(i, j)

    groups = {}
    for i in range(n):
        root = find(i)
        groups.setdefault(root, []).append(rects[i])

    clusters = []
    for group in groups.values():
        rect = fitz.Rect(group[0])
        for r in group[1:]:
            rect |= r
        clusters.append({"rect": rect, "count": len(group)})
    return clusters


def _get_vector_regions(page, min_area=150):
    try:
        drawings = page.get_drawings()
    except Exception:
        return []
    rects = [d["rect"] for d in drawings if d.get("rect") and d["rect"].width > 0 and d["rect"].height > 0]
    if not rects:
        return []

    page_area = page.rect.width * page.rect.height

    # Drop oversized individual shapes BEFORE clustering. A single vector
    # op covering most of the page is a background/border/watermark, not
    # part of a chart or table. Left in, its huge rect overlaps everything
    # else on the page and acts as a "bridge" that clustering merges into,
    # turning "background + nearby chart" into one page-sized cluster.
    rects = [r for r in rects if (r.get_area() / page_area if page_area > 0 else 0) < 0.5]
    if not rects:
        return []

    clusters = _cluster_rects(rects)

    regions = []
    for c in clusters:
        rect, count = c["rect"], c["count"]
        area = rect.get_area()
        if area < min_area:
            continue
        area_ratio = area / page_area if page_area > 0 else 0
        if count <= 3 and area_ratio > 0.2:
            continue  # background/border/watermark, not a real graphic
        if rect.width < 3 or rect.height < 3:
            continue
        regions.append(rect)
    return regions


def parse_pdf(path: str) -> dict:
    doc = fitz.open(path)
    pages_out = []

    for page_index in range(doc.page_count):
        page = doc[page_index]
        page_dict = page.get_text("dict")

        raw_lines = []       # [{bbox, runs:[{text,font,size,color,flags}]}]
        image_block_rects = []

        for block in page_dict.get("blocks", []):
            btype = block.get("type")

            if btype == 0:  # text block
                for line in block.get("lines", []):
                    line_bbox = line.get("bbox")
                    if not line_bbox:
                        continue
                    runs = []
                    for span in line.get("spans", []):
                        text = span.get("text", "")
                        if not text.strip():
                            continue
                        runs.append({
                            "text": text,
                            "font": span.get("font", ""),
                            "size": round(span.get("size", 0), 2),
                            "color": _color_to_rgb(span.get("color", 0)),
                            "flags": span.get("flags", 0),
                        })
                    if runs:
                        raw_lines.append({"bbox": list(line_bbox), "runs": runs})

            elif btype == 1:  # image
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

        # Drop whole lines that sit inside ANY rasterized region — real
        # embedded photos AND rasterized vector graphics (charts/tables) —
        # since page.get_pixmap() bakes in whatever text sits in that clip
        # area. Without this, chart/table labels get drawn twice: once
        # baked into the chart image, once as a separate floating textbox
        # slightly misaligned with it (the "wavy ghosting" artifact).
        text_lines = []
        char_count = 0
        for line in raw_lines:
            if any(_rects_overlap_ratio(ib, line["bbox"]) > 0.7 for ib in image_regions_for_render):
                continue
            char_count += sum(len(r["text"]) for r in line["runs"])
            text_lines.append(line)

        pages_out.append({
            "number": page_index + 1,
            "width": page.rect.width,
            "height": page.rect.height,
            "text_lines": text_lines,
            "images": images,
            "is_scanned": char_count < 20 and len(images) > 0,
        })

    result = {"page_count": doc.page_count, "pages": pages_out}
    doc.close()
    return result
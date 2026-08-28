import fitz  # PyMuPDF

from backend import ocr_engine


def _color_to_rgb(color_int):
    r = (color_int >> 16) & 255
    g = (color_int >> 8) & 255
    b = color_int & 255
    return [r, g, b]


def _rects_overlap_ratio(a, b):
    x0, y0 = max(a[0], b[0]), max(a[1], b[1])
    x1, y1 = min(a[2], b[2]), min(a[3], b[3])
    if x1 <= x0 or y1 <= y0:
        return 0.0
    inter = (x1 - x0) * (y1 - y0)
    area_b = (b[2] - b[0]) * (b[3] - b[1])
    return inter / area_b if area_b > 0 else 0.0


def _rect_area_ratio_to_page(bbox, page):
    x0, y0, x1, y1 = bbox
    area = max(x1 - x0, 0) * max(y1 - y0, 0)
    page_area = page.rect.width * page.rect.height
    return area / page_area if page_area > 0 else 0.0


def _cluster_rects(rects, pad=2):
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

    # Also drop TINY individual shapes — dash segments from decorative
    # dashed connector lines (e.g. arrows linking numbered sections) are
    # each just a few square points. Left in, a chain of dash-dash-dash
    # rects sitting close together bridges two unrelated icon clusters
    # (and everything between them) into one oversized merged region,
    # same mechanism as the background-bridging bug, different shape.
    # Real icons/chart bars/table borders are all comfortably larger
    # than this, so genuine graphics are unaffected.
    rects = [r for r in rects if r.get_area() > 9]

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
            continue
        if rect.width < 3 or rect.height < 3:
            continue
        regions.append(rect)
    return regions


def _ocr_lines_to_text_lines(ocr_lines):
    out = []
    for l in ocr_lines:
        size_pt = max((l["bbox"][3] - l["bbox"][1]) * 0.75, 6)
        out.append({
            "bbox": l["bbox"],
            "runs": [{
                "text": l["text"],
                "font": "Calibri",
                "size": round(size_pt, 1),
                "color": [90, 90, 90] if l["low_confidence"] else [15, 15, 15],
                "flags": 0,
            }],
        })
    return out


def parse_pdf(path: str) -> dict:
    doc = fitz.open(path)
    pages_out = []

    for page_index in range(doc.page_count):
        page = doc[page_index]
        page_dict = page.get_text("dict")

        raw_lines = []
        image_block_rects = []

        for block in page_dict.get("blocks", []):
            btype = block.get("type")
            if btype == 0:
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
                # alpha=True keeps empty space in the clip transparent instead
                # of opaque white. Without this, a graphic's bounding box (e.g.
                # a decorative dashed connector spanning a large diagonal
                # distance) renders as a solid white rectangle that visually
                # blocks any real text sitting inside that box but outside
                # the actual drawn shape.
                pix = page.get_pixmap(matrix=mat, clip=clip, alpha=True)
                images.append({
                    "bbox": rbbox,
                    "raw_bytes": pix.tobytes("png"),
                    "width": pix.width,
                    "height": pix.height,
                })
            except Exception:
                continue

        text_lines = []
        char_count = 0
        for line in raw_lines:
            if any(_rects_overlap_ratio(ib, line["bbox"]) > 0.7 for ib in image_regions_for_render):
                continue
            char_count += sum(len(r["text"]) for r in line["runs"])
            text_lines.append(line)

        ocr_confidence = None
        looks_scanned = char_count < 20 and len(images) > 0

        if looks_scanned and ocr_engine.is_available():
            # Full-page-ish images are the scan itself — OCR replaces
            # them with real text, so drop them to avoid drawing the
            # printed text twice (once baked into the scan, once as our
            # overlay — the same duplicate-text bug we hit with charts).
            full_page_images = [
                img for img in images if _rect_area_ratio_to_page(img["bbox"], page) > 0.6
            ]
            if full_page_images:
                try:
                    mat = fitz.Matrix(250 / 72, 250 / 72)
                    ocr_pix = page.get_pixmap(matrix=mat)
                    ocr_result = ocr_engine.ocr_page(ocr_pix, dpi=250)
                    if ocr_result["lines"]:
                        images = [img for img in images if img not in full_page_images]
                        text_lines.extend(_ocr_lines_to_text_lines(ocr_result["lines"]))
                        char_count = sum(len(l["text"]) for l in ocr_result["lines"])
                        ocr_confidence = ocr_result["avg_confidence"]
                except Exception as e:
                    print(f"[pdf_parser] OCR failed on page {page_index + 1}: {e}")

        pages_out.append({
            "number": page_index + 1,
            "width": page.rect.width,
            "height": page.rect.height,
            "text_lines": text_lines,
            "images": images,
            "is_scanned": looks_scanned,
            "ocr_confidence": ocr_confidence,  # None if not OCR'd
        })

    result = {"page_count": doc.page_count, "pages": pages_out}
    doc.close()
    return result
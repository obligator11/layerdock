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


def _point_in_bbox(px, py, bbox, pad=1):
    return (bbox[0] - pad) <= px <= (bbox[2] + pad) and (bbox[1] - pad) <= py <= (bbox[3] + pad)


def _cluster_rects(rects, pad=2):
    """
    Connected-components clustering by pairwise rect proximity. Returns
    each cluster's merged rect, member count, AND the member rects
    themselves (needed by table detection to tell which lines are
    horizontal vs vertical within one grid).
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
        clusters.append({"rect": rect, "count": len(group), "rects": group})
    return clusters


def _classify_line_rect(r, min_length=15, max_thickness=2.5):
    w, h = r.width, r.height
    if w >= min_length and h <= max_thickness:
        return "h"
    if h >= min_length and w <= max_thickness:
        return "v"
    return None


def _detect_tables(page, raw_lines):
    """
    Detect table grids from ruled lines (PDF vector drawing ops that are
    long-and-thin: horizontal or vertical rules). Groups of >=2 horizontal
    + >=2 vertical rules that intersect form a grid; text lines whose
    center falls inside a grid cell become that cell's content.

    Returns (tables, consumed_line_indices) — consumed_line_indices marks
    which entries in raw_lines were absorbed into a table cell, so the
    caller can exclude them from normal floating-textbox placement.
    """
    try:
        drawings = page.get_drawings()
    except Exception:
        return [], set()

    line_rects = []
    for d in drawings:
        r = d.get("rect")
        if not r or r.width <= 0 or r.height <= 0:
            continue
        if _classify_line_rect(r):
            line_rects.append(fitz.Rect(r))

    if len(line_rects) < 4:
        return [], set()

    page_area = page.rect.width * page.rect.height
    clusters = _cluster_rects(line_rects, pad=3)

    tables = []
    consumed_line_indices = set()

    for group in clusters:
        members = group["rects"]
        if len(members) < 4:
            continue
        rect = group["rect"]
        if (rect.get_area() / page_area if page_area > 0 else 0) > 0.9:
            continue  # a full-page border drawn with 4 rules, not a table

        h_ys, v_xs = set(), set()
        for r in members:
            kind = _classify_line_rect(r)
            if kind == "h":
                h_ys.add(round((r.y0 + r.y1) / 2, 1))
            elif kind == "v":
                v_xs.add(round((r.x0 + r.x1) / 2, 1))

        h_ys = sorted(h_ys)
        v_xs = sorted(v_xs)
        if len(h_ys) < 2 or len(v_xs) < 2:
            continue
        rows, cols = len(h_ys) - 1, len(v_xs) - 1
        if rows * cols < 2:
            continue  # a single bordered box, not a real table

        cells = []
        for ri in range(rows):
            y0, y1 = h_ys[ri], h_ys[ri + 1]
            row_cells = []
            for ci in range(cols):
                x0, x1 = v_xs[ci], v_xs[ci + 1]
                texts = []
                for idx, line in enumerate(raw_lines):
                    if idx in consumed_line_indices:
                        continue
                    lx0, ly0, lx1, ly1 = line["bbox"]
                    cx, cy = (lx0 + lx1) / 2, (ly0 + ly1) / 2
                    if x0 <= cx <= x1 and y0 <= cy <= y1:
                        texts.append(" ".join(r["text"] for r in line["runs"]))
                        consumed_line_indices.add(idx)
                row_cells.append(" ".join(texts).strip())
            cells.append(row_cells)

        col_widths = [v_xs[i + 1] - v_xs[i] for i in range(cols)]
        row_heights = [h_ys[i + 1] - h_ys[i] for i in range(rows)]

        tables.append({
            "bbox": [v_xs[0], h_ys[0], v_xs[-1], h_ys[-1]],
            "rows": rows,
            "cols": cols,
            "col_widths": col_widths,
            "row_heights": row_heights,
            "cells": cells,
        })

    return tables, consumed_line_indices


def _get_vector_regions(page, exclude_bboxes, min_area=150):
    try:
        drawings = page.get_drawings()
    except Exception:
        return []
    rects = [d["rect"] for d in drawings if d.get("rect") and d["rect"].width > 0 and d["rect"].height > 0]
    if not rects:
        return []

    page_area = page.rect.width * page.rect.height
    rects = [r for r in rects if (r.get_area() / page_area if page_area > 0 else 0) < 0.5]
    rects = [r for r in rects if r.get_area() > 9]

    # Exclude anything sitting inside an already-detected table region —
    # otherwise the same grid lines get rasterized again as a generic
    # "chart" on top of the real table we just built.
    def _in_excluded(r):
        cx, cy = (r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2
        return any(_point_in_bbox(cx, cy, b) for b in exclude_bboxes)

    rects = [r for r in rects if not _in_excluded(r)]
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

        # --- Table detection (before general text/image processing, so
        # cells consumed here are excluded from everything downstream) ---
        tables, consumed_line_indices = _detect_tables(page, raw_lines)
        table_bboxes = [t["bbox"] for t in tables]

        image_regions_for_render = [[r.x0, r.y0, r.x1, r.y1] for r in image_block_rects]

        for region in _get_vector_regions(page, table_bboxes):
            rbbox = [region.x0, region.y0, region.x1, region.y1]
            if any(_rects_overlap_ratio(ib, rbbox) > 0.6 for ib in image_regions_for_render):
                continue
            image_regions_for_render.append(rbbox)

        images = []
        for rbbox in image_regions_for_render:
            try:
                clip = fitz.Rect(rbbox)
                mat = fitz.Matrix(150 / 72, 150 / 72)
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
        for idx, line in enumerate(raw_lines):
            if idx in consumed_line_indices:
                continue  # absorbed into a table cell
            if any(_rects_overlap_ratio(ib, line["bbox"]) > 0.7 for ib in image_regions_for_render):
                continue
            char_count += sum(len(r["text"]) for r in line["runs"])
            text_lines.append(line)

        ocr_confidence = None
        looks_scanned = char_count < 20 and len(images) > 0

        if looks_scanned and ocr_engine.is_available():
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
            "tables": tables,
            "is_scanned": looks_scanned,
            "ocr_confidence": ocr_confidence,
        })

    result = {"page_count": doc.page_count, "pages": pages_out}
    doc.close()
    return result
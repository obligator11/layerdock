import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from backend.pdf_parser import parse_pdf

def main():
    if len(sys.argv) < 2:
        print("Usage: python debug_images.py <path_to_pdf> [--lines PAGE_NUM]")
        return

    pdf_path = sys.argv[1]
    result = parse_pdf(pdf_path)

    if "--lines" in sys.argv:
        page_num = int(sys.argv[sys.argv.index("--lines") + 1])
        page = result["pages"][page_num - 1]
        print(f"Page {page_num}: {len(page['text_lines'])} line entries, {len(page['images'])} image regions\n")
        for i, line in enumerate(page["text_lines"]):
            x0, y0, x1, y1 = line["bbox"]
            joined = "".join(r["text"] for r in line["runs"])
            fonts = {r["font"] for r in line["runs"]}
            print(f"[{i}] y0={y0:.2f} y1={y1:.2f} x0={x0:.2f} x1={x1:.2f} runs={len(line['runs'])} fonts={fonts}")
            print(f"     text: {joined!r}")
        return

    out_dir = os.path.join(os.path.dirname(__file__), "debug_output")
    os.makedirs(out_dir, exist_ok=True)
    print(f"Page count: {result['page_count']}")
    for page in result["pages"]:
        print(f"  Page {page['number']}: {len(page['text_lines'])} lines, {len(page['images'])} image regions")
        for idx, img in enumerate(page["images"]):
            fname = os.path.join(out_dir, f"page{page['number']}_img{idx}.png")
            with open(fname, "wb") as f:
                f.write(img["raw_bytes"])

if __name__ == "__main__":
    main()
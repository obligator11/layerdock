import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from backend.pdf_parser import parse_pdf

def main():
    if len(sys.argv) < 2:
        print("Usage: python debug_images.py <path_to_pdf>")
        return

    pdf_path = sys.argv[1]
    out_dir = os.path.join(os.path.dirname(__file__), "debug_output")
    os.makedirs(out_dir, exist_ok=True)

    print(f"Parsing: {pdf_path}")
    result = parse_pdf(pdf_path)
    print(f"Page count: {result['page_count']}")

    total_images = 0
    for page in result["pages"]:
        n_images = len(page["images"])
        n_text = len(page["text_blocks"])
        print(f"  Page {page['number']}: {n_text} text blocks, {n_images} image regions, is_scanned={page['is_scanned']}")

        for idx, img in enumerate(page["images"]):
            total_images += 1
            fname = os.path.join(out_dir, f"page{page['number']}_img{idx}.png")
            with open(fname, "wb") as f:
                f.write(img["raw_bytes"])
            print(f"    -> saved {fname}  bbox={img['bbox']}  {img['width']}x{img['height']}")

    print(f"\nTotal image regions found across all pages: {total_images}")
    print(f"Saved PNGs to: {out_dir}")

if __name__ == "__main__":
    main()
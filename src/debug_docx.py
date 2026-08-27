import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from backend.docx_builder import build_docx

def main():
    if len(sys.argv) < 2:
        print("Usage: python debug_docx.py <path_to_pdf>")
        return

    pdf_path = sys.argv[1]
    out_path = os.path.join(os.path.dirname(__file__), "debug_output.docx")

    def progress(cur, total):
        print(f"  page {cur}/{total}")

    result = build_docx(pdf_path, out_path, progress_cb=progress)
    print(f"\nSaved: {result['output_path']}")

if __name__ == "__main__":
    main()
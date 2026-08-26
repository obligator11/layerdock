# LayerDock

A native desktop app that converts PDFs into **editable, pixel-faithful** Word
documents — text position, fonts, colors, images, and tables preserved,
including OCR for scanned pages. Offline-first, cross-platform (Windows /
macOS / Linux).

Built with Python end-to-end:
- **App shell:** [pywebview](https://pywebview.flowrl.com/) — native window, no browser tab
- **Frontend:** HTML/CSS/JS (custom, no framework yet)
- **PDF parsing:** PyMuPDF
- **DOCX generation:** python-docx + raw OOXML
- **OCR:** Tesseract via pytesseract

## Status

🚧 **Step 1 of 8** — project scaffold + app shell UI. No conversion logic yet.
See [`docs/ROADMAP.md`](docs/ROADMAP.md) for the full build plan.

## Running it locally

Environment is managed with Anaconda/Miniconda, named `layerdock`.

```bash
conda env create -f environment.yml
conda activate layerdock
cd src
python main.py
```

If you change `requirements.txt` later and need to sync an existing env:

```bash
conda activate layerdock
pip install -r requirements.txt
```

> Note: `pywebview` needs a system webview backend. Windows and macOS have
> one built in. On Linux, install `python3-gi`, `gir1.2-webkit2-4.1` (or
> your distro's equivalent) first.

## Project layout

```
layerdock/
├── src/
│   ├── main.py            # app entry point
│   ├── backend/
│   │   ├── api.py         # JS <-> Python bridge
│   │   ├── pdf_parser.py  # (Step 2)
│   │   ├── docx_builder.py# (Step 3)
│   │   └── ocr_engine.py  # (Step 4)
│   └── frontend/
│       ├── index.html
│       ├── style.css
│       └── app.js
├── docs/
│   └── ROADMAP.md
├── environment.yml        # conda env spec (env name: layerdock)
└── requirements.txt
```

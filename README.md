# LayerDock

**LayerDock** is a native, offline-first Windows desktop application that converts PDFs into **editable, pixel-faithful Word documents** — preserving text position, fonts, colors, images, charts, and tables, with OCR support for scanned pages.

## Download

Grab the latest installer from the [Releases page](https://github.com/obligator11/layerdock/releases) — `LayerDock-Setup-x.x.x.exe`. No Python, no dependencies, Tesseract OCR is bundled in.

## Features

- **Pixel-perfect layout** — text, images, and charts land at their original PDF position, not reflowed
- **Real editable tables** — detected table grids become actual Word table objects, not flattened images
- **OCR for scanned pages** — bundled Tesseract recovers selectable text from image-only pages, fully offline
- **Batch conversion** — queue multiple PDFs, Convert All / Download All, per-file cancel, end-of-batch summary
- **Conversion history** — local SQLite log of every conversion, with quick access to outputs
- **Fully offline** — no document content ever leaves your device
- **Native app** — real installer, desktop shortcut, no browser tab

## Screenshots

*(add a screenshot or two of the Convert view and a converted document here)*

## Technology Stack

| Component       | Technology                                 |
| --------------- | ------------------------------------------- |
| App Shell       | [pywebview](https://pywebview.flowrl.com/)  |
| Frontend        | HTML / CSS / JavaScript                     |
| PDF Parsing     | PyMuPDF                                     |
| DOCX Generation | python-docx + raw OOXML                     |
| OCR             | Tesseract + pytesseract (bundled)           |
| Local Storage   | SQLite                                      |
| Packaging       | PyInstaller + Inno Setup                    |

## Development Status

Core conversion engine and native packaging are complete and working. Remaining polish items are tracked in [`docs/ROADMAP.md`](docs/ROADMAP.md).

### Done
- [x] Native app shell (pywebview) with custom UI
- [x] PDF parsing (text, images, vector graphics, tables)
- [x] DOCX generation with absolute positioning
- [x] Image & chart embedding (rasterized, correctly placed)
- [x] Real editable Word tables
- [x] OCR for scanned/image-only pages
- [x] Batch queue: convert all, download all, cancel, delete, history
- [x] Local SQLite history + settings
- [x] Windows installer with bundled Tesseract, desktop shortcut, branded wizard

### In progress
- [ ] Side-by-side PDF vs. DOCX review UI with automated visual-diff flagging
- [ ] macOS / Linux packaging
- [ ] Code signing

## Running from source (for development)

LayerDock uses **Anaconda/Miniconda** for environment management.

```bash
git clone https://github.com/obligator11/layerdock.git
cd layerdock
conda env create -f environment.yml
conda activate layerdock
cd src
python main.py
```

If `requirements.txt` changes after the environment already exists:
```bash
conda activate layerdock
pip install -r requirements.txt
```

### OCR (scanned PDFs) — dev only

The packaged installer bundles Tesseract automatically. When running from source, install it separately:
- **Windows:** [UB-Mannheim build](https://github.com/UB-Mannheim/tesseract/wiki) (default install path works out of the box)
- **macOS:** `brew install tesseract`
- **Linux:** `sudo apt install tesseract-ocr`

Check **Settings → OCR engine (Tesseract)** in the app to confirm detection.

### Linux (dev) — pywebview backend

```bash
sudo apt install python3-gi gir1.2-webkit2-4.1
```
Exact packages vary by distro.

## Building the installer yourself

```bash
pip install pyinstaller
pyinstaller layerdock.spec --clean --noconfirm
# then compile installer.iss with Inno Setup (https://jrsoftware.org/isdl.php)
```
Output lands in `installer_output/LayerDock-Setup-x.x.x.exe`.

## Project Structure

```text
layerdock/
├── src/
│   ├── main.py
│   ├── backend/
│   │   ├── api.py
│   │   ├── pdf_parser.py
│   │   ├── docx_builder.py
│   │   ├── ocr_engine.py
│   │   └── db.py
│   └── frontend/
│       ├── index.html
│       ├── style.css
│       ├── app.js
│       └── assets/
├── vendor/                 # bundled Tesseract (not tracked in git)
├── docs/ROADMAP.md
├── layerdock.spec           # PyInstaller build config
├── installer.iss            # Inno Setup installer script
├── environment.yml
└── requirements.txt
```

## Why this is hard

PDFs are fixed-layout; Word documents are structured for editing. LayerDock treats conversion as a **document reconstruction problem**: recovering text position/font/color, distinguishing real tables from decorative graphics, telling backgrounds apart from content, and rebuilding all of it as genuinely editable Word objects rather than a flattened picture of the page.

## Privacy

All processing happens locally. No document content is uploaded anywhere, with or without an internet connection.

## License

License information will be added ahead of the first public release.

---

**LayerDock** — pixel-perfect PDFs, without losing the ability to edit them.

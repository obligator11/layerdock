# LayerDock

**LayerDock** is a native, offline-first desktop application for converting PDFs into **editable, pixel-faithful Word documents**.

The goal is to preserve the original PDF's visual structure as closely as possible — including text positioning, fonts, colors, images, tables, and document layout — while producing a genuinely editable `.docx` file.

> 🚧 **Under active development:** LayerDock is currently in the early stages of development. The project scaffold and native application shell are in place; PDF-to-DOCX conversion is not implemented yet.

## ✨ Vision

PDFs are designed primarily for fixed-layout viewing, while Word documents are designed for editing. LayerDock aims to bridge that gap without sacrificing the original document's appearance.

The long-term goal is to support:

* 📄 **Pixel-faithful PDF → DOCX conversion**
* 📝 Editable text with preserved positioning
* 🔤 Font and text-style preservation
* 🎨 Text and background colors
* 🖼️ Image extraction and placement
* 📊 Table reconstruction
* 🔍 OCR for scanned and image-based PDFs
* 📴 Fully offline processing
* 🖥️ Windows, macOS, and Linux support
* ⚡ Native desktop experience without requiring a browser

## 🛠️ Technology Stack

LayerDock is being built entirely with Python on the backend, with a lightweight web-based UI running inside a native desktop window.

| Component       | Technology                                 |
| --------------- | ------------------------------------------ |
| App Shell       | [pywebview](https://pywebview.flowrl.com/) |
| Frontend        | HTML / CSS / JavaScript                    |
| PDF Parsing     | PyMuPDF                                    |
| DOCX Generation | python-docx + raw OOXML                    |
| OCR             | Tesseract + pytesseract                    |
| Environment     | Conda / Miniconda                          |
| Architecture    | Python backend + JS frontend               |

## 🚧 Development Status

**Current stage: Step 1 of 8 — Project Scaffold & App Shell**

The project is intentionally under construction.

### Completed

* [x] Initial project structure
* [x] Conda environment configuration
* [x] Native application shell
* [x] Initial frontend UI
* [x] Python ↔ JavaScript bridge foundation

### In Progress

* [ ] PDF document parsing
* [ ] Layout and typography extraction
* [ ] DOCX document reconstruction
* [ ] Image extraction and positioning
* [ ] Table reconstruction
* [ ] OCR pipeline
* [ ] Advanced formatting preservation
* [ ] Cross-platform packaging
* [ ] End-to-end conversion pipeline
* [ ] Testing and optimization

See [`docs/ROADMAP.md`](docs/ROADMAP.md) for the complete development plan.

## 📁 Project Structure

```text
layerdock/
├── src/
│   ├── main.py                 # Application entry point
│   ├── backend/
│   │   ├── api.py              # JavaScript ↔ Python bridge
│   │   ├── pdf_parser.py       # PDF parsing and layout extraction
│   │   ├── docx_builder.py     # DOCX generation and reconstruction
│   │   └── ocr_engine.py       # OCR processing
│   └── frontend/
│       ├── index.html           # Application UI
│       ├── style.css            # UI styling
│       └── app.js               # Frontend logic
├── docs/
│   └── ROADMAP.md              # Development roadmap
├── environment.yml             # Conda environment specification
├── requirements.txt             # Python dependencies
└── README.md
```

## 🚀 Running Locally

LayerDock currently uses **Anaconda/Miniconda** for environment management.

### 1. Clone the repository

```bash
git clone https://github.com/obligator11/layerdock.git
cd layerdock
```

### 2. Create the environment

```bash
conda env create -f environment.yml
```

### 3. Activate it

```bash
conda activate layerdock
```

### 4. Start the application

```bash
cd src
python main.py
```

### Updating dependencies

If `requirements.txt` changes after the environment has already been created:

```bash
conda activate layerdock
pip install -r requirements.txt
```

### Linux requirements

`pywebview` requires a system WebView backend.

On Debian/Ubuntu-based distributions, you may need:

```bash
sudo apt install python3-gi gir1.2-webkit2-4.1
```

The exact packages may vary depending on your Linux distribution.

## 🔬 Core Engineering Challenge

The difficult part of LayerDock isn't simply extracting text from a PDF.

The main challenge is reconstructing the **visual and structural relationships** inside a fixed-layout document and translating them into an editable Word document.

A successful conversion needs to reason about things such as:

* Text coordinates and bounding boxes
* Font families and sizes
* Font weight and styling
* Line spacing and paragraph structure
* Relative positioning
* Images and their placement
* Tables and cell boundaries
* Colors and backgrounds
* Multiple columns
* Headers and footers
* Overlapping elements
* Scanned pages requiring OCR

LayerDock therefore treats PDF conversion as a **document reconstruction problem**, rather than a simple text extraction task.

## 🔒 Offline-First

LayerDock is designed around local processing.

Documents are intended to remain on the user's machine during conversion, making the application suitable for documents where privacy and confidentiality matter.

No cloud-based conversion service is required for the core pipeline.

## 🗺️ Roadmap

LayerDock is being developed incrementally:

```text
Step 1  → Project Scaffold & App Shell       🚧
Step 2  → PDF Parsing & Layout Extraction    ⏳
Step 3  → DOCX Reconstruction                ⏳
Step 4  → OCR Pipeline                       ⏳
Step 5  → Advanced Layout Preservation       ⏳
Step 6  → Conversion Quality & Edge Cases    ⏳
Step 7  → Testing & Cross-Platform Support   ⏳
Step 8  → Packaging & Release                ⏳
```

The roadmap will evolve as the conversion engine is developed and real-world PDF edge cases are addressed.

## 📌 Current Limitations

Because LayerDock is still under construction:

* PDF conversion is **not available yet**
* OCR is **not implemented yet**
* DOCX reconstruction is **not implemented yet**
* Cross-platform packaging is **not ready**
* API and internal architecture may change during development

## 🤝 Contributing

LayerDock is currently in an early development phase. The architecture and APIs are expected to change significantly as the core conversion engine is implemented.

Contributions, ideas, bug reports, and technical discussion will become increasingly useful as the project approaches a functional release.

## 📄 License

License information will be added as the project approaches its first public release.

---

**LayerDock** — *Turning fixed-layout PDFs into editable documents without losing the layout.*

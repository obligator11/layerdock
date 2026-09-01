<div align="center">

# LayerDock

### PDF → Editable Word, without destroying the layout.

Convert PDFs into editable `.docx` documents while preserving text positioning, tables, images, charts, and page structure — with OCR for scanned PDFs and **100% local processing**.

[![Download](https://img.shields.io/github/v/release/obligator11/layerdock?display_name=tag&label=Download&color=7c5cff)](https://github.com/obligator11/layerdock/releases/latest)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%2B-blue)](#system-requirements)
[![Offline](https://img.shields.io/badge/processing-100%25%20offline-34e08a)](#privacy)
[![GitHub Stars](https://img.shields.io/github/stars/obligator11/layerdock?style=flat)](https://github.com/obligator11/layerdock/stargazers)

**No account. No upload. No cloud processing.**

[**Download LayerDock**](https://github.com/obligator11/layerdock/releases/latest) · [Report a Bug](https://github.com/obligator11/layerdock/issues) · [Request a Feature](https://github.com/obligator11/layerdock/issues)

</div>

---

## Why LayerDock?

PDFs are great for preserving how a document **looks**, but terrible when you need to actually **edit** that document.

Most PDF-to-Word workflows force a trade-off:

- Make the text editable → the layout gets mangled.
- Preserve the appearance → the page becomes a collection of images or otherwise difficult-to-edit elements.
- Upload the document online → your files leave your computer.

**LayerDock takes a different approach.**

Instead of simply flattening a PDF into a Word page, LayerDock analyzes the document and rebuilds it as an editable Word document.

The goal is simple:

> **Get your PDF back as a document you can actually work with.**

---

## What LayerDock does

LayerDock converts PDFs into `.docx` files while reconstructing the document's visual structure.

### ✏️ Editable text

Text is placed into the generated Word document according to its position and formatting rather than simply inserting the PDF as an image.

### 📊 Real editable tables

Detected tables are rebuilt as actual Word tables.

That means you can:

- Click inside cells
- Edit cell contents
- Add or remove information
- Select rows and columns
- Continue working with the table in Word

The table is not just a screenshot.

### 🖼️ Images & charts

Images and graphical elements are extracted and positioned in the generated document according to their location in the original PDF.

### 🔍 OCR for scanned PDFs

Image-only and scanned PDFs can be processed with built-in OCR.

LayerDock runs OCR locally to recover selectable and editable text instead of leaving the page as a picture.

Pages or regions where recognition may need additional checking can be flagged so you know where to review the result.

### 📚 Batch conversion

Have more than one PDF?

Queue multiple files and convert them together.

LayerDock provides per-file progress, cancellation, and a completion summary so you can process a collection of documents without repeating the workflow manually.

### 🔒 100% local processing

Your documents stay on your machine.

There is no upload step and no cloud conversion service involved in the conversion pipeline.

**Your PDFs don't need to leave your computer.**

---

## Screenshots

> **Coming soon:** real screenshots from LayerDock.

### The application

<!-- Replace this placeholder with your application screenshot -->

![LayerDock application](docs/screenshots/app.png)

### PDF → Word

<!-- Replace this placeholder with a before/after screenshot -->

![LayerDock PDF to Word conversion](docs/screenshots/before-after.png)

### Batch conversion

<!-- Replace this placeholder with a screenshot of multiple PDFs being converted -->

![LayerDock batch conversion](docs/screenshots/batch.png)

> If you don't have the `docs/screenshots/` folder yet, add it and place your screenshots there.

---

## Get LayerDock

### Windows

Download the latest installer from GitHub Releases:

**[⬇️ Download LayerDock for Windows](https://github.com/obligator11/layerdock/releases/latest)**

The installer is designed to be standalone. OCR support is included with the application, so there is no separate OCR package or runtime that you need to install.

### Installation

1. Download the latest `LayerDock` installer.
2. Run the installer.
3. Complete the installation.
4. Launch LayerDock.
5. Select or drag in your PDF.
6. Click **Convert**.

That's it.

---

## How to use

### Convert a single PDF

1. Open LayerDock.
2. Drag a PDF onto the application or click **Select PDF files**.
3. Choose **Convert**.
4. LayerDock generates an editable `.docx`.
5. Open the resulting Word document and continue editing.

### Convert multiple PDFs

1. Add multiple PDF files.
2. Choose **Convert All**.
3. Monitor the progress of each file.
4. Find the generated `.docx` files in the output location.
5. Use **Reveal** when you want to open the output location.

---

## What makes LayerDock different?

| Feature | LayerDock |
|---|:---:|
| PDF → editable DOCX | ✅ |
| Editable text | ✅ |
| Editable Word tables | ✅ |
| Images & charts | ✅ |
| OCR for scanned PDFs | ✅ |
| Batch conversion | ✅ |
| Local processing | ✅ |
| Internet required for conversion | ❌ |
| Account required | ❌ |
| Upload your PDF to a conversion server | ❌ |
| Windows standalone installer | ✅ |

### The important difference

LayerDock is not trying to create a Word document that merely **looks like a PDF**.

It attempts to reconstruct the document's content and layout so that you can continue editing it in Word.

That distinction matters most with documents containing:

- Tables
- Images
- Charts
- Multiple columns
- Headers and footers
- Mixed text and graphics
- Scanned pages

---

## Privacy

LayerDock is designed around local document processing.

### Your files stay local

PDF parsing, document reconstruction, and OCR run on your computer.

There is no upload step in the conversion workflow.

### No account required

You don't need to create an account just to convert a document.

### No cloud dependency

LayerDock does not require an online conversion service to perform its core PDF → Word workflow.

**If the document is confidential, you can convert it without sending the PDF to a third-party conversion server.**

---

## System requirements

- **Operating system:** Windows 10 or later
- **Architecture:** 64-bit
- **Internet:** Not required for the core conversion workflow
- **Additional software:** None required for the standalone installer

---

## Supported documents

LayerDock is designed for PDFs containing a mixture of:

- Text
- Tables
- Images
- Charts
- Multiple layout regions
- Scanned pages
- Image-based text

### A note about PDF conversion

PDF is fundamentally a presentation format, and real-world PDFs can be extremely inconsistent.

A PDF generated by Microsoft Word can behave very differently from:

- A scanned book
- A digitally generated invoice
- A government form
- A PDF exported from design software
- A document containing unusual fonts
- A heavily layered or complex PDF

LayerDock aims for high-fidelity reconstruction, but **no PDF converter can guarantee perfect reconstruction for every PDF ever created**.

If you find a document that doesn't convert correctly, please report it so it can be investigated and improved.

---

## Report a difficult PDF

This is one of the most useful ways you can help improve LayerDock.

If you find a PDF that produces a poor result, open an issue and include:

- What kind of PDF it is
- Whether it is scanned or digitally generated
- Whether it contains tables, images, columns, forms, etc.
- What went wrong
- What you expected to happen
- Screenshots of the original and generated document when possible

### Example

```text
PDF type:
Scanned / Digital / Mixed

Content:
Tables + images + multiple columns

Problem:
The second table is shifted down by approximately 2 cm.

Expected:
The table should remain aligned with the surrounding text.

Actual:
The table overlaps the paragraph below it.
```

Real-world PDFs are full of edge cases. Those edge cases are valuable for improving the converter.

**[Open an issue →](https://github.com/obligator11/layerdock/issues)**

---

## Roadmap

LayerDock is currently at **v1.0.0**.

Future improvements will be driven heavily by real-world documents and user feedback.

Possible areas of improvement include:

- [ ] Improved handling of complex PDF layouts
- [ ] Better font matching
- [ ] More robust table reconstruction
- [ ] Improved OCR accuracy and detection
- [ ] Better headers and footers
- [ ] More PDF edge-case coverage
- [ ] Additional conversion controls
- [ ] Continued performance improvements

Have an idea?

**[Request a feature →](https://github.com/obligator11/layerdock/issues)**

---

## Built with

LayerDock is built with:

- **Python**
- **PyWebView**
- **JavaScript**
- **CSS**
- **Inno Setup**

The application is packaged as a Windows standalone installer.

---

## Project structure

```text
LayerDock/
├── docs/
├── src/
├── .gitignore
├── LICENSE.txt
├── README.md
├── environment.yml
├── installer.iss
└── requirements.txt
```

---

## Contributing

Found a bug? Have a PDF that breaks the converter? Have an idea that would make LayerDock more useful?

Contributions, testing, issue reports, and real-world PDF examples are welcome.

Before opening a pull request for a large change, consider opening an issue first so the approach can be discussed.

---

## License

LayerDock is distributed under the license included in [`LICENSE.txt`](LICENSE.txt).

Please read the license before redistributing or modifying the software.

---

<div align="center">

## PDF → Word should mean editable.

Not a screenshot inside a `.docx`.

**[Download LayerDock](https://github.com/obligator11/layerdock/releases/latest)**

If LayerDock saves you time, consider giving the project a ⭐ on GitHub.

[GitHub](https://github.com/obligator11/layerdock) · [Issues](https://github.com/obligator11/layerdock/issues) · [Releases](https://github.com/obligator11/layerdock/releases)

</div>

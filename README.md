<div align="center">

# LayerDock

**Convert PDFs into fully editable Word documents — without losing the layout.**

[![Download](https://img.shields.io/badge/download-latest%20release-7c5cff)](https://github.com/obligator11/layerdock/releases/latest)
[![Platform](https://img.shields.io/badge/platform-Windows-blue)]()
[![Offline](https://img.shields.io/badge/processing-100%25%20offline-34e08a)]()

</div>

---

## What it does

Open any PDF in LayerDock and get back a `.docx` file where the text, images, charts, and tables sit exactly where they did in the original — and every one of them is a real, editable Word object, not a flattened screenshot of the page.

That distinction is the entire point of this app. Most converters either mangle your layout to make the text editable, or preserve the layout by turning everything into pictures you can't touch. LayerDock does neither: it rebuilds the document.

## Get it

**[Download the installer](https://github.com/obligator11/layerdock/releases/latest)** — one file, no setup required. OCR support is built in; nothing else to install.

Run the installer, keep the desktop shortcut checked, launch LayerDock, and you're converting.

## How to use it

1. Drop a PDF onto the window, or click **Select PDF files**
2. Hit **Convert** — or add several files and hit **Convert All**
3. Find the finished `.docx` in the output folder next to your source file (or click **Reveal**)

That's it. No accounts, no upload step, no internet required at any point.

## What makes it different

**Real tables, not pictures of tables.** LayerDock detects a table's actual grid — rows, columns, cell boundaries — and rebuilds it as a genuine Word table. Click into any cell and edit it like you would in any document you typed yourself.

**Charts and images land in the right spot.** Every graphic is placed at its exact original coordinates, sized correctly, and layered so it never blocks text sitting near or under it.

**Scanned pages get real text back.** Feed it an image-only PDF and LayerDock runs OCR locally to recover selectable, editable text — no picture-of-text left behind, and pages where the recognition was uncertain get flagged so you know exactly what to double-check.

**Everything stays on your machine.** There's no server in this pipeline. Parsing, conversion, and OCR all happen locally. Nothing about your documents is ever transmitted anywhere.

**Built for volume.** Queue up a folder of PDFs, convert the whole batch, track progress per file, cancel anything that's taking too long, and get a summary the moment it's done.

## Screenshots

*(drop a couple of screenshots here — the Convert screen with a batch running, and a before/after of a converted document)*

## System requirements

Windows 10 or later, 64-bit. Nothing else — the installer includes everything the app needs to run standalone.

## Privacy

LayerDock has no network calls in its conversion pipeline. Your PDFs never leave your computer, whether or not you're connected to the internet.

## Feedback and issues

Found a document that doesn't convert cleanly, or hit a bug? Open an issue on this repo with the general nature of the file (scanned, has tables, multi-column, etc.) — real-world PDFs are wildly inconsistent, and edge cases are how this gets better.

## License

See [LICENSE.txt](LICENSE.txt).

---

<div align="center">

Built for people who need their PDFs back as documents they can actually work with.

</div>

# LayerDock Roadmap

Each step ships as its own commit (and, once contributors are added, its own
PR) so progress stays reviewable.

- [x] **Step 1 — Project scaffold + app shell**
      pywebview window, dark next-gen UI (sidebar, drop zone, mock queue),
      Python↔JS bridge with a `ping()` health check and native file picker.
- [ ] **Step 2 — PDF parsing engine**
      PyMuPDF extraction of text runs (with position/font/color), images,
      and vector paths into a structured intermediate format (JSON).
- [ ] **Step 3 — Basic DOCX generation**
      Turn the intermediate format into a real `.docx`: positioned text
      boxes/frames, embedded images, matched fonts where possible.
- [ ] **Step 4 — OCR pipeline**
      Detect image-only pages, run Tesseract, overlay recovered text in the
      correct position, flag low-confidence regions.
- [ ] **Step 5 — Table detection & reconstruction**
      Rebuild ruled/aligned tables as real Word tables, not text boxes.
- [ ] **Step 6 — Batch queue + job manager**
      Background worker pool, per-file progress, pause/resume, wired to the
      existing queue UI.
- [ ] **Step 7 — Review UX**
      Side-by-side PDF vs DOCX preview, visual diff (SSIM) flagging.
- [ ] **Step 8 — Packaging**
      PyInstaller builds + installers for Windows/macOS/Linux, auto-update.

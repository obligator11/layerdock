import os
import json
import threading
import subprocess
import sys
import webview


class Api:
    def __init__(self):
        self._window = None

    def set_window(self, window):
        self._window = window

    def select_files(self):
        if self._window is None:
            return []
        file_types = ("PDF files (*.pdf)",)
        result = self._window.create_file_dialog(
            webview.FileDialog.OPEN, allow_multiple=True, file_types=file_types
        )
        if not result:
            return []
        return [
            {"path": p, "name": os.path.basename(p), "size": os.path.getsize(p)}
            for p in result
        ]

    def ping(self):
        return {"ok": True, "message": "LayerDock backend is running"}

    def parse_pdf(self, path):
        from backend.pdf_parser import parse_pdf
        try:
            result = parse_pdf(path)
            total_images = sum(len(p["images"]) for p in result["pages"])
            scanned_pages = sum(1 for p in result["pages"] if p["is_scanned"])
            return {
                "ok": True,
                "page_count": result["page_count"],
                "image_count": total_images,
                "scanned_pages": scanned_pages,
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def convert_pdf(self, path, job_id):
        """Kicks off conversion in a background thread and returns immediately.
        Progress/completion is pushed to JS via evaluate_js callbacks."""
        threading.Thread(target=self._convert_worker, args=(path, job_id), daemon=True).start()
        return {"ok": True, "started": True}

    def _convert_worker(self, path, job_id):
        from backend.docx_builder import build_docx
        try:
            output_dir = os.path.join(os.path.dirname(path), "LayerDock Output")
            try:
                os.makedirs(output_dir, exist_ok=True)
            except Exception:
                output_dir = os.path.dirname(path)  # fallback if not writable

            base = os.path.splitext(os.path.basename(path))[0]
            output_path = os.path.join(output_dir, base + ".docx")

            def progress_cb(current, total):
                pct = int(current / total * 100)
                self._window.evaluate_js(
                    f"window.onConvertProgress({json.dumps(job_id)}, {pct})"
                )

            result = build_docx(path, output_path, progress_cb=progress_cb)
            self._window.evaluate_js(
                f"window.onConvertDone({json.dumps(job_id)}, {json.dumps(result['output_path'])})"
            )
        except Exception as e:
            self._window.evaluate_js(
                f"window.onConvertError({json.dumps(job_id)}, {json.dumps(str(e))})"
            )

    def open_folder(self, path):
        """Reveal a folder in the OS file explorer — used by 'Download All'."""
        try:
            folder = path if os.path.isdir(path) else os.path.dirname(path)
            if sys.platform == "win32":
                os.startfile(folder)
            elif sys.platform == "darwin":
                subprocess.run(["open", folder])
            else:
                subprocess.run(["xdg-open", folder])
            return {"ok": True}
        except Exception as e:
            return {"ok": False, "error": str(e)}
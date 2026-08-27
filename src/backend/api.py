import os
import json
import threading
import subprocess
import sys
import webview

from backend import db


class Api:
    def __init__(self):
        self._window = None
        db.init_db()

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
        threading.Thread(target=self._convert_worker, args=(path, job_id), daemon=True).start()
        return {"ok": True, "started": True}

    def _resolve_output_dir(self, source_path):
        override = db.get_setting("output_folder_override")
        if override and os.path.isdir(override):
            return override
        output_dir = os.path.join(os.path.dirname(source_path), "LayerDock Output")
        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception:
            output_dir = os.path.dirname(source_path)
        return output_dir

    def _convert_worker(self, path, job_id):
        from backend.docx_builder import build_docx
        source_name = os.path.basename(path)
        try:
            output_dir = self._resolve_output_dir(path)
            base = os.path.splitext(source_name)[0]
            output_path = os.path.join(output_dir, base + ".docx")

            def progress_cb(current, total):
                pct = int(current / total * 100)
                self._window.evaluate_js(
                    f"window.onConvertProgress({json.dumps(job_id)}, {pct})"
                )

            result = build_docx(path, output_path, progress_cb=progress_cb)
            db.add_history_entry(
                source_name, path, result["output_path"], result["page_count"], "done",
            )
            self._window.evaluate_js(
                f"window.onConvertDone({json.dumps(job_id)}, {json.dumps(result['output_path'])})"
            )
        except Exception as e:
            db.add_history_entry(source_name, path, None, None, "error", str(e))
            self._window.evaluate_js(
                f"window.onConvertError({json.dumps(job_id)}, {json.dumps(str(e))})"
            )

    def open_folder(self, path):
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

    # --- History ---

    def get_history(self):
        try:
            return {"ok": True, "items": db.get_history()}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def clear_history(self):
        try:
            db.clear_history()
            return {"ok": True}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # --- Settings ---

    def get_settings(self):
        try:
            return {
                "ok": True,
                "output_folder_override": db.get_setting("output_folder_override"),
                "data_dir": db.get_app_data_dir(),
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def choose_output_folder_override(self):
        if self._window is None:
            return {"ok": False, "error": "no window"}
        result = self._window.create_file_dialog(webview.FileDialog.FOLDER)
        if not result:
            return {"ok": False, "cancelled": True}
        folder = result[0]
        db.set_setting("output_folder_override", folder)
        return {"ok": True, "output_folder_override": folder}

    def reset_output_folder_override(self):
        db.delete_setting("output_folder_override")
        return {"ok": True}

    def open_data_folder(self):
        return self.open_folder(db.get_app_data_dir())
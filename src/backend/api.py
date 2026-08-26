"""
Api: exposed to the frontend JS via pywebview's js_api bridge.
Step 1: file selection + a mock queue only. Real conversion logic
(pdf_parser, docx_builder, ocr_engine) gets wired in from Step 2 onward.
"""
import os
import webview


class Api:
    def __init__(self):
        self._window = None

    def set_window(self, window):
        self._window = window

    def select_files(self):
        """Open a native file picker for one or more PDFs."""
        if self._window is None:
            return []
        file_types = ("PDF files (*.pdf)",)
        result = self._window.create_file_dialog(
            webview.OPEN_DIALOG, allow_multiple=True, file_types=file_types
        )
        if not result:
            return []
        return [
            {"path": p, "name": os.path.basename(p), "size": os.path.getsize(p)}
            for p in result
        ]

    def choose_export_folder(self):
        if self._window is None:
            return None
        result = self._window.create_file_dialog(webview.FOLDER_DIALOG)
        return result[0] if result else None

    def ping(self):
        # simple sanity check the JS<->Python bridge is alive
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

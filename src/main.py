"""
LayerDock — PDF to DOCX Converter
App shell entry point (Step 1: UI shell only, no conversion logic yet).
"""
import os
import webview

from backend.api import Api

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend")
INDEX_HTML = os.path.join(FRONTEND_DIR, "index.html")


def main():
    api = Api()
    window = webview.create_window(
        title="LayerDock",
        url=INDEX_HTML,
        js_api=api,
        width=1180,
        height=760,
        min_size=(900, 600),
        background_color="#0b0d10",
        frameless=False,  # custom title bar comes in a later step
    )
    api.set_window(window)
    webview.start(debug=False)


if __name__ == "__main__":
    main()

import os
import sys
import webview

from backend.api import Api


def _get_base_dir():
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))

FRONTEND_DIR = os.path.join(_get_base_dir(), "frontend")
INDEX_HTML = os.path.join(FRONTEND_DIR, "index.html")

def main():
    icon_path = os.path.join(FRONTEND_DIR, "assets", "logo.ico")
    api = Api()
    window = webview.create_window(
        title="LayerDock",
        url=INDEX_HTML,
        js_api=api,
        width=1180,
        height=760,
        min_size=(900, 600),
        background_color="#0b0d10",
        frameless=False,
    )
    api.set_window(window)
    webview.start(debug=False, icon=icon_path if os.path.exists(icon_path) else None)


if __name__ == "__main__":
    main()

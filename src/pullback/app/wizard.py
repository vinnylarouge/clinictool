"""The intro setup wizard: a localhost web page that walks the user through how
to use pullback and saves their AI provider and API key.

Stdlib http.server only, bound to 127.0.0.1, so nothing is exposed off the
machine and no framework is pulled in. The page is served by GET; the form posts
to /save, which writes the config and shows the success state, then the server
shuts down.
"""

from __future__ import annotations

import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from pullback.llm.providers import PROVIDER_ORDER
from pullback.render.onboarding import render_onboarding
from pullback.store.config import config_from_form, load_config, mask_key, save_config


def _initial_selected() -> str:
    """Pre-select the saved provider if there is one, else the first option."""

    saved = load_config()
    if saved and saved.provider:
        return saved.provider
    return PROVIDER_ORDER[0].key


def _make_handler(state: dict):
    selected = _initial_selected()

    class WizardHandler(BaseHTTPRequestHandler):
        def log_message(self, *args):  # silence default stderr logging
            pass

        def _html(self, body: str, status: int = 200) -> None:
            data = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):  # noqa: N802 (stdlib naming)
            if urlparse(self.path).path in ("/", "/index.html"):
                self._html(render_onboarding(interactive=True, selected_provider=selected))
            else:
                self.send_response(404)
                self.end_headers()

        def do_POST(self):  # noqa: N802
            if urlparse(self.path).path != "/save":
                self.send_response(404)
                self.end_headers()
                return
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length).decode("utf-8")
            form = {k: v[0] for k, v in parse_qs(raw).items()}
            try:
                cfg = config_from_form(form)
                path = save_config(cfg)
                state["saved_path"] = path
                self._html(
                    render_onboarding(
                        interactive=True,
                        saved=True,
                        saved_provider=_label(cfg.provider),
                        config_path=str(path),
                        masked_key=mask_key(cfg.api_key),
                    )
                )
                state["done"].set()
            except Exception as exc:  # bad/missing key, unknown provider
                self._html(
                    render_onboarding(
                        interactive=True,
                        selected_provider=form.get("provider", selected),
                        error=str(exc),
                        form=form,
                    ),
                    status=400,
                )

    return WizardHandler


def _label(provider_key: str) -> str:
    for p in PROVIDER_ORDER:
        if p.key == provider_key:
            return p.label
    return provider_key


def run_wizard(
    *, host: str = "127.0.0.1", port: int = 0, open_browser: bool = True
) -> Path | None:
    """Serve the setup wizard until a config is saved, then stop.

    Returns the path the config was written to, or None if interrupted.
    """

    done = threading.Event()
    state: dict = {"done": done, "saved_path": None}
    httpd = HTTPServer((host, port), _make_handler(state))
    actual_port = httpd.server_address[1]
    url = f"http://{host}:{actual_port}/"

    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()
    print(f"pullback setup is open at {url}")
    print("Walk through the page and save your AI provider; this returns when you do.")
    if open_browser:
        try:
            webbrowser.open(url)
        except Exception:  # pragma: no cover - headless or no browser
            print("Could not open a browser automatically; visit the URL above.")

    try:
        done.wait()
    except KeyboardInterrupt:  # pragma: no cover - interactive
        print("\nSetup cancelled.")
    finally:
        threading.Thread(target=httpd.shutdown, daemon=True).start()

    return state["saved_path"]

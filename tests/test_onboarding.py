"""The intro interface: the walkthrough renders self-contained, both providers
appear, and the local wizard server saves a config end to end.
"""

import threading
import urllib.error
import urllib.request
from http.server import HTTPServer
from urllib.parse import urlencode

from pullback.app.wizard import _make_handler
from pullback.render.onboarding import render_onboarding
from pullback.store.config import load_config


def test_walkthrough_renders_self_contained():
    html = render_onboarding(interactive=False)
    assert html.lstrip().startswith("<!DOCTYPE html>")
    assert "<style>" in html
    # No external assets to fetch (the only script is inline; no src= anywhere).
    assert "src=" not in html


def test_both_providers_offered():
    html = render_onboarding(interactive=True)
    assert "OpenAI (GPT-5.5)" in html
    assert "Local Llama (on this device)" in html


def test_walkthrough_explains_the_safety_critical_distinctions():
    html = render_onboarding(interactive=True)
    # The same distinctions the field test probes must be taught here.
    assert "not yet checked" in html  # the empty-state distinction
    assert "Never ranked" in html  # alternatives are not advice
    assert "stays on this device" in html  # the data boundary, in plain words


def test_static_mode_tells_user_to_run_setup():
    html = render_onboarding(interactive=False)
    assert "pullback setup" in html


def test_success_state_shows_masked_key():
    html = render_onboarding(
        saved=True,
        saved_provider="OpenAI (GPT-5.5)",
        config_path="/home/u/.config/pullback/config.json",
        masked_key="****cdef",
    )
    assert "You are set up" in html
    assert "****cdef" in html


def _serve(handler_cls):
    httpd = HTTPServer(("127.0.0.1", 0), handler_cls)
    port = httpd.server_address[1]
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return httpd, port


def test_wizard_get_serves_page_and_post_saves_config(tmp_path, monkeypatch):
    monkeypatch.setenv("PULLBACK_CONFIG", str(tmp_path / "config.json"))
    done = threading.Event()
    handler = _make_handler({"done": done, "saved_path": None})
    httpd, port = _serve(handler)
    try:
        base = f"http://127.0.0.1:{port}"
        # GET the walkthrough.
        with urllib.request.urlopen(base + "/") as r:
            body = r.read().decode()
            assert r.status == 200
            assert "Welcome to pullback" in body

        # POST a valid OpenAI config.
        data = urlencode({"provider": "openai", "api_key": "sk-live-xyz"}).encode()
        with urllib.request.urlopen(base + "/save", data=data) as r:
            assert r.status == 200
            assert "You are set up" in r.read().decode()

        saved = load_config(tmp_path / "config.json")
        assert saved is not None
        assert saved.provider == "openai"
        assert saved.api_key == "sk-live-xyz"
        assert saved.model == "gpt-5.5"
        assert done.is_set()
    finally:
        httpd.shutdown()


def test_wizard_post_missing_key_shows_error(tmp_path, monkeypatch):
    monkeypatch.setenv("PULLBACK_CONFIG", str(tmp_path / "config.json"))
    handler = _make_handler({"done": threading.Event(), "saved_path": None})
    httpd, port = _serve(handler)
    try:
        data = urlencode({"provider": "openai", "api_key": ""}).encode()
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/save", data=data)
            assert False, "expected HTTP 400"
        except urllib.error.HTTPError as e:
            assert e.code == 400
            assert "API key" in e.read().decode()
        # Nothing was written.
        assert load_config(tmp_path / "config.json") is None
    finally:
        httpd.shutdown()

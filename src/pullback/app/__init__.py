"""Small local app surfaces. v0 has the setup wizard only; no web framework is
used (stdlib http.server, bound to localhost)."""

from pullback.app.wizard import run_wizard

__all__ = ["run_wizard"]

"""The saved AI provider configuration.

Written by the intro wizard (`pullback setup`) to a per-user file, readable only
by the owner because it holds an API key. The file location is
$PULLBACK_CONFIG if set, else ~/.config/pullback/config.json.

The API key is a secret: it is stored with 0600 permissions, never committed
(the path is outside the repo by default, and .pullback/ is gitignored for the
repo-local case), and only ever shown back masked.
"""

from __future__ import annotations

import json
import os
import stat
from dataclasses import asdict, dataclass
from pathlib import Path

from pullback.llm.client import LLMConfig
from pullback.llm.providers import get_provider


def config_path() -> Path:
    override = os.environ.get("PULLBACK_CONFIG")
    if override:
        return Path(override)
    base = os.environ.get("XDG_CONFIG_HOME")
    root = Path(base) if base else Path.home() / ".config"
    return root / "pullback" / "config.json"


@dataclass(frozen=True)
class SavedConfig:
    provider: str  # provider key, e.g. "openai" or "local-llama"
    base_url: str
    model: str
    api_key: str = ""

    def to_llm_config(self) -> LLMConfig:
        return LLMConfig(base_url=self.base_url, api_key=self.api_key, model=self.model)


def mask_key(key: str) -> str:
    if not key:
        return "(none)"
    if len(key) <= 4:
        return "*" * len(key)
    return f"{'*' * (len(key) - 4)}{key[-4:]}"


def save_config(cfg: SavedConfig, path: Path | None = None) -> Path:
    target = path or config_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(asdict(cfg), indent=2) + "\n", encoding="utf-8")
    # Owner read/write only: this file holds a secret.
    try:
        target.chmod(stat.S_IRUSR | stat.S_IWUSR)
    except OSError:  # pragma: no cover - platform dependent (e.g. some Windows)
        pass
    return target


def load_config(path: Path | None = None) -> SavedConfig | None:
    target = path or config_path()
    if not target.exists():
        return None
    data = json.loads(target.read_text(encoding="utf-8"))
    return SavedConfig(
        provider=data.get("provider", ""),
        base_url=data["base_url"],
        model=data["model"],
        api_key=data.get("api_key", ""),
    )


def config_from_form(form: dict[str, str]) -> SavedConfig:
    """Build a SavedConfig from submitted wizard fields.

    Provider presets supply defaults; the user may override base_url and model
    (the advanced fields). A provider that requires a key with none supplied is
    rejected, so the wizard cannot silently save an unusable OpenAI config.
    """

    provider_key = (form.get("provider") or "").strip()
    provider = get_provider(provider_key)

    base_url = (form.get("base_url") or "").strip() or provider.base_url
    model = (form.get("model") or "").strip() or provider.model
    api_key = (form.get("api_key") or "").strip()

    if provider.requires_key and not api_key:
        raise ValueError(f"{provider.label} needs an API key.")

    return SavedConfig(
        provider=provider.key, base_url=base_url, model=model, api_key=api_key
    )


def active_llm_config(path: Path | None = None) -> LLMConfig:
    """The effective model config: PULLBACK_LLM_* env vars win, else the saved
    file, else the local default. Lets the env override the wizard for CI or a
    one-off run without rewriting the saved key."""

    if "PULLBACK_LLM_BASE_URL" in os.environ:
        return LLMConfig.from_env()
    saved = load_config(path)
    if saved is not None:
        return saved.to_llm_config()
    return LLMConfig.from_env()

"""The saved AI provider config: form handling, persistence, masking, and the
env-over-file precedence the rest of the app relies on.
"""

import json
import stat

import pytest

from pullback.store.config import (
    SavedConfig,
    active_llm_config,
    config_from_form,
    load_config,
    mask_key,
    save_config,
)


def test_config_from_form_uses_provider_defaults_when_blank():
    cfg = config_from_form({"provider": "local-llama"})
    assert cfg.provider == "local-llama"
    assert cfg.base_url == "http://localhost:11434/v1"
    assert cfg.model == "llama3.1"
    assert cfg.api_key == ""


def test_config_from_form_openai_requires_key():
    with pytest.raises(ValueError, match="API key"):
        config_from_form({"provider": "openai", "api_key": ""})


def test_config_from_form_openai_with_key():
    cfg = config_from_form({"provider": "openai", "api_key": "sk-abc123"})
    assert cfg.provider == "openai"
    assert cfg.base_url == "https://api.openai.com/v1"
    assert cfg.model == "gpt-5.5"
    assert cfg.api_key == "sk-abc123"


def test_config_from_form_allows_overrides():
    cfg = config_from_form(
        {
            "provider": "local-llama",
            "base_url": "http://localhost:1234/v1",
            "model": "qwen2.5",
        }
    )
    assert cfg.base_url == "http://localhost:1234/v1"
    assert cfg.model == "qwen2.5"


def test_config_from_form_rejects_unknown_provider():
    with pytest.raises(ValueError, match="unknown provider"):
        config_from_form({"provider": "nope"})


def test_save_and_load_round_trip(tmp_path):
    path = tmp_path / "config.json"
    cfg = SavedConfig("openai", "https://api.openai.com/v1", "gpt-5.5", "sk-secret")
    save_config(cfg, path)
    loaded = load_config(path)
    assert loaded == cfg


def test_saved_config_is_owner_only(tmp_path):
    path = tmp_path / "config.json"
    save_config(SavedConfig("openai", "u", "m", "sk-x"), path)
    mode = stat.S_IMODE(path.stat().st_mode)
    # No group or other access to a file holding an API key.
    assert mode & (stat.S_IRWXG | stat.S_IRWXO) == 0


def test_load_missing_returns_none(tmp_path):
    assert load_config(tmp_path / "absent.json") is None


def test_mask_key():
    assert mask_key("") == "(none)"
    assert mask_key("sk-abcdef")[-4:] == "cdef"
    assert set(mask_key("sk-abcdef")[:-4]) == {"*"}
    assert mask_key("ab") == "**"


def test_to_llm_config_carries_fields():
    cfg = SavedConfig("openai", "https://api.openai.com/v1", "gpt-5.5", "sk-x")
    llm = cfg.to_llm_config()
    assert llm.base_url == "https://api.openai.com/v1"
    assert llm.model == "gpt-5.5"
    assert llm.api_key == "sk-x"


def test_active_config_prefers_env_over_file(tmp_path, monkeypatch):
    path = tmp_path / "config.json"
    save_config(SavedConfig("openai", "https://api.openai.com/v1", "gpt-5.5", "sk-x"), path)
    monkeypatch.setenv("PULLBACK_LLM_BASE_URL", "http://localhost:9999/v1")
    monkeypatch.setenv("PULLBACK_LLM_MODEL", "envmodel")
    llm = active_llm_config(path)
    assert llm.base_url == "http://localhost:9999/v1"
    assert llm.model == "envmodel"


def test_active_config_falls_back_to_file(tmp_path, monkeypatch):
    monkeypatch.delenv("PULLBACK_LLM_BASE_URL", raising=False)
    path = tmp_path / "config.json"
    save_config(SavedConfig("local-llama", "http://localhost:11434/v1", "llama3.1", ""), path)
    llm = active_llm_config(path)
    assert llm.base_url == "http://localhost:11434/v1"
    assert llm.model == "llama3.1"

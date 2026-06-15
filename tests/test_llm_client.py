"""The OpenAI-compatible model seam, tested without a network.

The device-boundary guard (invariant 4) is the load-bearing test here: a client
that will see raw narrative must refuse a non-local endpoint.
"""

import io
import json

import pytest

from pullback.llm.client import (
    ChatMessage,
    LLMConfig,
    LocalOnlyError,
    OpenAICompatibleClient,
    _content_from_response,
    is_local_host,
)


def _client(base_url="http://localhost:11434/v1", **kw):
    return OpenAICompatibleClient(LLMConfig(base_url=base_url, model="m"), **kw)


# ----- the boundary guard -----


def test_local_hosts_are_recognised():
    assert is_local_host("http://localhost:11434/v1")
    assert is_local_host("http://127.0.0.1:8000/v1")
    assert is_local_host("http://192.168.1.20:1234/v1")
    assert is_local_host("http://10.0.0.5/v1")
    assert is_local_host("http://workstation.local/v1")


def test_public_hosts_are_not_local():
    assert not is_local_host("https://api.openai.com/v1")
    assert not is_local_host("https://example.com/v1")
    assert not is_local_host("")


def test_narrative_client_refuses_non_local_endpoint():
    with pytest.raises(LocalOnlyError):
        _client(base_url="https://api.openai.com/v1", handles_narrative=True)


def test_narrative_client_accepts_local_endpoint():
    c = _client(base_url="http://127.0.0.1:11434/v1", handles_narrative=True)
    assert c.handles_narrative is True


def test_projection_client_may_target_remote():
    # Without handles_narrative the guard does not fire: only the coded
    # projection ever reaches a remote model, and it carries no narrative.
    c = _client(base_url="https://api.openai.com/v1")
    assert c.config.base_url == "https://api.openai.com/v1"


def test_for_local_parsing_factory_enforces_local(monkeypatch):
    monkeypatch.setenv("PULLBACK_LLM_BASE_URL", "https://api.openai.com/v1")
    with pytest.raises(LocalOnlyError):
        OpenAICompatibleClient.for_local_parsing()


# ----- config from env -----


def test_config_from_env():
    cfg = LLMConfig.from_env(
        {
            "PULLBACK_LLM_BASE_URL": "http://localhost:1234/v1",
            "PULLBACK_LLM_API_KEY": "sk-local",
            "PULLBACK_LLM_MODEL": "qwen2.5-7b",
            "PULLBACK_LLM_TIMEOUT": "30",
        }
    )
    assert cfg.base_url == "http://localhost:1234/v1"
    assert cfg.api_key == "sk-local"
    assert cfg.model == "qwen2.5-7b"
    assert cfg.timeout == 30.0


def test_config_defaults_are_local():
    cfg = LLMConfig.from_env({})
    assert is_local_host(cfg.base_url)


# ----- request building (pure) -----


def test_endpoint_and_payload_shape():
    c = _client()
    assert c._endpoint() == "http://localhost:11434/v1/chat/completions"
    payload = c._payload(
        [ChatMessage("user", "hello")],
        temperature=0.0,
        json_object=True,
        max_tokens=128,
    )
    assert payload["model"] == "m"
    assert payload["messages"] == [{"role": "user", "content": "hello"}]
    assert payload["temperature"] == 0.0
    assert payload["response_format"] == {"type": "json_object"}
    assert payload["max_tokens"] == 128


def test_headers_include_bearer_only_when_key_present():
    assert "Authorization" not in _client()._headers()
    keyed = OpenAICompatibleClient(LLMConfig(api_key="sk-x", model="m"))
    assert keyed._headers()["Authorization"] == "Bearer sk-x"


# ----- response parsing and the call (urlopen monkeypatched) -----


def test_content_from_response():
    raw = json.dumps(
        {"choices": [{"message": {"role": "assistant", "content": "hi there"}}]}
    )
    assert _content_from_response(raw) == "hi there"


def test_chat_posts_and_returns_content(monkeypatch):
    captured = {}

    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return json.dumps(
                {"choices": [{"message": {"content": '{"age_years": 78}'}}]}
            ).encode()

    def fake_urlopen(request, timeout=None):
        captured["url"] = request.full_url
        captured["body"] = json.loads(request.data.decode())
        captured["timeout"] = timeout
        return _Resp()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    c = _client(base_url="http://127.0.0.1:11434/v1", handles_narrative=True)
    out = c.chat_json([ChatMessage("user", "parse this")])
    assert out == {"age_years": 78}
    assert captured["url"] == "http://127.0.0.1:11434/v1/chat/completions"
    assert captured["body"]["response_format"] == {"type": "json_object"}
    assert captured["timeout"] == c.config.timeout

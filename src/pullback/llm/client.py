"""An OpenAI-API-compatible chat client, dependency-free (stdlib only).

Speaks the /chat/completions protocol, so it works against any OpenAI-compatible
endpoint: a local Ollama or llama.cpp or LM Studio or vLLM server, or a hosted
provider. base_url, api_key, and model are configuration, read from the
environment by default.

Device-boundary guard (invariant 4): a client that will be handed raw patient
narrative MUST point at a local or private host. Construct it with
`for_local_parsing()` (or pass handles_narrative=True) and a non-local base_url
raises LocalOnlyError before any request is built. The coded projection carries
no narrative or alias by construction (model.facets.CaseProjection), so
projection-only calls may target any endpoint.

Generation temperature defaults to 0: the clinical surface is a typesetter, not
an oracle (invariant 3).
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from ipaddress import ip_address
from typing import Any, Protocol, runtime_checkable
from urllib.parse import urlparse

# Default to a local Ollama-style endpoint; override via PULLBACK_LLM_BASE_URL.
DEFAULT_BASE_URL = "http://localhost:11434/v1"
DEFAULT_TIMEOUT = 60.0


class LocalOnlyError(ValueError):
    """Raised when a narrative-handling client targets a non-local host."""


def is_local_host(base_url: str) -> bool:
    """True if base_url points at the local machine or a private network.

    Loopback, link-local, and RFC1918 private ranges count as local, as do the
    hostnames 'localhost' and any '*.local' name (mDNS). Everything else, in
    particular any public hosted endpoint, is treated as off-device.
    """

    host = (urlparse(base_url).hostname or "").lower()
    if not host:
        return False
    if host == "localhost" or host.endswith(".local"):
        return True
    try:
        ip = ip_address(host)
    except ValueError:
        return False
    return ip.is_loopback or ip.is_private or ip.is_link_local


@dataclass(frozen=True)
class ChatMessage:
    role: str  # "system", "user", "assistant"
    content: str

    def to_dict(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content}


@dataclass(frozen=True)
class LLMConfig:
    base_url: str = DEFAULT_BASE_URL
    api_key: str = ""
    model: str = "local-model"
    timeout: float = DEFAULT_TIMEOUT

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> LLMConfig:
        e = env if env is not None else dict(os.environ)
        return cls(
            base_url=e.get("PULLBACK_LLM_BASE_URL", DEFAULT_BASE_URL),
            api_key=e.get("PULLBACK_LLM_API_KEY", ""),
            model=e.get("PULLBACK_LLM_MODEL", "local-model"),
            timeout=float(e.get("PULLBACK_LLM_TIMEOUT", DEFAULT_TIMEOUT)),
        )


@runtime_checkable
class LLMClient(Protocol):
    """The interface the rest of pullback depends on, so the concrete client is
    swappable (a different SDK, a mock in tests)."""

    def chat(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.0,
        json_object: bool = False,
        max_tokens: int | None = None,
    ) -> str: ...


class OpenAICompatibleClient:
    """A minimal OpenAI-compatible chat client over urllib.

    Build it three ways:
    - OpenAICompatibleClient.from_env(): config from PULLBACK_LLM_* env vars.
    - OpenAICompatibleClient.for_local_parsing(): same, but asserts the endpoint
      is local because the caller will pass raw narrative (invariant 4).
    - OpenAICompatibleClient(config): explicit config.
    """

    def __init__(self, config: LLMConfig, *, handles_narrative: bool = False) -> None:
        if handles_narrative and not is_local_host(config.base_url):
            raise LocalOnlyError(
                "Refusing to handle patient narrative against a non-local endpoint "
                f"({config.base_url!r}). The parser must run on-device (invariant 4). "
                "Point PULLBACK_LLM_BASE_URL at a localhost server, or only send "
                "CaseProjection to remote models."
            )
        self.config = config
        self.handles_narrative = handles_narrative

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> OpenAICompatibleClient:
        return cls(LLMConfig.from_env(env))

    @classmethod
    def for_local_parsing(
        cls, env: dict[str, str] | None = None
    ) -> OpenAICompatibleClient:
        return cls(LLMConfig.from_env(env), handles_narrative=True)

    # ----- request building (pure, unit-testable without a network) -----

    def _endpoint(self) -> str:
        return self.config.base_url.rstrip("/") + "/chat/completions"

    def _payload(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float,
        json_object: bool,
        max_tokens: int | None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.config.model,
            "messages": [m.to_dict() for m in messages],
            "temperature": temperature,
        }
        if json_object:
            payload["response_format"] = {"type": "json_object"}
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        return payload

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        return headers

    # ----- the call -----

    def chat(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.0,
        json_object: bool = False,
        max_tokens: int | None = None,
    ) -> str:
        """Send a chat-completions request and return the assistant content.

        Raises LLMError on transport or protocol failure. The narrative guard has
        already run at construction time, so this method itself is endpoint
        agnostic.
        """

        body = json.dumps(
            self._payload(
                messages,
                temperature=temperature,
                json_object=json_object,
                max_tokens=max_tokens,
            )
        ).encode("utf-8")
        request = urllib.request.Request(
            self._endpoint(), data=body, headers=self._headers(), method="POST"
        )
        try:
            with urllib.request.urlopen(request, timeout=self.config.timeout) as resp:
                raw = resp.read().decode("utf-8")
        except urllib.error.HTTPError as exc:  # pragma: no cover - network
            detail = exc.read().decode("utf-8", "replace")
            raise LLMError(f"LLM HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:  # pragma: no cover - network
            raise LLMError(f"LLM unreachable at {self._endpoint()}: {exc.reason}") from exc
        return _content_from_response(raw)

    def chat_json(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.0,
        max_tokens: int | None = None,
    ) -> Any:
        """Convenience for the parser: request a JSON object and parse it.

        block 3 (the freeform parser) will use this to extract the facet schema.
        """

        text = self.chat(
            messages, temperature=temperature, json_object=True, max_tokens=max_tokens
        )
        return json.loads(text)


class LLMError(RuntimeError):
    """Transport or protocol failure talking to the model endpoint."""


def _content_from_response(raw: str) -> str:
    data = json.loads(raw)
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMError(f"Unexpected chat-completions response shape: {raw[:200]}") from exc

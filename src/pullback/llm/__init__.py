"""The model seam: an OpenAI-API-compatible chat client.

"OpenAI-compatible" here is a protocol choice, not a vendor choice. The same
chat-completions shape is spoken by local runtimes (Ollama, llama.cpp server,
LM Studio, vLLM) and by hosted providers, so a single configurable base_url
covers both. That is exactly what invariant 4 needs: the local parser, which
sees raw patient narrative, points at a localhost server; only the coded
projection ever travels to anything remote.

The boundary is enforced here, not just trusted: a client constructed to handle
narrative must target a local or private host, or it raises LocalOnlyError. See
docs/03-regulatory.md and decision-log D7.
"""

from pullback.llm.client import (
    ChatMessage,
    LLMClient,
    LLMConfig,
    LocalOnlyError,
    OpenAICompatibleClient,
    is_local_host,
)

__all__ = [
    "ChatMessage",
    "LLMClient",
    "LLMConfig",
    "LocalOnlyError",
    "OpenAICompatibleClient",
    "is_local_host",
]

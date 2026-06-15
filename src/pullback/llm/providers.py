"""Named provider presets for the model seam.

"For now" the intro wizard offers two: OpenAI (GPT-5.5) and a local Llama running
on the doctor's own machine. Both speak the OpenAI-compatible protocol the client
already implements (decision-log D7), so a provider is just a set of defaults plus
a data-handling note shown to the user.

The is_local flag is load-bearing: a local provider can serve the narrative parser
directly (invariant 4); a remote provider may only ever receive the coded
CaseProjection, never raw history.
"""

from __future__ import annotations

from dataclasses import dataclass

from pullback.llm.client import is_local_host


@dataclass(frozen=True)
class Provider:
    key: str  # stable id stored in config
    label: str  # shown in the wizard
    base_url: str
    model: str
    requires_key: bool
    is_local: bool
    data_note: str  # the data-handling sentence the user sees before choosing


OPENAI = Provider(
    key="openai",
    label="OpenAI (GPT-5.5)",
    base_url="https://api.openai.com/v1",
    model="gpt-5.5",
    requires_key=True,
    is_local=False,
    data_note=(
        "Only the coded case projection (age, kidney function, dm+d drug codes, "
        "coded conditions) is sent to OpenAI. Raw patient history and your case "
        "alias never leave this device. Local parsing of free text still needs a "
        "local model."
    ),
)

LOCAL_LLAMA = Provider(
    key="local-llama",
    label="Local Llama (on this device)",
    base_url="http://localhost:11434/v1",
    model="llama3.1",
    requires_key=False,
    is_local=True,
    data_note=(
        "Everything stays on this device. The model runs locally (for example via "
        "Ollama or llama.cpp serving an OpenAI-compatible endpoint). Nothing, coded "
        "or otherwise, is sent to a third party."
    ),
)

PROVIDERS: dict[str, Provider] = {OPENAI.key: OPENAI, LOCAL_LLAMA.key: LOCAL_LLAMA}
PROVIDER_ORDER: tuple[Provider, ...] = (OPENAI, LOCAL_LLAMA)


def get_provider(key: str) -> Provider:
    try:
        return PROVIDERS[key]
    except KeyError:
        raise ValueError(
            f"unknown provider {key!r}; options: {', '.join(PROVIDERS)}"
        ) from None


def provider_for_base_url(base_url: str) -> Provider | None:
    """Best-effort: map a configured base_url back to a known preset, so the
    wizard can pre-select the right radio when re-opened."""

    for p in PROVIDER_ORDER:
        if p.base_url.rstrip("/") == base_url.rstrip("/"):
            return p
    # Fall back to the local preset for any local host.
    return LOCAL_LLAMA if is_local_host(base_url) else None

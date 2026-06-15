"""The intro interface: a walkthrough of how to use pullback plus the AI-provider
and API-key setup form.

Rendered as one self-contained HTML page (no external assets), served locally by
the setup wizard (pullback.app.wizard) or exported statically by `pullback
welcome`. The walkthrough doubles as user education for the field test
(docs/06-field-test.md): the same distinctions a clinician must read correctly
in the dossier are explained here in plain words.
"""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from pullback.llm.providers import PROVIDER_ORDER
from pullback.render.matrix import DISCLAIMER

_TEMPLATE_DIR = Path(__file__).parent / "templates"


def render_onboarding(
    *,
    interactive: bool = True,
    saved: bool = False,
    saved_provider: str = "",
    config_path: str = "",
    masked_key: str = "",
    selected_provider: str = "openai",
    error: str = "",
    form: dict[str, str] | None = None,
) -> str:
    """Render the intro page.

    interactive: the form posts to the local wizard (/save). When False (static
    export), the form is shown with a note to run `pullback setup` instead.
    saved: render the success state after a config has been written.
    """

    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATE_DIR)),
        autoescape=select_autoescape(["html", "j2"]),
    )
    template = env.get_template("onboarding.html.j2")
    return template.render(
        providers=PROVIDER_ORDER,
        interactive=interactive,
        saved=saved,
        saved_provider=saved_provider,
        config_path=config_path,
        masked_key=masked_key,
        selected_provider=selected_provider,
        error=error,
        form=form or {},
        disclaimer=DISCLAIMER,
    )

"""pullback CLI.

v0 exposes the one command that closes the loop: render the flagship dossier
from the in-repo fixtures to a single self-contained HTML page. The data-bearing
commands the spec foresees (ingest, build-tree, parse, refresh) are stubbed with
a clear message pointing at the spike block that delivers them, because each
needs a gated external resource (TRUD account, SPC downloads, a local parsing
model) not yet wired in.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _cmd_render_flagship(args: argparse.Namespace) -> int:
    from pullback.eval.evaluator import evaluate
    from pullback.fixtures.flagship import (
        flagship_case,
        flagship_corpus,
        flagship_query,
    )
    from pullback.render.matrix import render_dossier

    case = flagship_case()
    dossier = evaluate(case, flagship_query(), flagship_corpus())
    html = render_dossier(dossier, case)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"Wrote flagship dossier to {out} ({len(html)} bytes).")
    print(f"Corpus snapshot: {dossier.corpus_snapshot_id}")
    print(f"Oldest retrieval among citations: {dossier.oldest_retrieval.isoformat()}")
    return 0


def _cmd_setup(args: argparse.Namespace) -> int:
    from pullback.app.wizard import run_wizard

    path = run_wizard(open_browser=not args.no_browser)
    if path is None:
        print("No configuration saved.", file=sys.stderr)
        return 1
    print(f"Saved AI configuration to {path}.")
    return 0


def _cmd_welcome(args: argparse.Namespace) -> int:
    from pullback.render.onboarding import render_onboarding

    html = render_onboarding(interactive=False)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"Wrote the walkthrough to {out}. Run 'pullback setup' to save your AI provider.")
    return 0


_PENDING = {
    "ingest": "block 4 (SPC acquisition): needs manual SPC downloads from emc/MHRA.",
    "build-tree": "block 5 (section tree): needs the ingested SPC corpus.",
    "parse": "block 3 (freeform parser): needs a local parsing model on the doctor's machine.",
    "refresh": "block 11 (render and diff): needs the resident-tier sync, partially present via model.dossier.diff.",
}


def _cmd_pending(args: argparse.Namespace) -> int:
    print(f"'{args._name}' is not implemented in v0: {_PENDING[args._name]}", file=sys.stderr)
    print("See docs/04-spike-plan.md.", file=sys.stderr)
    return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pullback", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_setup = sub.add_parser(
        "setup", help="open the intro wizard to choose an AI provider and save your API key"
    )
    p_setup.add_argument(
        "--no-browser", action="store_true", help="do not open a browser automatically"
    )
    p_setup.set_defaults(func=_cmd_setup)

    p_welcome = sub.add_parser(
        "welcome", help="export the walkthrough page to HTML (read-only preview)"
    )
    p_welcome.add_argument(
        "--out", default="out/welcome.html", help="output HTML path (default: out/welcome.html)"
    )
    p_welcome.set_defaults(func=_cmd_welcome)

    p_render = sub.add_parser(
        "render-flagship", help="render the flagship dossier from fixtures to HTML"
    )
    p_render.add_argument(
        "--out", default="out/flagship.html", help="output HTML path (default: out/flagship.html)"
    )
    p_render.set_defaults(func=_cmd_render_flagship)

    for name in _PENDING:
        p = sub.add_parser(name, help=f"(pending) {_PENDING[name]}")
        p.set_defaults(func=_cmd_pending, _name=name)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

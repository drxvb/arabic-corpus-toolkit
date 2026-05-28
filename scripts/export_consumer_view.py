#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
export_consumer_view.py — produce a flattened, consumer-ready snapshot of toolkit assets.

Per the Codex-style API-design lens of the v0.2 multi-agent review,
some consumers want a stable, minimal view rather than the full schema
with v2.6+ optional fields, llm_votes provenance, regional_sensitivity
annotations, etc. This tool produces that minimal view as a pinned
snapshot — useful for:

  - **Vendoring** a fixed snapshot into a downstream skill that doesn't
    want to pull the full toolkit at runtime
  - **Adversarial-eval baselines** — snapshot before/after a triage pass
    to measure how many entries actually changed
  - **Documentation diffing** — render two snapshots side-by-side for
    a release-notes asset
  - **Translator's Stage A optimization** — flat key->value table without
    metadata overhead loads faster than the full schema

Three view modes:

  --view minimal           : just {calque: natural}
  --view standard          : {calque: {natural, domain, confidence}}
  --view full              : same as the source file (passes through)

Output formats: --format json (default) | --format tsv | --format markdown-table

Python 3 stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DICT = REPO_ROOT / "corpus" / "calque-dictionary.json"


def _load_entries(path: Path) -> List[Dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    return data.get("entries", [])


def _build_minimal_view(entries: List[Dict[str, Any]]) -> Dict[str, str]:
    """{calque: natural_arabic} — smallest possible useful view."""
    out: Dict[str, str] = {}
    for e in entries:
        c = (e.get("ai_default_calque") or "").strip()
        n = (e.get("natural_arabic") or "").strip()
        if c and n and c != n:
            out[c] = n
    return out


def _build_standard_view(entries: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """{calque: {natural, domain, confidence, is_topic_guarded}} — common consumer fields."""
    out: Dict[str, Dict[str, Any]] = {}
    for e in entries:
        c = (e.get("ai_default_calque") or "").strip()
        n = (e.get("natural_arabic") or "").strip()
        if not c or not n or c == n:
            continue
        is_guarded = bool(
            e.get("context_keywords_arabic") or e.get("context_keywords_english")
        )
        out[c] = {
            "natural": n,
            "domain": e.get("domain", "general"),
            "confidence": e.get("confidence", "medium"),
            "is_topic_guarded": is_guarded,
        }
    return out


def _filter_by_domain(entries: List[Dict[str, Any]], domain: str) -> List[Dict[str, Any]]:
    return [e for e in entries if e.get("domain") == domain]


def _filter_by_confidence(entries: List[Dict[str, Any]], min_confidence: str) -> List[Dict[str, Any]]:
    rank = {"low": 1, "medium": 2, "medium_consensus": 2, "topic-guarded": 3,
            "high": 4, "high_user_attested": 5}
    threshold = rank.get(min_confidence, 0)
    return [e for e in entries if rank.get(e.get("confidence", ""), 0) >= threshold]


def _emit_json(view: Any) -> str:
    return json.dumps(view, ensure_ascii=False, indent=2)


def _emit_tsv(view: Any) -> str:
    """Tab-separated lines. For minimal view: calque\tnatural. Standard: 4 cols."""
    lines: List[str] = []
    if isinstance(view, dict) and view and isinstance(next(iter(view.values())), str):
        lines.append("calque\tnatural")
        for c, n in sorted(view.items()):
            lines.append(f"{c}\t{n}")
    elif isinstance(view, dict):
        lines.append("calque\tnatural\tdomain\tconfidence\tis_topic_guarded")
        for c, v in sorted(view.items()):
            lines.append(f"{c}\t{v.get('natural','')}\t{v.get('domain','')}\t{v.get('confidence','')}\t{v.get('is_topic_guarded', False)}")
    return "\n".join(lines)


def _emit_markdown_table(view: Any) -> str:
    """Markdown table. Useful for release-notes diffing."""
    lines: List[str] = []
    if isinstance(view, dict) and view and isinstance(next(iter(view.values())), str):
        lines.append("| Calque (AI-default) | Natural Arabic |")
        lines.append("|---|---|")
        for c, n in sorted(view.items()):
            lines.append(f"| {c} | {n} |")
    elif isinstance(view, dict):
        lines.append("| Calque | Natural | Domain | Confidence | Topic-guarded |")
        lines.append("|---|---|---|---|---|")
        for c, v in sorted(view.items()):
            tg = "✓" if v.get("is_topic_guarded") else ""
            lines.append(f"| {c} | {v.get('natural','')} | {v.get('domain','')} | {v.get('confidence','')} | {tg} |")
    return "\n".join(lines)


def cli_main() -> int:
    p = argparse.ArgumentParser(description="Export a flat consumer-ready snapshot of toolkit assets")
    p.add_argument("--input", "-i", default=str(DEFAULT_DICT),
                   help=f"Input dictionary path (default: {DEFAULT_DICT})")
    p.add_argument("--view", choices=["minimal", "standard", "full"], default="standard",
                   help="View detail: minimal={calque:natural}; standard adds domain+confidence+topic-guarded; full passes through")
    p.add_argument("--format", choices=["json", "tsv", "markdown-table"], default="json",
                   help="Output format")
    p.add_argument("--filter-domain", help="Only include entries with this domain")
    p.add_argument("--filter-min-confidence", choices=["low", "medium", "topic-guarded", "high", "high_user_attested"],
                   help="Only include entries at or above this confidence rank")
    p.add_argument("--output", "-o", help="Write to file (default: stdout)")
    args = p.parse_args()

    entries = _load_entries(Path(args.input))
    if args.filter_domain:
        entries = _filter_by_domain(entries, args.filter_domain)
    if args.filter_min_confidence:
        entries = _filter_by_confidence(entries, args.filter_min_confidence)

    if args.view == "minimal":
        view = _build_minimal_view(entries)
    elif args.view == "standard":
        view = _build_standard_view(entries)
    else:
        view = entries

    if args.format == "json":
        out = _emit_json(view)
    elif args.format == "tsv":
        out = _emit_tsv(view) if not isinstance(view, list) else "(tsv not supported for full view)"
    else:
        out = _emit_markdown_table(view) if not isinstance(view, list) else "(markdown-table not supported for full view)"

    if args.output:
        Path(args.output).write_text(out, encoding="utf-8")
    else:
        print(out)

    return 0


if __name__ == "__main__":
    sys.exit(cli_main())

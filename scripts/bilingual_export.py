#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bilingual_export.py — v1.2.0 unified EN↔AR terminology export.

Bundles Asset G (paired terminology) across all domains into a single
exchange-format file suitable for external consumers: CAT tools (memoQ,
SDL Trados, OmegaT), MT post-editing workflows, or any system that wants
"the toolkit's terminology base" as a single artifact.

Output formats:
  --format tsv         : tab-separated (en\\tar\\tdomain\\tcorpus_freq\\tconfidence)
  --format json        : array of dicts
  --format tbx-lite    : tiny TermBase eXchange subset (CAT-tool compatible)
  --format markdown    : human-readable table

Confidence filter: --min-confidence {high,medium,low} (default: medium).

Run:
    python scripts/bilingual_export.py --format tsv --output terminology.tsv
    python scripts/bilingual_export.py --domains technology,news --min-confidence high \\
                                       --format tbx-lite -o terminology.tbx

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

_HERE = Path(__file__).resolve().parent
_CORPUS = _HERE.parent / "corpus"

CONFIDENCE_ORDER = {"high": 3, "medium": 2, "low": 1}


def _load_domain(domain: str) -> List[Dict[str, Any]]:
    """Return pairs for the given domain (technology / news / ...). Empty if missing."""
    fname = "domain-terminology.json" if domain == "technology" else f"domain-terminology-{domain}.json"
    p = _CORPUS / fname
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return []
    return data.get("pairs", [])


def gather(domains: List[str], min_confidence: str = "medium") -> List[Dict[str, Any]]:
    """Collect all pairs from the requested domains, filter by confidence, dedupe by AR."""
    threshold = CONFIDENCE_ORDER.get(min_confidence, 2)
    seen: Dict[str, Dict[str, Any]] = {}
    for domain in domains:
        for p in _load_domain(domain):
            conf = p.get("confidence", "medium")
            if CONFIDENCE_ORDER.get(conf, 0) < threshold:
                continue
            ar = (p.get("ar") or "").strip()
            en = (p.get("en") or "").strip()
            if not ar or not en:
                continue
            # If duplicate AR across domains, keep the one with higher corpus_freq
            existing = seen.get(ar)
            if existing is None or p.get("corpus_freq", 0) > existing.get("corpus_freq", 0):
                seen[ar] = {**p, "_source_domain": domain}
    return sorted(seen.values(), key=lambda p: p.get("corpus_freq", 0), reverse=True)


def emit_tsv(pairs: List[Dict[str, Any]]) -> str:
    lines = ["en\tar\tdomain\tcorpus_freq\tconfidence"]
    for p in pairs:
        lines.append("\t".join([
            p["en"].replace("\t", " "),
            p["ar"].replace("\t", " "),
            p.get("_source_domain", p.get("domain", "")),
            str(p.get("corpus_freq", 0)),
            p.get("confidence", "medium"),
        ]))
    return "\n".join(lines)


def emit_json(pairs: List[Dict[str, Any]]) -> str:
    out = [{
        "en": p["en"], "ar": p["ar"],
        "domain": p.get("_source_domain", p.get("domain", "")),
        "corpus_freq": p.get("corpus_freq", 0),
        "confidence": p.get("confidence", "medium"),
        "cross_llm_agreement": p.get("cross_llm_agreement"),
        "three_way_verdict": p.get("three_way_verdict"),
    } for p in pairs]
    return json.dumps(out, ensure_ascii=False, indent=2)


def emit_tbx_lite(pairs: List[Dict[str, Any]]) -> str:
    """Minimal TermBase eXchange (TBX) subset compatible with common CAT tools."""
    head = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<martif type="TBX-Basic" xml:lang="en">\n'
        '  <martifHeader><fileDesc><titleStmt><title>'
        'arabic-corpus-toolkit terminology export'
        '</title></titleStmt></fileDesc></martifHeader>\n'
        '  <text><body>\n'
    )
    body = []
    for i, p in enumerate(pairs, start=1):
        en_esc = p["en"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        ar_esc = p["ar"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        body.append(
            f'    <termEntry id="term-{i}">\n'
            f'      <descrip type="subjectField">{p.get("_source_domain", "general")}</descrip>\n'
            f'      <descrip type="reliability">{p.get("confidence", "medium")}</descrip>\n'
            f'      <descrip type="corpusFrequency">{p.get("corpus_freq", 0)}</descrip>\n'
            f'      <langSet xml:lang="en"><tig><term>{en_esc}</term></tig></langSet>\n'
            f'      <langSet xml:lang="ar"><tig><term>{ar_esc}</term></tig></langSet>\n'
            f'    </termEntry>'
        )
    foot = "\n  </body></text>\n</martif>\n"
    return head + "\n".join(body) + foot


def emit_markdown(pairs: List[Dict[str, Any]]) -> str:
    lines = [
        "| EN | AR | Domain | Freq | Confidence |",
        "|---|---|---|---|---|",
    ]
    for p in pairs:
        en = p["en"].replace("|", "\\|")
        ar = p["ar"].replace("|", "\\|")
        lines.append(
            f"| {en} | {ar} | {p.get('_source_domain', '')} | {p.get('corpus_freq', 0)} | {p.get('confidence', 'medium')} |"
        )
    return "\n".join(lines)


EMITTERS = {
    "tsv": emit_tsv,
    "json": emit_json,
    "tbx-lite": emit_tbx_lite,
    "markdown": emit_markdown,
}


def main() -> int:
    p = argparse.ArgumentParser(description="Bilingual terminology export for external tools")
    p.add_argument("--domains", default="technology,news",
                   help="Comma-separated domain names to bundle")
    p.add_argument("--min-confidence", default="medium",
                   choices=["high", "medium", "low"])
    p.add_argument("--format", default="tsv", choices=list(EMITTERS.keys()))
    p.add_argument("--output", "-o", help="Output path (default: stdout)")
    args = p.parse_args()

    domains = [d.strip() for d in args.domains.split(",") if d.strip()]
    pairs = gather(domains, min_confidence=args.min_confidence)
    sys.stderr.write(f"Gathered {len(pairs)} pairs from {domains} at min-confidence={args.min_confidence}\n")

    output = EMITTERS[args.format](pairs)
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        sys.stderr.write(f"Wrote {args.format} to {args.output}\n")
    else:
        print(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())

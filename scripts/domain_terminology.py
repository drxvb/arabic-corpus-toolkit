#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
domain_terminology.py — Loader for Asset G (paired EN↔AR terminology).

Asset G is the Phase-2 product of the terminology pipeline: validated EN↔AR
pairs with corpus-frequency evidence, LLM-proposer attribution, and optional
cross-vendor agreement. Built by scripts/pair_terminology.py from Asset F
candidates.

Public surface:
    load_pairs() -> dict                            # parsed file
    pair_count() -> int
    iter_pairs() -> Iterator[dict]
    find_by_en(en) -> list[dict]                   # case-insensitive
    find_by_ar(ar) -> dict | None
    pairs_for_en_text(text_en) -> list[dict]       # find all pairs whose EN appears in text
    top_pairs(n=50, by="corpus_freq") -> list[dict]
    soft_validate() -> list[str]
    stats() -> dict
    asset_path() -> Path

Python 3 stdlib only.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

_HERE = Path(__file__).resolve().parent
_CORPUS_DIR = _HERE.parent / "corpus"
_ASSET_PATH = _CORPUS_DIR / "domain-terminology.json"

_cache: Optional[Tuple[float, Dict[str, Any]]] = None


def asset_path() -> Path:
    return _ASSET_PATH


def load_pairs() -> Dict[str, Any]:
    """Return the parsed Asset G payload. mtime-keyed cache."""
    global _cache
    if not _ASSET_PATH.exists():
        raise FileNotFoundError(
            f"Asset G (domain-terminology) not found at {_ASSET_PATH}. "
            f"Build it by running: python scripts/pair_terminology.py"
        )
    mtime = _ASSET_PATH.stat().st_mtime
    if _cache is None or _cache[0] != mtime:
        _cache = (mtime, json.loads(_ASSET_PATH.read_text(encoding="utf-8")))
    return _cache[1]


def pair_count() -> int:
    return len(load_pairs().get("pairs", []))


def iter_pairs() -> Iterator[Dict[str, Any]]:
    yield from load_pairs().get("pairs", [])


def find_by_en(en: str) -> List[Dict[str, Any]]:
    """Return all pairs whose EN matches (case-insensitive exact match)."""
    needle = (en or "").strip().lower()
    if not needle:
        return []
    return [p for p in iter_pairs() if (p.get("en", "").strip().lower() == needle)]


def find_by_ar(ar: str) -> Optional[Dict[str, Any]]:
    """Return the first pair whose AR matches exactly. None if no match."""
    needle = (ar or "").strip()
    if not needle:
        return None
    for p in iter_pairs():
        if p.get("ar", "").strip() == needle:
            return p
    return None


def pairs_for_en_text(text_en: str) -> List[Dict[str, Any]]:
    """Find all pairs whose EN appears as a whole-word phrase in text_en.
    Used by translator Stage A to inject terminology hints for the LLM."""
    if not text_en:
        return []
    text_lower = text_en.lower()
    hits: List[Dict[str, Any]] = []
    for p in iter_pairs():
        en = p.get("en", "").strip().lower()
        if not en:
            continue
        # Whole-word(s) match — \b at the start, \b at the end
        pattern = r"\b" + re.escape(en) + r"\b"
        if re.search(pattern, text_lower):
            hits.append(p)
    return hits


def top_pairs(n: int = 50, by: str = "corpus_freq") -> List[Dict[str, Any]]:
    """Top N pairs sorted by the named field descending."""
    pairs = list(iter_pairs())
    if by == "corpus_freq":
        pairs.sort(key=lambda p: p.get("corpus_freq", 0), reverse=True)
    return pairs[:n]


def soft_validate() -> List[str]:
    """Cheap structural validation. Returns refusal-list-style errors; empty = OK."""
    errs: List[str] = []
    try:
        data = load_pairs()
    except Exception as e:
        return [f"could not load asset: {e}"]

    for key in ("$schema_version", "asset_name", "domain", "pairs", "provenance"):
        if key not in data:
            errs.append(f"missing top-level key {key!r}")

    if data.get("asset_name") != "domain-terminology":
        errs.append(f"asset_name should be 'domain-terminology', got {data.get('asset_name')!r}")

    pairs = data.get("pairs", [])
    if not isinstance(pairs, list) or not pairs:
        errs.append("pairs is empty or not a list")
        return errs

    # Sample-check the first pair has required fields
    first = pairs[0]
    for k in ("ar", "en", "domain", "corpus_freq", "confidence", "proposer"):
        if k not in first:
            errs.append(f"first pair missing {k!r}")

    # Check no duplicate AR terms (each AR should pair to one EN)
    ars = [p.get("ar") for p in pairs]
    dup_count = len(ars) - len(set(ars))
    if dup_count > 0:
        errs.append(f"{dup_count} duplicate AR terms found")

    return errs


def stats() -> Dict[str, Any]:
    try:
        data = load_pairs()
    except Exception as e:
        return {"error": str(e)}
    pairs = data.get("pairs", [])
    by_conf: Dict[str, int] = {"high": 0, "medium": 0, "low": 0}
    by_ngram: Dict[str, int] = {"unigram": 0, "bigram": 0, "trigram": 0}
    by_proposer: Dict[str, int] = {}
    cross_agree = 0
    for p in pairs:
        by_conf[p.get("confidence", "medium")] = by_conf.get(p.get("confidence", "medium"), 0) + 1
        size = p.get("ngram_size", "")
        if size in by_ngram:
            by_ngram[size] += 1
        proposer = p.get("proposer", "unknown")
        by_proposer[proposer] = by_proposer.get(proposer, 0) + 1
        if p.get("cross_llm_agreement"):
            cross_agree += 1
    return {
        "schema_version": data.get("$schema_version"),
        "asset_name": data.get("asset_name"),
        "domain": data.get("domain"),
        "n_pairs": len(pairs),
        "by_confidence": by_conf,
        "by_ngram_size": by_ngram,
        "by_proposer": by_proposer,
        "cross_llm_agreement_count": cross_agree,
        "provenance": data.get("provenance", {}),
    }


if __name__ == "__main__":
    import sys
    print("=== Asset G: domain-terminology ===")
    print(f"path: {_ASSET_PATH}")
    print()
    print(json.dumps(stats(), ensure_ascii=False, indent=2))
    print()
    errs = soft_validate()
    if errs:
        print(f"SOFT VALIDATION: {len(errs)} error(s)")
        for e in errs:
            print(f"  - {e}")
        sys.exit(1)
    print("SOFT VALIDATION: OK")
    sys.exit(0)

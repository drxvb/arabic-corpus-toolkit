#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
terminology.py — Loader for Asset F (terminology candidates + future pairs).

Asset F has TWO file shapes:

  1. terminology-candidates-<domain>.json — Phase 1 output (AR-side mining).
     Mined by scripts/mine_terminology.py. NO EN translations.

  2. domain-terminology.json — Phase 2 output (EN↔AR pairs).
     Built by promoting candidates after LLM-assisted pairing + corpus validation.
     Will ship with the first batch of paired terms.

v0.8 ships #1 only. #2 ships when the first paired batch is ready (toolkit v0.9+).

Public surface:
    load_candidates(domain="technology") -> dict       # parsed file
    candidate_count(domain="technology") -> int
    list_domains() -> tuple[str, ...]                  # which domains have files
    iter_candidates(domain) -> Iterator[dict]
    top_candidates(domain, n=50) -> list[dict]
    has_term(term_ar, domain) -> bool
    asset_path(domain) -> Path
    soft_validate(domain) -> list[str]                 # returns refusal-list-style errors
    stats() -> dict                                    # cross-domain summary

Python 3 stdlib only.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

_HERE = Path(__file__).resolve().parent
_CORPUS_DIR = _HERE.parent / "corpus"

# Cache: (mtime, data) keyed by domain
_cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}


def asset_path(domain: str) -> Path:
    return _CORPUS_DIR / f"terminology-candidates-{domain}.json"


def list_domains() -> Tuple[str, ...]:
    """Domains for which a candidates file is present on disk."""
    found: List[str] = []
    for p in sorted(_CORPUS_DIR.glob("terminology-candidates-*.json")):
        name = p.stem
        prefix = "terminology-candidates-"
        if name.startswith(prefix):
            found.append(name[len(prefix):])
    return tuple(found)


def load_candidates(domain: str = "technology") -> Dict[str, Any]:
    """Return the parsed candidates payload for a domain. mtime-keyed cache."""
    p = asset_path(domain)
    if not p.exists():
        raise FileNotFoundError(
            f"terminology candidates not found for domain {domain!r}: {p}. "
            f"Available: {list_domains()}"
        )
    mtime = p.stat().st_mtime
    cached = _cache.get(domain)
    if cached is None or cached[0] != mtime:
        _cache[domain] = (mtime, json.loads(p.read_text(encoding="utf-8")))
    return _cache[domain][1]


def candidate_count(domain: str = "technology") -> int:
    return len(load_candidates(domain).get("candidates", []))


def iter_candidates(domain: str = "technology") -> Iterator[Dict[str, Any]]:
    yield from load_candidates(domain).get("candidates", [])


def top_candidates(domain: str = "technology", n: int = 50) -> List[Dict[str, Any]]:
    """Return the top N candidates by frequency (file is already sorted)."""
    return load_candidates(domain).get("candidates", [])[:n]


def has_term(term_ar: str, domain: str = "technology") -> bool:
    """True iff the exact AR term appears in the candidates list for this domain."""
    return any(c.get("term_ar") == term_ar for c in iter_candidates(domain))


def soft_validate(domain: str = "technology") -> List[str]:
    """Cheap structural validation. Empty list = OK."""
    errs: List[str] = []
    try:
        data = load_candidates(domain)
    except Exception as e:
        return [f"could not load asset: {e}"]

    for key in ("$schema_version", "asset_name", "domain", "candidates", "provenance"):
        if key not in data:
            errs.append(f"missing top-level key {key!r}")

    if data.get("asset_name") != "terminology-candidates":
        errs.append(f"asset_name should be 'terminology-candidates', got {data.get('asset_name')!r}")

    if data.get("domain") != domain:
        errs.append(f"file claims domain={data.get('domain')!r} but loaded as {domain!r}")

    candidates = data.get("candidates", [])
    if not isinstance(candidates, list) or not candidates:
        errs.append("candidates is empty or not a list")
    else:
        # Spot-check the first candidate has the required shape
        first = candidates[0]
        for k in ("term_ar", "freq", "ngram_size"):
            if k not in first:
                errs.append(f"first candidate missing {k!r}")

    return errs


def stats() -> Dict[str, Any]:
    """Cross-domain summary."""
    out: Dict[str, Any] = {
        "domains_available": list(list_domains()),
        "domains": {},
    }
    for d in list_domains():
        try:
            data = load_candidates(d)
        except Exception as e:
            out["domains"][d] = {"error": str(e)}
            continue
        candidates = data.get("candidates", [])
        by_ngram: Dict[str, int] = {"unigram": 0, "bigram": 0, "trigram": 0}
        for c in candidates:
            sz = c.get("ngram_size", "unigram")
            by_ngram[sz] = by_ngram.get(sz, 0) + 1
        out["domains"][d] = {
            "schema_version": data.get("$schema_version"),
            "n_candidates": len(candidates),
            "by_ngram_size": by_ngram,
            "provenance": data.get("provenance", {}),
        }
    return out


if __name__ == "__main__":
    import sys
    print("=== Asset F: terminology candidates ===")
    print(f"Corpus dir: {_CORPUS_DIR}")
    print(f"Domains available: {list_domains()}")
    print()
    print(json.dumps(stats(), ensure_ascii=False, indent=2))
    print()
    for d in list_domains():
        errs = soft_validate(d)
        if errs:
            print(f"SOFT VALIDATION ({d}): {len(errs)} error(s)")
            for e in errs:
                print(f"  - {e}")
        else:
            print(f"SOFT VALIDATION ({d}): OK")
    sys.exit(0)

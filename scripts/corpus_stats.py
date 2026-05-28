#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
corpus_stats.py — read-only query API for empirical-patterns.json.

Adapted from the Codex-style API-design lens of the v0.2 multi-agent review,
calibrated to the actual schema of `corpus/empirical-patterns.json` (which
uses CORPUS CATEGORIES — quran/classical/news/lexicon — NOT the humanizer's
register policies — classical/news/opinion/technical). The two namespaces
overlap by name but mean different things:

  - **Corpus categories** (this module): genre of the source text in the
    100K-record mining run that produced the empirical patterns. `quran` =
    Quranic verses; `classical` = pre-modern prose; `news` = modern
    journalism; `lexicon` = dictionary entries.

  - **Register policies** (`register.py`): the humanizer's transformation
    policy categories. `classical` (in register.py) corresponds roughly to
    `classical` (in corpus_stats) but the mapping is intentional product
    design, not data alignment. Use `register.py` for gating decisions;
    use `corpus_stats.py` for empirical reference distributions.

Python 3 stdlib only.
"""
from __future__ import annotations

import json
import sys
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


class StatsError(Exception):
    pass


class StatsNotFoundError(StatsError):
    pass


class UnknownCategoryError(ValueError):
    pass


REPO_ROOT = Path(__file__).resolve().parent.parent
PATTERNS_PATH = REPO_ROOT / "corpus" / "empirical-patterns.json"

# The 4 corpus categories that the v2.3.0 mining run produced. Hardcoded
# because adding a new category would require a re-mining run AND consumer
# code changes — it's not data-driven runtime behavior.
KNOWN_CATEGORIES = ("quran", "classical", "news", "lexicon")

_CACHE: Dict[str, Any] = {}
_LOCK = threading.Lock()


def _load() -> Dict[str, Any]:
    if not PATTERNS_PATH.exists():
        raise StatsNotFoundError(f"empirical-patterns.json not found at {PATTERNS_PATH}")
    with _LOCK:
        if "data" in _CACHE:
            return _CACHE["data"]
        try:
            data = json.loads(PATTERNS_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise StatsError(f"invalid JSON in empirical-patterns.json: {e}")
        _CACHE["data"] = data
        return data


def clear_cache() -> None:
    with _LOCK:
        _CACHE.clear()


def known_categories() -> Tuple[str, ...]:
    return KNOWN_CATEGORIES


def metadata() -> Dict[str, Any]:
    """Return top-level metadata: input, sample_size, skipped, elapsed_s."""
    d = _load()
    return {
        "input": d.get("input"),
        "sample_size": d.get("sample_size"),
        "skipped": d.get("skipped"),
        "elapsed_s": d.get("elapsed_s"),
    }


def category_stats(category: str) -> Dict[str, Any]:
    """Return the full stats block for one corpus category."""
    if category not in KNOWN_CATEGORIES:
        raise UnknownCategoryError(
            f"unknown category: {category!r} (known: {KNOWN_CATEGORIES})"
        )
    d = _load()
    cats = d.get("categories", {})
    if category not in cats:
        raise StatsError(
            f"category {category!r} present in KNOWN_CATEGORIES but missing from data file"
        )
    return cats[category]


def token_count(category: str) -> int:
    """Total tokens mined for `category`."""
    return int(category_stats(category).get("n_tokens", 0))


def sentence_count(category: str) -> int:
    return int(category_stats(category).get("n_sentences", 0))


def mean_sentence_length(category: str) -> float:
    return float(category_stats(category).get("mean_sentence_length", 0.0))


def sentence_length_burstiness(category: str) -> float:
    """Burstiness: (stddev - mean) / (stddev + mean). Range [-1, 1].
    >0 = bursty (varied lengths); <0 = uniform. AI text typically scores
    closer to 0; human prose often scores 0.5+."""
    return float(category_stats(category).get("burstiness", 0.0))


def sentence_length_histogram(category: str) -> Dict[str, float]:
    """Percentage distribution over length bins (1-5, 6-10, 11-15, ...)."""
    return dict(category_stats(category).get("sentence_length_histogram_pct", {}))


def top_connectors(category: str, n: int = 10) -> List[Tuple[str, int]]:
    """Top-N connectors with raw counts. Returned as (token, count) tuples
    in descending order. Pass n=None for all."""
    raw = category_stats(category).get("top_connectors", [])
    pairs = [(item[0], int(item[1])) for item in raw if isinstance(item, list) and len(item) >= 2]
    return pairs if n is None else pairs[:n]


def connector_distribution(category: str) -> List[Tuple[str, int, float]]:
    """Connectors with raw count + percentage of total. Useful for
    distributional diversity scoring (Shannon entropy etc.)."""
    pairs = top_connectors(category, n=None)
    total = sum(c for _, c in pairs)
    if total == 0:
        return [(t, c, 0.0) for t, c in pairs]
    return [(t, c, 100.0 * c / total) for t, c in pairs]


def category_compare(metric: str) -> Dict[str, float]:
    """One metric across all categories. Useful for cross-category profiling.
    Supported metrics: n_tokens, n_sentences, mean_sentence_length,
    stddev_sentence_length, burstiness."""
    valid = {"n_tokens", "n_sentences", "mean_sentence_length",
             "stddev_sentence_length", "burstiness"}
    if metric not in valid:
        raise ValueError(f"unknown metric: {metric!r}. Supported: {sorted(valid)}")
    return {
        cat: float(category_stats(cat).get(metric, 0.0))
        for cat in KNOWN_CATEGORIES
        if cat in _load().get("categories", {})
    }


def cli_main() -> int:
    import argparse
    p = argparse.ArgumentParser(description="arabic-corpus-toolkit corpus statistics")
    p.add_argument("--meta", action="store_true", help="Show top-level metadata")
    p.add_argument("--category", help="Show full stats for one category (quran/classical/news/lexicon)")
    p.add_argument("--connectors", help="Top-10 connectors for category")
    p.add_argument("--compare", help="Compare one metric across categories (n_tokens/burstiness/...)")
    args = p.parse_args()

    if args.meta:
        m = metadata()
        print(f"# Empirical patterns metadata\n")
        print(f"- Input: {m['input']}")
        print(f"- Sample size: {m['sample_size']:,}")
        print(f"- Skipped: {m['skipped']}")
        print(f"- Mining elapsed: {m['elapsed_s']}s")
        print(f"- Categories: {', '.join(KNOWN_CATEGORIES)}")
        return 0

    if args.category:
        s = category_stats(args.category)
        print(json.dumps(s, ensure_ascii=False, indent=2))
        return 0

    if args.connectors:
        pairs = top_connectors(args.connectors, n=10)
        print(f"# Top 10 connectors in {args.connectors}:\n")
        for tok, count in pairs:
            print(f"  {tok}\t{count}")
        return 0

    if args.compare:
        result = category_compare(args.compare)
        print(f"# {args.compare} across categories:\n")
        for cat, val in result.items():
            print(f"  {cat}\t{val}")
        return 0

    p.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(cli_main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dictionary.py — read-only API for the calque dictionary.

v0.2 ships a deliberately minimal API. The Codex-style design review
(running concurrently with this v0.2 ship) will inform v0.3's full
surface (typed signatures, schema validation, caching strategy).

For v0.2, downstream consumers (humanizer, future translator, future
authoring suite) get:

  load_dictionary()         -> tuple[list, dict]  (keys, lookup)
  find_by_en(en)            -> list[entry]
  find_canonical(en)        -> entry | None
  iter_entries()            -> Iterator[entry]
  has_topic_guard(entry)    -> bool
  dictionary_path()         -> Path  (for raw access)
  stats()                   -> dict  (health-check counts)

Python 3 stdlib only.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


REPO_ROOT = Path(__file__).resolve().parent.parent
DICT_PATH = REPO_ROOT / "corpus" / "calque-dictionary.json"

_CACHE: Dict[str, Any] = {"loaded": False, "keys": [], "lookup": {}, "entries": []}


def dictionary_path() -> Path:
    return DICT_PATH


def _load(force: bool = False) -> None:
    if _CACHE["loaded"] and not force:
        return
    if not DICT_PATH.exists():
        _CACHE["loaded"] = True
        return
    data = json.loads(DICT_PATH.read_text(encoding="utf-8"))
    entries = data if isinstance(data, list) else data.get("entries", [])
    lookup: Dict[str, Dict[str, Any]] = {}
    keys: List[str] = []
    for e in entries:
        calque = e.get("ai_default_calque", "").strip()
        natural = e.get("natural_arabic", "").strip()
        if not calque or not natural or calque == natural:
            continue
        lookup[calque] = {
            "natural": natural,
            "alternatives": e.get("alternatives", []),
            "domain": e.get("domain", "general"),
            "confidence": e.get("confidence", "medium"),
            "context_keywords_arabic": e.get("context_keywords_arabic", []),
            "context_keywords_english": e.get("context_keywords_english", []),
            "context_keywords_required_count": e.get("context_keywords_required_count", 1),
            "exclude_if_pattern": e.get("exclude_if_pattern", []),
            "regional_sensitivity": e.get("regional_sensitivity"),
            "political_sensitivity": e.get("political_sensitivity"),
            "disambiguation_pair_id": e.get("disambiguation_pair_id"),
            "disambiguation_warning": e.get("disambiguation_warning"),
            "raw_entry": e,
        }
        keys.append(calque)
    keys.sort(key=len, reverse=True)
    _CACHE["loaded"] = True
    _CACHE["keys"] = keys
    _CACHE["lookup"] = lookup
    _CACHE["entries"] = entries


def load_dictionary() -> Tuple[List[str], Dict[str, Dict[str, Any]]]:
    _load()
    return _CACHE["keys"], _CACHE["lookup"]


def iter_entries() -> Iterator[Dict[str, Any]]:
    _load()
    for e in _CACHE["entries"]:
        yield e


def find_by_en(en: str) -> List[Dict[str, Any]]:
    _load()
    return [e for e in _CACHE["entries"] if e.get("en") == en]


def find_canonical(en: str) -> Optional[Dict[str, Any]]:
    candidates = find_by_en(en)
    if not candidates:
        return None
    rank = {"high": 4, "topic-guarded": 3, "medium": 2, "medium_consensus": 2, "low": 1}
    candidates.sort(key=lambda e: rank.get(e.get("confidence", ""), 0), reverse=True)
    return candidates[0]


def has_topic_guard(entry: Dict[str, Any]) -> bool:
    return bool(
        entry.get("context_keywords_arabic")
        or entry.get("context_keywords_english")
    )


def entry_count() -> int:
    _load()
    return len(_CACHE["entries"])


def stats() -> Dict[str, int]:
    _load()
    entries = _CACHE["entries"]
    return {
        "total": len(entries),
        "high_confidence": sum(1 for e in entries if e.get("confidence") == "high"),
        "topic_guarded": sum(1 for e in entries if has_topic_guard(e)),
        "with_disambiguation_warning": sum(1 for e in entries if e.get("disambiguation_warning")),
        "with_political_sensitivity": sum(1 for e in entries if e.get("political_sensitivity")),
    }


def cli_main() -> int:
    import argparse
    p = argparse.ArgumentParser(description="arabic-corpus-toolkit dictionary read API")
    p.add_argument("--stats", action="store_true", help="Print dictionary stats")
    p.add_argument("--find", help="Look up entries by English term (--find 'view')")
    p.add_argument("--canonical", help="Return single canonical entry for English term")
    args = p.parse_args()

    if args.stats:
        s = stats()
        print(f"# arabic-corpus-toolkit dictionary stats\n")
        print(f"- Total entries: {s['total']}")
        print(f"- High confidence: {s['high_confidence']}")
        print(f"- Topic-guarded (v2.6.3+): {s['topic_guarded']}")
        print(f"- With disambiguation_warning: {s['with_disambiguation_warning']}")
        print(f"- With political_sensitivity: {s['with_political_sensitivity']}")
        return 0

    if args.find:
        results = find_by_en(args.find)
        print(f"# Entries matching {args.find!r}: {len(results)}\n")
        for e in results:
            print(json.dumps(e, ensure_ascii=False, indent=2))
        return 0

    if args.canonical:
        e = find_canonical(args.canonical)
        if e is None:
            print(f"No entry for {args.canonical!r}")
            return 1
        print(json.dumps(e, ensure_ascii=False, indent=2))
        return 0

    p.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(cli_main())

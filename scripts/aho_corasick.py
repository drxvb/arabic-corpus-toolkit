#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
aho_corasick.py — v1.3.0 multi-pattern matcher.

Builds an Aho-Corasick automaton from any of the toolkit's pattern sets
(calque dictionary keys, terminology pairs, lexical-table phrases) and
scans long inputs in a single pass.

For typical translator inputs (<5KB), linear substring scan is already
fast enough — Aho-Corasick's value shows on documents >100KB where the
O(input + matches) bound beats the O(patterns × input) of linear scan.

Codex's v0.2 multi-agent review flagged this as a "forward-compat door"
to keep the API surface honest. v1.3.0 ships the implementation; consumers
that hit performance ceilings can adopt incrementally.

Usage:
    from aho_corasick import AhoCorasick
    ac = AhoCorasick.from_calque_dictionary()
    for start, end, key in ac.iter_matches(big_text):
        ...

    ac2 = AhoCorasick.from_strings(["foo", "bar"])

Python 3 stdlib only.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator, List, Optional, Set, Tuple
from collections import deque

_HERE = Path(__file__).resolve().parent
_CORPUS = _HERE.parent / "corpus"


class _Node:
    __slots__ = ("children", "fail", "outputs")

    def __init__(self):
        self.children: dict = {}
        self.fail: Optional["_Node"] = None
        self.outputs: List[str] = []


class AhoCorasick:
    """Aho-Corasick multi-pattern matcher.

    Build:  ac = AhoCorasick(patterns)
    Match:  for start, end, pattern in ac.iter_matches(text):
                ...
    """

    def __init__(self, patterns: List[str]):
        self.patterns = list(patterns)
        self.root = _Node()
        for p in patterns:
            if not p:
                continue
            node = self.root
            for ch in p:
                if ch not in node.children:
                    node.children[ch] = _Node()
                node = node.children[ch]
            node.outputs.append(p)
        # Build fail links via BFS
        queue = deque()
        for child in self.root.children.values():
            child.fail = self.root
            queue.append(child)
        while queue:
            node = queue.popleft()
            for ch, child in node.children.items():
                # Find longest proper suffix that's a prefix of some pattern
                fail = node.fail
                while fail is not None and ch not in fail.children:
                    fail = fail.fail
                child.fail = fail.children[ch] if fail and ch in fail.children else self.root
                # Inherit outputs of the fail target (suffix matches)
                child.outputs.extend(child.fail.outputs)
                queue.append(child)

    def iter_matches(self, text: str) -> Iterator[Tuple[int, int, str]]:
        """Yield (start, end, pattern) for every occurrence (overlapping)."""
        node = self.root
        for i, ch in enumerate(text):
            while node is not None and ch not in node.children:
                node = node.fail
            if node is None:
                node = self.root
                continue
            node = node.children[ch]
            for pat in node.outputs:
                start = i - len(pat) + 1
                yield (start, i + 1, pat)

    def has_any_match(self, text: str) -> bool:
        for _ in self.iter_matches(text):
            return True
        return False

    def find_first(self, text: str) -> Optional[Tuple[int, int, str]]:
        for m in self.iter_matches(text):
            return m
        return None

    @classmethod
    def from_strings(cls, patterns: List[str]) -> "AhoCorasick":
        return cls(patterns)

    @classmethod
    def from_calque_dictionary(cls, dictionary_path: Optional[Path] = None) -> "AhoCorasick":
        """Build matcher from calque dictionary's ai_default_calque keys (Asset A)."""
        p = dictionary_path or (_CORPUS / "calque-dictionary.json")
        data = json.loads(p.read_text(encoding="utf-8"))
        entries = data.get("entries", []) if isinstance(data, dict) else data
        patterns = [e.get("ai_default_calque", "") for e in entries if e.get("ai_default_calque")]
        return cls(patterns)

    @classmethod
    def from_terminology_pairs(cls,
                                 domain: str = "technology",
                                 side: str = "ar") -> "AhoCorasick":
        """Build matcher from Asset G pairs. side='ar' indexes AR terms; 'en' indexes EN terms."""
        fname = "domain-terminology.json" if domain == "technology" else f"domain-terminology-{domain}.json"
        p = _CORPUS / fname
        data = json.loads(p.read_text(encoding="utf-8"))
        patterns = [pair.get(side, "") for pair in data.get("pairs", []) if pair.get(side)]
        return cls(patterns)

    @classmethod
    def from_lexical_ai_phrases(cls) -> "AhoCorasick":
        """Build matcher from Asset C's ai_phrases input keys."""
        p = _CORPUS / "lexical-tables.json"
        data = json.loads(p.read_text(encoding="utf-8"))
        ai_phrases = data.get("tables", {}).get("ai_phrases", {}).get("entries", [])
        patterns = [e.get("input", "") for e in ai_phrases if e.get("input")]
        return cls(patterns)


if __name__ == "__main__":
    import argparse
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    ap = argparse.ArgumentParser(description="Aho-Corasick scanner over a toolkit asset")
    ap.add_argument("--source",
                    choices=["calque", "terminology-tech-ar", "terminology-news-ar",
                             "terminology-tech-en", "lexical-ai-phrases"],
                    default="calque")
    ap.add_argument("--input", help="File to scan (default: stdin)")
    ap.add_argument("--show-positions", action="store_true",
                    help="Print (start,end,pattern) tuples instead of just patterns")
    args = ap.parse_args()

    if args.source == "calque":
        ac = AhoCorasick.from_calque_dictionary()
    elif args.source == "terminology-tech-ar":
        ac = AhoCorasick.from_terminology_pairs("technology", "ar")
    elif args.source == "terminology-news-ar":
        ac = AhoCorasick.from_terminology_pairs("news", "ar")
    elif args.source == "terminology-tech-en":
        ac = AhoCorasick.from_terminology_pairs("technology", "en")
    elif args.source == "lexical-ai-phrases":
        ac = AhoCorasick.from_lexical_ai_phrases()
    else:
        print(f"unknown source: {args.source}", file=sys.stderr)
        sys.exit(1)

    text = Path(args.input).read_text(encoding="utf-8") if args.input else sys.stdin.read()
    n = 0
    seen: Set[str] = set()
    for start, end, pat in ac.iter_matches(text):
        n += 1
        if args.show_positions:
            print(f"{start}\t{end}\t{pat}")
        else:
            if pat not in seen:
                print(pat)
                seen.add(pat)
    sys.stderr.write(f"\n{n} match(es) of {len(ac.patterns)} pattern(s) in {len(text)} chars.\n")

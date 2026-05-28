#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_domain_terminology.py — Release gate for Asset G (paired EN↔AR terminology).
"""
from __future__ import annotations

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from domain_terminology import (
    asset_path,
    find_by_ar,
    find_by_en,
    iter_pairs,
    load_pairs,
    pair_count,
    pairs_for_en_text,
    soft_validate,
    stats,
    top_pairs,
)


def _assert(cond: bool, msg: str) -> bool:
    status = "PASS" if cond else "FAIL"
    print(f"  [{status}] {msg}")
    return cond


def main() -> int:
    print("=== Asset G: domain-terminology release gate ===\n")
    failures = 0

    if not _assert(asset_path().exists(),
                   f"asset_path exists: {asset_path()}"):
        failures += 1
        print("ABORT: no pairs file present. Run pair_terminology.py first.")
        return 1

    data = load_pairs()

    if not _assert(data.get("$schema_version") == "1.0.0",
                   f"schema_version is 1.0.0 (got {data.get('$schema_version')!r})"):
        failures += 1

    if not _assert(data.get("asset_name") == "domain-terminology",
                   f"asset_name is 'domain-terminology'"):
        failures += 1

    n_pairs = pair_count()
    if not _assert(n_pairs >= 20,
                   f"emitted >=20 pairs (got {n_pairs})"):
        failures += 1

    # The most important pair — artificial intelligence — must be present and correct
    ai_pair = find_by_ar("الذكاء الاصطناعي")
    if not _assert(ai_pair is not None,
                   "find_by_ar('الذكاء الاصطناعي') returns a pair"):
        failures += 1
    elif not _assert("intelligence" in ai_pair.get("en", "").lower(),
                     f"الذكاء الاصطناعي pairs to something containing 'intelligence' (got {ai_pair.get('en')!r})"):
        failures += 1

    # find_by_en reverse direction
    by_en = find_by_en("artificial intelligence")
    if not _assert(len(by_en) >= 1,
                   f"find_by_en('artificial intelligence') returns >=1 pair (got {len(by_en)})"):
        failures += 1

    # Case-insensitive find
    by_en_case = find_by_en("Artificial Intelligence")
    if not _assert(len(by_en_case) >= 1,
                   "find_by_en is case-insensitive"):
        failures += 1

    # text-scan
    hits = pairs_for_en_text("The CEO announced new artificial intelligence features.")
    if not _assert(len(hits) >= 1,
                   f"pairs_for_en_text finds >=1 hit in tech sentence (got {len(hits)})"):
        failures += 1

    # Confidence distribution — should have a non-trivial number of high-confidence
    s = stats()
    by_conf = s.get("by_confidence", {})
    if not _assert(by_conf.get("high", 0) >= 5,
                   f">=5 pairs with confidence=high (got {by_conf})"):
        failures += 1

    # Soft validate clean
    errs = soft_validate()
    if not _assert(errs == [], f"soft_validate returns no errors (got: {errs})"):
        failures += 1

    # Provenance has the proxy info
    prov = data.get("provenance", {})
    if not _assert("primary_proxy" in prov,
                   "provenance includes primary_proxy"):
        failures += 1

    # All pairs have required fields
    incomplete = [p for p in iter_pairs() if not all(
        k in p for k in ("ar", "en", "domain", "corpus_freq", "confidence", "proposer")
    )]
    if not _assert(len(incomplete) == 0,
                   f"all pairs have required fields (got {len(incomplete)} incomplete)"):
        failures += 1

    print()
    if failures:
        print(f"FAILED: {failures} test(s)")
        return 1
    print(f"OK: all release-gate tests pass. Asset G ready to ship.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

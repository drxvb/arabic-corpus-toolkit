#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_terminology.py — Release gate for Asset F (terminology candidates).

Validates that the shipped candidates file is structurally well-formed and
that the read API returns sensible values. Does NOT validate that the
candidates ARE good terminology — that's a domain-expert + LLM-pairing job
(Phase 2).
"""
from __future__ import annotations

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from terminology import (
    asset_path,
    candidate_count,
    has_term,
    iter_candidates,
    list_domains,
    load_candidates,
    soft_validate,
    stats,
    top_candidates,
)


def _assert(cond: bool, msg: str) -> bool:
    status = "PASS" if cond else "FAIL"
    print(f"  [{status}] {msg}")
    return cond


def main() -> int:
    print("=== Asset F: terminology release gate ===\n")
    failures = 0

    domains = list_domains()
    if not _assert("technology" in domains,
                   f"list_domains() includes 'technology' (got {domains})"):
        failures += 1
        print("ABORT: no technology candidates file present. Run mine_terminology.py first.")
        return 1

    data = load_candidates("technology")

    if not _assert(data.get("$schema_version") == "1.0.0",
                   f"schema_version is 1.0.0 (got {data.get('$schema_version')!r})"):
        failures += 1

    if not _assert(data.get("asset_name") == "terminology-candidates",
                   "asset_name is 'terminology-candidates'"):
        failures += 1

    if not _assert(data.get("domain") == "technology",
                   f"domain is 'technology' (got {data.get('domain')!r})"):
        failures += 1

    prov = data.get("provenance", {})
    n_articles = prov.get("n_articles_processed", 0)
    if not _assert(n_articles >= 100,
                   f"processed >=100 articles (got {n_articles:,})"):
        failures += 1

    n_tokens = prov.get("n_tokens_total", 0)
    if not _assert(n_tokens >= 10_000,
                   f"processed >=10K tokens (got {n_tokens:,})"):
        failures += 1

    count = candidate_count("technology")
    if not _assert(count >= 50,
                   f"emitted >=50 candidates (got {count})"):
        failures += 1

    # The top candidate should be a real tech term — for AITNews, Apple is dominant
    top5 = top_candidates("technology", n=5)
    top_terms = [c["term_ar"] for c in top5]
    if not _assert("آبل" in top_terms,
                   f"'آبل' (Apple) appears in top 5 (got {top_terms})"):
        failures += 1

    # has_term sanity
    if not _assert(has_term("آبل", "technology") is True,
                   "has_term('آبل', 'technology') is True"):
        failures += 1
    if not _assert(has_term("لا_يوجد_هذا_المصطلح_أبدا", "technology") is False,
                   "has_term(nonexistent) is False"):
        failures += 1

    # Top 50 candidates should have sample_contexts populated
    top_with_ctx = sum(1 for c in top_candidates("technology", n=50)
                      if c.get("sample_contexts"))
    if not _assert(top_with_ctx >= 30,
                   f">=30 of top 50 candidates have sample_contexts (got {top_with_ctx})"):
        failures += 1

    # ngram_size diversity — should have at least some bigrams/trigrams
    ngram_sizes = {c["ngram_size"] for c in iter_candidates("technology")}
    if not _assert(len(ngram_sizes) >= 2,
                   f"candidates span >=2 ngram sizes (got {ngram_sizes})"):
        failures += 1

    # soft_validate clean
    errs = soft_validate("technology")
    if not _assert(errs == [], f"soft_validate(technology) returns no errors (got: {errs})"):
        failures += 1

    # stats is structured
    s = stats()
    if not _assert("technology" in s.get("domains", {}),
                   "stats() includes 'technology' domain"):
        failures += 1

    # Asset path is real
    if not _assert(asset_path("technology").exists(),
                   f"asset_path('technology') exists: {asset_path('technology')}"):
        failures += 1

    print()
    if failures:
        print(f"FAILED: {failures} test(s)")
        return 1
    print(f"OK: all release-gate tests pass. Asset F (Phase 1) ready to ship.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

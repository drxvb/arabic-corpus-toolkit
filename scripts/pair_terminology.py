#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pair_terminology.py — Phase 2 of the Asset F pipeline.

Takes the Phase-1 candidates (corpus/terminology-candidates-<domain>.json)
and uses one or more LLM proxies to propose EN translations for each AR term.
Writes the result to corpus/domain-terminology.json with provenance + per-pair
confidence.

Uses LAN-local proxies documented at M:\\Main\\DevTools\\AI\\config\\llm-proxies.md.
No external API key needed — proxies are on `192.168.80.107`, free at runtime.

Usage:
    # Default: kimi-proxy, all candidates, written to corpus/domain-terminology.json
    python pair_terminology.py

    # Specify proxy, batch size, output
    python pair_terminology.py --proxy minimax --batch-size 25 \\
                               --output corpus/domain-terminology.json

    # Multi-vendor confirmation pass (after a single-vendor pass exists):
    #   Read existing pairs, send top N to a SECOND proxy, keep only pairs both agree on
    python pair_terminology.py --confirm-with codex --top 50

    # Sample mode (smoke test with first 10 candidates)
    python pair_terminology.py --sample 10

Python 3 stdlib only (urllib.request for HTTP).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


# Proxy registry — keys from M:\Main\DevTools\AI\config\llm-proxies.md §1
# (these are LAN-local only, not external API keys — see security notes in
# llm-proxies.md §6).
PROXIES = {
    "kimi":    {"url": "http://192.168.80.107:11435", "key": "U6hI7j57HpRpz9QaafTJLsJw5PlTXtxBM4pVNTknohE", "model": "kimi-cli"},
    "codex":   {"url": "http://192.168.80.107:11436", "key": "VJyi6yQDhEGNDE999FkHTqBAG21KdzmW",     "model": "gpt-5.5"},
    "gemini":  {"url": "http://192.168.80.107:11437", "key": "6fjc4jGwIhXQn7NejizvFVKR7Ps1SXES",     "model": "gemini-2.5-flash"},
    "minimax": {"url": "http://192.168.80.107:11438", "key": "xL5jUNR9A2lhN5HfLt1ulp9gE2CnBKf4",     "model": "MiniMax-M2.7"},
}


PAIRING_SYSTEM_PROMPT = (
    "You are a bilingual Arabic-English tech terminology expert. "
    "The user gives you Arabic tech-journalism terms (corpus-attested in Saudi/Gulf tech news). "
    "For each term, return the canonical English equivalent that a translator would use. "
    "Rules: "
    "(1) Output ONLY valid JSON array, no markdown fences, no prose explanation. "
    "(2) For brand names/transliterations (آبل, جوجل, آيفون), return the original English brand (Apple, Google, iPhone). "
    "(3) If a term is not technical terminology (generic words, dates, regions), set en=\"\" and confidence=\"low\". "
    "(4) Confidence: \"high\" = canonical translation universally agreed; \"medium\" = the most common but variants exist; "
    "\"low\" = unsure or term is generic. "
    "(5) Never invent. If you don't know, set en=\"\" and confidence=\"low\"."
)


def _build_user_prompt(batch: List[Dict[str, Any]]) -> str:
    """Build the user-content prompt for a batch of candidates."""
    lines = [
        "Map each Arabic tech term to its canonical English equivalent.",
        "",
        "Terms (with corpus frequency for context):",
    ]
    for i, c in enumerate(batch, start=1):
        lines.append(f"  {i}. {c['term_ar']}  (freq={c['freq']})")
    lines.append("")
    lines.append('Output JSON array. Example:')
    lines.append('[{"ar":"الذكاء الاصطناعي","en":"artificial intelligence","confidence":"high"},')
    lines.append(' {"ar":"البريد الإلكتروني","en":"email","confidence":"high"}]')
    return "\n".join(lines)


def _call_proxy(proxy_name: str, system_prompt: str, user_prompt: str,
                timeout: int = 120) -> Optional[str]:
    """POST to the chosen proxy. Returns the assistant's message content or None on failure."""
    if proxy_name not in PROXIES:
        sys.stderr.write(f"  unknown proxy: {proxy_name!r}\n")
        return None
    p = PROXIES[proxy_name]
    body = json.dumps({
        "model": p["model"],
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        "temperature": 0,  # determinism
    }, ensure_ascii=False).encode("utf-8")  # CRITICAL: UTF-8 not shell-encoded

    req = urllib.request.Request(
        url=p["url"] + "/v1/chat/completions",
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {p['key']}",
            "Content-Type":  "application/json; charset=utf-8",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        sys.stderr.write(f"  [{proxy_name}] network error: {e}\n")
        return None
    except (json.JSONDecodeError, KeyError) as e:
        sys.stderr.write(f"  [{proxy_name}] parse error: {e}\n")
        return None

    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        return None


def _parse_pairs_from_response(text: str) -> List[Dict[str, Any]]:
    """Extract JSON array of pairs from LLM response. Tolerates markdown fences,
    leading prose, trailing prose. Returns empty list on parse failure."""
    if not text:
        return []
    # Try direct parse first
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return parsed
    except json.JSONDecodeError:
        pass
    # Try to extract JSON array via greedy bracket match
    match = re.search(r"\[\s*\{.*\}\s*\]", text, re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group(0))
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            pass
    return []


def pair_candidates(candidates: List[Dict[str, Any]], proxy_name: str = "kimi",
                    batch_size: int = 20,
                    sleep_between: float = 0.5) -> List[Dict[str, Any]]:
    """Walk candidates in batches; query the proxy; accumulate pairs."""
    pairs: List[Dict[str, Any]] = []
    n_batches = (len(candidates) + batch_size - 1) // batch_size
    sys.stderr.write(f"Pairing {len(candidates)} candidates via {proxy_name} in "
                     f"{n_batches} batches of {batch_size} ...\n")

    started = time.time()
    for bi in range(n_batches):
        batch = candidates[bi * batch_size:(bi + 1) * batch_size]
        user_prompt = _build_user_prompt(batch)
        response = _call_proxy(proxy_name, PAIRING_SYSTEM_PROMPT, user_prompt)
        proposed = _parse_pairs_from_response(response or "")
        # Cross-reference proposed pairs against the batch's AR terms by exact match
        by_ar = {c["term_ar"]: c for c in batch}
        for prop in proposed:
            ar = prop.get("ar", "").strip()
            en = prop.get("en", "").strip()
            conf = prop.get("confidence", "medium").lower().strip()
            if not ar or ar not in by_ar:
                continue
            if not en or conf == "low":
                # Skip pairs the LLM was unsure about
                continue
            cand = by_ar[ar]
            pairs.append({
                "ar":   ar,
                "en":   en,
                "domain": "technology",
                "corpus_freq": cand["freq"],
                "ngram_size": cand["ngram_size"],
                "confidence": conf,
                "proposer":   proxy_name,
            })
        elapsed = time.time() - started
        sys.stderr.write(f"  batch {bi+1}/{n_batches}: {len(proposed)} proposed, "
                         f"{len(pairs)} accumulated, elapsed {elapsed:.1f}s\n")
        if sleep_between > 0 and bi < n_batches - 1:
            time.sleep(sleep_between)

    sys.stderr.write(f"Done. {len(pairs)} pairs collected from {len(candidates)} candidates.\n")
    return pairs


def confirm_with_second_vendor(pairs: List[Dict[str, Any]],
                               confirm_proxy: str,
                               batch_size: int = 20) -> List[Dict[str, Any]]:
    """For each pair, ask a second proxy to confirm the EN translation.
    Returns enriched pairs with cross_llm_agreement and proposer fields."""
    sys.stderr.write(f"Cross-checking {len(pairs)} pairs with {confirm_proxy} ...\n")

    confirmed_pairs: List[Dict[str, Any]] = []
    n_batches = (len(pairs) + batch_size - 1) // batch_size
    for bi in range(n_batches):
        batch = pairs[bi * batch_size:(bi + 1) * batch_size]
        candidates_for_batch = [
            {"term_ar": p["ar"], "freq": p["corpus_freq"], "ngram_size": p["ngram_size"]}
            for p in batch
        ]
        user_prompt = _build_user_prompt(candidates_for_batch)
        response = _call_proxy(confirm_proxy, PAIRING_SYSTEM_PROMPT, user_prompt)
        proposed = _parse_pairs_from_response(response or "")
        by_ar = {p["ar"]: p for p in batch}
        confirmed_by_ar = {}
        for prop in proposed:
            ar = prop.get("ar", "").strip()
            en = prop.get("en", "").strip().lower()
            if ar and en:
                confirmed_by_ar[ar] = en

        for p in batch:
            second_en = confirmed_by_ar.get(p["ar"], "").lower()
            first_en = p["en"].lower()
            if second_en and (second_en == first_en or first_en in second_en or second_en in first_en):
                enriched = dict(p)
                enriched["cross_llm_agreement"] = True
                enriched["confirmed_by"] = confirm_proxy
                enriched["confidence"] = "high"
                confirmed_pairs.append(enriched)
            else:
                enriched = dict(p)
                enriched["cross_llm_agreement"] = False
                enriched["confirmed_by"] = confirm_proxy
                enriched["disagreement_alt_en"] = confirmed_by_ar.get(p["ar"], "")
                confirmed_pairs.append(enriched)
        sys.stderr.write(f"  confirm batch {bi+1}/{n_batches}\n")
        time.sleep(0.3)

    n_agree = sum(1 for p in confirmed_pairs if p.get("cross_llm_agreement"))
    sys.stderr.write(f"Cross-check done. {n_agree}/{len(confirmed_pairs)} pairs agree.\n")
    return confirmed_pairs


def main() -> int:
    p = argparse.ArgumentParser(description="Phase 2: LLM-pair AR terminology candidates")
    p.add_argument("--input", "-i",
                   default="corpus/terminology-candidates-technology.json",
                   help="Path to Phase 1 candidates JSON")
    p.add_argument("--output", "-o",
                   default="corpus/domain-terminology.json",
                   help="Where to write the paired terminology JSON")
    p.add_argument("--proxy", default="kimi",
                   choices=list(PROXIES.keys()),
                   help="Primary LLM proxy")
    p.add_argument("--confirm-with", default=None,
                   choices=list(PROXIES.keys()),
                   help="Second LLM proxy for cross-vendor confirmation")
    p.add_argument("--batch-size", type=int, default=20)
    p.add_argument("--sample", type=int,
                   help="Process only first N candidates (smoke test)")
    p.add_argument("--top", type=int,
                   help="Process only top N candidates by frequency")
    p.add_argument("--ngram-filter", default="all",
                   choices=["all", "bigram_trigram", "bigram", "trigram"],
                   help="Filter candidates by n-gram size before pairing. "
                        "Default 'all'. 'bigram_trigram' skips unigrams "
                        "(most are particles/generic; multi-word terms are gold).")
    args = p.parse_args()

    # Load candidates
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: input candidates file not found: {input_path}", file=sys.stderr)
        return 1
    data = json.loads(input_path.read_text(encoding="utf-8"))
    candidates = data.get("candidates", [])
    if not candidates:
        print(f"ERROR: no candidates in input file", file=sys.stderr)
        return 1

    # Filter by n-gram size
    if args.ngram_filter == "bigram_trigram":
        candidates = [c for c in candidates if c["ngram_size"] in ("bigram", "trigram")]
    elif args.ngram_filter == "bigram":
        candidates = [c for c in candidates if c["ngram_size"] == "bigram"]
    elif args.ngram_filter == "trigram":
        candidates = [c for c in candidates if c["ngram_size"] == "trigram"]

    if args.top:
        candidates = candidates[:args.top]
    if args.sample:
        candidates = candidates[:args.sample]

    sys.stderr.write(f"Will pair {len(candidates)} candidates (after filters).\n")

    pairs = pair_candidates(candidates, proxy_name=args.proxy,
                            batch_size=args.batch_size)

    if args.confirm_with:
        pairs = confirm_with_second_vendor(pairs, args.confirm_with,
                                           batch_size=args.batch_size)

    payload = {
        "$schema_version": "1.0.0",
        "asset_name": "domain-terminology",
        "domain": data.get("domain", "technology"),
        "provenance": {
            "source_candidates_file": str(input_path),
            "source_candidates_count": len(candidates),
            "n_articles_processed": data.get("provenance", {}).get("n_articles_processed"),
            "primary_proxy": args.proxy,
            "primary_model": PROXIES[args.proxy]["model"],
            "confirm_proxy": args.confirm_with,
            "confirm_model": PROXIES[args.confirm_with]["model"] if args.confirm_with else None,
            "ngram_filter": args.ngram_filter,
            "pairing_timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        },
        "notes": [
            "Phase 2 output: LLM-paired EN translations for Phase-1 AR candidates.",
            "Each pair carries corpus_freq (Phase-1 frequency) + LLM proposer + confidence.",
            "When --confirm-with is used, pairs also carry cross_llm_agreement and confirmed_by fields.",
        ],
        "pairs": pairs,
    }
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                           encoding="utf-8")
    print(f"Wrote {len(pairs)} pairs to {output_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

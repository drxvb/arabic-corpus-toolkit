#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
domain_classify_and_pair.py — v1.9.0 single-pass classification + pairing.

Takes existing AR terminology candidates and asks an LLM to do two things at
once: propose the canonical EN translation AND classify the term into a domain
({business, legal, politics, geographic, other}). Output splits into separate
G.{domain} files.

This is the pragmatic domain-expansion approach. Instead of mining new corpora
(slow, expensive, requires source documents), we reuse Elaph's 498 news
candidates and let the LLM partition them by domain. The same minimax→codex→
gemini swarm pattern can then cross-validate each split.

Usage:
    python scripts/domain_classify_and_pair.py \\
        --input corpus/terminology-candidates-news.json \\
        --proxy minimax \\
        --output-dir corpus/ \\
        --top 300

Output files (only created if a domain has >= N pairs):
    corpus/domain-terminology-business.json
    corpus/domain-terminology-legal.json
    corpus/domain-terminology-politics.json

Pairs marked "geographic" or "other" are dropped — these are not actionable
terminology for translator/authoring stage A. The drop list is reported.

Python 3 stdlib only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.request
import urllib.error
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


PROXIES = {
    "kimi":    {"url": "http://192.168.80.107:11435", "key": "U6hI7j57HpRpz9QaafTJLsJw5PlTXtxBM4pVNTknohE", "model": "kimi-cli"},
    "codex":   {"url": "http://192.168.80.107:11436", "key": "VJyi6yQDhEGNDE999FkHTqBAG21KdzmW",     "model": "gpt-5.5"},
    "gemini":  {"url": "http://192.168.80.107:11437", "key": "6fjc4jGwIhXQn7NejizvFVKR7Ps1SXES",     "model": "gemini-2.5-flash"},
    "minimax": {"url": "http://192.168.80.107:11438", "key": "xL5jUNR9A2lhN5HfLt1ulp9gE2CnBKf4",     "model": "MiniMax-M2.7"},
}

CLASSIFY_PROMPT = (
    "You are a bilingual Arabic-English news/terminology classifier. "
    "For each Arabic term, produce TWO outputs: (1) the canonical English term, "
    "(2) a domain classification. "
    "Domains: business (economy, finance, trade, markets), "
    "legal (laws, courts, treaties, government institutions), "
    "politics (elections, parties, leaders, diplomacy, conflict), "
    "geographic (countries, regions, places — NOT terminology), "
    "other (general news, dates, names not classifiable). "
    "Rules: "
    "(1) Output ONLY a valid JSON array. No markdown fences. No prose. "
    "(2) Each item: {\"ar\":\"...\",\"en\":\"...\",\"domain\":\"business|legal|politics|geographic|other\",\"confidence\":\"high|medium|low\"}. "
    "(3) If a term is a proper name (Saddam Hussein, etc.) classify under the most relevant context — usually politics for political figures. "
    "(4) Never invent English. If you don't know, set en=\"\" and confidence=\"low\"."
)


def _build_user_prompt(batch: List[Dict[str, Any]]) -> str:
    lines = [
        "Classify and translate each Arabic term. Return JSON array.",
        "",
        "Terms (with corpus frequency for context):",
    ]
    for i, c in enumerate(batch, start=1):
        lines.append(f"  {i}. {c['term_ar']}  (freq={c['freq']})")
    lines.append("")
    lines.append('Output JSON array: [{"ar":"...","en":"...","domain":"...","confidence":"..."}, ...]')
    return "\n".join(lines)


def _call_proxy(proxy_name: str, system: str, user_prompt: str,
                timeout: int = 180) -> Optional[str]:
    p = PROXIES[proxy_name]
    body = json.dumps({
        "model": p["model"],
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0,
    }, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url=p["url"] + "/v1/chat/completions", data=body, method="POST",
        headers={"Authorization": f"Bearer {p['key']}",
                 "Content-Type": "application/json; charset=utf-8"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"]
    except (urllib.error.URLError, json.JSONDecodeError, KeyError, IndexError) as e:
        sys.stderr.write(f"  [{proxy_name}] error: {e}\n")
        return None


def _parse_array(text: str) -> List[Dict[str, Any]]:
    if not text:
        return []
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return parsed
    except json.JSONDecodeError:
        m = re.search(r"\[\s*\{.*\}\s*\]", text, re.DOTALL)
        if m:
            try:
                parsed = json.loads(m.group(0))
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                pass
    return []


def classify(candidates: List[Dict[str, Any]], proxy_name: str,
             batch_size: int = 20) -> List[Dict[str, Any]]:
    """Walk candidates, classify+translate via single LLM pass.
    Returns enriched candidates with domain + en fields."""
    n_batches = (len(candidates) + batch_size - 1) // batch_size
    sys.stderr.write(f"Classifying {len(candidates)} candidates via {proxy_name} in {n_batches} batches of {batch_size}...\n")
    enriched: List[Dict[str, Any]] = []
    started = time.time()
    by_ar_to_cand = {c["term_ar"]: c for c in candidates}
    for bi in range(n_batches):
        batch = candidates[bi * batch_size:(bi + 1) * batch_size]
        response = _call_proxy(proxy_name, CLASSIFY_PROMPT, _build_user_prompt(batch))
        proposed = _parse_array(response or "")
        n_kept = 0
        for prop in proposed:
            ar = (prop.get("ar") or "").strip()
            en = (prop.get("en") or "").strip()
            domain = (prop.get("domain") or "other").strip().lower()
            confidence = (prop.get("confidence") or "medium").lower().strip()
            if not ar or ar not in by_ar_to_cand:
                continue
            if not en or confidence == "low":
                continue
            cand = by_ar_to_cand[ar]
            enriched.append({
                "ar": ar, "en": en,
                "domain": domain,
                "corpus_freq": cand["freq"],
                "ngram_size": cand["ngram_size"],
                "confidence": confidence,
                "proposer": proxy_name,
            })
            n_kept += 1
        elapsed = time.time() - started
        sys.stderr.write(f"  batch {bi+1}/{n_batches}: kept {n_kept}/{len(batch)}, "
                         f"total {len(enriched)} pairs, elapsed {elapsed:.1f}s\n")
        if bi < n_batches - 1:
            time.sleep(0.3)
    sys.stderr.write(f"Done. {len(enriched)} pairs classified from {len(candidates)} candidates.\n")
    return enriched


def write_domain_files(pairs: List[Dict[str, Any]], output_dir: Path,
                      proxy_name: str,
                      include_domains: List[str],
                      min_pairs_per_domain: int = 5) -> Dict[str, int]:
    """Split pairs by domain, write one JSON file per included domain
    that has >= min_pairs_per_domain entries."""
    by_domain: Dict[str, List[Dict[str, Any]]] = {}
    for p in pairs:
        by_domain.setdefault(p["domain"], []).append(p)
    written: Dict[str, int] = {}
    for domain in include_domains:
        dpairs = by_domain.get(domain, [])
        if len(dpairs) < min_pairs_per_domain:
            sys.stderr.write(f"  Skipping {domain}: only {len(dpairs)} pairs (<{min_pairs_per_domain})\n")
            continue
        out_path = output_dir / f"domain-terminology-{domain}.json"
        payload = {
            "$schema_version": "1.0.0",
            "asset_name": "domain-terminology",
            "domain": domain,
            "provenance": {
                "source_method": "single-pass classify+pair from terminology-candidates-news.json",
                "primary_proxy": proxy_name,
                "primary_model": PROXIES[proxy_name]["model"],
                "n_pairs": len(dpairs),
                "pairing_timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            },
            "notes": [
                f"v1.9.0 domain expansion: {proxy_name}-classified pairs from Elaph news corpus.",
                f"Domain '{domain}' selected; geographic + other dropped.",
            ],
            "pairs": dpairs,
        }
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        written[domain] = len(dpairs)
        sys.stderr.write(f"  Wrote {len(dpairs)} pairs → {out_path}\n")
    return written


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="terminology-candidates-*.json")
    ap.add_argument("--proxy", default="minimax", choices=list(PROXIES.keys()))
    ap.add_argument("--batch-size", type=int, default=20)
    ap.add_argument("--top", type=int, help="Process only top N candidates")
    ap.add_argument("--output-dir", default="corpus/")
    ap.add_argument("--include-domains", default="business,legal,politics",
                    help="Comma-separated domains to write files for")
    ap.add_argument("--min-pairs-per-domain", type=int, default=5)
    args = ap.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: input not found: {input_path}", file=sys.stderr)
        return 1
    data = json.loads(input_path.read_text(encoding="utf-8"))
    candidates = data.get("candidates", [])
    if args.top:
        candidates = candidates[:args.top]

    enriched = classify(candidates, proxy_name=args.proxy, batch_size=args.batch_size)

    print()
    print(f"Domain distribution:")
    dist = Counter(p["domain"] for p in enriched)
    for domain, count in dist.most_common():
        print(f"  {domain:<15} {count}")
    print()

    out_dir = Path(args.output_dir)
    include = [d.strip() for d in args.include_domains.split(",") if d.strip()]
    written = write_domain_files(enriched, out_dir, args.proxy, include,
                                  min_pairs_per_domain=args.min_pairs_per_domain)
    print()
    print(f"Files written:")
    for domain, count in written.items():
        print(f"  domain-terminology-{domain}.json  ({count} pairs)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

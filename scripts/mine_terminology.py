#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mine_terminology.py — Phase 1 of the Asset F (terminology) pipeline.

Walks a monolingual Arabic news corpus, extracts candidate domain terminology
ranked by frequency, with sample contexts for each candidate. Writes the
results to corpus/terminology-candidates.json.

Phase 2 (downstream, not in this script): for each candidate, propose an EN
translation (via LLM, Kimi CLI, human review, etc.) and add validated pairs
to corpus/domain-terminology.json. The candidates file is the input for that
phase; it is NOT itself the final terminology dictionary.

Supported corpora (discovered by inspection):
  Y:\\Linguistics\\News\\Technology\\AITNews    -- 64K AR tech articles
  Y:\\Linguistics\\News\\General\\Elaph         -- 3.8K AR general news

Usage:
    # Mine AITNews (default), top 500 candidates, write to default path
    python mine_terminology.py

    # Specify corpus + output + cap
    python mine_terminology.py --corpus "Y:\\Linguistics\\News\\Technology\\AITNews" \\
                               --domain technology \\
                               --top 1000 \\
                               --output corpus/terminology-candidates-technology.json

    # Sample mode (fast — for development; reads first N articles only)
    python mine_terminology.py --sample 200

Python 3 stdlib only.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


# ── Stop words: high-frequency Arabic function words that should NOT be terminology candidates ──
# Curated list of common particles, prepositions, pronouns, common verbs that appear in nearly every
# article. Filtering them removes ~80% of noise from raw frequency counts.
ARABIC_STOPWORDS = {
    # Particles & conjunctions
    "في", "من", "إلى", "على", "عن", "مع", "هذا", "هذه", "ذلك", "تلك", "التي", "الذي",
    "ما", "لا", "لم", "لن", "إن", "أن", "أو", "كل", "كما", "حيث", "بين", "بعد", "قبل",
    "عند", "لدى", "كان", "كانت", "يكون", "تكون", "ليس", "ليست", "هو", "هي", "هم", "هن",
    "نحن", "أنت", "أنا", "أنتم", "قد", "لقد", "حتى", "إذا", "لكن", "ولكن", "أيضا", "ايضا",
    # Common verbs (conjugated forms)
    "قال", "قالت", "أكد", "أكدت", "أعلن", "أعلنت", "أوضح", "أوضحت", "ذكر", "ذكرت",
    "أشار", "أشارت", "يقول", "تقول", "يعتبر", "تعتبر", "يعد", "تعد", "يمكن", "تمكن",
    # Common adjectives / nouns that are too generic
    "الجديد", "الجديدة", "الكبير", "الكبيرة", "الصغير", "الصغيرة", "أول", "آخر", "الأخير",
    "العديد", "العديدة", "بعض", "كل", "جميع", "هناك", "هنا", "حالة", "حالات", "نحو",
    # Number / time words
    "اليوم", "أمس", "العام", "الأعوام", "السنة", "السنوات", "الشهر", "الأسبوع", "اليومين",
    "الأخيرة", "الأخير", "الماضي", "الماضية", "القادم", "القادمة", "الجاري", "الجارية",
    # Pronouns / demonstratives with attached prefixes
    "الذين", "اللاتي", "اللواتي", "اللذان", "اللتان", "نفس", "نفسه", "نفسها",
    # Vacuous words common in news
    "الحديث", "الحديثة", "المقبل", "المقبلة", "الراهن", "الراهنة", "هكذا", "أيضاً", "كذلك",
    # Single-letter / very-short noise
    "ا", "و", "أ", "إ",
    # ── v1.0.0 sample-feedback additions: words that survived initial filter ──
    "خلال", "وذلك", "مثل", "بشكل", "أنها", "أنه", "غير", "عام", "ايضا", "أيضا",
    "وذلك", "وهذا", "وقد", "حول", "نحو", "ضمن", "خلال", "خلاله", "فيه", "فيها",
    "حيث", "بحيث", "كانت", "وكان", "وكانت", "حين", "وحين", "إذ", "وإذ",
    "أكثر", "أقل", "أكبر", "أصغر", "أهم", "أبرز", "أعلى", "أدنى", "كبير", "كبيرة",
    "صغير", "صغيرة", "جديد", "جديدة", "قديم", "قديمة",
    # Numeric / quantitative without terminology value
    "مليون", "مليار", "ألف", "آلاف", "ملايين", "مليارات", "دولار", "ريال",
    "نسبة", "نسبتها", "بنسبة", "حوالي", "تقريبا", "تقريباً",
    # Time / news temporal noise
    "اليومين", "أيام", "ساعة", "ساعات", "دقيقة", "دقائق", "ثانية", "ثوان",
    # Generic high-frequency nouns (common across all news, low terminology signal)
    "شركة", "الشركة", "شركات", "الشركات",  # "company" — generic; if part of a brand bigram it'll still appear
    "موقع", "الموقع", "مواقع", "المواقع",  # "site/website" — too generic alone
    "تطبيق", "التطبيق", "تطبيقات", "التطبيقات",  # "app" — too generic alone (but real terminology in compounds)
    "جهاز", "الجهاز", "أجهزة", "الأجهزة",  # "device" — generic
    "هاتف", "الهاتف", "هواتف", "الهواتف",  # "phone" — generic (but valid in compounds)
    "نظام", "النظام", "أنظمة", "الأنظمة",  # "system" — generic
    "خدمة", "الخدمة", "خدمات", "الخدمات",  # "service" — generic
    "ميزة", "الميزة", "ميزات", "الميزات",  # "feature" — generic
}

# Tashkeel (diacritics) — strip for normalization
TASHKEEL_PATTERN = re.compile(r"[ً-ْٰـ]")
# Arabic letter range for term-candidate matching
ARABIC_WORD_RE = re.compile(r"[ء-ي]+")


def _normalize(text: str) -> str:
    """Strip tashkeel + tatweel. Don't fold alif/yaa variants — those carry meaning."""
    return TASHKEEL_PATTERN.sub("", text)


def _tokenize(text: str) -> List[str]:
    """Extract Arabic word tokens. Keeps multi-letter words only."""
    text = _normalize(text)
    return [t for t in ARABIC_WORD_RE.findall(text) if len(t) >= 3]


def _generate_ngrams(tokens: List[str], n: int) -> List[str]:
    """Generate n-grams from token list. Returns space-joined strings."""
    if len(tokens) < n:
        return []
    return [" ".join(tokens[i:i + n]) for i in range(len(tokens) - n + 1)]


def _extract_article_text(article_path: Path) -> str:
    """Pull the meaningful text out of an AITNews-style JSON article.
    Decodes HTML entities (the corpus has &quot; / &#8220; embedded).
    Tolerates non-dict shapes: a small minority of articles in AITNews are
    error-response wrappers stored as lists; skip them silently."""
    try:
        data = json.loads(article_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return ""
    if not isinstance(data, dict):
        return ""
    parts: List[str] = []
    for key in ("title", "description", "content"):
        v = data.get(key)
        if isinstance(v, str):
            parts.append(v)
    return html.unescape(" ".join(parts))


def _is_candidate_term(term: str) -> bool:
    """Filter rules for whether a unigram/bigram/trigram is a candidate term."""
    parts = term.split()
    # Each part must be Arabic letters only, and not a stop word
    for p in parts:
        if not ARABIC_WORD_RE.fullmatch(p):
            return False
        if p in ARABIC_STOPWORDS:
            return False
        # Reject the bare definite article (would survive ARABIC_WORD_RE)
        if p == "ال":
            return False
        # Strip leading ال for stop-word check (الكلمة → كلمة)
        if p.startswith("ال") and len(p) > 2:
            stem = p[2:]
            if stem in ARABIC_STOPWORDS:
                return False
    return True


def _prune_counter(counter: Counter, min_freq: int) -> None:
    """In-place: drop entries with freq < min_freq. Used to bound memory
    growth during the corpus walk — bigram/trigram counters explode with
    one-off entries that will never pass the final min-freq filter."""
    to_drop = [k for k, v in counter.items() if v < min_freq]
    for k in to_drop:
        del counter[k]


def mine_corpus(corpus_dir: Path, sample_limit: Optional[int] = None,
                progress_every: int = 1000,
                prune_every: int = 5000,
                prune_min_freq: int = 2) -> Dict[str, Any]:
    """Walk corpus_dir, return {unigrams, bigrams, trigrams, n_articles, n_tokens}.
    Each *gram entry is a Counter of term -> frequency.

    Memory management: every `prune_every` articles, drop counter entries with
    freq < prune_min_freq. This caps the long tail of one-off bigrams/trigrams
    that would never pass the final min-freq filter anyway. Keeps memory bounded
    at the cost of a slight under-count for borderline-rare terms (a term that
    appears 3 times in articles 1-5000 but 0 times after gets pruned at the
    5000 mark; this is acceptable for terminology mining where we only care
    about high-frequency terms).
    """
    unigrams: Counter = Counter()
    bigrams: Counter = Counter()
    trigrams: Counter = Counter()

    n_articles = 0
    n_tokens_total = 0
    n_prunes = 0
    started = time.time()

    files = sorted(corpus_dir.glob("*.json"))
    if sample_limit is not None:
        files = files[:sample_limit]

    sys.stderr.write(f"Walking {len(files):,} articles from {corpus_dir} ...\n")

    n_skipped = 0
    for i, article_path in enumerate(files, start=1):
        # Per-article try/except: a single bad article (corrupt JSON,
        # encoding error, unexpected shape) should not kill the whole walk.
        # The list-not-dict case is handled by _extract_article_text, but this
        # outer guard catches anything else (encoding errors, etc).
        try:
            text = _extract_article_text(article_path)
        except Exception:
            n_skipped += 1
            continue
        if not text:
            continue
        tokens = _tokenize(text)
        n_tokens_total += len(tokens)
        n_articles += 1

        for t in tokens:
            if _is_candidate_term(t):
                unigrams[t] += 1

        for bg in _generate_ngrams(tokens, 2):
            if _is_candidate_term(bg):
                bigrams[bg] += 1

        for tg in _generate_ngrams(tokens, 3):
            if _is_candidate_term(tg):
                trigrams[tg] += 1

        if i % prune_every == 0:
            before_u, before_b, before_t = len(unigrams), len(bigrams), len(trigrams)
            _prune_counter(unigrams, prune_min_freq)
            _prune_counter(bigrams, prune_min_freq)
            _prune_counter(trigrams, prune_min_freq)
            n_prunes += 1
            sys.stderr.write(f"  [prune {n_prunes}] unigrams {before_u:,}->{len(unigrams):,}, "
                             f"bigrams {before_b:,}->{len(bigrams):,}, "
                             f"trigrams {before_t:,}->{len(trigrams):,}\n")

        if i % progress_every == 0:
            elapsed = time.time() - started
            rate = i / elapsed if elapsed > 0 else 0
            sys.stderr.write(f"  {i:,}/{len(files):,} articles, "
                             f"{rate:.0f} art/s, "
                             f"{len(unigrams):,} unique unigrams, "
                             f"{len(bigrams):,} bigrams\n")

    elapsed = time.time() - started
    sys.stderr.write(f"Done in {elapsed:.1f}s. {n_articles:,} articles, "
                     f"{n_tokens_total:,} tokens, {n_prunes} prunes.\n")

    return {
        "n_articles_processed": n_articles,
        "n_tokens_total": n_tokens_total,
        "unigrams": unigrams,
        "bigrams": bigrams,
        "trigrams": trigrams,
        "elapsed_s": round(elapsed, 1),
        "n_prunes": n_prunes,
    }


def _sample_contexts(corpus_dir: Path, term: str, max_samples: int = 3,
                     max_articles_to_scan: int = 200) -> List[str]:
    """Find up to max_samples occurrence contexts for a term (best-effort).
    Scans up to max_articles_to_scan articles to keep this cheap."""
    contexts: List[str] = []
    files = sorted(corpus_dir.glob("*.json"))[:max_articles_to_scan]
    for f in files:
        if len(contexts) >= max_samples:
            break
        text = _normalize(_extract_article_text(f))
        idx = text.find(term)
        if idx < 0:
            continue
        # 50 chars before, 50 chars after
        start = max(0, idx - 50)
        end = min(len(text), idx + len(term) + 50)
        snippet = text[start:end].strip().replace("\n", " ")
        contexts.append(snippet)
    return contexts


def build_candidates_payload(mining_result: Dict[str, Any], corpus_dir: Path,
                             domain: str, top_n: int = 500,
                             min_freq: int = 5) -> Dict[str, Any]:
    """Convert the raw Counters into a structured candidates payload."""
    candidates: List[Dict[str, Any]] = []

    # Take top N from each n-gram size, weighted toward higher N (bigrams/trigrams
    # carry more terminological meaning than bare unigrams).
    per_bucket = max(50, top_n // 3)

    for n_label, counter in [("unigram", mining_result["unigrams"]),
                              ("bigram", mining_result["bigrams"]),
                              ("trigram", mining_result["trigrams"])]:
        for term, freq in counter.most_common(per_bucket):
            if freq < min_freq:
                break
            candidates.append({
                "term_ar": term,
                "freq": freq,
                "ngram_size": n_label,
                "sample_contexts": [],  # filled in below for top candidates
            })

    # Re-sort by freq desc, cap to top_n
    candidates.sort(key=lambda c: c["freq"], reverse=True)
    candidates = candidates[:top_n]

    # Sample contexts for the top 50 only (expensive scan)
    for c in candidates[:50]:
        c["sample_contexts"] = _sample_contexts(corpus_dir, c["term_ar"])

    return {
        "$schema_version": "1.0.0",
        "asset_name": "terminology-candidates",
        "domain": domain,
        "provenance": {
            "corpus_path": str(corpus_dir),
            "n_articles_processed": mining_result["n_articles_processed"],
            "n_tokens_total": mining_result["n_tokens_total"],
            "mining_elapsed_s": mining_result["elapsed_s"],
            "extraction_script": "scripts/mine_terminology.py",
            "min_freq_threshold": min_freq,
            "top_n_kept": top_n,
        },
        "notes": [
            "AR-side monolingual extraction. EN translations are NOT provided -- this is Phase 1.",
            "Phase 2 (downstream): propose EN translations per candidate and validate, then promote to corpus/domain-terminology.json.",
            "Top 50 candidates include sample_contexts (50-char windows). Others have empty contexts to keep file size manageable.",
            "Stop-word filtering applied; tashkeel stripped at tokenization time.",
        ],
        "candidates": candidates,
    }


def main() -> int:
    p = argparse.ArgumentParser(description="Phase 1 terminology mining for Asset F")
    p.add_argument("--corpus", default=r"Y:\Linguistics\News\Technology\AITNews",
                   help="Path to corpus directory containing JSON articles")
    p.add_argument("--domain", default="technology",
                   help="Domain tag for the output (technology / news / business / ...)")
    p.add_argument("--top", type=int, default=500,
                   help="Cap on number of candidates emitted")
    p.add_argument("--min-freq", type=int, default=5,
                   help="Minimum frequency for a candidate to be emitted")
    p.add_argument("--sample", type=int,
                   help="Sample mode: process only first N articles (for development)")
    p.add_argument("--output", "-o", required=True, help="Output JSON path")
    args = p.parse_args()

    corpus_dir = Path(args.corpus)
    if not corpus_dir.exists():
        print(f"ERROR: corpus not found: {corpus_dir}", file=sys.stderr)
        return 1

    result = mine_corpus(corpus_dir, sample_limit=args.sample)
    payload = build_candidates_payload(result, corpus_dir, args.domain,
                                       top_n=args.top, min_freq=args.min_freq)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                        encoding="utf-8")
    print(f"Wrote {len(payload['candidates'])} candidates to {out_path}",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

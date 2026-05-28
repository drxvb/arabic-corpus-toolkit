# 06 — Terminology pipeline (Asset F)

## Why this exists

The calque dictionary (Asset A) catalogs **AI errors**: "AI says X badly, here's the natural-AR fix." It's 340 entries focused on the AI-tell catalogue, not on standard terminology.

The translator's Stage A needs broader terminology coverage: standard EN↔AR pairs for common tech/news terms whether or not AI translates them badly. "Cloud computing" isn't a calque (the LLM can translate it), but it should still have a known standard translation Stage A injects into the prompt. Asset F (terminology) covers this gap.

## Why a two-phase pipeline

Per the v0.1.1 audit of `Y:\Linguistics\NewsDataForTranslation`, the SPA corpus has **0 paired EN-AR articles** (38,897 EN-only + 38,859 AR-only directories). The richest corpus available is **AITNews** (`Y:\Linguistics\News\Technology\AITNews`) — 64,486 monolingual Arabic tech articles.

Naive paths and why they're wrong:

- **LLM-generates 200 EN→AR pairs**: unverifiable. Hallucinations look plausible. No corpus authority.
- **Walk corpora for terms + assume the LLM can pair them**: same hallucination risk in the pairing step.
- **Wait for SPA download to complete**: indefinite (the download is 41,500/80,002 in progress with no ETA).

The two-phase approach makes pairing **verifiable**:

```
Phase 1 (this release):
  AR corpus  →  scripts/mine_terminology.py  →  corpus/terminology-candidates-<domain>.json
  (64K AR articles → top-N AR terms by frequency, with sample contexts)

Phase 2 (downstream, when first paired batch is ready):
  Candidates  →  LLM proposes EN for each AR term  →  verify proposed EN against EN-side corpus
  →  corpus/domain-terminology.json (validated EN↔AR pairs)
```

Phase 2's verification step is what separates real terminology from LLM invention: every AR term in the candidate list is **demonstrably used in real tech journalism** (frequency evidence + sample contexts), so an LLM-proposed EN that translates back to a similar AR phrase passes; one that translates to an AR phrase nobody uses fails.

## Phase 1 deliverables (toolkit v0.8)

- `scripts/mine_terminology.py` — extraction script. Python stdlib only. Walks a JSON-article corpus, tokenizes Arabic text (strip tashkeel + tatweel), filters by stopwords (~150 entries, expandable), counts unigrams/bigrams/trigrams, ranks by frequency, samples contexts for the top 50. Configurable: `--corpus`, `--domain`, `--top`, `--min-freq`, `--sample` (dev mode).
- `corpus/terminology-candidates-technology.json` — initial Phase-1 output from the full AITNews corpus (64,486 articles). Top 1000 candidates with min-freq 20.
- `corpus/terminology-candidates.schema.json` — JSON Schema draft-2020-12 for the Phase-1 file shape.
- `scripts/terminology.py` — read API. 9 functions: `load_candidates`, `candidate_count`, `list_domains`, `iter_candidates`, `top_candidates`, `has_term`, `asset_path`, `soft_validate`, `stats`.
- `scripts/test_terminology.py` — release gate.

## Phase 2 plan (toolkit v0.9+)

Not in this release. The Phase-2 file shape will be:

```json
{
  "$schema_version": "1.0.0",
  "asset_name": "domain-terminology",
  "pairs": [
    {
      "en": "cloud computing",
      "ar": "الحوسبة السحابية",
      "domain": "technology",
      "ar_corpus_freq": 1247,
      "ar_corpus_path": "Y:\\Linguistics\\News\\Technology\\AITNews",
      "pairing_method": "llm-proposed + corpus-validated",
      "pairing_provenance": "candidates-technology.json freq=1247 + LLM agreement (3-of-3)",
      "confidence": "high"
    },
    ...
  ]
}
```

Pairing workflow (executed via Kimi CLI / Claude / Codex — any LLM the user picks):

1. Take top N candidates from `terminology-candidates-<domain>.json`.
2. For each candidate, ask an LLM: "What's the English term that corresponds to this AR tech-journalism term? Return one canonical term."
3. Validate: the proposed EN term, when reverse-translated, should produce an AR term that exists in the candidates list at meaningful frequency (within 5x of the original).
4. Optionally: use 2-3 LLMs and accept only pairs where they agree (cross-LLM swarm — matches the v2.6.0 multi-agent review pattern).
5. Promote validated pairs to `domain-terminology.json`.

The user can run Phase 2 with any LLM tooling they have available — the scripts in this repo never make LLM calls themselves.

## Stopword calibration

The mining script's `ARABIC_STOPWORDS` set is intentionally **conservative-leaning-aggressive**: it filters more words than a generic NLP stopword list because the goal is *terminology candidates*, not lexical coverage. Common nouns like `شركة` (company), `جهاز` (device), `هاتف` (phone), `موقع` (website) are filtered from unigrams because they're too generic to be terminology on their own — but they survive in bigrams/trigrams where they're part of compound terms (`شركة آبل`, `الذكاء الاصطناعي`).

Expanding the stopword list and re-running is the expected iteration loop. The script runs in ~100 seconds on the full 64K AITNews corpus, so iterations are cheap.

## Provenance

Asset F is the first toolkit asset that didn't come from the humanizer's prior work — it's net-new corpus mining motivated by the user's request to give the translator a real terminology base beyond the AI-error catalog (recorded in this repo's session log; the user said "let kimi CLI or whatever extract and create dictionaries for that based on content data I provided for news and technology news, to know the right terminology and correct translations to be used").

Mining corpora: `Y:\Linguistics\News\Technology\AITNews` (64,486 articles, technology domain). `Y:\Linguistics\News\General\Elaph` (3,805 articles, news domain — pending).

## Outstanding work

- v0.8: Phase 1 for `technology` domain (this release).
- v0.8.1+ (when convenient): Phase 1 for `news` general domain (Elaph corpus).
- v0.9 (when first paired batch ready): Phase 2 → `domain-terminology.json` with validated pairs.
- Translator vNext: Stage A consumes both calque-dictionary (Asset A) AND domain-terminology (Asset F) so prompts get both AI-correction hints AND standard-translation hints.

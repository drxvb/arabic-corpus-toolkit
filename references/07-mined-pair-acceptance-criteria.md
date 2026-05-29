# 07 — Mined-pair acceptance criteria

**Toolkit version**: v1.12.1
**Status**: Canonical specification for what makes an AR↔EN pair "active" vs. "below threshold" vs. "rejected."

This document formalizes the release gate that's been operating informally since v1.10.0. Two of the four v1.10.0 roadmap-challenge vendors (Minimax + Kimi) independently flagged "mined-pair quality gate / acceptance criteria" as a missing P0/P1 item. This is the gate.

## Stages of a pair's lifecycle

### Stage 1 — Candidate (`terminology-candidates-*.json`)

Output of `scripts/mine_terminology.py` (or equivalent JSONL-based extractors for SPA-style bilingual corpora).

A **candidate** is an Arabic n-gram (1, 2, or 3 tokens) extracted from a source corpus by frequency, with:

- `term_ar: str` — the Arabic n-gram
- `freq: int` — corpus frequency
- `ngram_size: "unigram" | "bigram" | "trigram"`
- `sample_contexts: List[str]` — up to 3 corpus excerpts where it appears

**Acceptance criteria for candidates**:
- Must pass `_is_candidate_term()` (curated stopword filter + ≥3 characters + no digit-only / pure-punctuation)
- Must meet `--min-freq` (defaults 5 for Elaph-scale, 8-12 for SPA-scale depending on bucket)
- Top-N capped per domain (typically 200-300)

Candidates are NOT terminology yet. They're inputs to Stage 2.

### Stage 2 — Paired candidate (added to `domain-terminology-*.json`)

Output of `scripts/pair_terminology.py` or `scripts/domain_classify_and_pair.py`.

A **paired candidate** has:
- Everything in Stage 1
- `en: str` — the proposed English translation
- `proposer: str` — which LLM proposed it ("minimax", "kimi", "codex", "gemini")
- `confidence: "high" | "medium" | "low"` — proposer's self-rated confidence
- `corpus_freq: int` — copied from `freq` for downstream compatibility

**Acceptance criteria for paired candidates**:
- `en` is non-empty and non-whitespace
- Proposer didn't set `confidence == "low"` AND the script's `if conf == 'low': skip` policy enforced this
- Paired candidates land in the `pairs` array initially (pre-confirm)

A paired candidate is NOT active until Stage 4.

### Stage 3 — Cross-vendor confirmed (`*_agree` fields populated)

Each paired candidate is challenged independently by ≥3 independent LLM vendors (codex + gemini + kimi). The proposer (typically minimax) ALSO votes, but its vote is excluded from the consensus count because it carries self-bias.

A **confirmed pair** has:
- `codex_agree: bool`
- `gemini_agree: bool`
- `kimi_agree: bool`
- `minimax_agree: bool` (informational only — excluded from consensus)
- `*_alt: str | null` — when a vendor disagrees, its proposed alternative
- `n_independent_agree: int ∈ [0, 3]` — sum of codex/gemini/kimi yes-votes
- `n_vendors_agree: int ∈ [0, 4]` — sum of all 4 yes-votes (informational)
- `vendor_consensus: "strong" | "single_vendor" | "rejected"` — derived from n_independent_agree

### Stage 4 — Tier classification

`n_independent_agree` is the canonical gate. Pairs split into:

| Tier | n_independent_agree | Disposition | `vendor_consensus` field |
|---|---|---|---|
| **Strong** | 3 of 3 | `pairs` array (active) | `"strong"` |
| **Majority** | 2 of 3 | `pairs` array (active) | `"strong"` (currently same bucket; reserved for future split) |
| **Single-vendor** | 1 of 3 | `pairs` array (active) | `"single_vendor"` |
| **Rejected** | 0 of 3 | `pairs_below_threshold` array | `"rejected"` |

**Active threshold**: `n_independent_agree >= 1`. This is the default the `pairs` array reflects. Rejected pairs (0/3) are NEVER loaded by consumers reading the `pairs` field — they live in `pairs_below_threshold` for audit/provenance only.

### Stage 5 — Era / source provenance

- `source_corpus: "elaph-news-2003-2008" | "spa-news-2024" | absent` (v1.4.0+)
- `era_locked: str | absent` — era identifier when the pair's meaning is bound to a specific historical period (v1.5.0+)
- `era_locked_reason: str | absent` — human-readable rationale

## Consumer access patterns

### Default (preserves prior behavior)

```python
data = _load_domain_terminology("business")  # translator
# or: data = _load_asset_g("business")          # authoring
for pair in data["pairs"]:
    # All active pairs (n_independent_agree >= 1 OR pre-v1.10.0 legacy pairs)
    use(pair)
```

### Stricter — only majority-or-better consensus

```python
hits = translator.translate(text_en, domain="business", min_consensus=2)
# or:
hits = authoring._find_terminology_hits(text, domain="business", min_consensus=2)
```

### Filter out era-locked

```python
data = _load_domain_terminology("politics")
current_only = [p for p in data["pairs"] if not p.get("era_locked")]
```

### Combined — strict consensus AND current-only

```python
hits = translator.translate(text_en, domain="politics", min_consensus=2)
# Then post-filter the result for era_locked.
```

## Release gates (enforced)

Before any release that touches `domain-terminology-*.json`:

1. **`evals/contract_conformance.py`** must pass (56+ assertions; counts grow as schema does).
   - In particular: `pairs_below_threshold` array present per domain file, `n_independent_agree` ∈ [0,3] per active pair, `validation_method` block present.
2. **`evals/golden_e2e_test.py`** must pass (40 assertions covering the family pipeline).
3. **`asset-registry.json`** must reflect the new `current_version`, `n_active_pairs`, `n_below_threshold` for each modified asset.
4. **CHANGELOG.md** must have a release section with the version, date, methodology, per-vendor agreement matrix (when newly mined), and tier breakdown.

## What this gate does NOT enforce (deliberate gaps)

- **Per-vendor selection bias**: codex consistently rejects more politics pairs than gemini; we don't normalize for this. The 3-independent-vendor count is a raw OR, not a weighted average. Documented per-vendor rates in CHANGELOG release notes serve as transparency.
- **Embedding-based duplicate detection**: pairs with same EN but different AR (e.g., "حقوق الإنسان" vs "حقوق الانسان") are both kept; consumers handling normalization at translation time is the intended fallback.
- **BLEU / human evaluation**: pair quality is gated by vendor consensus, not by held-out human translation gold standard. This is intentional — the multi-vendor swarm IS the proxy for human consensus.
- **Frequency floor for `pairs_below_threshold`**: rejected pairs are preserved at full fidelity for audit; consumers wanting size optimization should filter on their side.

## Provenance of this gate

- v1.10.0 introduced the 4-vendor confirm + 3-independent-vendor consensus tier (after Sonnet/Codex/Kimi A5 evaluators flagged that v1.9.0 mined pairs lacked validation parity with G.technology).
- v1.10.1's `evals/contract_conformance.py` codified the schema-level assertions (assertion count grew as new fields landed).
- v1.11.0 extended the gate across multi-corpus sources (Elaph + SPA) with additive `source_corpus` field.
- v1.12.0 added era-locking metadata.
- **v1.12.1 (this document) formalizes the gate that's been operating informally for two releases.**

When a new domain (G.health, G.science, etc.) is added in the future, this document is the binding spec for what "active" means.

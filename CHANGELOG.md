# Changelog

Per the Kimi-style asset-promotion lens of the v0.2 multi-agent review, this toolkit uses **per-asset SemVer with a registry** rather than monolithic versions. The toolkit release version (v0.3, etc.) coordinates ship cadence; the schema version of each data file lives **inside** the file under `$schema_version` and follows independent SemVer.

## v1.4.2 — Documentation reconciliation (3-evaluator audit response)

**Released:** 2026-05-28

Triangulated evaluation by Sonnet (filesystem-grounded), Codex (gpt-5.5), and Gemini (gemini-2.5-pro) scored the family 62/72/65 = mean 66/100 with **strong consensus on documentation drift between claimed state (SKILL.md, CHANGELOG, ROADMAP) and observed state (actual code + asset files)**.

Sonnet found specific evidence:
- CHANGELOG ended at v1.0.0 but `domain-terminology.json` was at schema 1.4.0
- Aho-Corasick claimed "out of scope" in v1.0.0 entry but shipped fully in v1.3.0
- `bilingual_export.py` shipped without any CHANGELOG/SKILL.md/ROADMAP mention
- Toolkit SKILL.md body Roadmap table called v0.3 "current" and scheduled v1.0 for Q2 2027

This release backfills the missing CHANGELOG entries. No code change.

## v1.4.1 — Golden e2e regression suite (roadmap item #3)

**Released:** 2026-05-28

`evals/golden_e2e_test.py`: 21 deterministic OFFLINE assertions across all 4 siblings. Toolkit asset shapes + counts, translator Stage A hit counts, humanizer score_text + Asset D/E behavior, authoring suite Asset G consumption. All anchor pairs (artificial intelligence, cloud computing, 5G, email) verified to be present in Asset G. Catches silent regressions when any release ships.

Multi-agent roadmap consensus item (both codex + minimax critics ranked top-5).

## v1.4.0 — Codex cross-validation of v0.12+v0.13 legacy pairs (roadmap item #2)

**Released:** 2026-05-28

v0.9.1 + v0.10 cross-vendored the top 50 + 16 disagreements. v0.12 + v0.13 added 328 more pairs single-vendor (minimax). v1.4.0 sent all 328 through codex-proxy for confirmation. **182/328 codex agreement (55%).** Lower than v0.9.1's 68% because mid-frequency pairs have more genuine ambiguity (synonym variants, register-specific preferences). Asset G `domain-terminology.json` now has cross-LLM coverage on the full 422 technology pairs. Schema bumped to v1.4.0 (provenance fields added).

## v1.3.0 — Aho-Corasick matcher (closes Codex's v0.2 forward-compat door)

**Released:** 2026-05-28

Aho-Corasick deferred since v0.3 because the linear scan was sufficient at 340 patterns × KB-sized inputs. v1.3.0 ships it anyway to close Codex's v0.2 multi-agent review "forward-compat door" promise. `AhoCorasick.from_calque_dictionary()` builds in 4ms from 340 patterns. `AhoCorasick.from_terminology_pairs(domain, side='ar'|'en')` from 422 pairs. `AhoCorasick.from_lexical_ai_phrases()` from 67 phrases. Generic `from_strings(list)` for ad-hoc patterns. `iter_matches(text)` yields (start, end, pattern) including overlapping matches. O(L+matches) scan vs linear O(P*L). Python 3 stdlib only.

**Note:** the v1.0.0 entry below stated this was "deliberately out of scope" — v1.3.0 reversed that decision because the architecture promise was load-bearing for the toolkit's v1.x stability claim. Future v2.0 consumer can adopt incrementally.

## v1.2.0 — bilingual_export.py for external CAT tools

**Released:** 2026-05-28

`scripts/bilingual_export.py`: unifies Asset G across all domains (technology + news = 472 pairs total, 386 high-confidence) into a single exchange artifact for external consumers — CAT tools (memoQ/SDL Trados/OmegaT), MT post-editing pipelines. Four formats: tsv, json, tbx-lite (TermBase eXchange Basic subset), markdown. Filters by `--domains` and `--min-confidence {high,medium,low}`. Dedup by AR (prefers higher corpus_freq when same AR appears in multiple domains).

## v1.1.0 — family_doctor.py cross-asset health check

**Released:** 2026-05-28

`scripts/family_doctor.py`: single-command introspection across the family. Reports 9 assets (A/B/C/D/E/F.tech/F.news/G.tech/G.news) with schema versions + item counts + sizes, 3 consumer skills with reachability checks, 4 LLM proxies with health probes. Exit code 0 = full health, 1 = asset validation failure, 2 = consumer missing. JSON mode for monitoring integration.

## v1.0.0 — STABLE FREEZE

**Released:** 2026-05-28

The toolkit is stable. All seven assets are present with documented schemas, soft-validation, and at least one live consumer.

### Asset inventory at v1.0.0

| Asset | File | Schema | Consumers |
|---|---|---|---|
| A | `corpus/calque-dictionary.json` | v1.2.0 | humanizer v2.7.0+, translator v0.2+ |
| B | `corpus/empirical-patterns.json` | v1.0.0 | translator v0.3+ (via corpus_stats) |
| B' | `scripts/register.py` (code-encoded) | n/a | humanizer, authoring-suite |
| C | `corpus/lexical-tables.json` | v1.1.0 | **humanizer v2.7.1+ (hard dep v2.8.0+)**, translator v0.2.2+ |
| D | `corpus/typography-rules.json` | v1.0.0 | (consumer integration pending) |
| E | `corpus/reader-respect-patterns.json` | v1.0.0 | (consumer integration pending) |
| F | `corpus/terminology-candidates-{technology,news}.json` | v1.0.0 | translator v0.3.0+ (verification signal) |
| G | `corpus/domain-terminology.json` (technology, 422 pairs cross-vendor validated) + `domain-terminology-news.json` (news, 50 pairs) | v1.3.1 | translator v0.3.1+ (direct EN injection) |

### Stability commitments

- **Per-asset SemVer is enforced**: MAJOR bumps require consumer updates; MINOR/PATCH are backward-compatible. The schema-major-refuse pattern is implemented in every consumer cutover.
- **No schema breaking changes** without MAJOR bump (e.g., v1.x → v2.0.0).
- **LICENSE attribution chain** documented for all seven assets including the LLM-proxy provenance for Assets F/G.
- **Multi-vendor LLM swarm** is operational for terminology validation: minimax + codex + gemini all available as drop-in OpenAI endpoints.

### Pipeline maturity

```
Corpus mining   → Phase 1 candidates → LLM pairing (single vendor) →
Cross-LLM confirmation (codex) → Three-way tiebreaker (gemini) → Bulk expansion → Multi-domain.
                                                                            ↑ proven through v0.8 → v0.14
```

Every step in the pipeline has been exercised at scale and audited through the Agent Portal (`taskbus.AuditEvents`).

### What's deliberately out of scope for v1.0.0

- **Aho-Corasick matcher**: not implemented in v1.0.0. The linear scan was sufficient for typical KB-sized inputs at 340 patterns. **NOTE (added in v1.4.2 docs reconciliation):** v1.3.0 reversed this decision and shipped the full implementation at `scripts/aho_corasick.py`. The v1.0.0 "out of scope" claim was accurate at the time but became contradictory once v1.3.0 shipped. See v1.3.0 entry above.
- Consumer integrations for Assets D and E: pending — toolkit ships the data; consumers haven't cut over yet. Doesn't block v1.0.0.
- News-domain cross-LLM validation: v0.14 ships single-vendor pairs. v1.x can add cross-vendor passes for the news domain matching the technology workflow.

## v0.14 — News domain added (50 paired terms from Elaph)

50 paired terms from Elaph corpus (3,801 AR articles). Second domain after technology. Note: corpus is Iraq-War-era heavy; terminology is dated but valid.

## v0.13 — Codex confirmation on v0.12 new pairs + Elaph corpus mined

34/50 codex agreement on top 50 of v0.12 additions. Plus: Elaph mined (498 candidates). Pairing landed in v0.14.

## v0.12 — Bulk-pair expansion to 422 pairs (third portal-native release)

**Released:** 2026-05-28

**Coverage scale-up.** v0.10 had 162 paired terms covering the highest-frequency tech terms. v0.12 pairs the remaining bigram+trigram candidates [300:666] from v0.8's terminology-candidates-technology.json (366 new candidates) via minimax-proxy. Result: **+260 new pairs (71% acceptance), final 422 pairs**. Third portal-native release: TaskID=12, PlanID=12.

### Highlights of newly-added terminology

| AR | EN | Corpus freq |
|---|---|---|
| القابل للطي | foldable | 987 |
| بطاقات الذاكرة | memory cards | 987 |
| فتحة عدسة | lens aperture | 976 |
| الشاشة الرئيسية | home screen | 964 |
| منصات التواصل | social media platforms | 978 |
| الأسواق العالمية | global markets | 964 |
| التقاط الصور | photo capture | 985 |
| الصور ومقاطع الفيديو | photos and videos | 956 |
| نشرة الأخبار | newsletter | 975 |

### Why 71% acceptance on mid-tier vs 56% on top-tier

Counterintuitive but explainable. Top candidates include the most generic terms (الشركة = company, الإنترنت = internet) and geographic noise (الإمارات, السعودية) that get filtered as not-terminology. Mid-frequency candidates are MORE likely to be specific terminology: foldable phones, memory cards, lens apertures. The long tail of corpus frequency has higher terminology density than the head.

### Merge behavior

- **Zero overlap** between v0.10 (candidates [0:300]) and v0.12 (candidates [300:666]) — disjoint slices by design
- Existing pairs preserved: v0.10's cross_llm_agreement / three_way_verdict / needs_manual_review fields intact for the top 50 + 16
- New pairs are single-vendor (minimax) at confidence high/medium — future v0.13 could cross-validate with codex+gemini

### Schema bump 1.2.0 → 1.3.0 (MINOR additive — more rows, same shape)

No new fields, no schema changes. v1.0.0/1.1.0/1.2.0 readers see 422 pairs where they used to see fewer; nothing else differs. The translator's `pairs_for_en_text()` finds more hits on the same input automatically (mtime cache picks up the new asset).

### Portal trace

Audit timeline rows #26-#30:
- #26 task_started
- #27 plan_created (PlanID=12)
- #28 plan_approved (via portal actions API)
- #29 plan_executed
- #30 task_completed

### Asset version state at end of v0.12

| Asset | Schema | Notes |
|---|---|---|
| `corpus/domain-terminology.json` | **v1.3.0** | **422 pairs** (162 from v0.10 + 260 new from minimax). Translator picks up the expansion automatically via mtime cache. |

## v0.10 — Three-way LLM tiebreaker (gemini-proxy resolves v0.9.1 disagreements)

**Released:** 2026-05-28

**Completes the multi-vendor swarm.** v0.9 paired via minimax. v0.9.1 cross-checked via codex (34/50 agreement). v0.10 brings gemini-2.5-flash as **third independent vendor** to resolve the 16 remaining disagreements. Second portal-native release: TaskID=11, PlanID=11 in `taskbus`, audit timeline #21-#25.

### Decision rule

| Codex says | Gemini says | Verdict |
|---|---|---|
| empty | empty | **drop_consensus** (2+ LLMs reject as non-terminology) |
| same as minimax | — | keep_minimax |
| codex's alt | matches codex | switch_to_codex (better English) |
| differ | differ from both | three_way_differ → keep minimax + `needs_manual_review: true` |

### Outcomes from the 16 disagreements

| Verdict | Count | Examples |
|---|---|---|
| `drop_consensus` | **6** | UAE / Saudi Arabia (2 forms) / Middle East & Africa / European Union / دولة الإمارات — all geographic, codex+gemini agreed not-terminology |
| `switch_to_codex` | **5** | IT→`information technology` (×2), `videos`→`video clips`, `mAh`→`milliampere`, `ICT`→`information and communications` |
| `keep_minimax` | **3** | `الجيل الثالث` (codex's "3G" was too specific, gemini agreed third generation); `البوابة التقنية` (codex said empty, gemini agreed tech portal); `فيروس كورونا → coronavirus` (codex said empty; gemini correctly identified pandemic-era tech-news terminology) |
| `three_way_differ` | **2** | `بنظام أندرويد` (three reasonable English variants); `بسعة جيجابايت` (three paraphrases). Kept minimax + flagged `needs_manual_review` |

### Net change

- **v0.9.1 had 168 pairs. v0.10 has 162 pairs** (-6 geographic).
- **5 pairs got better English** via codex+gemini consensus.
- **3 minimax wins survived** the codex challenge thanks to gemini's independent vote.

### The coronavirus diagnostic

`فيروس كورونا`: codex returned empty (thought it wasn't tech). Minimax and gemini both kept it as `coronavirus`. This is the most architecturally important resolution: **two vendors disagreeing with one another is more informative than two vendors agreeing wrongly**. If v0.10 had been a two-LLM swarm (minimax+codex), codex's empty would have dropped coronavirus from the dictionary. With three independent vendors, gemini rescued it. The vendor-diversity property of the proxy fleet is what makes this resilient.

### Schema bump 1.1.0 → 1.2.0 (MINOR additive)

New optional fields on tiebroken pairs:
- `gemini_tiebreaker_en: str`
- `three_way_verdict: str` (one of: `drop_consensus` / `keep_minimax (gemini concurs)` / `switch_to_codex (gemini concurs)` / `three_way_differ` / `three_way_agree (normalization)`)
- `needs_manual_review: bool` (only present when `three_way_differ`)
- `previous_en: str` (only present when `switch_to_codex`; preserves what was overridden)

v1.0.0 and v1.1.0 readers ignore all new fields. `domain_terminology.py` loader unchanged.

### Portal trace

Audit timeline rows #21-#25:
- #21 task_started
- #22 plan_created (PlanID=11)
- #23 plan_approved (via portal actions API)
- #24 plan_executed
- #25 task_completed

### Asset version state at end of v0.10

| Asset | Schema | Notes |
|---|---|---|
| `corpus/domain-terminology.json` | **v1.2.0** | 162 pairs (down from 168), 5 enriched with three-way verdict + tiebreaker EN; 2 flagged for manual review |

## v0.9.1 — Cross-LLM confirmation on top 50 paired terms (executed via Agent Portal Phase 2)

**Released:** 2026-05-28

**Operationalized through the Agent Portal.** Used the portal infrastructure documented at `M:\Main\AI\Master\docs\AGENT-PORTAL.md`:

1. Registered agent `arabic-corpus-toolkit-claude` in `taskbus.Capabilities` with 9-action whitelist.
2. Enqueued task `arabic-corpus-toolkit.v0.9.1.cross-llm-confirmation` (TaskID=10).
3. Proposed a 5-step Phase-2 plan (PlanID=10) — flagged `NeedsConfirmation=true` because 3 steps are mutating (edit_code + write_documentation + commit_release).
4. Approved via `POST http://192.168.80.112:3100/api/plans/10/approve`.
5. Executed: codex-proxy confirmation pass on top 50 minimax-paired terms.
6. Marked plan + task complete; audit timeline shows the full sequence.

**Result:** 34/50 cross-LLM agreement (68%). The 16 disagreements reveal three signal types:

| Type | Example | Interpretation |
|---|---|---|
| Synonym preference | minimax: `IT` / codex: `information technology` | Both valid; codex prefers expanded form |
| Precision improvement | minimax: `videos` / codex: `video clips` | Codex more rigorous |
| **Real filter** | minimax: `الإمارات العربية المتحدة → United Arab Emirates` / codex: `""` | **Codex correctly rejects geographic term as non-tech terminology** |

The geographic-term rejection is the most important diagnostic: v0.9 had 4-6 country/region names paired as "tech terminology" because they had high AITNews frequency (UAE/Saudi Arabia mentions in tech news). Codex's stricter confidence filter caught them. v0.9.1 preserves them with `cross_llm_agreement: false` + `disagreement_alt_en: ""` so a future v0.10 review can prune.

**Schema bump v1.0.0 → v1.1.0 (MINOR additive).** Three optional fields added to enriched pairs: `cross_llm_agreement: bool`, `confirmed_by: str`, `disagreement_alt_en: str`. v1.0.0 readers ignore them. The translator's `domain_terminology.py` loader continues to work unchanged.

### Asset version state at end of v0.9.1

| Asset | Schema | Notes |
|---|---|---|
| `corpus/domain-terminology.json` | **v1.1.0** | Top 50 pairs enriched with cross-LLM agreement field. Other 118 pairs unchanged from v0.9. |

## v0.9 — Asset G (paired EN↔AR terminology) — Phase 2 of the terminology pipeline

**Released:** 2026-05-28

**The Phase 2 ship.** v0.8 mined 999 AR-side candidates from AITNews. v0.9 executes the LLM-pairing step the user asked for ("let kimi CLI or whatever extract and create dictionaries"). Made possible by reading `M:\Main\DevTools\AI\config\.ai-instructions.md` which documents four LAN-local OpenAI-compatible LLM proxies (`192.168.80.107:11435-11438` — kimi/codex/gemini/minimax, free, no signup). The proxies aren't external API calls — they're free-at-runtime LAN services explicitly intended for AI sessions to use.

- **`scripts/pair_terminology.py`** — Phase-2 pairing script. Loads Phase-1 candidates, batches them, sends to a chosen proxy with a strict system prompt ("output only valid JSON array, no markdown, never invent"), parses the response with tolerant regex fallback, accumulates validated pairs. Configurable: `--proxy` (kimi/codex/gemini/minimax), `--batch-size`, `--ngram-filter` (skip noisy unigrams), `--top` / `--sample`, `--confirm-with` (multi-vendor agreement). Uses `urllib.request` only — no `pip install openai` needed (matches the toolkit's stdlib-only discipline).
- **`corpus/domain-terminology.json`** — Phase-2 output. Top 300 bigram+trigram candidates from technology domain paired by minimax-proxy. Each pair: `{ar, en, domain, corpus_freq, ngram_size, confidence, proposer}`. Pairs with cross-vendor agreement also carry `cross_llm_agreement: bool` + `confirmed_by`. Schema v1.0.0.
- **`corpus/domain-terminology.schema.json`** — JSON Schema for paired terms. Tracks proposer + confidence taxonomy + optional cross-vendor fields.
- **`scripts/domain_terminology.py`** — 9-function read API: `load_pairs`, `pair_count`, `iter_pairs`, `find_by_en` (case-insensitive), `find_by_ar`, `pairs_for_en_text` (whole-word scan for translator Stage A injection), `top_pairs`, `soft_validate`, `stats`.
- **`scripts/test_domain_terminology.py`** — 10-assertion release gate.

### Why proxies instead of external APIs

The .ai-instructions.md routes AI sessions to LAN proxies because they're free at runtime, sub-second latency on flash models, and bound to subscriptions Basil already pays for. For terminology pairing this matters because:
1. **Cost:** ~300 batched LLM calls = real money on external APIs. Free here.
2. **Latency:** Pairing 300 candidates takes ~17 minutes; on external APIs the latency would be similar but with real-dollar cost per token.
3. **Multi-vendor:** Kimi + Codex + Gemini + MiniMax all available as drop-in OpenAI endpoints, enabling the cross-LLM-agreement filter the original v2.6.0 multi-agent review architecture depends on.

### Stdlib-only LLM client

`pair_terminology.py` uses `urllib.request` rather than the `openai` SDK because the toolkit's discipline is Python stdlib only — `pip install openai` would violate the "no pip install required" property of every script in this repo. The HTTP shape is OpenAI-compatible (the proxies *are* OpenAI Chat Completions schema), so urllib's 30-line POST does the same job as `openai.ChatCompletion.create(...)`. Matches the same pattern as the translator's existing Stage C LLM client (also urllib).

### Asset version state at end of v0.9

| Asset | Schema | Notes |
|---|---|---|
| `corpus/terminology-candidates-technology.json` | v1.0.0 | unchanged from v0.8 |
| `corpus/domain-terminology.json` | **v1.0.0** | **NEW** in v0.9 |

## v0.8 — Asset F (terminology candidates) — net-new corpus-mined asset

**Released:** 2026-05-28

**Why this exists.** The calque dictionary (Asset A) catalogs AI errors. It does NOT cover standard terminology. A user translating "cloud computing" through the translator gets no Stage A hint because it's not a known calque — the LLM defaults to whatever it thinks. Asset F fills that gap: corpus-mined EN-tech terminology with sample contexts, ready for Phase 2 LLM-assisted pairing into validated EN↔AR pairs.

**First net-new asset.** A-E all came from the humanizer's prior work. Asset F is mined from scratch from `Y:\Linguistics\News\Technology\AITNews` (64,485 monolingual AR tech articles). User-driven: "let kimi CLI or whatever extract and create dictionaries for that based on content data I provided for news and technology news, to know the right terminology and correct translations to be used."

- **`scripts/mine_terminology.py`** — Python stdlib extractor. Walks a JSON-article corpus, decodes HTML entities, tokenizes Arabic (strip tashkeel + tatweel, keep ≥3-char words), filters by ~150-entry stopword set (particles, generic nouns, temporal noise, intensifiers), counts unigrams + bigrams + trigrams, prunes counters every 5000 articles to bound memory (drops freq=1 entries), samples 50-char contexts for the top 50 candidates. Configurable: `--corpus`, `--domain`, `--top`, `--min-freq`, `--sample` (dev mode).
- **`corpus/terminology-candidates-technology.json`** — Phase-1 output. Top 1000 candidates with min-freq 20 from the full 64,485-article AITNews corpus. Schema v1.0.0.
- **`corpus/terminology-candidates.schema.json`** — JSON Schema draft-2020-12 covering the candidate-file shape. Top-level required fields: `$schema_version`, `asset_name` (const "terminology-candidates"), `domain` (free-form string), `provenance` (corpus path + article/token counts), `candidates` (array of `{term_ar, freq, ngram_size, sample_contexts}`).
- **`scripts/terminology.py`** — 9-function typed read API: `load_candidates`, `candidate_count`, `list_domains`, `iter_candidates`, `top_candidates`, `has_term`, `asset_path`, `soft_validate`, `stats`. mtime-keyed cache keyed by domain (multi-domain support: one cache slot per domain).
- **`scripts/test_terminology.py`** — release gate. Validates: schema fields present, ≥100 articles processed, ≥10K tokens, ≥50 candidates emitted, top 5 includes a known tech term, `has_term` works both ways, top 50 candidates have sample_contexts, n-gram diversity, soft-validate clean, stats structured.
- **`references/06-terminology-pipeline.md`** — permanent record. Documents why two-phase (Phase 1 mines AR-side candidates, Phase 2 LLM-pairs them with EN translations + validates), why naive paths (LLM-only generation; SPA download wait) were rejected, stopword calibration approach, and the Phase 2 workflow template for the user to execute via Kimi CLI / Claude / Codex / whatever LLM tooling they have.

### Phase 2 plan (not in this release)

Promote validated EN↔AR pairs from candidates into `corpus/domain-terminology.json` (separate asset). Workflow: top N candidates → LLM proposes EN per AR term → reverse-translation verifies AR appears in candidates at meaningful frequency → cross-LLM agreement filter (Kimi + Claude + Codex multi-vendor swarm) → promote to pairs file. The scripts in this repo never make LLM calls themselves; Phase 2 is run by the user with their LLM tooling of choice.

### Translator integration (not in this release; lands in translator vNext)

Asset F's Phase 1 candidates don't have EN translations, so they can't be naively injected into Stage A's LLM prompt. The right integration is a **verification signal**: Stage A's existing calque-dictionary recommendations get a `corpus_confirmed: bool` field via `terminology.has_term(natural_arabic, "technology")`. Calques whose natural-AR form appears in the candidates list get higher Stage-A confidence than those that don't. Lands in a follow-up translator release once toolkit v0.8 is on disk.

### Asset version state at end of v0.8

| Asset | Schema | Notes |
|---|---|---|
| `corpus/lexical-tables.json` | v1.1.0 | unchanged from v0.7.1 |
| `corpus/terminology-candidates-technology.json` | **v1.0.0** | **NEW** in v0.8 |

## v0.7.1 — Asset C parity audit + humanizer-code reconciliation

**Released:** 2026-05-28

**Why this exists.** v0.7 migrated Asset C from `arabic-ai-text-humanizer/references/13-inherited-lexical-tables.md` (Markdown documentation). When preparing the humanizer cutover, reading `scripts/humanize_v2.py` revealed the live code had evolved past the documentation. v0.7.1 brings the asset to parity with the v2.7.0 humanizer code before any consumer touches it.

- **`corpus/lexical-tables.json`** → schema **v1.1.0** (MINOR, backward-relaxing):
  - `ai_phrases`: **40 → 67 entries**. Added 6 pro-drop deletions (Arabic prefers implicit subjects for fluff verbs; `""` is a valid alternative), 7 clause-preserving variants (distinct treatment for `…أن` clausal vs bare), 16 newsroom AI-tells (from the cross-LLM journalist critique), 4 English-calque pipeline entries (`خط أنابيب → مسار عمل`), tashkeel-bearing variants.
  - `connectors`: 21 → 22 (added tashkeel-bearing `في حين أنّ` alongside bare `في حين أن`).
  - `repetitive_starters`: 7 → 11 detectors (humanizer has tashkeel + bare variants for the same verbs).
  - `quote_verbs`: 3 → 4 entries (separate tashkeel + bare for `ذكر أن`/`أنّ`).
  - **`structural_openers`** (NEW table, replaces v1.0.0's `templated_starters`): 10 regex patterns with capture groups and `{0}`-positional substitution — was `advisory_strategy` in v1.0.0 (documentation-only); now `regex_capture_substitute` (mechanically applicable).
  - **`intensifier_destack`** (NEW table, replaces v1.0.0's `global_policies.intensifier_destacking` advisory note): 8 regex patterns as first-class table with `regex_substitute` policy.
- **`corpus/lexical-tables.schema.json`** → updated with two new policy defs (`table_regex_capture_substitute`, `table_regex_substitute`); relaxed `alternatives` items from `minLength: 1` to `minLength: 0` so pro-drop `""` is structurally valid; `x-changelog` block documents the v1.0.0 → v1.1.0 evolution.
- **`scripts/lexical_tables.py`** → added `structural_opener_patterns()`, `intensifier_destack_patterns()`; updated `soft_validate()`'s EXPECTED_POLICIES map.
- **`scripts/test_lexical_tables.py`** → 19 assertions → 24 assertions, updated to humanizer-parity content (e.g., `quote_verb_pool('قال')` now expects `أكّد` with tashkeel; ai_phrases count is 67).
- **`references/05-asset-c-migration-audit.md`** — permanent record of the v0.7 gap, why it happened, and the principle encoded for future migrations: **the cutover step IS the audit step; data-asset migrations should always terminate at the consumer's actual code, not its documentation.**

### Asset version state at end of v0.7.1

| Asset | Schema | Notes |
|---|---|---|
| `corpus/lexical-tables.json` | **v1.1.0** | **Parity with humanizer v2.7.0** confirmed |

## v0.7 — Asset C migration (lexical-tables) with policy-in-data

**Released:** 2026-05-28

- **`corpus/lexical-tables.json`** (Asset C — final base asset from the original v0.2 migration plan): consolidated deterministic lexical-substitution layer migrated from `arabic-ai-text-humanizer/references/13-inherited-lexical-tables.md`. Schema v1.0.0.
  - Seven sub-tables: `ai_phrases` (30 v1 + 10 Gap A), `connectors` (8 v1 + 13 Gap B), `repetitive_starters` (7 detectors + 4 replacements), `fillers` (4 entries), `numbered_transitions` (5 entries), `quote_verbs` (3 entries, Gap D rotation pools), `templated_starters` (10 advisory entries, Gap C).
  - **Policy-in-data**: each sub-table declares its own substitution policy (`deterministic_all_matches`, `probabilistic_per_match` with probability, `consecutive_repeat_trigger`, `intensity_gated`, `rotation_pool`, `advisory_strategy`). Consumers no longer encode policy in code — they read it from the asset.
  - Source-tag attribution per entry: `v1_substrate` vs `gap_a` / `gap_b` / `gap_c` / `gap_d` so future audits can trace provenance.
  - `global_policies` block documents Gap E (register gating), Gap F (quoted-span bypass), Gap G (intensifier de-stacking) — advisory for consumers; not enforced by the asset itself.
- **`corpus/lexical-tables.schema.json`** — JSON Schema draft-2020-12 with per-policy `$defs` (`table_deterministic_alternatives`, `table_probabilistic_replacement`, `table_consecutive_trigger`, `table_intensity_gated`, `table_rotation_pool`, `table_advisory_strategy`). Uses `$ref` to dispatch per table; the validator in `scripts/lexical_tables.py:soft_validate()` covers the policy checks without needing full draft-2020-12 implementation.
- **`scripts/lexical_tables.py`** — 13-function typed read API (`load_tables`, `schema_version`, `table_names`, `get_table`, `ai_phrase_alternatives`, `connector_replacement`, `is_repetitive_starter`, `starter_replacements`, `filler_entries`, `numbered_transition_replacement`, `quote_verb_pool`, `templated_starter_strategies`, `soft_validate`, `stats`). mtime-keyed cache. Stdlib only. Module also runnable as CLI: `python scripts/lexical_tables.py` prints stats + soft validation.
- **`scripts/test_lexical_tables.py`** — 19-assertion release gate covering: schema version, all seven tables present, v1 substrate entries, Gap A/B/D extension entries, missing-key returns `None`, exact entry counts (40 / 21 / 5).

### Asset version state at end of v0.7

| Asset | Schema version | Notes |
|---|---|---|
| `corpus/calque-dictionary.json` | **v1.2.0** | unchanged from v0.5 |
| `corpus/empirical-patterns.json` | **v1.0.0** | unchanged from v0.5 |
| `corpus/typography-rules.json` | **v1.0.0** | unchanged from v0.5 |
| `corpus/reader-respect-patterns.json` | **v1.0.0** | unchanged from v0.5 |
| `corpus/lexical-tables.json` | **v1.0.0** | **NEW** in v0.7 |
| `scripts/lexical_tables.py` | n/a | **NEW** in v0.7 |

## v0.6 — Consumer-view export

**Released:** 2026-05-28

- **`scripts/export_consumer_view.py`** — three view modes (minimal / standard / full) × three formats (JSON / TSV / Markdown-table). Filter by `domain`, `min_confidence`. Lets consumers materialize a slice of the calque dictionary without depending on the full v1.2.0 schema.
- No asset schema bumps. Tooling-only release.

## v0.5 — Typography + reader-respect promotion + schema-diff enforcement

**Released:** 2026-05-28

- **`corpus/typography-rules.json`** (Asset E from Kimi-style lens): 9 typography-hygiene rules promoted from `arabic-ai-text-humanizer/references/15-typography-hygiene.md` (Markdown narrative → machine-readable JSON). Includes the 13-source authority log (Al Jazeera Learning, Drasah, Loghate, Mawdoo3, Mobt3ath, KSU, Itwadi, Shoair, Albuthi, Alukah, proof-reading-service, Kaplan, King Fahd Complex). Schema v1.0.0.
- **`corpus/reader-respect-patterns.json`** (Asset F): 6 anti-patterns from the humanizer's Dim 14 (inverse-scored cognitive-restraint dimension) promoted to JSON. Each pattern carries `examples_to_delete`, `humanizer_lex_function` reference, `severity`. Schema v1.0.0.
- **`scripts/diff_schema.py`** (deferred from v0.3 per Kimi-style + Codex-style review): JSON-Schema diff tool that classifies changes as PATCH / MINOR / MAJOR per the per-asset SemVer policy. Refuses MAJOR breaks without `--allow-break` flag. Walks `properties`, `items`, `definitions`, and `required` fields. Detects type changes, enum additions/removals, newly-required fields.
- **Second consumer live**: `arabic-corpus-translator` v0.1 ships concurrently, consuming the calque dictionary for its Stage A terminology lookup. Two real consumers now stress-test the toolkit's API surface.

### Asset version state at end of v0.5

| Asset | Schema version | Notes |
|---|---|---|
| `corpus/calque-dictionary.json` | **v1.2.0** | unchanged from v0.4 |
| `corpus/empirical-patterns.json` | **v1.0.0** | unchanged from v0.4 |
| `corpus/typography-rules.json` | **v1.0.0** | **NEW** in v0.5 |
| `corpus/reader-respect-patterns.json` | **v1.0.0** | **NEW** in v0.5 |
| `scripts/dictionary.py` | n/a | unchanged |
| `scripts/corpus_stats.py` | n/a | unchanged |
| `scripts/register.py` | n/a | unchanged |
| `scripts/validate.py` | n/a | unchanged |
| `scripts/diff_schema.py` | n/a | **NEW** in v0.5 |

## v0.4 — Empirical-patterns API + formal schema + first live consumer

**Released:** 2026-05-28

- **`scripts/corpus_stats.py`** — 10-function read API for `empirical-patterns.json`. Functions: `metadata`, `category_stats`, `token_count`, `sentence_count`, `mean_sentence_length`, `sentence_length_burstiness`, `sentence_length_histogram`, `top_connectors`, `connector_distribution`, `category_compare`. Pure stdlib. Mtime-aware caching shared with the rest of the toolkit pattern.
- **`corpus/empirical-patterns.schema.json`** — JSON Schema draft-07 for the mining-run output. Documents the 4 corpus categories (`quran`/`classical`/`news`/`lexicon`) and clarifies they are **distinct from the humanizer's register policies** (which live in `scripts/register.py`).
- **Architectural milestone**: `arabic-ai-text-humanizer` **v2.7.0** ships concurrently, switching its `_load_calque_dictionary()` to read from this toolkit by default. The vendored copy remains in the humanizer through v2.7.x as a fallback shim. Two-tier resolution: toolkit first, vendored copy as fallback.

### Asset version state at end of v0.4

| Asset | Schema version | Notes |
|---|---|---|
| `corpus/calque-dictionary.json` | **v1.2.0** | unchanged from v0.3 |
| `corpus/empirical-patterns.json` | **v1.0.0** | formal schema now in place; data unchanged |
| `scripts/dictionary.py` | n/a — API | unchanged |
| `scripts/corpus_stats.py` | n/a — API | **NEW** in v0.4 |
| `scripts/register.py` | n/a — API | unchanged |
| `scripts/validate.py` | n/a — API | unchanged |

## v0.3 — Schema validator + read API trio + asset-level SemVer

**Released:** 2026-05-28

Net-new contributions from the multi-agent review:

- **`scripts/validate.py`** (Codex-style API-design lens): typed `SchemaReport` dataclass with separated ERRORS/WARNINGS/unknown-field tracking + v2.6+ optional-field coverage report. The "regression detector" the humanizer never had — catches what manual review caught in v2.6.0's surgical-fix sweep.
- **`scripts/register.py`** (Codex-style): register policy lookup as code (not JSON) — adding a register is a deliberate code change that all consumers must handle. `policy_for()` / `known_registers()` / `applies()`.
- **`corpus/calque-dictionary.schema.json`** (JSON Schema draft-07): formal schema covering base v1.0.0 fields + v1.1.0 (v2.6.0 triage) + v1.2.0 (v2.6.3 topic-guard) extensions.
- **`references/03-api-design.md`**: narrative rationale for the API surface (JSON-vs-SQLite trade-off, per-asset SemVer rationale, Aho-Corasick forward-compat door).
- **`references/04-multi-agent-synthesis.md`**: preserved Kimi-style + Codex-style outputs from the v0.2 multi-agent review.
- **`CHANGELOG.md`** (this file): per-asset SemVer log.

### Per-asset version state at end of v0.3

| Asset | Schema version | Notes |
|---|---|---|
| `corpus/calque-dictionary.json` | **v1.2.0** | base (v1.0.0) + v2.6.0 triage fields (v1.1.0) + v2.6.3 topic-guard fields (v1.2.0). 340 entries. |
| `corpus/empirical-patterns.json` | v1.0.0 | unchanged from humanizer v2.3.0 mining run |
| `scripts/dictionary.py` | n/a — API | `load_dictionary` + 5 lookup functions. Stable since v0.2. |
| `scripts/register.py` | n/a — API | new in v0.3. 4 known registers. |
| `scripts/validate.py` | n/a — API | new in v0.3. SchemaReport dataclass. |

## v0.2 — Asset migration + read API + external-sources catalog

**Released:** 2026-05-28

Migrated from `arabic-ai-text-humanizer` (v2.6.4 state):

- `corpus/calque-dictionary.json` (214 KB, 340 entries including v2.6.3 topic-guarded entries for view/partition/trigger/process/task/worker)
- `corpus/empirical-patterns.json` (19 KB, 71.28M-token mining output)
- `scripts/dictionary.py` — 6-function read API
- `references/02-external-sources.md` — 12 authoritative institutions for cross-referencing (Gemini-style grounding-lens output)

## v0.1 — Scaffold

**Released:** 2026-05-28

- `SKILL.md`, `README.md`, `LICENSE`
- `references/01-charter.md`
- Directory structure for the four-sibling family pattern

## Schema-versioning policy

Per Kimi-style asset-promotion lens recommendation:

| Change class | Example | Bump | Consumer impact |
|---|---|---|---|
| **PATCH** (`1.2.0 → 1.2.1`) | Add a new dictionary entry; fix a typo in `natural_arabic`; tighten an existing regex | None for consumers | Auto-pickup |
| **MINOR** (`1.2.0 → 1.3.0`) | Add a NEW optional field | Additive | Consumers ignore unknown fields; old code keeps working |
| **MAJOR** (`1.2.0 → 2.0.0`) | Rename a field; change a value domain; drop a field; change a default | Breaking | Consumers MUST update; toolkit ships a `migrate_X_to_Y.py` |

Consumers pin compatibility:

```python
# In arabic-ai-text-humanizer (planned v2.7.0):
TOOLKIT_DICTIONARY_COMPAT = ">=1.0.0, <2.0.0"
```

The validator (`scripts/validate.py`) refuses breaking changes without an explicit `--allow-break` flag.

## Why per-asset, not monolithic

The connector inventory (asset D in Kimi's catalog) won't change at the same rate as the calque dictionary (asset A). Coupling them via monolithic SemVer means a dictionary tweak forces a connector-table version bump, forces a consumer re-test, discourages dictionary tweaks. Decouple.

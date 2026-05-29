---
name: arabic-corpus-toolkit
description: "Shared Arabic-language corpus infrastructure: calque dictionary, corpus statistics, register policies, style guide. Consumed at runtime by three RELEASED siblings: arabic-ai-text-humanizer (16-dim humanizer + 5-axis English path), arabic-corpus-translator (corpus-grounded EN↔AR translation, v1.9.0), and arabic-authoring-suite (long-form authoring, v1.8.0). Centralizes the load-bearing assets so dictionary fixes propagate to all consumers in one place, and ships the shared `safe_llm_call` LLM-proxy resilience contract (retries + per-vendor circuit breaker + structured failure envelope) that those consumers adopt at runtime. NOT a standalone humanizer or translator — it's the data + reference + shared-contract layer those skills read from. Triggers on 'arabic corpus toolkit', 'shared arabic dictionary', 'arabic calque dictionary lookup', 'arabic linguistic resources', 'MSA register policy', 'arabic terminology base'. Do NOT use for direct text transformation (use arabic-ai-text-humanizer), for translation (use arabic-corpus-translator), or for content generation. Primarily a read-only data + reference layer (plus the safe_llm_call utility contract)."
---

# arabic-corpus-toolkit — Shared Arabic Linguistic Infrastructure

**Status:** **v1.13.0 — STABLE + shared LLM proxy failure-resilience contract (cross-cutting A7 must-have).** `scripts/safe_llm_call.py` ships `safe_llm_call(vendor_url, api_key, payload, timeout, max_retries, retry_backoff_s) → LLMCallResult` with structured failure envelope (`.ok`, `.payload`, `.error_class`, `.error_detail`, `.latency_ms`, `.attempts`, `.circuit_open`, `.http_status`). NEVER raises; consumers check `.ok`. Per-vendor circuit breaker (3 consecutive failures → 60s open). Error classes: `timeout`, `http_5xx`, `http_4xx`, `auth`, `network`, `json_decode`, `schema_mismatch`, `empty_response`, `circuit_open`, `payload_encode`. Retries exponential-backoff bounded; 4xx/json_decode/schema_mismatch/empty don't retry (deterministic failures). 12/12 self-test PASS. Adopted at runtime by translator v1.9.0 (Stage C draft), humanizer v2.17.0 (score_text_deep), and authoring v1.8.0 (draft_section via humanizer dependency). Closes the **strongest convergent A7 signal**: translator 4/4 vendors flagged LLM provider failure as #1 must-have, humanizer 3/4 vendors agreed, deepseek explicitly named it "the single biggest blocker." **v1.12.1 — STABLE + mined-pair acceptance criteria formalized (Minimax + Kimi missing-item gap).** `references/07-mined-pair-acceptance-criteria.md` codifies what's been operating informally since v1.10.0: the 5-stage pair lifecycle (Candidate → Paired → Cross-vendor confirmed → Tier classified → Era/source-stamped), the canonical `n_independent_agree >= 1` active-threshold gate, consumer access patterns (`min_consensus` API, `era_locked` filter, combined), release gates (conformance 56+ + golden 40 + registry sync + CHANGELOG matrix), and explicit non-enforcements (no per-vendor bias normalization, no embedding dedup, no BLEU — the multi-vendor swarm IS the proxy for human consensus). Closes the convergent missing-item flagged by Minimax + Kimi A5 critiques. **v1.12.0 — STABLE + G.politics era-locked metadata (Codex A5 P0).** Tag-don't-delete approach per Codex's framing: 7 Iraq War-era and equivalent proper nouns in G.politics now carry `era_locked` + `era_locked_reason` fields. Pairs tagged: مجلس الحكم (iraq-2003-2004-transition, dissolved June 2004), الرئيس بوش (usa-2001-2009), جلال الطالباني (iraq-2005-2014, deceased 2017), السيد جلال الطالباني (honorific variant), الدكتور أياد علاوي (iraq-2004-2005), حسن نصر الله (lebanon-1992-2024, killed Sept 2024), رئيس الوزراء العراقي (iraq-elaph-era, contextual ambiguity). Nothing deleted — historical-content translation still benefits from tagged pairs; consumers can filter `era_locked` for current-only terminology. Schema bumped 1.4.0 → 1.5.0 (additive `era_locked` + `era_locked_reason`). Total G.politics active still 14. **v1.11.0 — STABLE + SPA mining lands → G.legal escapes placeholder.** Mined 7,420 bilingual SPA EN+AR pairs (corpus walked + bucketed in v1.10.1) through the full pipeline: AR-side n-gram extraction → minimax pair → 4-vendor confirm (codex+gemini+kimi+minimax) → 3-independent-vendor consensus tier. Merged with v1.10.0 active pairs (additive, deduped). Results: **G.business 51 → 69 active (+18)**, **G.legal 0 (placeholder) → 23 active (+23) — placeholder status DROPPED**, **G.politics 13 → 14 active (+1, SPA political content too Saudi-specific for general validation, codex+gemini both 0/36 rejection)**. Total active across all 3 domains: 64 → 106 (+66%). Schema bumped 1.3.0 → 1.4.0 (additive `source_corpus` field per pair + `provenance.v1_4_*` fields documenting Elaph 2003-2008 + SPA 2024 multi-corpus heritage). Conformance 56/56 + golden e2e 40/40. Per-vendor SPA agreement: legal codex 13/74 minimax 34/74 gemini 20/74 kimi 6/74; business codex 16/69 minimax 38/69 gemini timed-out kimi 18/69; politics codex 0/36 minimax 1/36 gemini 0/36 kimi 1/36. **v1.10.1 — STABLE + inter-sibling contract conformance suite + SPA corpus ingestion (substrate for v1.11+).** Closes the convergent A5 roadmap-challenge gap (3 of 4 vendors — codex, minimax, kimi — independently flagged: "shared regression test proving every sibling still obeys G1-G4 contracts after any change"). `evals/contract_conformance.py` — 54 assertions exercising G1 normalize adoption (7), G2 registry adoption with npm-range parsing (9), G3 telemetry across all 3 consumers including A4 killer-finding fix (10), G4 install_family (4), schema-1.3.0 tier conformance (13), and consumer min_consensus API behavioral checks (8). 54/54 PASS. Iteration-1 caught my own wrong-API assumption (`asset_registry.load()` doesn't exist) — the test surfacing that on first run IS the value. Parallel: walked 77,760 SPA NewsDataForTranslation folders → bucketed `corpus/raw/spa-economic.jsonl` (1,773 EN+AR pairs), `corpus/raw/spa-political.jsonl` (1,317), `corpus/raw/spa-general.jsonl` (4,330). 7,420 modern (2024) bilingual pairs, no era-lock, no classify+pair-via-LLM step needed (EN side already exists). Substrate for v1.11+ G.business expansion / G.politics modernization / G.legal/governance activation. **v1.10.0 — STABLE + 4-vendor consensus tiered prune (G.business / G.legal / G.politics).** Closes the deferred validation debt flagged independently by Sonnet, Codex, Kimi, and Gemini in the fifth audit (mean score 91.2/100, +1.5 from A4). Each Elaph-derived pair was challenged by 4 LAN-local LLM proxies (codex + gemini + kimi + minimax) and tiered by 3-INDEPENDENT-vendor consensus (minimax excluded as proposer). Final active counts: **G.business 51 pairs** (14 unanimous 3/3 + 19 majority 2/3 + 18 single-vendor 1/3); **G.politics 13 pairs** (all single-vendor 1/3 — codex 0/126 strict rejection, gemini 7, kimi 6); **G.legal 0 pairs — PLACEHOLDER** (all 8 unanimously rejected, even by minimax-the-proposer; v1.11+ pending dedicated legal corpus). Schema bumped 1.2.0 → 1.3.0 (additive: `pairs_below_threshold`, `n_independent_agree`, `vendor_consensus` fields). Backward compatible — consumers reading `pairs` automatically get only validated active subset; stricter consumers can filter by `n_independent_agree >= 2`. **v1.9.0 — STABLE + domain expansion landed.** Strategic pivot after four audits showed diminishing internal-architecture returns. v1.9.0 ships three new Asset G domains (G.business 27 pairs, G.legal 5 pairs, G.politics 69 pairs) via single-pass LLM classify+pair from existing Elaph news candidates. Registry now lists 12 assets (was 9). Translator + authoring automatically gain coverage via existing domain-keyed lookup — no consumer code change needed. **Architectural ceiling:** four foundational contracts G1+G2+G3+G4 stay closed; full adoption matrix (12/12 cells) intact; golden e2e 40/40 PASS; four-audit score trajectory 66→77→85→89.7. **v1.8.0 — STABLE + ALL 4 foundational debt items closed (G1+G2+G3+G4).** This release ships `install_family.py` at the repo root — a cross-platform (Windows/Linux/Mac) installer that clones any missing siblings and verifies the install via `family_doctor.py` + `golden_e2e_test.py`. Verified end-to-end: `[2/2] VERIFY ... ✓ Family installed and verified. All 4 siblings present + 40/40 e2e PASS.` Closes Gemini's "how do I install this?" complaint. The four-contract architecture (G1 arabic_normalize + G2 asset_registry + G3 influence_telemetry + G4 install_family) brings the toolkit to its **architectural completion point** — every evaluator-flagged foundational debt is closed with a contract + at least one consumer adoption. **v1.7.0 — STABLE + all 3 foundational debt items closed.** This release ships `influence_telemetry.py` (Gap G3): `InfluenceTrace` append-only causal record with `record()` / `as_json()` / `from_json()` / filter+summary APIs. 11 standardized triggers + `other` fallback. Self-test passes, golden e2e expanded 34 → 40 assertions. Together with **v1.6.0** (asset version registry, Gap G2) and **v1.5.0** (Unicode normalization contract, Gap G1), the toolkit now closes all three foundational debt items flagged by the 3-evaluator audit. **v1.5.0 — STABLE + Unicode normalization contract shipped.** Closes the foundational gap (Gap G1) that both swarm runs flagged: `scripts/arabic_normalize.py` is now the canonical Arabic normalization source for all four siblings. Three levels (light/medium/aggressive) with verified idempotence + monotonicity. 14 edge cases + idempotence + char-ratio checks pass. Golden e2e expanded 21 → 28 assertions. **v1.4.2 — STABLE.** Seven assets + 5 helper scripts beyond the v1.0.0 stable freeze. Asset state at v1.4.2: A calque-dictionary 340 entries, B empirical-patterns, B' register policies (code), C lexical-tables v1.1.0 (67 ai_phrases + 8 intensifier patterns), D typography-rules v1.0.0 (9 rules), E reader-respect-patterns v1.0.0 (6 anti-patterns), F terminology-candidates technology 999 + news 498, G domain-terminology technology v1.4.0 (422 pairs, all cross-LLM-validated via codex) + news (50 pairs). Helpers: `bilingual_export.py` (v1.2.0 — TBX-Lite for CAT tools), `family_doctor.py` (v1.1.0 — cross-asset health), `aho_corasick.py` (v1.3.0 — multi-pattern matcher), `evals/golden_e2e_test.py` (v1.4.1 — family regression, 21/21 PASS). Live consumers: humanizer v2.13.0 (hard dependency, also reads Assets C/D/E), translator v1.3.0 (Asset A+F+G), authoring-suite v1.3.0 (Asset G). Paired v0.8 candidates [300:666] via minimax-proxy. 260 new pairs (71% acceptance, higher than v0.9's 56% because mid-frequency candidates have higher terminology density than the brand-heavy top tier). Net: 162 → 422 paired EN↔AR tech terms, 2.6× expansion. Schema 1.2.0 → 1.3.0 (MINOR additive — more rows, same shape). Translator picks up the expansion automatically via mtime cache. v0.10 — **Three-way LLM tiebreaker via gemini-proxy completes the multi-vendor swarm.** Second portal-native release (TaskID=11, PlanID=11). Sends the 16 v0.9.1 disagreements through gemini-2.5-flash as third independent vendor. Decision rule: codex+gemini agree on EN → switch to it; minimax+gemini agree → keep minimax; both agree on empty → drop pair; three-way differ → keep minimax + flag for review. Result: **6 geographic terms dropped** (UAE/Saudi/EU/MENA — codex+gemini consensus they're not terminology), **5 better-English switches** (IT→information technology, videos→video clips), **3 minimax wins preserved** (notably coronavirus survived codex's empty vote because gemini correctly identified it as pandemic-era tech-news terminology). Net: 168 → 162 pairs, every pair vetted by 1-3 LLMs. Schema 1.1.0 → 1.2.0 (MINOR additive). v0.9.1 — **Cross-LLM confirmation pass on top 50 v0.9 pairs, executed through the Agent Portal.** Used the cross-project portal infrastructure (`M:\Main\AI\Master\docs\AGENT-PORTAL.md`): registered `arabic-corpus-toolkit-claude` agent, enqueued task in `taskbus.Tasks`, proposed Phase-2 plan, approved via portal API, ran codex-proxy confirmation on top 50 minimax-paired terms from v0.9. Result: 34/50 agreement (68%); 16 disagreements surface real signal (synonym preferences + precision improvements + geographic-term filter). Schema bumped 1.0.0 → 1.1.0 (MINOR additive). v0.9 — **Asset G (paired EN↔AR terminology) ships — Phase 2 of the terminology pipeline.** v0.8 mined 999 AR-side candidates; v0.9 pairs the top 300 bigram+trigram candidates via minimax-proxy (one of four LAN-local LLM proxies documented at `M:\Main\DevTools\AI\config\.ai-instructions.md`) into validated EN↔AR pairs with corpus-frequency evidence, LLM-proposer attribution, and confidence taxonomy. `scripts/pair_terminology.py` is the pairing pipeline (stdlib urllib only — no pip install). `corpus/domain-terminology.json` is the Phase-2 product. Translator vNext can consume this for full EN↔AR injection in Stage A (current v0.3.0 uses Asset F as verification signal only; v0.3.1 will read Asset G for direct term-pair injection). v0.8 — **Asset F (terminology candidates) ships.** New net-new asset — not migrated from the humanizer, mined from the AITNews 64K-article AR tech corpus. Phase 1 of a two-phase pipeline: `scripts/mine_terminology.py` walks the corpus, extracts unigram/bigram/trigram candidates by frequency (with stopword filtering + tashkeel stripping + HTML-entity decoding), writes `corpus/terminology-candidates-technology.json` (top 1000 candidates, min-freq 20). `scripts/terminology.py` is the 9-function read API; `scripts/test_terminology.py` is the release gate. Phase 2 (downstream, when first paired batch ready): LLM-assisted EN→AR pairing + corpus validation → `corpus/domain-terminology.json` with verified pairs. References/06-terminology-pipeline.md is the permanent record. v0.7.1 — Asset C parity audit. v0.7 was migrated from stale Markdown documentation; v0.7.1 brings the asset to full parity with the live humanizer code (67 ai-phrases including pro-drop deletions + clause-preserving variants + newsroom AI-tells + English-calque pipeline; 22 connectors; 11 repetitive-starter detectors; 4 quote-verb rotation pools; structural_openers as regex with capture groups; intensifier_destack as first-class regex table). Schema bumped to v1.1.0 (MINOR, backward-relaxing). See `references/05-asset-c-migration-audit.md` for the permanent record of the v0.7 gap. Consumers live today: `arabic-ai-text-humanizer` v2.7.0, `arabic-corpus-translator` v0.2.1, `arabic-authoring-suite` v0.1.1.

- **v0.2**: assets migrated from `arabic-ai-text-humanizer` (340-entry calque dictionary + 71.28M-token empirical patterns); `scripts/dictionary.py` 6-function read API; `references/02-external-sources.md` from Gemini-style lens.
- **v0.3 (current)**:
  - `scripts/validate.py` — typed `SchemaReport` validator with separated ERRORS / WARNINGS / unknown-field tracking + per-v2.6+ field coverage report. The "regression detector the humanizer never had" — Kimi-style lens identified this as the load-bearing net-new contribution.
  - `scripts/register.py` — register policy lookup (`policy_for`, `applies`, `known_registers`) per Codex-style API design (encoded in code, not JSON — adding a register requires consumer code changes).
  - `corpus/calque-dictionary.schema.json` — formal JSON Schema draft-07 covering base v1.0.0 + v2.6.0 triage (v1.1.0) + v2.6.3 topic-guard (v1.2.0) extensions.
  - `CHANGELOG.md` — per-asset SemVer log (Kimi-style: per-asset versioning, not monolithic).
  - `references/03-api-design.md` — design rationale (JSON-vs-SQLite trade-off, Aho-Corasick forward-compat door, errors-as-data discipline).
  - `references/04-multi-agent-synthesis.md` — preserved Gemini + Kimi + Codex findings from the v0.2 review.

## Why this skill exists

Per Agent C's architectural review (multi-agent synthesis in `M:\Main\AI\Corpus\humanizer-v2.6-multi-agent-synthesis.md`), the calque dictionary, corpus statistics, and register policies currently embedded inside `arabic-ai-text-humanizer` are about to be consumed by three sibling skills:

1. **`arabic-ai-text-humanizer`** (existing) — detects + transforms AR/EN AI-slop prose
2. **`arabic-corpus-translator`** (v0.1 scheduled v2.8.0 of the humanizer family) — EN↔AR corpus-grounded translation
3. **`arabic-authoring-suite`** (Q1 2027) — long-form AR/EN: books, articles, courses, news, with corpus-grounded outline discipline

If each sibling vendors its own copy of the calque dictionary, **a single bad entry takes 3× the work to fix** and the dictionaries WILL drift. This toolkit is the load-bearing shared module — one location, one set of fixes, all consumers benefit.

## What this skill owns

12 assets, canonical state per `corpus/asset-registry.json`. Per-asset SemVer; consumers query the registry for compat ranges rather than hardcoding versions.

| Asset | Toolkit path | Current schema | Notes |
|---|---|---|---|
| **A** — calque-dictionary | `corpus/calque-dictionary.json` | 1.2.0 | 340 entries; v2.6.0 triaged with topic-guards + three_way_verdict fields |
| **B** — empirical-patterns | `corpus/empirical-patterns.json` | 1.0.0 | 100K-record mining; 4 register categories, sentence-length burstiness |
| **B'** — register policies | `scripts/register.py` | code-versioned | Per Codex-style API: encoded in code, not JSON |
| **C** — lexical-tables | `corpus/lexical-tables.json` | 1.1.0 | 67 ai_phrases + 22 connectors + 11 starters + intensifier-destack regex; v1.1.0 added regex_capture_substitute policy |
| **D** — typography-rules | `corpus/typography-rules.json` | 1.0.0 | 9 rules + 13-source authority log; consumed by humanizer v2.12.0+ |
| **E** — reader-respect-patterns | `corpus/reader-respect-patterns.json` | 1.0.0 | 6 anti-patterns (tautology, re-explanation, forced-conclusion) |
| **F.technology** | `corpus/terminology-candidates-technology.json` | 1.0.0 | 999 candidates from AITNews 64,484 articles |
| **F.news** | `corpus/terminology-candidates-news.json` | 1.0.0 | 498 candidates from Elaph 3,801 articles |
| **G.technology** | `corpus/domain-terminology.json` | 1.4.0 | 422 paired EN↔AR tech terms; all cross-vendor-validated through v1.4.0 |
| **G.news** | `corpus/domain-terminology-news.json` | 1.0.0 | 50 paired EN↔AR news terms |
| **G.business** | `corpus/domain-terminology-business.json` | 1.4.0 | 69 active pairs (multi-corpus: Elaph 2003-2008 + SPA 2024); 3-vendor consensus tiered |
| **G.legal** | `corpus/domain-terminology-legal.json` | 1.4.0 | 23 active pairs from SPA 2024 governance/audit content; placeholder status DROPPED in v1.11.0 |
| **G.politics** | `corpus/domain-terminology-politics.json` | **1.5.0** | 14 active pairs; v1.5.0 added `era_locked` + `era_locked_reason` on 7 Iraq War-era proper nouns (Codex A5 P0) |

Plus four foundational contract scripts (Gaps G1-G4):
- `scripts/arabic_normalize.py` (G1, v1.5.0) — light/medium/aggressive normalization, verified idempotent + monotone
- `scripts/asset_registry.py` (G2, v1.6.0) — npm-range parser + `check_consumer()` compat reports
- `scripts/influence_telemetry.py` (G3, v1.7.0) — `InfluenceTrace` append-only causal record with 11+1 triggers
- `install_family.py` (G4, v1.8.0) — cross-platform installer at repo root (acquire + verify phases)

Conformance gate: `evals/contract_conformance.py` (v1.10.1, 56 assertions) verifies every consumer adopts G1-G4 + schema-1.3.0+ tier conformance + min_consensus API. Golden e2e: `evals/golden_e2e_test.py` (40 assertions).

## What this skill does NOT own

- The 16-dimension humanizer analyzer (lives in arabic-ai-text-humanizer)
- The 5-axis English scorer (lives in arabic-ai-text-humanizer)
- Translation logic (will live in arabic-corpus-translator)
- Content generation (will live in arabic-authoring-suite)
- Sacred-text guard (lives in arabic-ai-text-humanizer/scripts/sacred_text_guard.py — moved here in a later version once two skills need it)

## Read-only API (live)

Python helper modules exposing the assets to consumers (all stdlib, no pip install):

```python
# Asset A — calque dictionary
from scripts import dictionary
entries = dictionary.find_by_en("personalization")     # 1+ entries with full schema
entry = dictionary.find_canonical("personalization")   # single best entry

# Asset B — empirical patterns
from scripts import corpus_stats
top = corpus_stats.top_connectors("news", n=10)

# Asset B' — register policies (code-encoded)
from scripts import register
policy = register.policy_for("classical")

# Asset C — lexical tables (NEW in v0.7)
from scripts import lexical_tables
alts = lexical_tables.ai_phrase_alternatives("من المهم ملاحظة")
replacement = lexical_tables.connector_replacement("وعلاوة على ذلك،")
pool = lexical_tables.quote_verb_pool("قال")           # Gap D rotation
errs = lexical_tables.soft_validate()                  # release-gate
```

Each helper is pure Python 3 stdlib — no SQLite, no FAISS, no LLM call. Modifications go through the toolkit's own write API (versioned, audited).

## Roadmap

**Current state**: v1.12.1 (toolkit) + v2.16.0 (humanizer) + v1.8.0 (translator) + v1.6.0 (authoring). All four foundational contracts G1-G4 shipped + adopted across 12/12 cells (verified by `evals/contract_conformance.py`).

### Shipped milestones

| Version | Ships | Status |
|---|---|---|
| v0.2–v0.7 | Asset A/B/C/D/E migration from humanizer | ✅ |
| v0.8–v0.10 | Asset F mining (AITNews 64K + Elaph 3.8K) + Asset G pairing + cross-LLM swarm validation | ✅ |
| v1.0.0 — v1.4.2 | Stable freeze; consumers adopt domain-keyed loaders; family pipeline integration | ✅ |
| **v1.5.0** | **G1**: `arabic_normalize.py` canonical contract — light/medium/aggressive levels, idempotent + monotone | ✅ |
| **v1.6.0** | **G2**: `asset_registry.py` + JSON — npm-range parsing, `check_consumer()` reports | ✅ |
| **v1.7.0** | **G3**: `influence_telemetry.py` — `InfluenceTrace` append-only causal record, 11+1 triggers | ✅ |
| **v1.8.0** | **G4**: `install_family.py` — cross-platform acquire + verify phases | ✅ |
| v1.9.0 | Domain expansion (G.business 27 / G.legal 5 / G.politics 69 via single-pass classify+pair from Elaph) | ✅ |
| **v1.10.0** | 4-vendor consensus tiered prune (Sonnet/Codex/Kimi/Gemini/MiniMax A5 audit prescribed) | ✅ |
| **v1.10.1** | Inter-sibling contract conformance suite (3-of-4 A5 vendor flag) + SPA bilingual corpus ingestion (77K folders walked) | ✅ |
| **v1.11.0** | SPA-2024 mining: **G.legal escapes placeholder** (0→23 active), G.business 51→69, G.politics 13→14; multi-corpus heritage | ✅ |
| **v1.12.0** | G.politics era_locked metadata on 7 Iraq War-era proper nouns (Codex A5 P0) | ✅ |
| **v1.12.1** | `references/07-mined-pair-acceptance-criteria.md` formalizes the 5-stage pair lifecycle gate (Minimax + Kimi missing-item) | ✅ |

### Deferred work (post-A5 panel verdict)

| Item | Why deferred | Source |
|---|---|---|
| Usage telemetry dashboard | Requires real infrastructure (per-consumer metrics, daily/weekly aggregation); genuinely P2 | Gemini A5 #1 leverage pick |
| Audit variance root cause analysis | Research task — why MiniMax 89 vs Gemini 94 on identical data; for a future A6 audit | Minimax + Gemini A5 |
| G.health / G.science / G.tech-startups domains | Wait for dedicated corpora; SPA general bucket already saturated for governance | A5 panel P3 |
| Aho-Corasick consumer integration | Current Python lookup adequate; YAGNI per all 4 vendors | A5 panel rejected |
| 5th sibling: arabic-validator | Premature extraction; no consumers have requested it | A5 panel rejected |

Future v1.13+ would either (a) ingest a new bilingual corpus that surfaces healthcare/science terminology, (b) wire telemetry once a real consumer asks for the dashboard, or (c) run an A6 audit cycle and process whatever the panel converges on next.

## Constraints

- **No transformations.** The toolkit reads and serves data. Any transformation (humanize, translate, author) belongs in the consumer skill, not here.
- **No LLM calls.** Pure data + lookup. Consumers may call LLMs; this skill never does.
- **Schema is versioned.** Breaking schema changes bump the toolkit's major version, and consumers pin against a compatible range. v2.5.1 of the dictionary schema (post-v2.6.0 triage) is the first stable schema.
- **No vendoring.** The whole point is that consumers DON'T vendor a copy. They import or read by path.

## Provenance

The migrated assets retain their full multi-source provenance:
- Calque dictionary built from 8,850-article AITNews tech-news corpus + multi-LLM swarm (Claude + Codex) on 361 seed terms, validated against `Y:\Linguistics\News\Technology\AITNews`. Native-MSA review (v2.6.0) added `regional_sensitivity` / `political_sensitivity` / `disambiguation_pair_id` annotations.
- Empirical patterns mined from 100K records (1.31M sentences, 71.28M tokens, 4 register categories) of the source corpora.
- Sacred-text-guard heuristics derived from classical hadith citation conventions + Quranic typography (U+06D6–U+06ED).

## License

MIT. Inherits the humanizer's license; English-pattern-catalogue portions trace to `hardikpandya/stop-slop` (MIT). See LICENSE file once v0.2 ships with the migrated assets.

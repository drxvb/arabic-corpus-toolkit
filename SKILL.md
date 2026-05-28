---
name: arabic-corpus-toolkit
description: "Shared Arabic-language corpus infrastructure: calque dictionary, corpus statistics, register policies, style guide. Consumed by arabic-ai-text-humanizer (16-dim humanizer + 5-axis English path) and the upcoming arabic-corpus-translator (corpus-grounded EN↔AR translation) + arabic-authoring-suite. Centralizes the load-bearing assets so dictionary fixes propagate to all consumers in one place. NOT a standalone humanizer or translator — it's the data + reference layer those skills read from. Triggers on 'arabic corpus toolkit', 'shared arabic dictionary', 'arabic calque dictionary lookup', 'arabic linguistic resources', 'MSA register policy', 'arabic terminology base'. Do NOT use for direct text transformation (use arabic-ai-text-humanizer), for translation (use arabic-corpus-translator when released), or for content generation. Read-only reference + lookup layer."
---

# arabic-corpus-toolkit — Shared Arabic Linguistic Infrastructure

**Status:** **v1.5.0 — STABLE + Unicode normalization contract shipped.** Closes the foundational gap (Gap G1) that both swarm runs flagged: `scripts/arabic_normalize.py` is now the canonical Arabic normalization source for all four siblings. Three levels (light/medium/aggressive) with verified idempotence + monotonicity. 14 edge cases + idempotence + char-ratio checks pass. Golden e2e expanded 21 → 28 assertions. **v1.4.2 — STABLE.** Seven assets + 5 helper scripts beyond the v1.0.0 stable freeze. Asset state at v1.4.2: A calque-dictionary 340 entries, B empirical-patterns, B' register policies (code), C lexical-tables v1.1.0 (67 ai_phrases + 8 intensifier patterns), D typography-rules v1.0.0 (9 rules), E reader-respect-patterns v1.0.0 (6 anti-patterns), F terminology-candidates technology 999 + news 498, G domain-terminology technology v1.4.0 (422 pairs, all cross-LLM-validated via codex) + news (50 pairs). Helpers: `bilingual_export.py` (v1.2.0 — TBX-Lite for CAT tools), `family_doctor.py` (v1.1.0 — cross-asset health), `aho_corasick.py` (v1.3.0 — multi-pattern matcher), `evals/golden_e2e_test.py` (v1.4.1 — family regression, 21/21 PASS). Live consumers: humanizer v2.13.0 (hard dependency, also reads Assets C/D/E), translator v1.3.0 (Asset A+F+G), authoring-suite v1.3.0 (Asset G). Paired v0.8 candidates [300:666] via minimax-proxy. 260 new pairs (71% acceptance, higher than v0.9's 56% because mid-frequency candidates have higher terminology density than the brand-heavy top tier). Net: 162 → 422 paired EN↔AR tech terms, 2.6× expansion. Schema 1.2.0 → 1.3.0 (MINOR additive — more rows, same shape). Translator picks up the expansion automatically via mtime cache. v0.10 — **Three-way LLM tiebreaker via gemini-proxy completes the multi-vendor swarm.** Second portal-native release (TaskID=11, PlanID=11). Sends the 16 v0.9.1 disagreements through gemini-2.5-flash as third independent vendor. Decision rule: codex+gemini agree on EN → switch to it; minimax+gemini agree → keep minimax; both agree on empty → drop pair; three-way differ → keep minimax + flag for review. Result: **6 geographic terms dropped** (UAE/Saudi/EU/MENA — codex+gemini consensus they're not terminology), **5 better-English switches** (IT→information technology, videos→video clips), **3 minimax wins preserved** (notably coronavirus survived codex's empty vote because gemini correctly identified it as pandemic-era tech-news terminology). Net: 168 → 162 pairs, every pair vetted by 1-3 LLMs. Schema 1.1.0 → 1.2.0 (MINOR additive). v0.9.1 — **Cross-LLM confirmation pass on top 50 v0.9 pairs, executed through the Agent Portal.** Used the cross-project portal infrastructure (`M:\Main\AI\Master\docs\AGENT-PORTAL.md`): registered `arabic-corpus-toolkit-claude` agent, enqueued task in `taskbus.Tasks`, proposed Phase-2 plan, approved via portal API, ran codex-proxy confirmation on top 50 minimax-paired terms from v0.9. Result: 34/50 agreement (68%); 16 disagreements surface real signal (synonym preferences + precision improvements + geographic-term filter). Schema bumped 1.0.0 → 1.1.0 (MINOR additive). v0.9 — **Asset G (paired EN↔AR terminology) ships — Phase 2 of the terminology pipeline.** v0.8 mined 999 AR-side candidates; v0.9 pairs the top 300 bigram+trigram candidates via minimax-proxy (one of four LAN-local LLM proxies documented at `M:\Main\DevTools\AI\config\.ai-instructions.md`) into validated EN↔AR pairs with corpus-frequency evidence, LLM-proposer attribution, and confidence taxonomy. `scripts/pair_terminology.py` is the pairing pipeline (stdlib urllib only — no pip install). `corpus/domain-terminology.json` is the Phase-2 product. Translator vNext can consume this for full EN↔AR injection in Stage A (current v0.3.0 uses Asset F as verification signal only; v0.3.1 will read Asset G for direct term-pair injection). v0.8 — **Asset F (terminology candidates) ships.** New net-new asset — not migrated from the humanizer, mined from the AITNews 64K-article AR tech corpus. Phase 1 of a two-phase pipeline: `scripts/mine_terminology.py` walks the corpus, extracts unigram/bigram/trigram candidates by frequency (with stopword filtering + tashkeel stripping + HTML-entity decoding), writes `corpus/terminology-candidates-technology.json` (top 1000 candidates, min-freq 20). `scripts/terminology.py` is the 9-function read API; `scripts/test_terminology.py` is the release gate. Phase 2 (downstream, when first paired batch ready): LLM-assisted EN→AR pairing + corpus validation → `corpus/domain-terminology.json` with verified pairs. References/06-terminology-pipeline.md is the permanent record. v0.7.1 — Asset C parity audit. v0.7 was migrated from stale Markdown documentation; v0.7.1 brings the asset to full parity with the live humanizer code (67 ai-phrases including pro-drop deletions + clause-preserving variants + newsroom AI-tells + English-calque pipeline; 22 connectors; 11 repetitive-starter detectors; 4 quote-verb rotation pools; structural_openers as regex with capture groups; intensifier_destack as first-class regex table). Schema bumped to v1.1.0 (MINOR, backward-relaxing). See `references/05-asset-c-migration-audit.md` for the permanent record of the v0.7 gap. Consumers live today: `arabic-ai-text-humanizer` v2.7.0, `arabic-corpus-translator` v0.2.1, `arabic-authoring-suite` v0.1.1.

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

| Asset | Toolkit path | Schema version | Migrated in |
|---|---|---|---|
| **A** — calque-dictionary | `corpus/calque-dictionary.json` (340 entries, v2.6.0 triaged) | 1.2.0 | v0.2 |
| **B** — empirical-patterns | `corpus/empirical-patterns.json` (100K-record mining output) | 1.0.0 | v0.2 |
| **B'** — register policies | `scripts/register.py` (encoded in code per Codex-style API) | code-versioned | v0.3 |
| **D** — typography-rules | `corpus/typography-rules.json` (9 rules + 13-source authority log) | 1.0.0 | v0.5 |
| **E** — reader-respect-patterns | `corpus/reader-respect-patterns.json` (6 inverse-scored anti-patterns) | 1.0.0 | v0.5 |
| **C** — lexical-tables | `corpus/lexical-tables.json` (5 v1 tables + Gap A/B/C/D extensions + per-table policies) | 1.0.0 | **v0.7 (this release)** |

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

| Version | Ships | Status |
|---|---|---|
| **v0.1** | Scaffold (this release): SKILL.md, README, LICENSE, directory structure, intent docs | ✅ Current |
| **v0.2** | Migrate `calque-dictionary.json` + `empirical-patterns.json`; `arabic-ai-text-humanizer` v2.7.0 reads from here | Pending humanizer v2.7.0 |
| **v0.3** | Migrate register policies + connector tables + MSA style guide | Pending humanizer v2.7.0 |
| **v0.4** | Add `arabic-corpus-translator` integration layer (the read API translator needs) | Pending translator scaffold |
| **v0.5** | Add `arabic-authoring-suite` integration layer (fact-pack schema, outline discipline) | Pending authoring scaffold |
| **v1.0** | All three consumers stable on toolkit ≥ v0.5; semantic versioning enforced for breaking changes | Q2 2027 |

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

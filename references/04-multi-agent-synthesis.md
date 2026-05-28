# 04 — Multi-Agent Synthesis (v0.2 → v0.3)

The v0.2 release of `arabic-corpus-toolkit` ran three Claude subagents in parallel as adversarial lenses — Gemini-style (grounded-factuality), Kimi-style (long-context decompositional), Codex-style (implementation precision). This file preserves the load-bearing findings from each, so future maintainers can re-read the rationale and audit decisions made on top of it.

This is a permanent reference. **Do not delete.**

## Lens 1 — Gemini-style (external grounding)

**Charter**: identify authoritative external sources the toolkit should cross-reference, and the gaps no LLM consensus can solve.

**Key findings:**

1. **12 authoritative institutions** identified — UN DGACM Arabic Translation Service, Al Jazeera Arabic Stylebook, Mu'jam al-Wasīṭ (Cairo Academy 4th ed.), Mu'jam al-Lughah al-'Arabiyyah al-Mu'āṣirah (Ahmad Mukhtar Omar), ALECSO Arabization Bureau (Rabat), Damascus Academy *Majallat al-Majma'*, King Salman Global Academy for Arabic Language, WHO EMRO, IPCC AR6 Arabic Glossary, Hans Wehr Dictionary, King Fahd Complex orthographic conventions, W3C Arabic Layout Requirements. Catalogued by asset class (terminology / register / typography / sacred-text) in `references/02-external-sources.md`.

2. **Three current dictionary claims flagged for verification**:
   - `personalization → الشخصنة` (post-v2.6.0 correction) — classically means "ad hominem"; needs corpus-frequency verification in Al Jazeera Net archives
   - `platform → منصة` vs. older ALECSO-preferred `أرضية` — needs institutional anchor not just frequency
   - `content (digital) → محتوى` collective plural — `محتويات` vs. `مُحتَوى` distinction needs Mu'jam al-Wasīṭ ruling

3. **The fiqh-adjacent gap no LLM can solve**: sacred-text and honorific adjacency rules (spacing between Qur'anic citations and secular prose, line-break prohibitions inside ayah/hadith chains, font-switching conventions, when transliteration of sacred names is permitted vs. forbidden). Training data conflates Sunni / Shia / Orientalist conventions. **Recommended sourcing**: King Fahd Complex (Madinah) + Al Jazeera Stylebook §sacred-text + peer-reviewed *Journal of Qur'anic Studies* or al-Azhar's *Majallat al-Buḥūth al-Islāmiyyah*. **Do not synthesize from LLM output.**

→ **Shipped in v0.2 as `references/02-external-sources.md`**

## Lens 2 — Kimi-style (asset promotion + structure)

**Charter**: identify what 5-10 distinct asset types should migrate into the toolkit, propose v0.2 file structure, define schema-versioning policy, name the first net-new contribution.

**Key findings:**

1. **8 distinct asset types** identified for migration from humanizer:
   - **A** — Calque dictionary (`corpus/calque-dictionary.json`)
   - **B** — Empirical corpus statistics (`corpus/empirical-patterns.json`)
   - **C** — Inherited lexical-substitution tables (`AI_PHRASES_AR`, connectors, repetitive starters, fillers, numbered transitions) — currently Markdown, needs JSON promotion
   - **D** — Connector inventory + reference distribution (10 classical connectors with Shannon-entropy reference)
   - **E** — Typography hygiene rules (5 mechanical rules + 13-source authority log)
   - **F** — Reader-respect (cognitive-restraint) patterns (6 anti-patterns with deletion regexes)
   - **G** — Register policy matrix (the gating logic itself is the asset, not the prose)
   - **H** — Topic-guard policy module (context-keywords-gate spec + v2.6.3 exclusion catalogue)

   **Explicit non-includes**: sacred-text guard, orthographic validator, verb-agreement validator — these are *transformations*, which the toolkit's charter forbids. Resist scope creep.

2. **v0.2 file structure** proposal (partial implementation in v0.2; remaining ships v0.3+):
   - `corpus/calque-dictionary.schema.json` ✅ (v0.3)
   - `corpus/empirical-patterns.schema.json` ⏳ (v0.4)
   - `corpus/lexical-tables.json` (asset C) ⏳ (v0.4)
   - `corpus/connectors.json` (asset D) ⏳ (v0.4)
   - `corpus/typography-rules.json` (asset E) ⏳ (v0.5)
   - `corpus/reader-respect-patterns.json` (asset F) ⏳ (v0.5)
   - `corpus/register-policies.json` (asset G) — superseded by `scripts/register.py` (in code, per Codex)
   - `corpus/topic-guards.json` (asset H) — already encoded in the dictionary's `context_keywords_*` fields ✅
   - `scripts/lookup.py` — replaced by `scripts/dictionary.py` ✅ + `scripts/register.py` ✅
   - `scripts/validate_dictionary.py` — generalized as `scripts/validate.py` ✅
   - `scripts/diff_schema.py` ⏳ (v0.5)
   - `scripts/export_consumer_view.py` ⏳ (v0.6)
   - `CHANGELOG.md` ✅ (v0.3)

3. **Schema-versioning policy**: **per-asset SemVer, not monolithic.** Each JSON file carries `$schema_version` internally. Three change classes:
   - PATCH (1.2.0 → 1.2.1): new entries, typo fixes, regex tightening — no consumer impact
   - MINOR (1.2.0 → 1.3.0): new optional field — additive, consumers ignore unknown fields
   - MAJOR (1.2.0 → 2.0.0): rename / drop / value-domain change — breaking, requires `migrate_X_to_Y.py`

   Adopted in `CHANGELOG.md`. Calque dictionary schema state at v0.3: **v1.2.0** (base + v2.6.0 triage + v2.6.3 topic-guard).

4. **The "first net-new contribution"**: a **formal schema validator with typed report** (Codex's `validate.py` shipped this). Reasoning: mere relocation doesn't justify the shared module. The toolkit earns its existence the moment dictionary edits have a *verified contract that survives across consumers*. The humanizer's v2.6.0 review caught 14 wrong entries via manual review; the validator converts that tribal knowledge into mechanical checks.

→ **Shipped in v0.3 as `scripts/validate.py`, `corpus/calque-dictionary.schema.json`, `CHANGELOG.md`**

## Lens 3 — Codex-style (implementation precision)

**Charter**: design three Python module files (dictionary, corpus_stats, register), the schema validation function, and the consumer migration path for humanizer. Push back on at least one design decision.

**Key findings:**

1. **Three module files, typed**: `dictionary.py` with `CalqueEntry` TypedDict + 7 query functions + mtime-keyed cache; `corpus_stats.py` with `ConnectorRow` TypedDict + 4 query functions; `register.py` as code-not-JSON with 4 policy entries + `UnknownRegisterError`. All stdlib-only.

2. **`SchemaReport` dataclass**: separates ERRORS (blocking, missing required fields), WARNINGS (non-blocking, unknown enum values, missing recommended fields), UNKNOWN FIELDS (forward-compat tracking — catches typos like `politcal_sensitivity` without rejecting new v2.7+ fields), and COVERAGE (per-v2.6+ optional field, count of entries that carry it — the regression detector for triage coverage).

3. **Consumer migration path**: concrete diff against `humanize_v2.py::_load_calque_dictionary`. The internal lookup shape (`{"natural": ..., "alternatives": ..., ...}`) stays identical so downstream `lex_apply_calque_dictionary` and `_matches_topic` don't change. Only the loader switches from local file to toolkit import. Compat shim during transition; removed in humanizer v2.8.0.

4. **Pushback: JSON stays. Reject SQLite-FTS.**
   - Argument B's "SQLite-FTS at >2K entries" is the wrong threshold — the right metric is access pattern, not entry count.
   - The humanizer's hot loop is whole-table scan sorted by length. SQLite-FTS optimizes substring search inside a corpus — the *opposite* workload.
   - SQLite kills `git diff` review-ability of triage edits — and the v2.6.0 review depended on that.
   - At 2K+ entries the real bottleneck isn't lookup, it's the longest-first regex sweep — solved by an **Aho-Corasick automaton** built once at load time (stdlib trie), not by SQLite.
   - **Concession**: `empirical-patterns.json` if it grows multi-MB is a candidate for SQLite as a *derived artifact*, not as source. Source stays human-readable.

→ **Shipped in v0.3 as `scripts/dictionary.py` (v0.2), `scripts/register.py` (v0.3), `scripts/validate.py` (v0.3) — Codex's design adopted verbatim with minor naming tweaks. `corpus_stats.py` deferred to v0.4 pending empirical-patterns schema formalization. JSON-vs-SQLite decision documented in `references/03-api-design.md`.**

## What's in v0.3 (this release)

| Asset | Source lens | File |
|---|---|---|
| Schema validator | Codex-style | `scripts/validate.py` |
| Register policy API | Codex-style | `scripts/register.py` |
| Formal JSON Schema | Kimi-style | `corpus/calque-dictionary.schema.json` |
| Per-asset SemVer log | Kimi-style | `CHANGELOG.md` |
| API design narrative | Codex-style | `references/03-api-design.md` |
| This synthesis | Cross-lens | `references/04-multi-agent-synthesis.md` |

## What's deferred to v0.4+

| Asset | Target version |
|---|---|
| `corpus_stats.py` + `empirical-patterns.schema.json` | v0.4 |
| Asset C migration (lexical-tables.json) | v0.4 |
| Asset D migration (connectors.json) | v0.4 |
| Aho-Corasick `compiled_matcher()` in dictionary.py (Codex forward-compat door) | v0.5 (when humanizer/translator request it) |
| Asset E (typography-rules.json) | v0.5 |
| Asset F (reader-respect-patterns.json) | v0.5 |
| `scripts/diff_schema.py` (MAJOR-break refusal CLI) | v0.5 |
| `scripts/export_consumer_view.py` | v0.6 |
| Humanizer migration to consume toolkit (v2.7.0 of humanizer) | concurrent with v0.4 |
| Translator scaffold (v2.8.0 of humanizer family) | post-v0.5 |

## Method note

This synthesis is preserved as a permanent reference because **the v0.2 multi-agent review uncovered the same architectural pattern that the v2.6.0 humanizer review uncovered**: cross-LLM lenses surface load-bearing decisions that no single perspective catches. The v0.2 review independently found:

- Gemini-style: external authoritative sources are not optional (the fiqh-adjacent gap)
- Kimi-style: the toolkit's *value* is a verified contract, not relocation
- Codex-style: typed schemas + dataclass reports are the mechanical version of the v2.6.0 manual triage

All three are the same lesson at different abstraction levels: **multi-LLM consensus is unreliable for fine-grained Arabic, so the toolkit's job is to make verification mechanical and per-entry auditable.**

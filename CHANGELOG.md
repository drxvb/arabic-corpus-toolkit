# Changelog

Per the Kimi-style asset-promotion lens of the v0.2 multi-agent review, this toolkit uses **per-asset SemVer with a registry** rather than monolithic versions. The toolkit release version (v0.3, etc.) coordinates ship cadence; the schema version of each data file lives **inside** the file under `$schema_version` and follows independent SemVer.

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

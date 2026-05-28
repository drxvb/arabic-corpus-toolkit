# Changelog

Per the Kimi-style asset-promotion lens of the v0.2 multi-agent review, this toolkit uses **per-asset SemVer with a registry** rather than monolithic versions. The toolkit release version (v0.3, etc.) coordinates ship cadence; the schema version of each data file lives **inside** the file under `$schema_version` and follows independent SemVer.

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

# 05 — Asset C migration audit (v0.7 → v0.7.1)

## TL;DR

Toolkit **v0.7** migrated the lexical-tables asset from `arabic-ai-text-humanizer/references/13-inherited-lexical-tables.md` (Markdown documentation). The documentation lagged the live code. **v0.7.1** brings the asset to parity with `arabic-ai-text-humanizer/scripts/humanize_v2.py` (the actual source of truth). This document is the permanent record of the gap and its resolution.

## How the gap was discovered

The v0.7 release was followed by an attempt to cut over the humanizer to read Asset C from the toolkit. The cutover step required reading the live humanizer code to know what API surface it needed. That reading revealed the in-code tables were significantly richer than the documentation I had migrated from. The cutover was paused; v0.7.1 was opened to close the gap before any consumer touched the asset.

This pattern — "the cutover step IS the audit step" — is now a documented principle: data-asset migrations should always finish at the consumer cutover, because that's the step that proves the asset is faithful to actual usage. Stopping at "asset migrated, lint passes" leaves the gap invisible.

## What was missing in v1.0.0

### Content gaps (`ai_phrases`)

| Category | v1.0.0 had | v1.0.0 missed (now in v1.1.0) |
|---|---|---|
| v1 substrate | 30 entries (matched doc) | — |
| Gap A (corpus mining) | 10 entries | — |
| **Clause-preserving variants** | 0 | 7 entries with distinct treatment for `…أن` (clausal) vs bare forms |
| **Pro-drop deletions** | 0 | 7 entries with `""` as a valid alternative (Arabic prefers implicit subjects for fluff verbs) |
| **Newsroom AI-tells** | 0 | 16 entries from the cross-LLM journalist critique |
| **English-calque pipeline** | 0 | 4 entries (`خط أنابيب → مسار عمل` and variants) |
| **Tashkeel-bearing variants** | 0 | 1 explicit (`لا شك أنّ`); folded into existing entries |

**v1.0.0 total: 40 ai_phrases. v1.1.0 total: 67 ai_phrases** (6 pro-drop + 1 tautology + 7 clause-preserving + 21 v1 substrate + 4 English-calque + 16 newsroom AI-tells + 12 Gap A).

### Policy gaps

| Sub-table | v1.0.0 policy | v1.1.0 policy | Why it matters |
|---|---|---|---|
| `structural_openers` (was `templated_starters`) | `advisory_strategy` (documentation-only) | `regex_capture_substitute` (mechanically-applicable) | The humanizer ACTUALLY applies these via `re.sub` with capture groups. Calling them "advisory" was a misclassification. |
| `intensifier_destack` | `global_policies` advisory note | First-class table with `regex_substitute` policy | The humanizer has 8 enforced regex de-stack patterns; documenting them as "global policy" hid them from the loader's API. |

### Schema gaps

- **`alternatives` items required `minLength: 1`.** This made pro-drop deletion (the `""` alternative) structurally invalid in v1.0.0. Relaxed to `minLength: 0` in v1.1.0 with a description explaining the pro-drop semantics.
- **No `regex_capture_substitute` policy.** Added.
- **No `regex_substitute` policy.** Added.

## What did NOT change

- Per-asset SemVer rules still hold. v1.1.0 is MINOR not MAJOR: additive (new tables, new policy types) and backward-relaxing (`minLength` 1→0). v1.0.0 readers that don't know about `structural_openers` / `intensifier_destack` simply ignore them.
- `quote_verbs` still has 4 entries (the tashkeel/bare distinction for `ذكر أن`/`أنّ` was always there in the humanizer; v1.0.0 collapsed them — now restored).
- `connectors`, `numbered_transitions`, `fillers` tables were correct in v1.0.0; minor tashkeel updates only.

## Why the v0.7 migration drifted

The lexical-tables documentation in the humanizer (`references/13-inherited-lexical-tables.md`) was authored once at v2.5.x and updated rarely. The code (`scripts/humanize_v2.py`) was updated continuously through v2.5.1 → v2.6.0 → v2.6.4 → v2.7.0 with newsroom AI-tells, calque dictionary entries, pro-drop deletions, and structural-opener regex patterns. The doc's "## How v2 calls this layer" Python snippet still listed the original 5 tables; the actual code had ~8 tables and ~50% more entries.

This is not a defect of the v2.7.0 humanizer — the doc was always an introduction to the layer, never a contract. The migration's mistake was treating the doc as the source of truth.

## Lesson encoded in the toolkit

`scripts/diff_schema.py` already enforces per-asset SemVer for **schema** changes. v0.7.1 demonstrates the equivalent need for **content** parity: when migrating an asset from a consumer, the migration must terminate at the consumer's actual code, not its documentation. Future asset migrations (e.g., a v0.8 promotion of the humanizer's sacred-text-guard heuristics) should follow this rule.

## State at v0.7.1

| Asset | Schema | Parity with humanizer v2.7.0 |
|---|---|---|
| `lexical-tables.json` | **v1.1.0** | ✅ Full parity confirmed by `scripts/test_lexical_tables.py` (counts + sample assertions) |

Cutover (humanizer reads from toolkit) is now safe to schedule for a future humanizer minor release.

## Provenance trail

- v1.0.0: derived from `arabic-ai-text-humanizer/references/13-inherited-lexical-tables.md` (lagging doc). Released in toolkit v0.7.
- v1.1.0: derived from `arabic-ai-text-humanizer/scripts/humanize_v2.py` lines 51-209 (humanizer v2.7.0). Released in toolkit v0.7.1.

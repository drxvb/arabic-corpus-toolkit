# arabic-corpus-toolkit

> Shared Arabic linguistic infrastructure: calque dictionary, corpus stats, register policies, MSA style guide. Consumed by `arabic-ai-text-humanizer`, the upcoming `arabic-corpus-translator`, and the future `arabic-authoring-suite`.

**Status:** v0.7.1 — Asset C parity audit ships. v0.7 was migrated from stale docs; v0.7.1 reconciles to the live humanizer code (asset schema v1.1.0). Six assets now live in this toolkit; three sibling skills consume them (`arabic-ai-text-humanizer` v2.7.0, `arabic-corpus-translator` v0.2.1, `arabic-authoring-suite` v0.1.1).

## Why this exists

Three sibling skills are about to consume the same calque dictionary, empirical-pattern statistics, and register policies that currently live inside `arabic-ai-text-humanizer`. Letting each sibling vendor its own copy guarantees they will drift. This toolkit is the shared, versioned, read-only foundation.

Architecturally validated by the multi-agent review documented at `M:\Main\AI\Corpus\humanizer-v2.6-multi-agent-synthesis.md` (Agent C: scope critic — recommended this as the "load-bearing keystone" of the 4-sibling family).

## Family map

```
                              ┌─────────────────────────────┐
                              │  arabic-corpus-toolkit      │
                              │  (this repo — shared infra) │
                              │  · calque-dictionary.json   │
                              │  · empirical-patterns.json  │
                              │  · register policies        │
                              │  · MSA style guide          │
                              │  · connector tables         │
                              └──────────────┬──────────────┘
                                             │ read-only consumption
                  ┌──────────────────────────┼──────────────────────────┐
                  ▼                          ▼                          ▼
   ┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐
   │ arabic-ai-text-      │  │ arabic-corpus-       │  │ arabic-authoring-    │
   │ humanizer            │  │ translator           │  │ suite                │
   │ (v2.6.0 — live)      │  │ (v0.1 — planned)     │  │ (Q1 2027 — planned)  │
   │ humanize prose       │  │ EN↔AR translation    │  │ books/articles/      │
   │                      │  │                      │  │ courses/news         │
   └──────────────────────┘  └──────────────────────┘  └──────────────────────┘
```

## Roadmap

| Version | Ships | Status |
|---|---|---|
| **v0.1** | Scaffold (SKILL.md, README, LICENSE, directory tree) | ✅ Done |
| **v0.2** | Asset A (calque-dictionary) + Asset B (empirical-patterns) + `dictionary.py` read API | ✅ Done |
| **v0.3** | `validate.py` SchemaReport + `register.py` policy lookup + schema files + CHANGELOG | ✅ Done |
| **v0.4** | `corpus_stats.py` 10-function read API for translator | ✅ Done |
| **v0.5** | Asset D (typography-rules) + Asset E (reader-respect-patterns) + `diff_schema.py` CLI | ✅ Done |
| **v0.6** | `export_consumer_view.py` (3 view modes × 3 formats) | ✅ Done |
| **v0.7** | **Asset C (lexical-tables): 40 ai-phrases + 21 connectors + 5 numbered + 4 fillers + 7 repetitive starters + 3 quote-verb pools + 10 advisory templated starters; per-table substitution policies in data; `lexical_tables.py` 13-function read API + soft-validate + stats** | ✅ **This release** |
| v0.8+ | Aho-Corasick matcher for dictionary; humanizer cutover to read Asset C from toolkit | Pending |
| v1.0 | All consumers pinned to stable schemas; per-asset SemVer enforced | Q2 2027 |

## License

MIT. See `LICENSE`. Migrated content retains upstream provenance (humanizer → stop-slop for the English portions; humanizer's own multi-LLM-swarm + AITNews mining for Arabic calque dictionary).

## Full charter

See `SKILL.md` for the full skill specification, including frontmatter triggers, scope boundaries, read-only API intent, and migration plan.

# arabic-corpus-toolkit

> Shared Arabic linguistic infrastructure: calque dictionary, corpus stats, register policies, MSA style guide. Consumed by `arabic-ai-text-humanizer`, the upcoming `arabic-corpus-translator`, and the future `arabic-authoring-suite`.

**Status:** v0.1 scaffold. Asset migration from `arabic-ai-text-humanizer` is staged for v0.2.

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
| **v0.1** | Scaffold (SKILL.md, README, LICENSE, directory tree) | ✅ Current |
| **v0.2** | Migrate `calque-dictionary.json` + `empirical-patterns.json` from humanizer | Pending humanizer v2.7.0 |
| **v0.3** | Migrate register policies + connector tables + MSA style guide | Pending humanizer v2.7.0 |
| **v0.4** | Read API for `arabic-corpus-translator` | Pending translator scaffold |
| **v0.5** | Read API for `arabic-authoring-suite` | Pending authoring scaffold |
| **v1.0** | All three consumers stable; semver enforced | Q2 2027 |

## License

MIT. See `LICENSE`. Migrated content retains upstream provenance (humanizer → stop-slop for the English portions; humanizer's own multi-LLM-swarm + AITNews mining for Arabic calque dictionary).

## Full charter

See `SKILL.md` for the full skill specification, including frontmatter triggers, scope boundaries, read-only API intent, and migration plan.

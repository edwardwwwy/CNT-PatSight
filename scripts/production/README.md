# Continuous production pipeline

This module runs the legal full-text producer and local Qwen extraction
consumer as two independent Windows background processes. It reads the frozen
`screening_rules_v1.2` metadata snapshot and never writes the formal source
packages or `data/processed/`.

```powershell
python scripts/production/pipeline.py prepare
python scripts/production/pipeline.py smoke-test
python scripts/production/pipeline.py start
python scripts/production/pipeline.py status --watch
python scripts/production/pipeline.py stop --all
python scripts/production/pipeline.py resume
```

`prepare` verifies frozen hashes, assigns A batches `50/50/50/58` and B
batches `50/50/50/50/50/50/50/21`, writes the 579-row derived production
Manifest, snapshots the Qwen/prompt/schema/parser/unit configuration, and
idempotently seeds the 23 reviewed pilot candidates.

The Qwen task state and isolated eight-table staging data live in one local
SQLite database under `data/interim/llm_extraction/`. Raw v0.2 attempts are
immutable. Valid results are staged as `needs_review`; no command in this
module creates or promotes `formal_extract`.

PID, lock, heartbeat, stop signal, and logs use the single
`data/interim/runtime/` directory. A normal stop is cooperative and completes
the current atomic step before the worker exits.

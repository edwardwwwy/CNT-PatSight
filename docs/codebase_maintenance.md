# Codebase maintenance guide

This repository combines an active pipeline with curated research-build
artifacts. Treating those two layers differently keeps maintenance predictable.

## Active code paths

- `collect_metadata/`, `fetch_fulltext/`, and `parse_fulltext/` ingest and parse
  legally accessible source material.
- `extraction/package.py` selects compact, evidence-oriented input packages.
- `production/staging.py` validates extraction payloads and maps them into the
  eight-table contract.
- `validation/validate_tables.py` is the final package and formalization gate.
- `production/pipeline.py doctor` is the clean-clone repository self-check.

Changes to these paths require tests, a full Ruff check, and the configured
`python -m mypy scripts` check.

## Curated batch builders

The numbered `build_a_class_batch_*.py` files encode source-specific research
decisions and reproduce historical staged data. They are intentionally
data-heavy, but they are not an application framework.

- Reusable row, schema, and evidence helpers belong in `batch_common.py`.
- New pipeline behavior belongs in the active modules above.
- Do not add a new numbered builder when a declarative fixture or normal staging
  input can represent the same information.
- Do not refactor scientific values mechanically without comparing regenerated
  eight-table output.

## Dependency layers

- `requirements.txt`: core collection, parsing, staging, and validation runtime.
- `requirements-dev.txt`: test and lint tools.
- `requirements-reporting.txt`: optional Pandas/ReportLab PDF reporting.
- `scripts/nanopub_demo/requirements.txt`: optional nanopublication demo.

## Repository hygiene

Raw content, SQLite databases, runtime queues, and bulk intermediate CSV files
are local artifacts even when old commits still contain them. Keep public Git
content limited to source, configuration, tests, small licensed examples, and
reviewed benchmark/report outputs. Use `git ls-files -ci --exclude-standard` to
detect files that remain tracked despite `.gitignore`.

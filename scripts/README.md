# Script map

Scripts are grouped by production responsibility:

| Directory | Responsibility |
|---|---|
| `collect_metadata/` | API collection, normalization, conservative deduplication, and screening inputs |
| `fetch_fulltext/` | Legal open-full-text discovery, download, signature checks, and hashing |
| `parse_fulltext/` | PDF/HTML parsing, section detection, tables, captions, and candidate spans |
| `extraction/` | Evidence-package selection, shared batch helpers, and curated historical batch builders |
| `production/` | Queueing, leases, recovery, monitoring, extraction validation, and transactional staging |
| `validation/` | Formal eight-table schema, relationship, evidence, issue, and review-state validation |
| `screening_benchmark/` | Metadata screening and deduplication benchmark |
| `regression/` | Reproducible regression-package builders |
| `reporting/` | Optional PDF reports; install `requirements-reporting.txt` first |

## Maintenance boundaries

- `scripts/extraction/batch_common.py` owns shared row and evidence helpers.
- `build_a_class_batch_*.py` files are curated, source-specific research
  artifacts. They should not define reusable infrastructure.
- New automated extraction logic belongs in `production/staging.py`, with tests,
  rather than in another source-specific batch script.
- Runtime state, downloaded content, and generated reports stay outside tracked
  source code.

Common checks:

```powershell
python scripts/production/pipeline.py doctor
python -m pytest -q
python -m ruff check scripts tests
python -m mypy scripts
python scripts/validation/validate_tables.py data/interim/<source_id>
```

See [`docs/codebase_maintenance.md`](../docs/codebase_maintenance.md) for the
active-versus-curated boundary and dependency policy.

# CNT-LitSight repository structure

## Data lifecycle

```text
raw -> interim -> processed -> benchmark -> audit
```

```text
data/
├─ raw/
│  ├─ literature/{pdf,html,metadata,supplements}/
│  ├─ api_responses/<provider>/<run>.jsonl.gz
│  └─ source_manifest.csv
├─ interim/
│  ├─ parsed_text/by_source/<source_id>.parsed.json
│  ├─ extraction/{A,B,C}/<source_id>.extraction.json
│  ├─ evidence/evidence_candidates.jsonl
│  └─ review_queue/{pending,resolved}.jsonl
├─ processed/{eight_tables,analysis,snapshots}/
├─ benchmark/{gold,fixtures,templates,results}/
└─ audit/{samples,issues,summaries}/
```

Top-level `runs/` holds execution logs, `cache/` holds renders and mutable
databases, and `reports/` holds curated final reports. These directories are
not alternate data sources.

## Invariants

- Each source has at most one extraction package, under exactly one A/B/C tier.
- A parsed source has exactly one `<source_id>.parsed.json` artifact.
- `data/processed/eight_tables/` is the only formal eight-table source.
- A/B/C are record attributes; they do not create separate formal datasets.
- Company data is outside this repository and is located with
  `CNT_COMPANY_DATA_DIR`.
- Historical runs and superseded artifacts are kept in the external archive,
  not under `data/`.

Run `python -m scripts.validation.validate_data_layout` after changing a data
boundary. The safe migration entrypoint is
`python -m scripts.migration.restructure_data --help`.

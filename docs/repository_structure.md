# CNT-PatSight repository structure

## Active data flow

```text
data/raw/metadata/
  -> data/raw/fulltext/
  -> data/interim/parsed_text/
  -> data/interim/extraction_candidates/
  -> data/interim/extraction_batches/
  -> data/interim/eight_table_staging/
  -> data/review/extraction/
  -> data/processed/
```

## Directory responsibilities

| Path | Purpose |
|---|---|
| `config/` | Eight-table schema, field dictionary, extraction contracts, screening rules |
| `data/raw/metadata/` | API responses, normalized metadata, frozen screening snapshots |
| `data/raw/fulltext/` | Legal OA acquisition registry and verified PDF/HTML/text assets |
| `data/interim/parsed_text/` | Regenerable parsed full text |
| `data/interim/extraction_candidates/` | Sections, candidate experiment spans, parse status |
| `data/interim/extraction_control/` | Generic extraction queue and transactional staging database |
| `data/interim/extraction_batches/` | Bounded extraction batch manifests and cost metrics |
| `data/interim/eight_table_staging/` | First-pass eight-table packages awaiting independent evidence review |
| `data/interim/regression/gold/` | Reviewer-authored regression gold packages |
| `data/interim/legacy_audit/` | Retired immutable attempts retained only for audit |
| `data/review/extraction/` | Current evidence-review queues and decisions |
| `data/processed/` | Agent-reviewed data that passed the formalization gate |
| `scripts/extraction/` | Evidence-package selection, shared batch helpers, and curated batch builders |
| `scripts/production/` | Metadata/full-text/candidate queue, extraction validation, and staging control |
| `scripts/validation/` | Eight-table schema, relation, evidence, and issue validation |
| `scripts/regression/` | Reproducible regression package builders |
| `tmp/` | Deletable rendering, parsing, and debugging files |

## Invariants

- Source truth remains the eight formal tables.
- First-pass packages remain `needs_review`.
- A designated review agent may set `formal_extract` and `reviewed` after the formalization gate passes.
- Retired audit artifacts are not imported, queued, or executed.
- Local model binaries and runtimes are not part of the repository.

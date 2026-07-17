# Production pipeline

The production layer now covers:

```text
frozen metadata
-> legal full-text acquisition
-> PDF/HTML validation and deduplication
-> text/section/table/caption parsing
-> candidate_extract queue
```

It does not launch a local language model. Extraction tasks are completed by an
evidence-grounded reviewer and written through the model-independent validation
and eight-table staging code.

```powershell
python scripts/production/pipeline.py prepare
python scripts/production/pipeline.py smoke-test
python scripts/production/pipeline.py start
python scripts/production/pipeline.py status
python scripts/production/pipeline.py export-review --source-id <SOURCE_ID>
python scripts/production/pipeline.py stop --all
python scripts/production/pipeline.py resume
```

Active control state is stored under:

```text
data/interim/extraction_control/
data/interim/runtime/
```

Validated review-layer exports are stored under:

```text
data/interim/eight_table_staging/review_packages/
```

No command promotes a source to `formal_extract` or `reviewed`.

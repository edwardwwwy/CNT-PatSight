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
python scripts/production/pipeline.py doctor
python scripts/production/pipeline.py prepare
python scripts/production/pipeline.py smoke-test
python scripts/production/pipeline.py start
python scripts/production/pipeline.py status
python scripts/production/pipeline.py export-review --source-id <SOURCE_ID>
python scripts/production/pipeline.py stop --all
python scripts/production/pipeline.py resume
```

`doctor` checks the public schemas, field dictionary, configuration JSON, and a
temporary production database. It works on a clean clone. `prepare` and
`smoke-test` additionally require the local metadata, full-text, and candidate
databases described below.

Active control state is stored under:

```text
data/interim/extraction_control/
data/interim/runtime/
```

Validated review-layer exports are stored under:

```text
data/interim/eight_table_staging/review_packages/
```

Formalization is a separate review step. A designated evidence-review agent may
set `formal_extract` and `reviewed` after the package passes the gates in
`docs/review_and_formalization.md`; routine owner approval is not required.

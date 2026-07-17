# Rule-based full-text parser

This module converts the primary registered PDF/HTML for each source into
reviewable text sections and experiment candidate spans. It is an intermediate
layer only: no LLM is called and none of the eight formal tables is written.

## Dependencies

Install the project dependencies, which include `pdfplumber` and `pypdf`.

```powershell
python -m pip install -r requirements.txt
```

## Run

```powershell
python scripts/parse_fulltext/parse.py run
python scripts/parse_fulltext/parse.py report
python scripts/parse_fulltext/parse.py export
```

Use `--source-id <id>` for a selected source and `--force` after changing parser
rules. Caching is keyed by source content hash and parser version.

## Outputs

- Candidate registry: `data/interim/extraction_candidates/extraction_candidates.sqlite3`
- Faithful raw text: `data/raw/fulltext/text/<source_id>.txt`
- Per-source structured package: `data/interim/parsed_text/<source_id>/`
- Section export: `data/interim/extraction_candidates/paper_text_section.csv`
- Candidate export: `data/interim/extraction_candidates/candidate_experiment_span.csv`
- Per-source status: `data/interim/extraction_candidates/parse_source_status.csv`
- OCR queue: `data/interim/extraction_candidates/ocr_queue.csv`
- Run reports: `data/interim/extraction_candidates/reports/`

Each per-source package contains `document_metadata.json`, `full_text.txt`,
`sections.json`, `tables.json`, `figures_captions.json`, and
`parse_report.json`. These files preserve the parser result used for review and
later extraction benchmarking without writing to the formal eight-table layer.

PDF parsing uses page-aware text extraction, conservative two-column ordering,
table extraction, figure-caption detection, and metadata fallbacks. HTML parsing
keeps headings, paragraphs, figure captions, and table rows.

Normalized section types include title, abstract, methods, experimental,
catalyst preparation, CVD growth, characterization, results/discussion,
conclusions, references, tables, figure captions, and supplementary hints.
Candidate span types cover catalyst, process, gas, yield, characterization,
purification, and scale/safety signals. Every first-pass section and candidate
has `needs_review = 1`.

The status export also records `parse_quality` (`good`, `partial`, `scanned`,
`broken_layout`, `metadata_only`, or `unreadable`), page and character counts,
table count, references/experimental-section detection, and `ocr_required`.
OCR is only recommended for a PDF classified as `scanned`; this module does not
run OCR automatically.

`fulltext_relevance_status = candidate_extract` is only recommended when the
parsed text contains CNT identity, an experimental/methods/growth section, and
multiple experimental evidence types including catalyst/process/gas evidence.
This intermediate recommendation never creates `formal_extract` and does not
write any of the eight formal tables.

The parser deliberately produces candidate evidence rather than facts. Run
splitting, field interpretation, evidence mapping, and transfer into the formal
eight-table package remain human-reviewed downstream work.

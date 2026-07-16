# Extraction candidate layer

This directory contains reviewable Python extraction outputs before any formal
eight-table mapping:

- `paper_text_section.csv`: normalized document sections with page ranges.
- `candidate_experiment_span.csv`: keyword/rule-selected experimental spans.
- `parse_source_status.csv`: one row per metadata source, including explicit
  skipped/failed reasons, parse quality, page/text/table metrics, OCR flag, and
  full-text relevance recommendation.
- `ocr_queue.csv`: only sources classified as scanned PDFs after ordinary text
  extraction; OCR itself is not run automatically.
- `extraction_candidates.sqlite3`: authoritative local candidate registry.
- `reports/`: per-run summaries and `latest.json`.

All sections and spans are first-pass material with `needs_review = 1`. These
files must not be treated as verified experimental facts.

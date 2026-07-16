# Full-text acquisition layer

This module turns the phase-one metadata registry into a traceable full-text
coverage registry. It does **not** write any of the eight formal extraction
tables.

## Inputs and configuration

- Metadata registry: `data/raw/metadata/literature.sqlite3`
- Local PDFs already registered in metadata: `data/raw/papers/`
- Candidate PDF/HTML URLs, DOI, paper ID, and OA metadata from phase one
- Optional manually verified OA candidates:
  `data/raw/fulltext/verified_oa_candidates.csv`
- `UNPAYWALL_EMAIL` from `.env` for DOI lookups

Credentials and email addresses are never written to reports. The `.env` file
must remain local.

## Run

```powershell
python scripts/fetch_fulltext/fetch.py queue
python scripts/fetch_fulltext/fetch.py run
python scripts/fetch_fulltext/fetch.py report
python scripts/fetch_fulltext/fetch.py export
```

`queue` generates exactly one derived acquisition row for each current A/B
canonical work. M is excluded until metadata is improved and rescored; C and R
are excluded by default. `run` consumes this queue in priority order. Use
`--all-metadata` only for an explicit diagnostic override.

The verified-candidate CSV is an auditable fallback for official publisher or
institutional-repository links that are missing from the API metadata. Rows are
eligible only when both `verified` and `legal_oa` are true. The fetcher records
the supplied source, access type, and licence; unverified rows are ignored.

Limit a diagnostic run with repeated `--source-id` options. `--force` retries
remote candidates, while successful content is still stored by hash and atomic
rename. `--no-unpaywall` disables the DOI lookup.

## Outputs

- SQLite registry: `data/raw/fulltext/fulltext.sqlite3`
- PDF cache: `data/raw/fulltext/pdf/`
- HTML cache: `data/raw/fulltext/html/`
- Per-attempt reports: `data/raw/fulltext/reports/`
- Detailed export: `data/raw/fulltext/fulltext_source.csv`
- Acquisition queue: `data/raw/fulltext/fulltext_acquisition_queue.csv`
- One-row-per-source acceptance view: `data/raw/fulltext/fulltext_coverage.csv`
- Verified OA fallback input: `data/raw/fulltext/verified_oa_candidates.csv`

`fulltext_source` records successes and failures separately. A successful local
or downloaded file is never downgraded by a later failed URL. Local PDFs remain
at their original path and are registered by SHA-256; they are not copied,
renamed, or overwritten. Remote responses must pass content sniffing before a
PDF or scholarly full-text HTML document is saved.

Repeated runs reuse successful content by `fulltext_id`, local path, and content
hash. Unavailable sources may be retried so that temporary publisher failures
can recover, but a retry cannot create another copy of an existing artifact.

Queue statuses are `queued`, `downloading`, `downloaded`, `validated`,
`not_pdf`, `blocked`, `paywalled`, `not_found`, `failed_retryable`,
`failed_final`, and `local_existing`. The queue stores HTTP/MIME results,
resolved URL, attempt count, local path, byte size, SHA-256, failure reason,
access type, license when supplied, and the queue-rule version. Direct PDF/HTML
candidates are accepted only from OA metadata or Unpaywall; DOI/publisher pages
may be inspected for openly served content but are never saved as PDF merely
because the URL or response claims PDF.

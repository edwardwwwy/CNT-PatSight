# Full-text acquisition layer

This module turns the phase-one metadata registry into a traceable full-text
coverage registry. It does **not** write any of the eight formal extraction
tables.

## Inputs and configuration

- Metadata registry: `data/raw/literature/metadata/literature.sqlite3`
- Local PDFs already registered in metadata: `data/raw/literature/pdf/local_papers/`
- Candidate PDF/HTML URLs, DOI, paper ID, and OA metadata from phase one
- Optional manually verified OA candidates:
`data/raw/literature/metadata/fulltext_registry/verified_oa_candidates.csv`
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

`queue` generates exactly one derived acquisition row for each eligible
canonical work in deterministic production lanes A, B, C, then D. D contains
frozen M records only after the metadata-enrichment completion gate; R remains
excluded. `run` consumes this queue in lane and priority order. Use
`--all-metadata` only for an explicit diagnostic override.

For a source without validated full text, candidates are attempted in this
order:

1. Existing local PDF, registered in place and never overwritten.
2. Unpaywall OA PDF/HTML.
3. OpenAlex and Semantic Scholar open-full-text locations retained in the
   source-provider records.
4. DOI/publisher pages for public OA, accepted manuscripts, or public
   scholarly HTML.
5. Verified arXiv, ChemRxiv, bioRxiv, Zenodo, HAL, CORE, PubMed Central,
   Europe PMC, institutional-repository, or author-page locations.
6. Verified related preprint, accepted-manuscript, author-manuscript, and
   published versions with an explicit version relation.
7. DOI and publisher URL for download through an authorised institutional
   subscription.

The verified-candidate CSV is the auditable input for step 5 and step 6 links
that are missing from API metadata. Rows are eligible only when both
`verification_status=verified` and `access_type=legal_oa`. It may add
`acquisition_step`, `version_type`, `version_relation`, and
`related_source_id`. Non-published versions require an explicit relation:
`preprint_of`, `accepted_manuscript_of`, or `author_manuscript_of`; otherwise
the row is ignored to prevent false merging.

Sci-Hub, shadow libraries, unknown PDF mirrors, and other unauthorised sources
are permanently prohibited and are never a fallback step.

Limit a diagnostic run with repeated `--source-id` options. `--force` retries
remote candidates, while successful content is still stored by hash and atomic
rename. `--no-unpaywall` disables the DOI lookup.

## Outputs

- SQLite registry: `data/raw/literature/metadata/fulltext_registry/fulltext.sqlite3`
- PDF cache: `data/raw/literature/pdf/`
- Raw HTML: `data/raw/literature/html/`
- Per-attempt reports: `runs/fulltext/`
- Detailed export: `data/raw/literature/metadata/fulltext_registry/fulltext_source.csv`
- Acquisition queue: `data/raw/literature/metadata/fulltext_registry/fulltext_acquisition_queue.csv`
- One-row-per-source acceptance view: `data/raw/literature/metadata/fulltext_registry/fulltext_coverage.csv`
- Verified OA fallback input: `data/raw/literature/metadata/fulltext_registry/verified_oa_candidates.csv`

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

When all legal candidates are exhausted, the control and coverage exports keep
the metadata row and record:

```text
fulltext_status = unavailable_legally
acquisition_status = manual_access_required
failure_reason = no_legal_fulltext_found
```

The same row retains `doi`, `publisher_url`, and `manual_access_url` for an
authorised user or company subscription.

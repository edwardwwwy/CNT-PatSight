# CNT-PatSight nanopublication PoC

This directory contains a local-only export layer for one existing, manually curated eight-table paper package. The formal CSV tables remain the source of truth. Version 0.2 creates five independent run-level nanopublications instead of one paper-sized RDF mirror.

## Environment

The demo uses the `ML` conda environment and the Python `nanopub` package. No server upload or nanopub signing is performed.

```powershell
conda run -n ML python scripts/nanopub_demo/build_demo.py
```

## Input

`data/interim/P003_Pan_2025_FeMo_MgO_Methane_CNT/`

All eight CSV tables are read. Core assertion facts come from a strict whitelist of key catalyst, reactor/process/gas, yield, and product-quality fields. Missing, not-applicable, not-assessed, cost/scale assessment, mixed-status text, and fields without explicit evidence support remain in the formal CSVs and are summarized in `completeness_report.json`.

The original `evidence_index.csv` remains record-level. The exporter does not rewrite it. Instead, a deterministic audited whitelist binds only fields explicitly supported by the existing evidence text. Each exported fact records both the derived field binding and the original `target_fields=record_level` status.

## Output

- `data/derived/nanopub_demo/P003_Pan_2025_FeMo_MgO_Methane_CNT.trig` (combined five-run dataset)
- `data/derived/nanopub_demo/runs/*.trig` (five independent run-level nanopublications)
- `data/derived/nanopub_demo/P003_Pan_2025_FeMo_MgO_Methane_CNT_mapping.json`
- `data/derived/nanopub_demo/metrics.json`
- `data/derived/nanopub_demo/completeness_report.json`
- `reports/nanopub_demo.html`

The script hashes all input tables before and after export and fails if any formal input changes. It also fails if a missing or non-publishable value enters the assertion, if any assertion fact lacks its audited evidence binding, if run nanopublication URIs collide, or if an individual TriG cannot be read back through the `nanopub` library. Numeric facts use `xsd:decimal` and explicit unit URIs.

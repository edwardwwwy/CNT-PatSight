# Phase-four Qwen staging extraction

This package runs the local Qwen GGUF model against the Python candidate-span
layer. It produces staging JSON and review queues only; it never writes the
formal eight tables.

## Minimal closure sample

The default sample set is defined in `config/llm_sample_set.json`:

- P001 Dubey 2012: three-run regression case;
- P002 Chotmunkhongsin 2023: methane CVD with hydrogen and kinetics;
- P006 Saetang 2024: temperature/feed-ratio/stability comparison.

These are deliberately three high-value regression samples, not an attempt to
expand the literature pool.

## Runtime

The expected model is `models/Qwen3-14B-Q4_K_M.gguf`. The local runtime used for
the current Windows GPU setup is `llama-completion.exe` from the ignored
`.tools/llama.cpp/current/` directory. It uses the Vulkan RTX 5070 Ti device,
temperature 0, fixed seed 42, quantized KV cache, and schema-constrained JSON.

If the runtime is elsewhere, pass `--runtime <path>`. Install Python validation
support with `python -m pip install -r requirements-llm.txt`.

## Commands

```powershell
# Prepare auditable span packages without calling the model
python scripts/extract_llm/extract.py prepare

# Run the three-sample minimal closure
python scripts/extract_llm/extract.py pipeline

# Repeat safely; existing validated JSON is reused
python scripts/extract_llm/extract.py pipeline

# Re-run after changing prompt/schema/runtime parameters
python scripts/extract_llm/extract.py pipeline --force

# Run one paper only
python scripts/extract_llm/extract.py pipeline --source-id P001_Dubey_2012_FeMo_MgO_tMWCNT
```

## Outputs

- `data/interim/llm_extraction/validated/`: schema/evidence-validated JSON;
- `data/review/llm_extraction/review_queue.csv`: one row per extracted source;
- `data/review/llm_extraction/validation_issues.csv`: validator findings;
- `data/review/llm_extraction/latest.json`: review export summary.

Raw request packages, prompts, model stdout/stderr, and run reports are kept in
the ignored `data/interim/llm_extraction/` subdirectories for local auditability.

The validator checks source/hash identity, candidate ID references, duplicate
IDs, evidence span existence, exact normalized quote inclusion, field-level
evidence coverage, run references, and open review-issue state. A valid result
is still marked `validated_needs_review`; validation is not human review and is
not permission to populate the eight tables.

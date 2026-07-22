# Extraction helpers

This package contains shared, source-independent code for:

- selecting section and experiment spans;
- building field-slot input packages;
- normalizing extraction payloads;
- validating evidence grounding and semantic consistency;
- mapping validated facts into the eight-table staging contract.

`llm_runner.py` adds one provider-neutral extraction entry point. The same run
planning, field schema, evidence hydration, eight-table mapping, and validators
are used for:

- a remote OpenAI-compatible API;
- a local Ollama model;
- a local llama.cpp server.

No paper-specific facts belong in the runner. First-pass extraction remains
`needs_review`; a separate evidence-grounded review may promote the package
after the formalization gate passes. See [LLM_RUNNER.md](LLM_RUNNER.md) for the
architecture and commands.

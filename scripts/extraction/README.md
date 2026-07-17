# Extraction helpers

This package contains model-independent code for:

- selecting section and experiment spans;
- building field-slot input packages;
- normalizing extraction payloads;
- validating evidence grounding and semantic consistency;
- mapping validated facts into the eight-table staging contract.

It does not start or manage a local language model. First-pass extraction is
performed by an evidence-grounded reviewer, and every resulting package remains
`needs_review` until human verification.

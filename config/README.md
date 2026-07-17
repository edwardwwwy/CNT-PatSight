# Configuration

- `schema.json`: authoritative eight-table filenames, columns, identities,
  foreign keys, and required fields.
- `field_dictionary.csv`: field semantics, units, population expectations,
  null policy, and inclusion rationale.
- `extraction_result_v0.2.schema.json`: evidence-value extraction payload
  contract.
- `run_plan_v1.schema.json`: experiment/run planning contract.
- `extraction_unit_rules_v1.json`: unit normalization and non-conversion rules.
- `screening_rules.json`: metadata screening rules.
- `review_policy.json`: first-pass states, agent-review formalization gates,
  legacy status compatibility, and owner-escalation conditions.

When the formal eight-table contract changes, update `schema.json`,
`field_dictionary.csv`, validators, tests, documentation, and any required
migration together.

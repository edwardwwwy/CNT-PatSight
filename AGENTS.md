# CNT-PatSight Project Background

## Project Identity

CNT-PatSight is a long-term research data workspace for collecting, structuring, and analyzing literature, patent, and experimental information related to carbon nanotube research and development.

The project is intended to support industrial CNT R&D, especially the development and optimization of CVD-based carbon nanotube production processes.

It is not primarily a web app, dashboard, or software product at the current stage. Its core value is to transform scattered scientific and patent information into structured, comparable, and evidence-backed R&D data.

---

## Project Skill Trigger

Before performing CNT-PatSight work involving literature or patent screening, metadata collection, PDF or full-text extraction, `run_id` construction, structured data extraction, schema design, table validation, catalyst/process/product comparison, CNT-type verification, industrial scale-up review, or R&D recommendations, read and use as project guidance:

```text
skills/cnt-patsight/SKILL.md
```

For schema design, field mapping, extraction outputs, or validation of the five main tables, consult when useful:

```text
skills/cnt-patsight/references/schema.md
```

Do not load the detailed schema reference for unrelated repository maintenance, general file organization, or tasks that do not operate on CNT research data. Treat the Skill as project-specific operating guidance: apply its evidence and uncertainty safeguards consistently while adapting its recommended fields and workflow to the value and completeness of each source.

---

## Core Motivation

Carbon nanotube research contains a large amount of useful information across papers, patents, theses, reports, and internal experiments. However, most of this information is scattered, inconsistent, and difficult for an R&D team to directly compare.

Important details are often distributed across experimental sections, tables, figures, patent examples, supporting information, and characterization results.

CNT-PatSight exists to solve this problem by building a structured knowledge base for CNT synthesis and industrial optimization.

The goal is not simply to summarize papers. The goal is to convert technical sources into reusable R&D data that can help answer questions such as:

- Which catalyst systems are most frequently reported?
- Which catalyst compositions are associated with higher yield or better MWCNT quality?
- Which supports, promoters, and preparation methods appear promising?
- What CVD process windows are commonly used?
- Which routes appear more suitable for industrial scale-up?
- Which reported results are reproducible, comparable, and relevant to company R&D?
- Which routes may reduce raw material cost, energy consumption, or post-treatment burden?

---

## Current Research Priority

The current priority of CNT-PatSight is:

- CVD / CCVD / catalytic decomposition routes for CNT synthesis
- Methane, CH4, natural gas, or methane-rich gas as the carbon source
- Multi-walled carbon nanotubes, especially MWCNT for industrial applications
- Industrial production optimization
- Catalyst formulation, support, promoter, preparation, and activation
- CVD conditions such as temperature, gas composition, flow rate, pressure, time, and reactor type
- Yield, productivity, product quality, purity, defect level, morphology, and cost-related indicators

This priority reflects the current R&D interest. It should not be treated as a permanent boundary. The project may later include other carbon sources, CNT forms, production routes, internal experimental data, cost models, or application-driven product requirements.

---

## Long-Term Project Goal

The long-term goal is to build a structured CNT R&D data system that can support:

- Literature and patent intelligence
- Catalyst comparison
- CVD process comparison
- Industrial feasibility evaluation
- Experimental planning
- Internal data integration
- Machine learning or statistical modeling
- R&D recommendation generation

The project should eventually help an industrial CNT R&D team move from scattered technical documents toward a data-driven understanding of catalyst-process-product relationships.

---

## Intended Users

The intended users include:

- CNT R&D engineers
- Catalyst development researchers
- Process engineers
- Materials scientists
- Data engineers supporting R&D
- Researchers evaluating patent and literature trends
- Future model or agent systems assisting CNT data extraction and analysis

The system should be useful to people who care about practical CNT production, not only academic summaries.

---

## Data Philosophy

CNT-PatSight values structured, traceable, and comparable data.

A useful data record should preserve the connection between:

- Source document
- Experimental or patent example
- Catalyst system
- CVD process
- Product result
- Quality characterization
- Industrial relevance

The project should avoid treating vague claims, broad patent ranges, or unsupported assumptions as concrete experimental facts.

The project should preserve uncertainty where information is incomplete. Missing information should remain missing rather than being invented.

The v0.1 five-table structure is the stable formal schema. By default, do not add fields to the five main tables unless the user explicitly requests a schema change. Stable and comparable run-level information should use the existing standard fields where practical.

Schema stability must not narrow information capture. Valuable exceptions, incomplete observations, unusual catalyst chemistry, negative results, and information outside the current priority should be preserved as source observations instead of forcing new main-table fields or fabricating a complete run. Preserve important conflicting values when they affect interpretation.

Screening should normally assign priority and relevance rather than permanently delete potentially useful sources. A source that cannot form a complete experimental run may still be useful for field design, mechanism comparison, catalyst preparation, CNT-type verification, failure analysis, scale-up, safety, or future experimental planning.

---

## v0.1 Schema Stability and Broad Capture

Use the following five tables as the stable v0.1 formal data model:

- `source_run`
- `catalyst_system`
- `reactor_process_gas`
- `yield_quality`
- `cost_scale_review`

Follow the principle: **schema strict, capture broad.**

- Do not add fields to the five main tables by default. Add or change a formal field only when the user explicitly requests it.
- Do not discard potentially useful R&D information merely because it does not fit the current schema or cannot form a complete `run_id`.
- Route source-level material to `source_level_observations` and information that does not map stably to the five tables to `valuable_unmapped_information`.
- Persist these observations in `data/interim/source_observations.jsonl` when saving extraction results.
- Treat `source_observations.jsonl` as a temporary information inbox, not as a sixth formal business table.

The observation inbox may retain mechanism explanations, failed conditions, deactivation causes, temperature effects, catalyst-preparation ideas, patent apparatus designs, scale-up risks, safety or environmental information, transferable information from other carbon sources or CNT types, and other useful evidence that cannot yet support a complete `run_id`.

Do not create main-table fields merely to avoid using observations. After approximately 20–30 representative sources have been extracted and reviewed, summarize recurring observation types and decide with the user whether any should be promoted into the formal schema.

Use screening as classification rather than deletion:

- `formal_extract`: extract evidence-supported runs into the five main tables; retain additional observations where useful.
- `candidate_extract`: keep as a candidate pending human review.
- `source_observation_only`: do not force formal runs; retain useful information as observations.
- `background_reference`: retain as background without detailed formal extraction.
- `reject`: use only for clearly irrelevant material.

Do not reject a source simply because it is not methane-based MWCNT work. Preserve it as an observation when it offers transferable catalyst design, activation, temperature-window, CNT-type evidence, reactor, failure-mode, or industrial insight.

For the first-round LLM extraction:

- Send evidence-supported formal run data to the five main tables.
- Send valuable non-run information to observations.
- Keep missing information as `null` or `not_reported` rather than guessing.
- Do not assign industrial scores or rankings without supporting evidence.

---

## Recommended Information Routing

Use these five main tables as the stable v0.1 organization for formal run data:

- `source_run`: source and run identity, route classification, extraction status, and derived aggregation keys such as `combo_key`.
- `catalyst_system`: catalyst composition, support, promoter, precursor, preparation, acidification, complexation, calcination, reduction, activation, and catalyst properties.
- `reactor_process_gas`: reactor and scale, process stages, gas program, actual run temperature, reported suitable or optimal temperature, failed temperature, and temperature effects.
- `yield_quality`: yield definition, conversion, CNT type, morphology and quality, including whether SWCNT is reported or supported by TEM/HRTEM, Raman RBM, diameter, or wall-count evidence.
- `cost_scale_review`: reported cost and scale facts, suitable-condition synthesis, reproduction value, industrial assessment, missing critical information, and recommended next action.

Use `combo_key` to support aggregation across catalyst, carbon source, reactor, and CNT type. Treat it as a derived analysis key, retain its components separately, and do not present it as an experimental fact.

Keep source-reported optimum conditions separate from reviewer-selected conditions. Keep reported facts separate from inferred, calculated, and review-assessment values. These distinctions are more important than forcing every record into identical completeness.

---

## Industrial R&D Perspective

The project should think from the perspective of an industrial CNT R&D team.

A technically interesting result is not automatically industrially valuable. Industrial relevance depends on factors such as:

- Catalyst cost
- Catalyst lifetime
- Availability of raw materials
- Methane or natural gas utilization
- Hydrogen or nitrogen consumption
- Energy demand
- Process complexity
- Purification burden
- Product consistency
- Continuous operation potential
- Scale-up feasibility
- Safety and environmental issues
- Product quality for downstream applications

CNT-PatSight should help distinguish between academic novelty and practical industrial usefulness.

---

## Relationship to Internal Experimental Data

The project may later integrate company or laboratory experimental data.

Public literature and patent data can be used to build the initial structure and external reference base. Internal experimental data may later be added for comparison, validation, model building, and process optimization.

Internal data should be treated as sensitive by default. The project should be designed so that public data and confidential internal data can be separated when necessary.

---

## Expected Project Character

CNT-PatSight should remain flexible and configurable.

The current focus on methane or natural gas CVD synthesis of MWCNT is a working priority, not a fixed limitation. Future work may expand to other CNT synthesis routes, different carbon sources, other CNT product types, catalyst cost modeling, battery-grade product evaluation, or automated extraction pipelines.

The project should favor clear data structure, traceability, and long-term maintainability over quick but fragile one-off scripts.

---

## Success Definition

CNT-PatSight is successful if it helps transform CNT literature, patents, and experiments into a structured R&D asset.

A useful outcome is not merely a collection of PDFs or summaries. A useful outcome is a database and analysis workflow that helps researchers answer:

- What has already been tried?
- Under what conditions?
- With what catalyst?
- What product was obtained?
- How good was the result?
- How reliable is the evidence?
- Is it worth reproducing or modifying?
- What should the R&D team try next?

The project should ultimately support better experimental decisions, faster literature digestion, and more systematic CNT process optimization.

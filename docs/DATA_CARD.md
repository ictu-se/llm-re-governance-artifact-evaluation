# Data Card: LLM Requirements-Governance Artifact Benchmark

## Purpose

This dataset supports an empirical benchmark for evaluating whether locally executed LLMs can generate structured requirements-engineering governance artifacts for LLM-based software systems.

The intended use is research evaluation and replication. The dataset should not be interpreted as a complete industrial requirements corpus or as validated operational governance advice.

## Dataset Scope

- Task count: 240
- System types: 20
- Tasks per system type: 12
- Required output fields: 6
- Evaluation dimensions: correctness, completeness, traceability usefulness, governance adequacy, hallucination/risk

Each task contains:

- `task_id`
- `system_type`
- `stakeholder_intent`
- `context`
- `available_evidence`
- `disallowed_behavior`
- `gold_keywords`
- `risk_keywords`
- `trace_keywords`

## Task Design

The benchmark focuses on LLM-based software systems such as academic advising assistants, HR policy assistants, clinical information assistants, legal information assistants, financial education assistants, DevOps incident assistants, privacy compliance assistants, and IT ticket triage assistants.

Tasks are scenario-based and intentionally abstract. They are designed to test whether a model can produce a reviewable governance artifact from stakeholder intent and bounded context, not whether it can solve a full industrial requirements-engineering project.

## Evaluation Artifacts

The repository stores:

- benchmark tasks in `data/tasks/`
- saved model predictions in `results/predictions/`
- cleaned final predictions and summaries in `results/final/`
- schema/no-schema ablation outputs in `results/ablation/`
- scoring and agreement scripts in `scripts/`
- protocol and rubric documentation in `docs/`

## Known Limitations

- The benchmark is synthetic/scenario-based rather than collected from deployed industrial projects.
- The rubric scores are automated proxy scores unless replaced by independent expert ratings.
- Keyword recall is a reproducible proxy and does not capture all valid synonyms or semantic alternatives.
- Local LLM outputs may vary with model revision, quantization, Ollama version, hardware, and runtime load.
- The task set covers 20 system types but does not cover all possible regulated or safety-critical domains.

## Recommended Reporting

When using this dataset, report:

- model tags and runtime environment;
- whether saved predictions or regenerated predictions were used;
- cleaning and retry policy;
- parse success and slot coverage;
- rubric totals and dimension-level scores;
- whether agreement values come from automated proxy raters or independent human raters.

Do not report synthetic placeholder ratings as human evaluation.

## Ethics and Safety

Generated requirements-governance artifacts may include unsupported claims, weak controls, or invented evidence sources. Outputs should be treated as drafts for expert review, not as approved requirements or governance policies.

The benchmark contains scenario text and does not contain real personal data. If adapted to private organizational settings, users should review task contexts and outputs for confidential information before sharing artifacts.

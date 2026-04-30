# Rubric for LLM-Based Requirements Engineering Artifacts

This rubric scores each generated artifact on five 0-2 dimensions. The unit of analysis is one model output for one task.

## R1. Correctness

- 0: The artifact is not parseable, does not answer the task, or contradicts the task context.
- 1: The artifact is partly aligned with the system type and stakeholder intent but misses key constraints or includes vague requirements.
- 2: The artifact is aligned with the system type, stakeholder intent, allowed evidence, and disallowed behavior.

## R2. Completeness

- 0: Fewer than four required slots are present and non-empty.
- 1: Four or five required slots are present and non-empty, or all slots exist but some are superficial.
- 2: All six required slots are present and contain task-relevant content.

Required slots: `capability_requirement`, `source_constraints`, `failure_behavior`, `validation_scenarios`, `traceability_links`, `runtime_signals`.

## R3. Traceability Usefulness

- 0: Traceability is absent or generic.
- 1: Traceability mentions at least one relevant source, artifact, validation scenario, or model/version link.
- 2: Traceability connects requirements to evidence, validation, runtime monitoring, and review/change artifacts.

## R4. Governance Adequacy

- 0: The artifact omits safety, refusal, escalation, privacy, uncertainty, or monitoring controls.
- 1: The artifact includes some governance controls but misses important task-specific risk behavior.
- 2: The artifact includes task-specific controls for allowed evidence, refusal/escalation, privacy/safety, validation, and runtime monitoring.

## R5. Hallucination and Risk

- 0: The artifact invents unsupported system behavior, relies on disallowed evidence, or encourages a disallowed behavior.
- 1: The artifact is mostly grounded but includes broad claims, weak source boundaries, or ambiguous risk handling.
- 2: The artifact stays within the supplied context, cites only allowed evidence/source types, and explicitly handles disallowed behavior.

## Agreement Protocol

For Q1-grade reporting, two human reviewers should independently score a stratified sample or the full set. The accompanying scripts also produce two deterministic automated proxy raters for auditability and pipeline testing; these proxy agreement scores must not be described as human inter-rater reliability.

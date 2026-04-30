# Human Evaluation Protocol

This protocol is intended for replacing the synthetic placeholder ratings with independent expert ratings.

## Purpose

The human evaluation estimates whether generated requirements-governance artifacts are acceptable as reviewable first drafts. It does not certify that the artifacts are ready for deployment without requirements-engineering review.

## Reviewers

- Use three independent reviewers when possible.
- Recommended profiles: requirements engineering, software engineering governance, AI assurance, safety/security/privacy, or domain-specific compliance.
- Reviewers should work independently before any adjudication.

## Review Material

Each reviewer receives a CSV template containing:

- model output,
- task id,
- system type,
- stakeholder intent,
- context,
- available evidence,
- disallowed behavior.

If practical, remove or mask the `model` column before review to reduce model-identity bias. Keep an unblinded mapping separately for analysis.

## Rating Scale

Each artifact is scored on five 0-2 dimensions:

- `correctness_0_2`
- `completeness_0_2`
- `traceability_usefulness_0_2`
- `governance_adequacy_0_2`
- `hallucination_risk_0_2`

Use the rubric in `docs/RUBRIC_Q1.md`.

## Sampling

The current template uses 336 artifacts:

- 7 selected models,
- 48 artifacts per model,
- artifacts drawn from the 240-task benchmark.

This sample is large enough to report per-dimension agreement and to compare broad model behavior. If reviewer time is limited, a smaller stratified sample can be used, but the manuscript should report the exact sampling rule.

## Agreement Reporting

For three reviewers, report:

- Fleiss' kappa for categorical agreement,
- ordinal Krippendorff's alpha for the 0-2 ordered scale,
- optional pairwise Cohen's kappa for reviewer pairs.

Agreement should be reported per dimension. Do not collapse all dimensions before checking agreement.

The main analysis script also reports model-level human score summaries and the correlation between automated rubric scores and mean human scores:

```powershell
python scripts\human_eval_analysis.py --ratings results\human_eval\real_human_ratings_3reviewers.csv --rubric-glob "results/final/*_rubric.csv" --outdir results\human_eval\real_analysis
```

The key outputs are:

- `human_agreement.csv`
- `human_item_mean_scores.csv`
- `human_model_score_summary.csv`
- `human_automated_correlation.csv`

## Adjudication

After independent scoring:

1. Keep raw reviewer scores unchanged.
2. Compute agreement on the raw scores.
3. Resolve disagreements only after agreement has been computed.
4. Store adjudicated scores in a separate file.

## Manuscript Use

In the manuscript, clearly distinguish:

- automated proxy rubric scores,
- raw independent human ratings,
- inter-rater agreement,
- adjudicated human scores, if used.

Synthetic placeholder files must not be reported as human evaluation evidence.

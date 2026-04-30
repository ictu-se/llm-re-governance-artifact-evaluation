# Q1 Experimental Results Package

Generated on 2026-04-30.

## Final Included Data

The final v240 analysis currently includes 15 completed model runs, each with 240 tasks:

- `codegemma:7b`
- `granite-code:3b`
- `granite-code:8b`
- `llama3.2:3b`
- `qwen2.5:1.5b`
- `qwen2.5:3b`
- `qwen2.5:7b`
- `qwen2.5-coder:1.5b`
- `qwen2.5-coder:3b`
- `qwen2.5-coder:7b`
- `qwen2.5-coder:14b`
- `qwen3:8b`
- `qwen3:14b`
- `starcoder2:3b`
- `starcoder2:7b`

`qwen3:4b` is excluded from the final table until it reaches 240/240 tasks.

## Cleaning Decisions

Retry outputs were merged without overwriting successful original rows:

- `starcoder2:3b`: 42 timeout rows were replaced by successful retry rows; 31 timeout rows remain.
- `starcoder2:7b`: 5 timeout rows were replaced by successful retry rows; 2 timeout rows remain.

Manifest: `runs/final/final_prediction_manifest.csv`.

## Rubric

Rubric dimensions are defined in `RUBRIC_Q1.md`:

- correctness
- completeness
- traceability usefulness
- governance adequacy
- hallucination/risk

Each dimension is scored from 0 to 2. Total rubric score ranges from 0 to 10.

## Agreement

Agreement was computed between two deterministic automated proxy raters:

- Cohen's kappa by dimension: `runs/final/rubric_agreement.csv`
- Krippendorff's ordinal alpha by dimension and overall: `runs/final/rubric_agreement.csv`

Important reporting note: these are automated proxy agreement values for pipeline validation. They should not be reported as human inter-rater reliability unless replaced by independent human annotations.

## Final Tables

- Automatic metrics summary: `runs/final/final_automatic_metrics_summary.csv`
- Model-level rubric summary with bootstrap 95% CIs: `runs/final/final_model_rubric_summary.csv`
- Family-level rubric summary with bootstrap 95% CIs: `runs/final/final_family_rubric_summary.csv`
- Pairwise family statistical comparisons: `runs/final/statistical_comparisons_family.csv`

## Current Rubric Ranking by Mean Total Score

Top completed models:

1. `qwen2.5:3b`: 7.1146
2. `qwen2.5-coder:7b`: 6.9000
3. `qwen3:14b`: 6.8875
4. `llama3.2:3b`: 6.8292
5. `qwen2.5:1.5b`: 6.7812

Lowest completed family:

- `starcoder2`: 0.8104 family mean, affected by parse failures and remaining timeout rows.

## Ablation

A prompt-schema ablation has been configured as a 60-task balanced sample:

- 20 system types
- 3 tasks per system type
- 3 representative models
- conditions: `schema` vs `no_schema`

Runner: `run_ablation_schema.ps1`.

Outputs:

- predictions: `runs/ablation/*_predictions_v48.jsonl`
- rubric scores: `runs/ablation/*_rubric_v48.csv`
- summary after completion: `runs/ablation/ablation_schema_summary_v48.csv`

The ablation job is currently running in the background.

## Remaining Work Before Manuscript Submission

For a Q1 submission, replace or supplement automated proxy rubric scores with independent human review:

- Use the same five rubric dimensions.
- Have two reviewers score at least a stratified sample, preferably all model outputs used in the key claims.
- Recompute Cohen's kappa or Krippendorff's alpha on human labels.
- Report automated scores as secondary reproducibility metrics, not as human quality judgments.

## Synthetic Placeholder Human Evaluation

A synthetic 12-reviewer placeholder file was generated only for pipeline testing and table drafting:

- ratings: `runs/final/synthetic_12_expert_human_eval_PLACEHOLDER.csv`
- multi-rater agreement: `runs/final/synthetic_12_expert_agreement_PLACEHOLDER.csv`
- reviewer 1 vs reviewer 2 agreement: `runs/final/synthetic_reviewer01_02_agreement_PLACEHOLDER.csv`

Every row is marked with `synthetic_data=1` and `replacement_required_before_submission=1`.

Do not report this as expert evaluation. Replace it with independent human ratings before submission.

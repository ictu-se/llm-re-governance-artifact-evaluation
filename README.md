# Local LLMs for Requirements-Governance Artifact Evaluation

This repository contains the replication package for the paper draft:

**Evaluating Local LLMs for Requirements-Engineering Governance Artifacts in LLM-Based Software Systems**

The study evaluates whether locally executed LLMs can generate structured requirements-engineering governance artifacts for LLM-based software systems. The benchmark contains 240 tasks across 20 system types. The final analysis includes 15 completed local model runs, automatic structure metrics, a five-dimension rubric, family-level statistical comparisons, and a schema-prompt ablation.

## Repository Layout

```text
.
|-- config/                         # Model list and experiment configuration
|-- data/tasks/                     # Benchmark task files
|-- docs/                           # Protocol, rubric, and result notes
|-- results/
|   |-- predictions/                # Saved model outputs used by the paper
|   |-- final/                      # Final metrics, rubric summaries, manifest
|   `-- ablation/                   # Schema/no-schema ablation outputs
|-- scripts/                        # Reusable experiment and analysis scripts
|-- run_full_experiment.ps1         # Re-run local model generation with Ollama
|-- run_q1_pipeline.ps1             # Recompute final metrics and summaries
`-- run_ablation_schema.ps1         # Re-run schema-prompt ablation
```

## Requirements

- Python 3.10 or newer.
- Ollama running locally at `http://localhost:11434` for model generation.
- The model tags listed in `config/models.json` pulled locally before full re-execution.
- No third-party Python package is required; the scripts use the Python standard library.

Example Ollama setup:

```powershell
ollama serve
ollama pull qwen2.5:3b
ollama pull llama3.2:3b
```

## Quick Verification Without Re-running Models

The repository includes the saved prediction files used for the current paper draft. To recompute metrics, rubric scores, final summaries, and the final manifest:

```powershell
.\run_q1_pipeline.ps1
```

Expected high-level outputs:

- `results/final/final_prediction_manifest.csv`
- `results/final/final_automatic_metrics_summary.csv`
- `results/final/final_model_rubric_summary.csv`
- `results/final/final_family_rubric_summary.csv`
- `results/final/statistical_comparisons_family.csv`
- one `*_metrics.csv` and one `*_rubric.csv` file per included model run

## Re-running the Main Experiment

To regenerate predictions from local Ollama models:

```powershell
.\run_full_experiment.ps1
.\run_q1_pipeline.ps1
```

The full experiment can take a long time because it runs 240 tasks for each model. The generation script is resumable: if an output JSONL already contains completed task IDs, it skips those rows and appends only missing tasks.

The final paper excludes `qwen3:4b` from the main final table because that run was incomplete during drafting. The full experiment script follows the included final-analysis model list.

## Re-running the Prompt-Schema Ablation

To recompute ablation scores from the saved ablation predictions:

```powershell
.\run_ablation_analysis.ps1
```

To regenerate ablation predictions from local Ollama models:

```powershell
.\run_ablation_schema.ps1
```

This creates or refreshes the balanced 60-task ablation set and evaluates three representative models under schema and no-schema prompting.

## Evaluation Design

Each generated artifact is expected to contain six governance-oriented fields:

- `capability_requirement`
- `source_constraints`
- `failure_behavior`
- `validation_scenarios`
- `traceability_links`
- `runtime_signals`

The rubric has five 0--2 dimensions:

- correctness
- completeness
- traceability usefulness
- governance adequacy
- hallucination/risk

See `docs/RUBRIC_Q1.md` for scoring rules.

## Human Evaluation

The repository includes scripts for preparing human-review templates and computing agreement statistics, including Cohen's kappa and Krippendorff's alpha. Synthetic placeholder ratings are intentionally not included in this repository and must not be reported as human evaluation. Replace the template with real independent expert ratings before making human-evaluation claims.

## Reproducibility Notes

Local LLM output can vary with hardware, Ollama version, quantization, model revision, and runtime load. The saved prediction files provide traceability for the paper draft, while the scripts provide a repeatable route for independent re-execution.

## Citation

If this package is used, cite the corresponding paper once bibliographic information is finalized. A placeholder `CITATION.cff` is included for repository metadata.

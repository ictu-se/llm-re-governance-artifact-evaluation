# Artifact License and Distribution Notes

## Repository Contents

This replication package contains benchmark task definitions, saved model outputs, analysis scripts, rubric documentation, and final summary tables for the paper:

> Generating Requirements-Engineering Governance Artifacts for LLM-Based Software Systems: A Benchmark Study of Local LLMs

## Third-Party Data

The benchmark tasks are scenario-based and do not redistribute third-party source-code repositories. Model outputs are generated from the benchmark task contexts included in this repository.

## Model Outputs

Saved predictions are included to support metric recomputation without requiring readers to rerun local LLM inference. These outputs should be treated as research artifacts, not as validated requirements or governance policies.

## Local Re-execution

Rerunning the full experiment requires local Ollama model tags listed in `config/models.json`. Model licenses and acceptable-use terms are governed by the corresponding model providers and the local Ollama distribution.

## Human Evaluation Placeholders

Synthetic placeholder ratings are not part of the empirical evidence and must not be reported as human evaluation. If independent expert ratings are added later, store raw ratings separately and document reviewer qualifications, blinding policy, sampling, and adjudication.

## Citation

If this package is used, cite the corresponding paper once bibliographic details are finalized.

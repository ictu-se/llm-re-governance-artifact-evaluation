$ErrorActionPreference = "Stop"

$tasks = "data/tasks/llm_re_tasks_v240.jsonl"

New-Item -ItemType Directory -Force results/final | Out-Null
New-Item -ItemType Directory -Force results/baseline | Out-Null

python scripts/merge_clean_outputs.py --base results/predictions/starcoder2_3b_predictions_v240.jsonl --retry results/predictions/starcoder2_3b_predictions_v240_retry_timeouts.jsonl --out results/final/starcoder2_3b_predictions_v240_clean.jsonl
python scripts/merge_clean_outputs.py --base results/predictions/starcoder2_7b_predictions_v240.jsonl --retry results/predictions/starcoder2_7b_predictions_v240_retry_timeouts.jsonl --out results/final/starcoder2_7b_predictions_v240_clean.jsonl

$predictionFiles = @(
  "results/predictions/codegemma_7b_predictions_v240.jsonl",
  "results/predictions/granite-code_3b_predictions_v240.jsonl",
  "results/predictions/granite-code_8b_predictions_v240_dedup.jsonl",
  "results/predictions/llama3.2_3b_predictions_v240.jsonl",
  "results/predictions/qwen2.5_1.5b_predictions_v240.jsonl",
  "results/predictions/qwen2.5_3b_predictions_v240.jsonl",
  "results/predictions/qwen2.5_7b_predictions_v240.jsonl",
  "results/predictions/qwen2.5-coder_1.5b_predictions_v240.jsonl",
  "results/predictions/qwen2.5-coder_3b_predictions_v240.jsonl",
  "results/predictions/qwen2.5-coder_7b_predictions_v240.jsonl",
  "results/predictions/qwen2.5-coder_14b_predictions_v240.jsonl",
  "results/predictions/qwen3_8b_predictions_v240.jsonl",
  "results/predictions/qwen3_14b_predictions_v240_dedup.jsonl",
  "results/final/starcoder2_3b_predictions_v240_clean.jsonl",
  "results/final/starcoder2_7b_predictions_v240_clean.jsonl"
)

foreach ($pred in $predictionFiles) {
  $name = [System.IO.Path]::GetFileNameWithoutExtension($pred)
  python scripts/evaluate_re_outputs.py --tasks $tasks --predictions $pred --out "results/final/$($name)_metrics.csv"
  python scripts/rubric_score_outputs.py --tasks $tasks --predictions $pred --out "results/final/$($name)_rubric.csv"
}

python scripts/summarize_any_metrics.py --glob "results/final/*_metrics.csv" --out "results/final/final_automatic_metrics_summary.csv"
python scripts/agreement_stats_final.py --rubric-glob "results/final/*_rubric.csv" --outdir "results/final"
python scripts/paired_model_comparisons.py --rubric-glob "results/final/*_rubric.csv" --models "qwen2.5:3b" "qwen2.5-coder:7b" "qwen3:14b" "llama3.2:3b" "qwen3:8b" "codegemma:7b" --out "results/final/paired_model_comparisons_top_models.csv"
python scripts/final_manifest.py --tasks $tasks --out "results/final/final_prediction_manifest.csv" $predictionFiles
python scripts/runtime_and_slice_analysis.py --tasks $tasks --manifest "results/final/final_prediction_manifest.csv" --rubric-glob "results/final/*_rubric.csv" --outdir "results/final"
python scripts/final_slice_summaries.py --tasks $tasks --rubric-glob "results/final/*_rubric.csv" --outdir "results/final"
python scripts/scenario_slice_analysis.py --tasks $tasks --rubric-glob "results/final/*_rubric.csv" --out "results/final/scenario_slice_summary_non_starcoder.csv"
python scripts/error_taxonomy_analysis.py --rubric-glob "results/final/*_rubric.csv" --out-summary "results/final/error_taxonomy_summary.csv" --out-by-model "results/final/error_taxonomy_by_model.csv"

python scripts/make_template_baseline.py --mode generic --tasks $tasks --out "results/baseline/template_baseline_generic_predictions_v240.jsonl"
python scripts/make_template_baseline.py --mode grounded --tasks $tasks --out "results/baseline/template_baseline_grounded_predictions_v240.jsonl"
python scripts/evaluate_re_outputs.py --tasks $tasks --predictions "results/baseline/template_baseline_generic_predictions_v240.jsonl" --out "results/baseline/template_baseline_generic_metrics.csv"
python scripts/evaluate_re_outputs.py --tasks $tasks --predictions "results/baseline/template_baseline_grounded_predictions_v240.jsonl" --out "results/baseline/template_baseline_grounded_metrics.csv"
python scripts/rubric_score_outputs.py --tasks $tasks --predictions "results/baseline/template_baseline_generic_predictions_v240.jsonl" --out "results/baseline/template_baseline_generic_rubric.csv"
python scripts/rubric_score_outputs.py --tasks $tasks --predictions "results/baseline/template_baseline_grounded_predictions_v240.jsonl" --out "results/baseline/template_baseline_grounded_rubric.csv"
python scripts/summarize_any_metrics.py --glob "results/baseline/template_baseline_*_metrics.csv" --out "results/baseline/template_baseline_metrics_summary.csv"

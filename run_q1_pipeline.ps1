$ErrorActionPreference = "Stop"

$tasks = "data/tasks/llm_re_tasks_v240.jsonl"

New-Item -ItemType Directory -Force results/final | Out-Null

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
python scripts/final_manifest.py --tasks $tasks --out "results/final/final_prediction_manifest.csv" $predictionFiles

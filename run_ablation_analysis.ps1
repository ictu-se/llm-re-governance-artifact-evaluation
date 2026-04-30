$ErrorActionPreference = "Stop"

$tasks = "data/tasks/llm_re_tasks_v240_ablation48.jsonl"
New-Item -ItemType Directory -Force results/ablation | Out-Null

$files = @(
  "llama3.2_3b_no_schema",
  "llama3.2_3b_schema",
  "qwen2.5_3b_no_schema",
  "qwen2.5_3b_schema",
  "qwen2.5-coder_3b_no_schema",
  "qwen2.5-coder_3b_schema"
)

foreach ($name in $files) {
  python scripts/rubric_score_outputs.py --tasks $tasks --predictions "results/ablation/$($name)_predictions_v48.jsonl" --out "results/ablation/$($name)_rubric_v48.csv"
}

python scripts/ablation_summary.py --rubric-glob "results/ablation/*_rubric_v48.csv" --out "results/ablation/ablation_schema_summary_v48.csv"

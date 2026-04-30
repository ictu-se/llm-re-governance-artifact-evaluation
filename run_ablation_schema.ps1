$ErrorActionPreference = "Stop"

$tasks = "data/tasks/llm_re_tasks_v240_ablation48.jsonl"
New-Item -ItemType Directory -Force results/ablation | Out-Null
python scripts/make_ablation_tasks.py --tasks data/tasks/llm_re_tasks_v240.jsonl --out $tasks --per-system 3

$models = @(
  @{ tag = "llama3.2:3b"; file = "llama3.2_3b" },
  @{ tag = "qwen2.5:3b"; file = "qwen2.5_3b" },
  @{ tag = "qwen2.5-coder:3b"; file = "qwen2.5-coder_3b" }
)

foreach ($m in $models) {
  python scripts/run_model_ablation.py --tasks $tasks --model $m.tag --mode no_schema --out "results/ablation/$($m.file)_no_schema_predictions_v48.jsonl"
  python scripts/run_model_ablation.py --tasks $tasks --model $m.tag --mode schema --out "results/ablation/$($m.file)_schema_predictions_v48.jsonl"
  python scripts/rubric_score_outputs.py --tasks $tasks --predictions "results/ablation/$($m.file)_no_schema_predictions_v48.jsonl" --out "results/ablation/$($m.file)_no_schema_rubric_v48.csv"
  python scripts/rubric_score_outputs.py --tasks $tasks --predictions "results/ablation/$($m.file)_schema_predictions_v48.jsonl" --out "results/ablation/$($m.file)_schema_rubric_v48.csv"
}

python scripts/ablation_summary.py --rubric-glob "results/ablation/*_rubric_v48.csv" --out "results/ablation/ablation_schema_summary_v48.csv"

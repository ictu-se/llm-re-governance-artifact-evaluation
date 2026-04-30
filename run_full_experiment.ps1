$ErrorActionPreference = "Stop"

$config = Get-Content "config/models.json" -Raw | ConvertFrom-Json
$tasks = $config.task_file
New-Item -ItemType Directory -Force $config.prediction_dir | Out-Null

foreach ($m in $config.models) {
  $out = Join-Path $config.prediction_dir $m.file
  Write-Host "Running $($m.tag) -> $out"
  python scripts/run_model_resumable.py --tasks $tasks --model $m.tag --out $out
}

Write-Host "Generation complete. Run .\run_q1_pipeline.ps1 to recompute final metrics."

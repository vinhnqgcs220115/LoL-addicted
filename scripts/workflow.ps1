param(
    [Parameter(Position = 0)]
    [ValidateSet("collect", "dashboard", "deploy-db", "features", "help", "models", "process", "rebuild", "refresh", "smoke", "sync", "test")]
    [string]$Command = "help"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $repoRoot ".venv\Scripts\python.exe"
$requirementsPath = Join-Path $repoRoot "requirements-dev.txt"
$databasePath = Join-Path $repoRoot "data\lol.duckdb"

function Invoke-Checked {
    param([scriptblock]$Command)

    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code $LASTEXITCODE."
    }
}

function Show-Usage {
    Write-Host "Usage: .\scripts\workflow.ps1 <command>"
    Write-Host ""
    Write-Host "Commands:"
    Write-Host "  sync      Install requirements into .venv with uv"
    Write-Host "  collect   Download configured Riot match data"
    Write-Host "  dashboard  Start the Streamlit dashboard locally"
    Write-Host "  process   Load raw JSON into DuckDB"
    Write-Host "  features  Rebuild the feature matrix"
    Write-Host "  models    Train clustering and persist labels"
    Write-Host "  refresh   Run collect, process, features, and models"
    Write-Host "  rebuild   Recreate DuckDB from raw data, then rebuild features and models"
    Write-Host "  deploy-db  Build and sanitise the deployment database"
    Write-Host "  test      Run the pytest suite"
    Write-Host "  smoke     Run a five-match live pipeline check"
    Write-Host "  help      Show this message"
}

function Invoke-Smoke {
    $script = @'
import duckdb

from src import collector, features, models, processor

collector.run_collection(count=5)
processor.run_pipeline()
features.run_features()
models.run_models()

with duckdb.connect(str(processor.DB_PATH), read_only=True) as conn:
    counts = {
        "matches": conn.execute("SELECT COUNT(*) FROM matches").fetchone()[0],
        "timelines": conn.execute("SELECT COUNT(*) FROM match_timelines").fetchone()[0],
        "features": conn.execute("SELECT COUNT(*) FROM feature_matrix").fetchone()[0],
        "labels": conn.execute("SELECT COUNT(*) FROM cluster_labels").fetchone()[0],
    }

print(counts)
'@

    $script | & $pythonPath -
}

if ($Command -notin @("sync", "help") -and -not (Test-Path $pythonPath)) {
    throw "Expected virtual environment Python at $pythonPath"
}

Push-Location $repoRoot
try {
    switch ($Command) {
        "sync" {
            if (-not (Test-Path $pythonPath)) {
                Invoke-Checked { uv venv --python 3.11 .venv }
            }
            Invoke-Checked { uv pip install --python $pythonPath -r $requirementsPath }
        }
        "collect" {
            Invoke-Checked { & $pythonPath -m src.collector }
        }
        "process" {
            Invoke-Checked { & $pythonPath -m src.processor }
        }
        "features" {
            Invoke-Checked { & $pythonPath -m src.features }
        }
        "models" {
            Invoke-Checked { & $pythonPath -m src.models }
        }
        "refresh" {
            Invoke-Checked { & $pythonPath -m src.collector }
            Invoke-Checked { & $pythonPath -m src.processor }
            Invoke-Checked { & $pythonPath -m src.features }
            Invoke-Checked { & $pythonPath -m src.models }
        }
        "rebuild" {
            if (Test-Path $databasePath) {
                Remove-Item -LiteralPath $databasePath
            }
            Invoke-Checked { & $pythonPath -m src.processor }
            Invoke-Checked { & $pythonPath -m src.features }
            Invoke-Checked { & $pythonPath -m src.models }
        }
        "deploy-db" {
            Invoke-Checked { & $pythonPath (Join-Path $repoRoot "scripts\build_deploy_db.py") }
        }
        "dashboard" {
            Invoke-Checked { & $pythonPath -m streamlit run dashboard\app.py }
        }
        "test" {
            Invoke-Checked { & $pythonPath -m pytest tests -q }
        }
        "smoke" {
            Invoke-Checked { Invoke-Smoke }
        }
        default {
            Show-Usage
        }
    }
}
finally {
    Pop-Location
}

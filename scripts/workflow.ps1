param(
    [Parameter(Position = 0)]
    [ValidateSet("sync", "collect", "process", "features", "models", "refresh", "rebuild", "deploy-db", "test", "smoke", "help")]
    [string]$Command = "help"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $repoRoot ".venv\Scripts\python.exe"
$requirementsPath = Join-Path $repoRoot "requirements.txt"
$databasePath = Join-Path $repoRoot "data\lol.duckdb"
$deployDatabasePath = Join-Path $repoRoot "data\lol_deploy.duckdb"

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
    Write-Host "  process   Load raw JSON into DuckDB"
    Write-Host "  features  Rebuild the feature matrix"
    Write-Host "  models    Train clustering and persist labels"
    Write-Host "  refresh   Run collect, process, features, and models"
    Write-Host "  rebuild   Recreate DuckDB from raw data, then rebuild features and models"
    Write-Host "  deploy-db Copy the verified local DuckDB file for Streamlit deployment"
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

if ($Command -notin @("sync", "deploy-db", "help") -and -not (Test-Path $pythonPath)) {
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
            if (-not (Test-Path $databasePath)) {
                throw "Expected local database at $databasePath"
            }
            Copy-Item -LiteralPath $databasePath -Destination $deployDatabasePath -Force
            Write-Host "Created $deployDatabasePath"
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

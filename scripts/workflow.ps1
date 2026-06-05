param(
    [Parameter(Position = 0)]
    [ValidateSet("sync", "collect", "process", "refresh", "test", "smoke", "status", "help")]
    [string]$Command = "help"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$expectedVenvPath = Join-Path $repoRoot ".venv"
$activateScript = Join-Path $repoRoot ".venv\Scripts\Activate.ps1"
$requirementsPath = Join-Path $repoRoot "requirements.txt"

function Invoke-Step {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Label,
        [Parameter(Mandatory = $true)]
        [scriptblock]$Action
    )

    Write-Host "==> $Label"
    & $Action
}

function Show-Usage {
    Write-Host "Usage: .\scripts\workflow.ps1 <command>"
    Write-Host ""
    Write-Host "Commands:"
    Write-Host "  sync     Activate .venv and install dependencies with uv pip install -r requirements.txt"
    Write-Host "  collect  Run the Riot API collection pipeline"
    Write-Host "  process  Load raw JSON into DuckDB"
    Write-Host "  refresh  Run collect, then process"
    Write-Host "  test     Run pytest"
    Write-Host "  smoke    Run a small live collection and processing verification"
    Write-Host "  status   Show whether the repo virtual environment is active"
    Write-Host "  help     Show this message"
}

function Invoke-Smoke {
    $script = @'
from src.collector import run_collection
from src.processor import run_pipeline
import duckdb

run_collection(count=5)
run_pipeline()

conn = duckdb.connect('data/lol.duckdb')
try:
    matches_count = conn.execute('SELECT COUNT(*) FROM matches').fetchone()[0]
    timelines_count = conn.execute('SELECT COUNT(*) FROM match_timelines').fetchone()[0]
finally:
    conn.close()

print(f'matches={matches_count}')
print(f'timelines={timelines_count}')
'@

    $script | python -
}

function Get-NormalizedPath {
    param(
        [string]$PathValue
    )

    if (-not $PathValue) {
        return $null
    }

    return [System.IO.Path]::GetFullPath($PathValue).TrimEnd("\\")
}

function Test-RepoVenvActive {
    $activeVenvPath = Get-NormalizedPath $env:VIRTUAL_ENV
    $normalizedExpectedPath = Get-NormalizedPath $expectedVenvPath

    return $activeVenvPath -and $activeVenvPath -eq $normalizedExpectedPath
}

function Show-Status {
    $activeVenvPath = Get-NormalizedPath $env:VIRTUAL_ENV
    $normalizedExpectedPath = Get-NormalizedPath $expectedVenvPath
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue

    Write-Host "Repo venv active: $(Test-RepoVenvActive)"
    Write-Host "Expected VIRTUAL_ENV: $normalizedExpectedPath"
    Write-Host "Current VIRTUAL_ENV : $activeVenvPath"
    if ($pythonCommand) {
        Write-Host "Python executable   : $($pythonCommand.Source)"
    }
}

function Ensure-RepoVenvActive {
    if (Test-RepoVenvActive) {
        return
    }

    if ($env:VIRTUAL_ENV) {
        Write-Host "Switching virtual environment from $env:VIRTUAL_ENV to $expectedVenvPath"
    }
    else {
        Write-Host "Activating repo virtual environment at $expectedVenvPath"
    }

    & $activateScript
}

if (-not (Test-Path $activateScript)) {
    throw "Expected virtual environment activation script at $activateScript"
}

Push-Location $repoRoot
try {
    Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned

    switch ($Command) {
        "sync" {
            Ensure-RepoVenvActive
            Invoke-Step "Installing dependencies with uv" { uv pip install -r $requirementsPath }
        }
        "collect" {
            Ensure-RepoVenvActive
            Invoke-Step "Running collector" { python -m src.collector }
        }
        "process" {
            Ensure-RepoVenvActive
            Invoke-Step "Running processor" { python -m src.processor }
        }
        "refresh" {
            Ensure-RepoVenvActive
            Invoke-Step "Running collector" { python -m src.collector }
            Invoke-Step "Running processor" { python -m src.processor }
        }
        "test" {
            Ensure-RepoVenvActive
            Invoke-Step "Running pytest" { python -m pytest tests -q }
        }
        "smoke" {
            Ensure-RepoVenvActive
            Invoke-Step "Running live smoke verification" { Invoke-Smoke }
        }
        "status" {
            Show-Status
        }
        default {
            Show-Usage
        }
    }
}
finally {
    Pop-Location
}
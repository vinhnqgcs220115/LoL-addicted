# LoL Mid-Lane Analytics

> **L2 Reference** · front door for humans · owner: Claude · update: when setup or features change

A personal League of Legends review tool for one mid laner. It collects my ranked Solo/Duo games from the Riot API, stores them in DuckDB and shows them in a Streamlit dashboard. The aim is to understand my own play: first season stats, then what happened in each game's lane phase and which decisions I made.

**Live app:** https://myishaa.streamlit.app/

## Status

Being rebuilt. The live app shows the previous dashboard until milestone M1 ships. Progress is in [`ROADMAP.md`](ROADMAP.md).

## What it will do

- **Season overview:** Riot ID, rank, games and win rate for the current season.
- **Champion pool:** every champion played in mid this season, with matchups and win rate per opponent.
- **Match history:** every Solo/Duo game of the season, with a button to collect new games.
- **Per-game review:** the lane phase (0–14 min) against the lane opponent, covering CS, gold, XP, deaths, recalls, plates and roams.

## How it works

Riot API → raw JSON (never edited) → DuckDB → analytics in `src/` → Streamlit dashboard. The live app reads a DuckDB snapshot committed to the repo.

## Set up on a new machine

1. Install Python 3.11 and [uv](https://docs.astral.sh/uv/), then clone this repo.
2. Copy `.env.example` to `.env`. Fill in `RIOT_API_KEY` (from [developer.riotgames.com](https://developer.riotgames.com)) and either `GAME_NAME` + `TAG` or `PUUID`.
3. From the repo root, in PowerShell:

```powershell
.\scripts\workflow.ps1 sync       # create .venv and install dependencies
.\scripts\workflow.ps1 refresh    # collect new games and process them
.\scripts\workflow.ps1 dashboard  # open the app locally
```

The raw match files (`data/raw/`) are not in git. Back them up separately, because older games may no longer be downloadable.

## Docs

- [`ROADMAP.md`](ROADMAP.md): what's being built, and what's next.
- [`.claude/CONTEXT.md`](.claude/CONTEXT.md): what each work session did.
- [`.claude/CLAUDE.md`](.claude/CLAUDE.md): the full scope and rules, written for the coding agent.

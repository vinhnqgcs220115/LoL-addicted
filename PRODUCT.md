# Product Definition

Source of truth for **what this project is for** and **when it is done**.

Rules of use:
- This file outranks every other document on product questions. If a plan, a chat handoff, or a session note disagrees with this file, this file wins.
- Only the user edits the `USER-OWNED` sections. An agent may transcribe the user's own dictated content into them; it may not invent or infer their content.
- Lines marked `UNCONFIRMED` were reconstructed from a truncated source and are not yet authoritative. Confirm or correct them.
- This file contains no counts, no status, no dates. Those live in `.claude/CONTEXT.md`.

---

## 1. What this is

A single-summoner League of Legends ranked analytics app: Riot API to raw JSON to DuckDB to features to K-Means to a public Streamlit dashboard.

**Personal-first.** Confirmed by the user, 2026-08-12:

> Personal usefulness is the primary product objective. Portfolio and readability for outside viewers is secondary. When the two conflict, personal usefulness wins.

The primary user is the player, using it to review their own games and improve. Portfolio value is a consequence, not the goal — a tool that genuinely serves its one user reads better to an outside viewer than an accumulation of statistics does.

## 2. Audience — USER-OWNED

- **Primary: the player who owns the account.** Knows the game and this specific account. Comes to answer a question about their own play, not to browse numbers.
- **Secondary: an outside viewer** — a recruiter, a peer, another player — who has no stake in the account. Should be able to follow what the tool concluded and why, without knowing the player.
- League knowledge assumed of the primary audience: full, mid-lane specific. Of the secondary audience: none required to follow the conclusions.
- Data-science knowledge assumed: none required. Method is visible on request, never in the way.

`<FILL IN — the "# 4. Personal-first Scope" section from your source did not survive the paste. Anything in it that is not captured above goes here.>`

## 3. The 30-second test — USER-OWNED

A visitor lands, reads for 30 seconds, closes the tab. These are the sentences they should be able to say afterward.

> **UNCONFIRMED — reconstructed from a truncated paste. Confirm or correct.**
>
> 1. I understand **why I am losing**.
> 2. I can see **what patterns keep appearing** in my games.
> 3. I know **which games I should review** to improve.

Every page element must serve one of these sentences. Anything that serves none gets cut. This is the test used to accept or reject dashboard changes.

The UI is evaluated from this perspective, not from whether it already exists:

> `<FILL IN — UNCONFIRMED. Your source read: "Can a player understand t…" and was cut off. This is the phrasing of the UI evaluation question; it is not recoverable from the paste.>`

Current UI is judged **unsatisfactory** and is not to be preserved on the grounds that it is already built.

## 4. The insight hierarchy

The acceptance test for every number, chart, and card on the page.

```text
Raw Data
    ↓
Reliable Metrics
    ↓
Meaningful Analysis
    ↓
Gameplay Patterns
    ↓
Interpretation
    ↓
Actionable Insight
```

**Rule: an element must reach layer 4 or higher, or be explicitly framed as context and reference rather than as a finding.** Raw metrics are allowed on the page; raw metrics *presented as the conclusion* are not. This is the resolution of the tension with section 8 — when a slice is too small to support interpretation, the answer is to frame it as reference or omit it, never to manufacture an interpretation the data cannot carry.

Worked example:

**Bad** — stops at layer 2:
```text
Zoe — 100 games — 53% WR
```

**Better** — reaches layer 4:
```text
Zoe — 100 games — 53% WR
Strong against control mages
Weak against early-pressure assassins
```

**Better still** — reaches layer 6:
```text
Zoe — 100 games — 53% WR
+8% above your overall mid-lane baseline against control mages
-9% below baseline against early-pressure assassins
Most recent losses against assassins involve an early CS/XP deficit
followed by repeated deaths during side-lane play.
```

The goal is **understanding**, not statistic accumulation.

## 5. Definition of done — USER-OWNED

The criteria the finished project must satisfy. Proposed starting set; edit freely, delete what you do not care about, add what is missing.

1. The live dashboard passes the 30-second test with someone who has never seen the project.
2. Every displayed element reaches layer 4 of the insight hierarchy, or is explicitly framed as reference rather than as a finding.
3. Every displayed number is either statistically defensible at its sample size, or visibly marked as underpowered.
4. Every heuristic proxy label reads as an estimate in the UI, never as a gameplay fact.
5. The player can name, from the dashboard alone, which specific games to rewatch and what to look for in them.
6. The README explains the project to a stranger in under two minutes, with current screenshots.
7. `<FILL IN — anything else that must be true before you stop>`

These are criteria, not a checklist. Which of them currently hold is project state and is tracked in `.claude/CONTEXT.md`.

Backlog items are **not** part of done. They live in `.claude/CONTEXT.md` and may be abandoned without reopening this file.

## 6. Scope — fixed

Derived from the code and the decisions log. Changing any of these is a product decision, not an implementation detail.

| In scope | Detail |
|---|---|
| One summoner | Own account only. PUUID from `.env`. |
| One queue | Ranked Solo/Duo, `queue=420`. |
| One role for analytics | Season 16 `team_position = 'MIDDLE'`. |
| All roles at rest | Collection and processing keep every role for future expansion. |
| One deployment | Streamlit Cloud, reading committed `data/lol_deploy.duckdb` read-only. |

## 7. Non-goals — fixed

Do not build these. Do not let an agent propose them as "improvements". Each was decided and closed.

- Live or in-game features of any kind.
- Multi-user, multi-account, or account-lookup input.
- Win-probability prediction. Removed: output was not surfaceable usefully.
- Manual-input predictor form. Removed: no use case during or after a game.
- All-role analytics. Requires role-aware opponent extraction, new tests, full DuckDB rebuild.
- Pro-player comparison. Stretch only; requires KR/EUW routing.
- Any display that stops at layer 1 or 2 of the insight hierarchy and presents itself as a finding. This is what OP.GG already does and what this project exists to be different from.

## 8. Honesty constraints — fixed

The project claims to be analytics. These are what keep that claim true.

- **Proxy labels are estimates.** Throw, Comeback, Overextension, Deficit Fight, Post-Laning Throw, and every roam-derived feature are inferred from single-player timeline data, not confirmed team state. `GAME_MECHANICS.md` is authoritative on the gap. The UI must never present them as gameplay ground truth.
- **Sample size gates confidence.** The Season 16 mid dataset is small, and per-matchup slices are far smaller still. No color-coded verdict, ranking, or "best/worst" claim may render on a slice too small to support it. Show the count next to the claim. Current sizes are in `.claude/CONTEXT.md`.
- **Interpretation is earned, not asserted.** Reaching layer 5 or 6 requires evidence the data actually contains. Where it does not, the honest move is to say less, not to invent a narrative that sounds insightful.
- **Clusters are behavior groups, not archetypes.** Silhouette is weak. Cluster names came from centroid review and are labels of convenience; sample size per cluster must be visible wherever a cluster is named.
- **No invented thresholds.** A cutoff that changes what a user concludes is a user decision, not an agent's default.

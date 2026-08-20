# Product Definition

Source of truth for **what this project is for** and **when it is done**.

Rules of use:
- This file outranks every other document on product questions. If a plan, a chat handoff, or a session note disagrees with this file, this file wins.
- Only the user edits the `USER-OWNED` sections. An agent may transcribe the user's own dictated content into them; it may not invent or infer their content.
- This file contains no counts, no status, no dates. Those live in `.claude/CONTEXT.md`.

---

## 1. What this is

A **personal League of Legends analytics and self-review platform**. Riot API to raw JSON to DuckDB to features to analytics to a Streamlit application.

The primary user is the player themselves.

**Personal-first.** Confirmed by the user:

> Personal usefulness is the primary product objective. Portfolio and readability for outside viewers is secondary. When the two conflict, personal usefulness wins. I do not want the project optimized around looking impressive as a portfolio project at the expense of being genuinely useful to me.

The project must evolve from *"a dashboard showing League statistics"* into *"a personal analytical tool that helps me understand my own gameplay."*

It answers one question: **"I played these games. What can this application actually teach me about how I play League of Legends?"**

The existing implementation is evidence of the project's history, not automatically the specification. Do not assume a component deserves to remain because it already exists.

## 2. Audience — USER-OWNED

- **Primary: the player who owns the account.** Knows the game and this specific account. Comes to answer a question about their own play, not to browse numbers.
- **Secondary: an outside viewer** — a recruiter, a peer, another player — who has no stake in the account. Should be able to follow what the tool concluded and why. Never at the primary user's expense.
- League knowledge assumed of the primary audience: full, mid-lane specific. Of the secondary audience: none required to follow the conclusions.
- Data-science knowledge assumed: none required. Method is visible on request, never in the way.

### Personal-first scope

Do not over-engineer for multi-user scale. Prioritize fast iteration, correctness, transparency, debuggability, useful analytics, good UX, and easy experimentation.

Do not introduce distributed infrastructure, microservices, complex authentication, or large-scale cloud architecture because they might be needed later. **But do not make architecture decisions that render future expansion unnecessarily difficult.**

A future version may support multiple players, accounts, cloud deployment, public profiles, comparative analytics, AI coaching, and larger datasets. Future concern, not current priority — and explicitly not forbidden.

## 3. Page purpose — USER-OWNED

**Every page must have a clear user question, and every element on that page must support that question.** An element that supports no question is cut.

| Page | The question it answers |
|---|---|
| Overview | How am I doing, and what should I investigate? |
| Champions | Which champions actually work for me, and how? |
| Matchups | Which matchups are strong, weak, or uncertain for me? |
| Match History | Which games should I inspect? |
| Match Detail | What actually happened in this game? |
| Patterns | What behaviors keep repeating across my games? |

### The 30-second test

This is the acceptance test for **the Overview specifically** — not a rule applied literally to every page and every element. A visitor lands, reads for 30 seconds, closes the tab. They should be able to say:

1. I understand **why I am losing**.
2. I can see **what patterns keep appearing** in my games.
3. I know **which games I should review** to improve.

### How the UI is judged

> **"Can a player understand this information quickly and use it?"**

rather than:

> "Can I fit more statistics onto this page?"

The current UI is judged **unsatisfactory** and is not to be preserved on the grounds that it is already built.

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

**Rule, confirmed by the user:** raw metrics may exist as context and reference, but must not be presented as findings unless the evidence supports layer 4 or higher. The goal is not to remove raw data — it is to prevent raw data from pretending to be insight.

Insufficient sample size must produce **reference, explicit uncertainty, or omission** — never a fabricated conclusion.

Worked example.

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

## 5. The analysis loop

The product exists to support one movement, and every navigation decision serves it:

```text
Overview → Problem → Evidence → Specific Game → Gameplay Context → Improvement
```

Progressive disclosure is the mechanism: champion summary, then matchup overview, then a specific matchup, then individual games, then timeline, then raw events. Do not expose every level at once.

## 6. Functional areas

What the product contains. Depth per area is a scheduling question; presence is not.

- **Overview** — current form, recent trend, streak, strongest and weakest champions, champion pool composition, recent meaningful patterns, high-confidence insights. Prioritize high-value information; do not display every available metric.
- **Match History** — fast scanning, not maximum density. Filter and sort by date, champion, opponent, role, result, queue, season, and date range.
- **Match Detail** — overview, lane phase (CS/XP/gold/level difference, first recall, plates, solo kills, deaths, wave and lane state), a chronological timeline of important events, and death context.
- **Champion Pool** — per-champion metrics and archetype composition. Answers "what kind of champions do I naturally play" and "what kinds of gameplay am I actually successful at".
- **Advanced Champion Analysis** — for champions with meaningful sample size, break performance down by opponent archetype and by specific matchup.
- **Matchup Classification** — see §7.
- **Pocket Pick Detection** — low-played but unusually successful picks, labeled `Potential Pocket Pick`, `Matchup-specific Pocket Pick`, `Emerging Pick`, or `Insufficient Data`. Small-sample outliers must never become strong recommendations.
- **Roam Analysis** — count, timing, destination, duration, resulting kills and assists, objective impact, lane cost. The purpose is not to count roams; it is to answer "are my roams actually effective".
- **Death Context** — why a death happened, not that it happened. Categories may include lane mistake, gank, roam, overextension, objective fight, teamfight, vision-related, side-lane, dive, isolated, greedy reset, unknown. Classification must be explainable from evidence and must state its own confidence.
- **Gameplay Patterns** — recurring behavior supported by repeated evidence. One unusual game is never a pattern.

## 7. Statistical discipline

**Champion archetypes.** The working taxonomy, subject to evolution: Burst Mages, Control Mages, Assassins, Bruisers, Fighters, Tanks, Marksmen, Enchanters, Catchers, Specialists, Artillery, Skirmishers, Divers, Juggernauts.

**Matchup classification.** Every matchup resolves to exactly one of:

| Class | Meaning |
|---|---|
| Positive | Performance meaningfully above the relevant baseline |
| Negative | Performance meaningfully below the relevant baseline |
| Skill-based | Close to baseline; no evidence the matchup is inherently favorable or unfavorable |
| Uncertain | Not enough evidence to conclude anything useful |

Never classify on raw win rate. `2 games, 100% WR` must never outrank `35 games, 60% WR`. Acceptable tools include minimum sample sizes, confidence intervals, Wilson intervals, Bayesian estimation, shrinkage, and baseline comparison. **Choose the simplest method that yields a statistically responsible conclusion** — not every technique listed.

**Confidence must be communicated**: High, Medium, Low, or Insufficient data.

**Low-data states are distinct and must not be collapsed**: no data; insufficient data; statistically uncertain; data unavailable; feature not implemented. A rate of `0%` that means "not enough games" is a bug.

**Metrics need definitions.** Every important metric documents its source, calculation, assumptions, and limitations. This is what stops analytics becoming arbitrary over time.

**Avoid metric explosion.** Before adding a metric: what question does it answer, who needs it, does it change interpretation, is it more useful than an existing metric, can the user understand it, is it statistically reliable? If not, it is not a priority.

## 7b. UX rules

**Hierarchy.** Important information visually dominates low-value information. A page reads: what matters, then why it matters, then supporting evidence, then raw detail. Do not display all metrics with equal visual weight.

**Scannability.** Avoid giant walls of numbers, overly dense tables, repetitive cards, unnecessary charts, excessive decorative UI, and information with little practical meaning.

**Progressive disclosure.** Do not expose every level at once. The user drills down when they want more.

**Context.** A number must carry meaning. `CS/min 7.1` alone is insufficient; `7.1, +0.6 vs your recent average` is better; adding what that advantage does later in the game is the target.

**Tables versus charts.** Tables when exact comparison matters. Charts when trends, distributions, relationships, or visual patterns matter. Never a chart merely because one is possible.

## 7c. Insight generation

An insight must be:

- **Evidence-based** — derived from real data.
- **Context-aware** — accounts for sample size and the relevant baseline.
- **Explainable** — the user can investigate why the system said it.
- **Actionable** — points toward something to review or improve.

Bad: *"Your performance is unusual."*

Better: *"Your win rate against assassins is 11 percentage points below your overall mid-lane baseline."*

Best: *"Your win rate against assassins is 11 points below your mid-lane baseline. In 7 of your 10 losses, you were behind in CS/XP by 10 minutes. Review early-wave and level-3/4 interaction patterns."*

The last is the target direction.

## 7d. Failure modes to avoid

Generic dashboards. Charts without purpose. Huge tables containing every metric. Treating every statistic as equally important. Tiny-sample win rates without context. Fabricated certainty. Aesthetics over usability. Technical complexity over practical value. Rewriting stable code without understanding its dependencies. Features added because they sound advanced. An AI layer before reliable analytics exist.

## 8. Definition of done — USER-OWNED

The criteria the finished project must satisfy.

1. The Overview passes the 30-second test with someone who has never seen the project.
2. Every page has a stated user question and every element on it serves that question.
3. Every displayed element reaches layer 4 of the insight hierarchy, or is explicitly framed as reference.
4. Every displayed number is either statistically defensible at its sample size, or visibly marked as underpowered — with its confidence band named.
5. Every heuristic proxy reads as an estimate, never as a gameplay fact.
6. The player can complete the analysis loop in §5 end to end: from a dashboard observation to a specific game and what to look for in it.
7. The README explains the project to a stranger in under two minutes, with current screenshots.

These are criteria, not a checklist. Which of them currently hold is project state and is tracked in `.claude/CONTEXT.md`.

## 9. Scope — fixed

| In scope | Detail |
|---|---|
| One summoner | Own account only. PUUID from `.env`. |
| One queue for analytics | Ranked Solo/Duo, `queue=420`. |
| One role for analytics | Season 16 `team_position = 'MIDDLE'`. |
| All roles at rest | Collection and processing keep every role. Match History may surface them behind a role filter before role-aware analytics exist. |
| One deployment | Streamlit Cloud, reading committed `data/lol_deploy.duckdb` read-only. |

## 10. Not now — and why

Deferred, not forbidden. Each may be revisited; none is a current priority.

- **Multi-user, accounts, public profiles, cloud, comparative analytics.** Future version. Do not build for it now; do not architect against it either.
- **AI explanation layer.** Only ever on top of structured, validated analytics — never an LLM inferring from raw match data when deterministic analytics can answer more reliably. Reliable analytics come first.
- **All-role analytics.** Requires role-aware opponent extraction, direct tests, and a full DuckDB rebuild.
- **Pro-player comparison.** Requires KR/EUW routing.

## 11. Forbidden

- Live or in-game features of any kind.
- Win-probability prediction, and the manual-input predictor form. Both removed: the output was not surfaceable usefully.
- Any display that stops at layer 1 or 2 of the insight hierarchy and presents itself as a finding.
- Fabricated certainty. When required data does not exist: identify what is missing, determine whether it can be derived, determine whether more ingestion is needed, document the limitation, and implement the strongest valid approximation — or nothing. Never fake the result.
- Charts added because a chart is possible. A chart harder to read than its underlying table is not helping.
- Redesigning around a data limitation that could cheaply be removed from the pipeline instead.

## 12. Honesty constraints

- **Proxy labels are estimates.** Throw, Comeback, Overextension, Deficit Fight, Post-Laning Throw, and every roam-derived feature are inferred from single-player timeline data, not confirmed team state. `GAME_MECHANICS.md` is authoritative on the gap.
- **"Deficit" means opponent-relative.** A deficit claim must rest on actual opponent evidence, not on the player's own timeline compared against itself.
- **Sample size gates confidence.** No colored verdict, ranking, or best/worst claim on a slice too small to support it. Show the count next to the claim. Current sizes are in `.claude/CONTEXT.md`.
- **Interpretation is earned.** Where the data does not support layer 5 or 6, say less rather than inventing a narrative that sounds insightful.
- **Clusters are behavior groups, not archetypes.** Sample size per cluster must be visible wherever a cluster is named.
- **No invented thresholds.** A cutoff that changes what a user concludes is a user decision, not an agent's default.
- **Correctness precedes presentation.** A visually impressive statistic calculated incorrectly is worse than no statistic.

## 13. Priority ladder

When choosing what to build next:

| Tier | Contains |
|---|---|
| P0 | Product usability: navigation, information hierarchy, readability, basic workflows, correctness |
| P1 | Core analytics: match history, recent performance, champion pool, champion analysis, matchup analysis |
| P2 | Advanced analysis: timeline, lane analysis, death context, roam analysis |
| P3 | Higher-level intelligence: patterns, pocket picks, automated insights, confidence-aware recommendations |
| P4 | Future: AI assistant, multi-user, cloud, public sharing, comparative analytics |

Sequencing within this ladder is recorded in `.claude/CONTEXT.md`. Where a P2 data change cheaply unblocks P0 or P1 quality, it is pulled forward — per §11, do not design around a limitation that can cheaply be removed.

## 14. How to work here

Incremental over rewrite. Preserve useful functionality, refactor where necessary, keep analytics logic separate from presentation, keep data definitions explicit, avoid duplicating business logic in UI components.

When replacing an implementation, state: what is being replaced, why, what behavior must remain, and what behavior is intentionally changing.

**UX is a functional requirement.** A feature is not done because the data exists, the calculation is correct, and the component renders. It is done when the user can discover it, understand it, interact with it, interpret the result, and use that result to review their gameplay. A UI task is not complete because the code compiles — run the app and inspect the rendered result.

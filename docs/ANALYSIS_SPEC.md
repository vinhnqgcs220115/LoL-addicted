# Analysis Spec

How this project operationalizes domain concepts using the data that actually exists.

Three homes, one job each:

```text
docs/domain/       what a mechanic means          (independent of our telemetry)
docs/DATA_AUDIT.md what current telemetry observes (generated, never hand-edited)
this file          how we operationalize a concept with what we have
```

**Status: v0, provisional.** Keyed to *Mid-Laner Decision Catalogue v1*, whose entries are
all `status: candidate` and none of which have been verified by the player yet. Nothing
here is committed to until those entries are reviewed and owned. Availability verdicts,
however, are measured — they come from `DATA_AUDIT.md` over the full corpus and do not
depend on whether a catalogue entry survives review.

---

## 1. The observable primitives

Everything below is derived from these, and nothing else exists.

**Per minute, for all ten participants** (zero nulls, zero partial fields, whole corpus):
position, total gold, current gold, CS, jungle CS, XP, level, health, health max, mana,
mana max, armour, MR, AD, AP, movement speed, and damage dealt/taken split by
physical/magic/true — including `totalDamageDoneToChampions`.

**Millisecond-exact events:** champion kills (with position, killer, victim, assists, and
full per-source damage attribution), item purchases, sells and destroys, skill level-ups,
level-ups, ward placed and killed, turret plates, buildings, elite monsters, objective
bounties, pause end.

**Positioned events — only these five:** `CHAMPION_KILL`, `CHAMPION_SPECIAL_KILL`,
`BUILDING_KILL`, `ELITE_MONSTER_KILL`, `TURRET_PLATE_DESTROYED`.

**Static per game:** champions, runes, summoner spells, final items, ~129 `challenges`
aggregates (undocumented, cross-check only).

**What does not exist, at all:** minion positions or wave state; ability casts and
cooldowns; ward positions; non-lethal champion damage as discrete events; vision state
(who could see what); recall as an event; player intent.

---

## 2. Availability verdicts — catalogue v1, sections I-VII

`BUILDABLE` — the decision can be detected and evaluated from the primitives above.
`PARTIAL` — the action is detectable but a load-bearing part of the judgement is not.
`NOT OBSERVABLE` — a required input does not exist in the data.

| # | Entry | Verdict | Why |
|---|---|---|---|
| 1 | Greedy Farm, Late to Early Skirmish | **BUILDABLE** | Kill events pin the fight in time and space with participants; your minute positions and CS delta show what you did instead |
| 2 | Abandoning Valuable Wave for Low-Value Action | PARTIAL | Payoff is measurable; "valuable wave" needs wave state. CS delta is a weak proxy |
| 3 | Shove Without a Purpose | PARTIAL | Follow-up purpose (recall, roam, objective) is observable; "shove" needs wave state. CS-rate spike is a weak proxy |
| 4 | Roam Without Wave Setup | PARTIAL | The roam is detectable; the setup is not. You see the departure, never whether it was prepared |
| 5 | Over-Pushing Before a Vulnerable Rotation | **BUILDABLE** | Your position relative to static tower coordinates is observable, as is every enemy's position |
| 6 | Missed Crash | **NOT OBSERVABLE** | Requires wave position |
| 7 | Unnecessary Crash | **NOT OBSERVABLE** | Requires wave position |
| 8 | Failed Freeze Maintenance | **NOT OBSERVABLE** | Requires wave position |
| 9 | Refusing to Break a Freeze | **NOT OBSERVABLE** | Requires wave position |
| 10 | Poor Reset Timing | PARTIAL | Recall is inferable from purchase timestamps plus base position; CS/XP loss is measurable; wave state is not |
| 11 | Greedy Stay for One More Wave | PARTIAL | Death, unspent gold and CS are observable; the wave that motivated staying is not |
| 12 | Wrong Wave Investment | **NOT OBSERVABLE** | Mana spent on the wave versus on the opponent is indistinguishable — no ability casts |
| 13 | No-Roam When a High-Value Window Exists | PARTIAL | That you stayed and a fight happened is observable; "high-value window" is judgement |
| 14 | Low-Probability Roam | PARTIAL | Roam and outcome observable; probability is judgement |
| 15 | Wrong Roam Target | PARTIAL | All lane states are observable per minute, so comparison is possible; weighting is judgement |
| 16 | Roam Too Long | **BUILDABLE** | Duration off the mid corridor and the CS foregone are both measurable |
| 17 | Failed Roam Compounded | **BUILDABLE** | A sequence of off-lane minutes with no takedowns is directly visible |
| 18 | Enemy Roam Not Matched or Punished | **BUILDABLE** | The enemy mid's position is known every minute; so is what you gained while they were gone |
| 19 | Blind Follow | PARTIAL | Both players leaving is observable; "blind" is an information state, and vision is not recorded |
| 20 | Roam Into Unfavorable Numbers | **BUILDABLE** | Ten positions per minute — count the bodies near the fight |
| 21 | Ignoring Enemy Jungler Information | PARTIAL | Jungler position is observable; whether you *had* that information is not, because ward positions do not exist |
| 22 | Playing Strongside Without Support | **BUILDABLE** | Ally positions per minute |
| 23 | Abandoning Jungler Skirmish | **BUILDABLE** | Same shape as entry 1 |
| 24 | Forced Jungle Fight From Bad Lane State | PARTIAL | "Lane state" means wave state |
| 25 | Failure to Exploit Enemy Jungle Absence | PARTIAL | Jungler distance is observable; what counts as exploitation needs a definition |
| 26 | Bad Trade on Minion Disadvantage | **NOT OBSERVABLE** | No minion state, no non-lethal damage events |
| 27 | Trade Without Resource Advantage | **NOT OBSERVABLE** | HP/mana known only at minute boundaries; no trade instants |
| 28 | Missing Advantage Window | **NOT OBSERVABLE** | Requires cooldown and summoner-spell state |
| 29 | Extended Trade After Win Condition | **NOT OBSERVABLE** | Requires within-trade resolution |
| 30 | Fight Without Exit Condition | **NOT OBSERVABLE** | Requires cooldowns and intent |
| 31 | Blind Push | PARTIAL | Push depth is observable; "blind" is not |
| 32 | Irrelevant Ward | **NOT OBSERVABLE** | `WARD_PLACED` carries no position |
| 33 | Missing Critical Vision Before Action | **NOT OBSERVABLE** | Same |
| 34 | Staying on a Known Dangerous Side | PARTIAL | Position observable; "known" is not |
| 35 | Delayed Power-Spike Recall | **BUILDABLE** | `currentGold` per minute makes unspent gold directly visible |
| 36 | Recall Before Immediate Value | PARTIAL | Recall inferable; foregone value needs a definition |
| 37 | Wrong Itemization for Immediate State | **BUILDABLE** | Items and exact purchase times are recorded; the judgement needs matchup domain knowledge |
| 38 | Delayed Power-Spike Conversion | PARTIAL | Item completion time is exact; "conversion" is partly behavioural |
| 39 | Late Objective Rotation | **BUILDABLE** | Objective kills carry time and position; spawn timers are domain constants; your position is known each minute |
| 40 | Objective Fight Without Lane Preparation | PARTIAL | Lane preparation means wave state |
| 41 | Contesting an Unwinnable Objective | **BUILDABLE** | Positions and deaths around the objective |
| 42 | Failure to Trade Objective | **BUILDABLE** | Objective events for both teams, plus what you took meanwhile |
| 43 | Objective Tunnel Vision | PARTIAL | Persistence is observable; the changing value that should have redirected you is judgement |

### Tally

| Verdict | Count | Share |
|---|---|---|
| BUILDABLE | 13 | 30% |
| PARTIAL | 18 | 42% |
| NOT OBSERVABLE | 12 | 28% |

### The unbuildable twelve are not scattered — they cluster

**Wave state (6, 7, 8, 9, 12).** Every freeze and crash entry. Minion positions do not
exist in Match-V5 at any resolution, and the 60-second frame interval would not be enough
even if they did — a wave crosses the lane in about that time.

**Trading (26, 27, 28, 29, 30).** The entire section. Non-lethal champion damage produces
no events; `victimDamageReceived` exists only on kills. There are no ability casts and no
cooldown state.

**Ward locations (32, 33).** `WARD_PLACED` records who, when, and what type — never where.

These are the two areas the player most wants coached, and they are the two the data
cannot reach. That is a finding, not a gap to engineer around.

---

## 3. What this means for the report

The per-game report leads with what it can see and states what it cannot judge.

**It can:** locate the minutes where things went wrong; place every player on the map at
your decision points; eliminate hypotheses (it was not jungle pressure, it was not CS);
measure what you gave up and what you got.

**It must not:** claim to know why a trade was lost, assert a wave state, or infer what
you could see.

A `PARTIAL` entry ships only with the missing half named in the output. An entry whose
judgement rests entirely on an unobservable input is not shipped as a verdict at all — at
most it becomes a prompt to review a specific minute.

---

## 4. Open

- Catalogue v1 entries are unverified candidates; none is domain truth yet.
- Sections VIII-XV (mid-game, macro, meta) are unclassified — out of the current laning scope.
- Entry 53 and parts of 63-65 are evaluator rules, not player decisions, and belong elsewhere.
- Overlapping entries (2/14/52, 10/11, 29/59) need merging under one-canonical-home.
- Per-metric definitions — source, calculation, assumptions, limitations — are written here
  as each metric stabilizes, not before.

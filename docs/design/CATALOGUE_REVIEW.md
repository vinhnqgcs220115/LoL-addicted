# Decision Catalogue — player review sheet

**Every entry below is `status: candidate`.** They were generated with research citations,
not authored from your own play. Nothing here is domain truth until you mark it.

**How to use this.** Fill the `Verdict` line on each card. Values:

```text
KEEP         the definition matches a real decision you make
RENAME       right concept, wrong words
MERGE        duplicates another entry — say which
SPLIT        two different decisions wearing one name
REVIEW_ONLY  real, but should only ever produce a review prompt, never a verdict
REMOVE       not a decision you actually make, or not meaningful
UNDECIDED    come back to it
```

**Recommendations marked `[proposal]` are mine and carry no authority.** Leave `Verdict`
blank if you disagree; do not treat a proposal as a default.

**Scope of this sheet.** Full cards for the 23 entries that block implementation — the 13
BUILDABLE, the 6 domain-rule-blocked, and the 4 requiring renames. The remaining 47 are in
the compact tables at the end, because none of them can be implemented regardless of your
verdict, so reviewing them is not urgent.

---

## Part 1 — BUILDABLE (13)

These can be detected *and* evaluated from historical Match-V5 today. **They are the
implementation queue.** A `REMOVE` or `REVIEW_ONLY` here changes what gets built first, so
these are the highest-value verdicts.

---

### #1 · Greedy Farm, Late to Early Skirmish
**Means.** A fight breaks out elsewhere while you keep farming mid. You arrive late or not
at all, and your team fights a body down.
**Not.** A deliberate trade — taking a crash or plates while they fight is a decision with a
payoff. This one has no payoff.
**Inputs.** Kill event time + position + participants · your frame positions either side ·
CS gained during the window.
**Implement when.** Verified. Needs no threshold beyond "a fight occurred", which kill
events define.
**Proposed wording** `[proposal]` — unchanged.
**Verdict:**

---

### #5 · Over-Pushing Before a Vulnerable Rotation
**Means.** You push into an exposed position without information or protection, and become
vulnerable to jungle or support intervention.
**Not.** Intentional pressure when you know where the enemy is or have backup.
**Inputs.** Your position against static tower coordinates · all ten positions per minute.
**Implement when.** Verified. Note the *knowledge* half ("without information") is not
observable — only the exposure is.
**Proposed wording** `[proposal]` — *Pushed past a safe position with enemy nearby*. Drops
the unobservable "without adequate information".
**Verdict:**

---

### #16 · Roam Too Long
**Means.** The reason you left lane has ended, but you keep moving around the map and keep
paying the lane cost.
**Not.** Extending because a new high-value opportunity appeared.
**Inputs.** Duration off the mid corridor · CS foregone versus lane opponent.
**Implement when.** Verified. **Caveat:** "off the corridor" currently uses an invented
2,500-unit width (`MID_LANE_CORRIDOR_WIDTH`). That constant is a threshold and therefore
yours — see the threshold sheet.
**Verdict:**

---

### #17 · Failed Roam Compounded
**Means.** A roam fails and, instead of recovering lane tempo, you keep forcing more
low-probability actions.
**Not.** Continuing because the failure created a new opening.
**Inputs.** Consecutive off-lane minutes with no takedowns.
**Implement when.** Verified. Depends on the same corridor constant as #16.
**Proposed** `[proposal]` — possible MERGE into #16; both are "stayed away too long", one
after success and one after failure. Worth a look. **Your call whether these are genuinely
two different mistakes.**
**Verdict:**

---

### #18 · Enemy Roam Not Matched or Punished
**Means.** The enemy mid leaves and you extract nothing from their absence — no push, no
plates, no vision, no rotation of your own.
**Not.** Unable to follow safely, or deliberately taking a better trade-off.
**Inputs.** Enemy mid position every minute · what you gained while they were gone.
**Implement when.** Verified. **Strongest entry in the catalogue** — fully observable, and
genuinely invisible to you in-game.
**Verdict:**

---

### #20 · Roam Into Unfavorable Numbers
**Means.** You join a fight where the enemy has the numbers, position, or strength that
should have discouraged going.
**Not.** Joining because your arrival flips the numbers.
**Inputs.** All ten positions per minute — count bodies near the fight.
**Implement when.** Verified. Needs a proximity radius defining "at the fight" `[proposal]`
— suggest deriving it from observed fight spread rather than picking a number.
**Verdict:**

---

### #22 · Playing Strongside Without Support
**Means.** You position as though help is nearby when your teammates cannot actually reach
you.
**Not.** Deliberate pressure the enemy cannot punish.
**Inputs.** Ally positions per minute.
**Implement when.** Verified. Shares a proximity definition with #20.
**Verdict:**

---

### #23 · Abandoning Jungler Skirmish
**Means.** Your jungler contests something nearby that you could influence, and you stay on
a low-value lane action.
**Not.** Wave or resource cost genuinely too high, or the fight already lost.
**Inputs.** Same shape as #1, scoped to jungler involvement.
**Proposed** `[proposal]` — possible MERGE with #1; both are "a fight happened, you did not
go". The distinction is only who was fighting. **Your call whether that distinction
matters to you.**
**Verdict:**

---

### #35 · Delayed Power-Spike Recall
**Means.** You stay on the map with enough gold for a meaningful purchase while gaining
little from staying.
**Not.** Staying to finish a wave, protect an objective, or exploit a temporary lead.
**Inputs.** `currentGold` per minute — unspent gold is directly visible · item costs from
Data Dragon.
**Implement when.** Verified, plus a definition of "meaningful purchase" `[proposal]` —
suggest a completed item in your actual build path rather than a flat gold number.
**Verdict:**

---

### #37 · Wrong Itemization for Immediate State
**Means.** Your build poorly addresses the matchup or threat in front of you.
**Not.** A deliberate off-meta choice serving a different purpose.
**Inputs.** Items and exact purchase times · both champions · patch.
**Implement when.** **Judgement needs domain knowledge that does not exist yet** — what the
*right* item is per matchup per patch. Detection is buildable; evaluation is not.
**Proposed** `[proposal]` — REVIEW_ONLY until a build reference exists. The system can show
the build and flag nothing.
**Verdict:**

---

### #39 · Late Objective Rotation
**Means.** You start moving toward an objective after the fight for it has begun.
**Not.** Deliberately conceding it.
**Inputs.** Objective kill time + position · your positions · spawn timers.
**Implement when.** Verified. **Spawn timers are now empirically derivable** from the
corpus, so this no longer waits on a hand-maintained constant.
**Verdict:**

---

### #41 · Contesting an Unwinnable Objective
**Means.** You contest without the numbers, resources, or position to make it realistic.
**Not.** A calculated low-probability contest justified by the objective's value.
**Inputs.** Positions and deaths around the objective.
**Implement when.** Verified. Shares proximity definition with #20/#22.
**Verdict:**

---

### #42 · Failure to Trade Objective
**Means.** The enemy takes something you cannot contest and you take nothing elsewhere.
**Not.** No meaningful alternative existed.
**Inputs.** Objective events for both teams · what you gained meanwhile.
**Implement when.** Verified, plus a definition of "meaningful alternative" `[proposal]`.
**Verdict:**

---

## Part 2 — Blocked only by a threshold you define (6)

**These need no new data.** The telemetry exists; a number is missing. Cheapest unblocks in
the catalogue. Thresholds are on the separate decision sheet in
`FINALIZATION_DECISIONS.md`; this sheet asks only whether the *entry* is real.

| # | Name | Means | Missing definition |
|---|---|---|---|
| 13 | No-Roam When a High-Value Window Exists | A convertible opportunity appeared; you stayed in lane without sufficient reason | what makes a window "high value" |
| 14 | Low-Probability Roam | You left for a play with little realistic chance | what makes a roam "low probability" |
| 15 | Wrong Roam Target | You picked a destination worth less than an available alternative | how to compare two destinations |
| 25 | Failure to Exploit Enemy Jungle Absence | Jungler demonstrably elsewhere; you did not use the window | what counts as exploiting it |
| 38 | Delayed Power-Spike Conversion | You hit a spike and kept playing at your old power level | what counts as converting |
| 43 | Objective Tunnel Vision | You kept pursuing an objective after its value dropped | what counts as value dropping |

**Verdicts:** #13 ____ #14 ____ #15 ____ #25 ____ #38 ____ #43 ____

---

## Part 3 — Renames required before these can ship (4)

Current names assert **what you knew**. The data never shows player knowledge — only enemy
position. Shipping the current wording would be a false claim.

| # | Current — unsupportable | Proposed `[proposal]` | Verdict |
|---|---|---|---|
| 19 | Blind Follow | Followed enemy mid rotation — vision state unknown | |
| 21 | Ignoring Enemy Jungler Information | Acted with enemy jungler at known distance — player knowledge unknown | |
| 31 | Blind Push | Pushed into exposed position with enemy proximity — visibility unknown | |
| 34 | Staying on a Known Dangerous Side | Objectively exposed position | |

#34 matters most: *known* and *dangerous* are two separate claims and the data supports only
a weak form of the second.

---

## Part 4 — Cannot be implemented regardless of verdict (12)

Real mechanics, no structured source. These become **review prompts** pointing you at a
replay timestamp — never automatic verdicts. Review is not urgent; they are listed so the
catalogue stays complete, and because if better data ever arrives they are already written.

| # | Name | Blocked by |
|---|---|---|
| 6 | Missed Crash | wave state — no minion data in any Riot source |
| 7 | Unnecessary Crash | wave state |
| 8 | Failed Freeze Maintenance | wave state |
| 9 | Refusing to Break Freeze | wave state |
| 12 | Wrong Wave Investment | ability casts — cannot separate mana spent on wave vs opponent |
| 26 | Bad Trade on Minion Disadvantage | minions + casts |
| 27 | Trade Without Resource Advantage | enemy HP/mana at the trade instant |
| 28 | Missing Advantage Window | cooldowns, summoner availability |
| 29 | Extended Trade After Win Condition | enemy HP, casts |
| 30 | Fight Without Exit Condition | cooldowns, intent |
| 32 | Irrelevant Ward | ward position — `WARD_PLACED` has no coordinates |
| 33 | Missing Critical Vision Before Action | ward position |

---

## Part 5 — PARTIAL, ship with the missing half named (remaining)

Action detectable, judgement input missing. Each ships only with its gap stated in the
output. Lower review priority than Parts 1–3.

| # | Name | Missing |
|---|---|---|
| 2 | Abandoning Valuable Wave for Low-Value Action | wave state |
| 3 | Shove Without a Purpose | wave state |
| 4 | Roam Without Wave Setup | wave state |
| 10 | Poor Reset Timing | wave state |
| 11 | Greedy Stay for One More Wave | wave state, intent |
| 24 | Forced Jungle Fight From Bad Lane State | wave state |
| 36 | Recall Before Immediate Value | wave state |
| 40 | Objective Fight Without Lane Preparation | wave state |

---

## Part 6 — Unclassified (sections VIII–XV, entries 44–70)

Mid-game, macro, positioning, adaptation, advantage conversion, defensive play, information,
and meta-habits. **Outside the current laning scope and unclassified against the data.**

Two structural problems to note if you extend scope later `[proposal]`:

- **#53 Outcome-Validated Hindsight is not a player decision.** It is an error the
  *evaluator* can make. It belongs in the analysis rules, not a catalogue of your choices.
  Same for parts of #63–65.
- **Heavy overlap** — #2 / #14 / #52 are arguably one idea; #10 / #11 likewise; #29 / #59
  likewise. One-canonical-home will force merges.

---

## Summary

| Part | Entries | Why review now |
|---|---|---|
| 1 · BUILDABLE | 13 | **Implementation queue — review first** |
| 2 · Threshold-blocked | 6 | Cheapest unblocks; need a number from you |
| 3 · Renames | 4 | Current wording makes unsupportable claims |
| 4 · Replay-only | 12 | Cannot build either way |
| 5 · PARTIAL | 8 | Ship degraded; lower priority |
| 6 · Unclassified | 27 | Out of scope |

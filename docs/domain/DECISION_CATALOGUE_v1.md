> **L2 Domain** · Mid-Laner Decision Catalogue v1 — verbatim session message, unreviewed, may include surrounding text · owner: user · status: candidate, unverified · update: user only
> Source: Claude Code session `34e9a6b4`, user message of 2026-09-15 04:47 UTC. Review sheet: `docs/design/CATALOGUE_REVIEW.md`.

---

# Mid-Laner Decision Catalogue — v1

## How to use this catalogue

Each entry describes a **recognizable decision pattern**, not automatically a "mistake."

A decision should only be judged after considering its context:

```text
Decision
→ available state/information
→ alternative options
→ cost
→ payoff
→ outcome
→ evaluation
```

The catalogue therefore includes both **negative patterns** and their legitimate alternatives.

Also, a catalogue entry should not imply that the current Riot telemetry can necessarily detect it. Whether something is observable belongs in `DATA_AUDIT.md`, not here.

---

# I. Wave / Lane-Economy Decisions

These are foundational because the wave determines what opportunities and costs exist for many subsequent mid-lane decisions. Riot has explicitly described synchronized wave timing as increasing the opportunity cost of leaving mid to roam. ([League of Legends][1])

### 1. Greedy Farm, Late to Early Skirmish

**What it is:**
A fight breaks out elsewhere on the map while you continue farming mid. You arrive late or not at all, and your team fights with fewer players.

**Not to be confused with:**
A deliberate trade-off where you take a valuable wave, crash the wave, take plates, or secure another concrete resource while the fight is occurring.

**Typical evaluation:**
Potential mistake when the fight was reachable, valuable, and the lane resources you chose were worth less than your team's opportunity.

---

### 2. Abandoning a Valuable Wave for Low-Value Action

**What it is:**
You leave a wave containing meaningful gold/XP to participate in an action with little realistic payoff.

**Not to be confused with:**
Giving up farm intentionally to secure a high-value kill, objective, defensive play, or favorable map state.

**Typical evaluation:**
Mistake when the lost lane resources substantially exceed the realistic value of the action.

---

### 3. Shove Without a Purpose

**What it is:**
You rapidly clear the wave without an identifiable follow-up purpose such as recall, roam, objective setup, vision, jungle assistance, plate pressure, or denying the opponent's desired movement.

**Not to be confused with:**
Fast pushing simply because clearing the wave is itself the correct immediate action.

**Typical evaluation:**
Potential inefficiency; strength of the criticism depends on what opportunity the push creates or destroys.

Current coaching material repeatedly frames wave control as a means to create time windows rather than an objective in itself. ([Dodge.gg][2])

---

### 4. Roam Without Wave Setup

**What it is:**
You leave mid while the wave is positioned such that the opponent can collect the wave, push into your tower, or otherwise gain substantial lane value.

**Not to be confused with:**
Leaving urgently to respond to an exceptionally valuable, time-sensitive fight where sacrificing lane resources is justified.

**Typical evaluation:**
Mistake when the opportunity was insufficient to compensate for the lane cost.

Wave setup before movement is a recurring principle in current mid-lane guidance. ([Dodge.gg][2])

---

### 5. Over-Pushing Before a Vulnerable Rotation

**What it is:**
You push yourself into an exposed position without adequate information or protection, then become vulnerable to jungle/support intervention.

**Not to be confused with:**
Intentional pressure where you know the enemy's position or have sufficient support to make the exposure acceptable.

**Typical evaluation:**
Mistake when the additional push provides little extra value but substantially increases risk.

---

### 6. Missed Crash

**What it is:**
You had a realistic opportunity to fully push the wave into the opponent's tower but leave it in a state that lets the opponent retain control or establish a favorable response.

**Not to be confused with:**
Intentionally stopping short because maintaining the current wave state is the better objective.

**Typical evaluation:**
Mistake when crashing would have enabled a clearly superior reset, roam, denial, or pressure sequence.

---

### 7. Unnecessary Crash

**What it is:**
You deliberately crash a wave even though maintaining or freezing the existing position would provide greater value.

**Not to be confused with:**
Crashing because you genuinely need to reset the lane, recall, roam, contest an objective, or deny the opponent.

**Typical evaluation:**
Context-dependent.

---

### 8. Failed Freeze Maintenance

**What it is:**
You establish or inherit a favorable freeze but break it unnecessarily, allowing the opponent to regain access or causing the wave to push away from the intended state.

**Not to be confused with:**
Breaking the freeze intentionally to create a new objective such as a crash, roam, reset, or defensive reposition.

**Typical evaluation:**
Potential mistake.

---

### 9. Refusing to Break a Freeze

**What it is:**
You maintain a freeze even after the strategic reason for holding it disappears or a more valuable map action becomes available.

**Not to be confused with:**
Continuing the freeze because the opponent is severely constrained by it and no higher-value play exists.

**Typical evaluation:**
Potentially greedy lane optimization at the expense of map impact.

---

### 10. Poor Reset Timing

**What it is:**
You recall at a point where you unnecessarily lose significant CS/XP, surrender pressure, or allow the opponent to obtain a favorable wave state.

**Not to be confused with:**
A deliberately inefficient-looking recall made necessary by low HP, mana, item breakpoint, objective timing, or imminent danger.

**Typical evaluation:**
Mistake when a materially better reset was available.

Recall timing is consistently treated as part of mid-lane wave/tempo management rather than an isolated shopping action. ([Mobalytics][3])

---

### 11. Greedy Stay for One More Wave

**What it is:**
You remain in lane for additional farm despite already having a favorable opportunity to reset, and the extra greed creates an avoidable death, lost recall timing, or worse item/tempo state.

**Not to be confused with:**
Staying because the extra wave completes a meaningful breakpoint or because the lane is demonstrably safe.

**Typical evaluation:**
Mistake when incremental farm has poor marginal value relative to reset risk.

---

### 12. Wrong Wave Investment

**What it is:**
You spend excessive mana, HP, cooldowns, or time manipulating a wave when that resource should have been preserved for an impending fight or lane interaction.

**Not to be confused with:**
Spending resources to obtain a wave state that creates a larger strategic payoff.

**Typical evaluation:**
Trade-off decision; requires context.

---

# II. Priority / Roaming Decisions

Riot has specifically described mid lane as a position where the tension between winning lane and influencing other areas is central to the role. ([League of Legends][1])

### 13. No-Roam When a High-Value Window Exists

**What it is:**
A strong and realistically convertible map opportunity appears, but you remain in lane without a sufficiently valuable reason to stay.

**Not to be confused with:**
Staying because leaving would cost a large wave, expose your tower, abandon a critical reset, or produce a low-probability play.

**Typical evaluation:**
Potential missed opportunity.

---

### 14. Low-Probability Roam

**What it is:**
You leave lane for a play that has little realistic chance of producing meaningful value.

**Not to be confused with:**
Taking a calculated low-probability play because the alternative is substantially worse.

**Typical evaluation:**
Mistake when the opportunity cost is high and the expected payoff is weak.

Current guides emphasize not merely leaving lane, but whether the destination can actually convert the time invested. ([Kaizen's Clan][4])

---

### 15. Wrong Roam Target

**What it is:**
You choose a destination that has less potential value than another available destination.

**Not to be confused with:**
Choosing the less obvious target because it is safer, more reliable, or strategically more important.

**Typical evaluation:**
Requires comparing target state, travel time, enemy information, conversion potential, and lane cost.

---

### 16. Roam Too Long

**What it is:**
The original reason for leaving lane has ended, but you continue moving around the map and accumulate unnecessary opportunity cost.

**Not to be confused with:**
Extending the play because a new, high-value opportunity emerges.

**Typical evaluation:**
Mistake when the additional seconds produce little additional value.

---

### 17. Failed Roam Compounded

**What it is:**
A roam fails, and instead of immediately recovering lane tempo, you continue forcing low-probability actions and compound the original loss.

**Not to be confused with:**
Continuing because the failed attempt creates a new favorable opportunity.

**Typical evaluation:**
Often a distinct second decision from the original failed roam.

---

### 18. Enemy Roam Not Matched or Punished

**What it is:**
The opposing mid leaves lane and you neither follow nor extract meaningful value from their absence.

**Not to be confused with:**
Unable to follow safely or choosing a better trade-off such as pushing, taking plates, securing vision, or assisting another objective.

**Typical evaluation:**
Potential missed opportunity rather than automatic mistake.

---

### 19. Blind Follow

**What it is:**
You follow the enemy mid's movement without knowing their destination, without adequate information, or without a favorable fight condition.

**Not to be confused with:**
Following because matching the rotation is strategically necessary and sufficiently safe.

**Typical evaluation:**
Mistake when you convert an enemy's unknown movement into a forced disadvantageous response.

---

### 20. Roam Into Unfavorable Numbers

**What it is:**
You enter a fight where the enemy has a numerical, positional, resource, or champion-strength advantage that should have discouraged the rotation.

**Not to be confused with:**
Joining a fight because your arrival changes the numbers or position enough to make the fight favorable.

**Typical evaluation:**
Potential mistake.

---

# III. Jungle / External-Pressure Decisions

Mid is unusually connected to jungle movement and side-lane activity; current guidance emphasizes tracking jungler position and using lane priority to affect river/jungle fights. ([Dodge.gg][2])

### 21. Ignoring Enemy Jungler Information

**What it is:**
You make an aggressive lane or map decision without accounting for relevant information about the enemy jungler.

**Not to be confused with:**
A calculated play where you accept the known jungle risk because the reward is sufficient.

**Typical evaluation:**
Mistake when the missing information was available or the risk was avoidable.

---

### 22. Playing Strongside Without Support

**What it is:**
You position or pressure as though allied support is nearby when your relevant teammates cannot actually respond.

**Not to be confused with:**
Intentional weak-information pressure when the enemy cannot punish it.

**Typical evaluation:**
Potential positioning/decision error.

---

### 23. Abandoning Jungler Skirmish

**What it is:**
Your jungler enters a nearby contest that you could reasonably influence, but you prioritize a low-value lane activity instead.

**Not to be confused with:**
Not rotating because the wave/timing/resource cost is too high or the fight is already lost.

**Typical evaluation:**
Context-dependent.

---

### 24. Forced Jungle Fight From Bad Lane State

**What it is:**
You create or enter a jungle fight despite having a lane state that makes the rotation prohibitively expensive.

**Not to be confused with:**
A fight so valuable that sacrificing the lane is strategically justified.

**Typical evaluation:**
Trade-off decision.

---

### 25. Failure to Exploit Enemy Jungle Absence

**What it is:**
The enemy jungler is known to be elsewhere, creating an unusually safe opportunity for pressure or movement, but you fail to use it.

**Not to be confused with:**
Ignoring the opportunity because the lane state or resource state remains unfavorable.

**Typical evaluation:**
Potential missed opportunity.

---

# IV. Trading Decisions

Your definition explicitly treats detailed skill trading as optional because it requires much finer-grained state than the normal Match-V5 timeline provides. So these should be defined conceptually now but not assumed to be currently measurable.

### 26. Bad Trade on Minion Disadvantage

**What it is:**
You initiate or continue a trade while the enemy has a sufficiently stronger minion advantage for the expected exchange to be unfavorable.

**Not to be confused with:**
Taking the trade because the opponent is sufficiently vulnerable or because the trade itself is necessary to survive the wave.

**Typical evaluation:**
Potential mistake.

---

### 27. Trade Without Resource Advantage

**What it is:**
You engage while having a significant HP, mana, cooldown, summoner-spell, or item disadvantage.

**Not to be confused with:**
A short trade designed specifically to force the enemy's remaining resources or create a later advantage.

**Typical evaluation:**
Potential mistake.

---

### 28. Missing Advantage Window

**What it is:**
You have a temporary advantage—level, item, resource, cooldown, summoner spell, positioning—but fail to use it before it disappears.

**Not to be confused with:**
Preserving the advantage because using it carries excessive risk.

**Typical evaluation:**
Potential missed opportunity.

---

### 29. Extended Trade After Win Condition Is Complete

**What it is:**
You already achieved the objective of the trade, such as forcing the opponent away, winning a health exchange, or burning a resource, but continue fighting and create unnecessary risk.

**Not to be confused with:**
Extending because the opponent's subsequent state creates a clearly favorable all-in.

**Typical evaluation:**
Classic overextension decision.

---

### 30. Fight Without Exit Condition

**What it is:**
You enter a trade/all-in without a clear understanding of how you will disengage if the desired outcome does not occur.

**Not to be confused with:**
A deliberate all-in where the champion's kit makes retreat unnecessary or impossible because the objective is decisive.

**Typical evaluation:**
Potential mistake.

---

# V. Vision / Information Decisions

Vision should be treated as information management, not merely "did you place wards."

### 31. Blind Push

**What it is:**
You push into a dangerous lane position without sufficient information about the likely source of punishment.

**Not to be confused with:**
Intentional blind pressure where the enemy cannot realistically punish you.

**Typical evaluation:**
Potential mistake.

---

### 32. Irrelevant Ward

**What it is:**
You spend vision resources somewhere that provides little useful information relative to an upcoming decision.

**Not to be confused with:**
A defensive ward whose value is difficult to see immediately but protects a specific future action.

**Typical evaluation:**
Efficiency problem rather than automatically a mistake.

---

### 33. Missing Critical Vision Before Action

**What it is:**
You execute a roam, invade, objective rotation, or aggressive push without obtaining information that was reasonably available and important to the decision.

**Not to be confused with:**
Taking the action precisely because you know you lack information but have enough reason to accept the uncertainty.

**Typical evaluation:**
Potential information-management error.

---

### 34. Staying on a Known Dangerous Side

**What it is:**
You knowingly remain on the side of the map with insufficient vision or known enemy threat.

**Not to be confused with:**
Holding the position because leaving would surrender a more valuable resource or because assistance is arriving.

**Typical evaluation:**
Potential positioning error.

---

# VI. Recall / Item / Power-Spike Decisions

### 35. Delayed Power-Spike Recall

**What it is:**
You remain on the map despite having enough resources for a meaningful purchase, while gaining little additional value from staying.

**Not to be confused with:**
Staying to complete a wave, protect an objective, deny the enemy, or exploit a temporary lane advantage.

**Typical evaluation:**
Context-dependent.

---

### 36. Recall Before Immediate Value

**What it is:**
You recall despite having a safe opportunity to gain a substantial amount of additional lane/map value first.

**Not to be confused with:**
A defensive recall where staying creates disproportionate death or resource risk.

**Typical evaluation:**
Potentially inefficient reset.

---

### 37. Wrong Itemization for Immediate State

**What it is:**
You choose an item path that poorly addresses the current matchup, threat profile, or strategic objective.

**Not to be confused with:**
Choosing a theoretically lower-EHP/lower-DPS option because it serves a different strategic purpose.

**Typical evaluation:**
Requires matchup- and patch-aware context.

---

### 38. Delayed Power-Spike Conversion

**What it is:**
You obtain a meaningful item/level/power spike but continue playing as though your previous power state still exists, failing to seek the opportunities enabled by the spike.

**Not to be confused with:**
Using the spike defensively or saving it for an upcoming objective.

**Typical evaluation:**
Potential missed opportunity.

---

# VII. Objective Decisions

Mid's proximity to objectives makes wave timing and rotation decisions especially important. Current guides explicitly connect mid priority with objective access. ([Shok Guide][5])

### 39. Late Objective Rotation

**What it is:**
You begin moving toward an objective after the important setup/fight has already started.

**Not to be confused with:**
Remaining in lane because the objective should be intentionally conceded.

**Typical evaluation:**
Potentially costly timing error.

---

### 40. Objective Fight Without Lane Preparation

**What it is:**
You rotate to an objective while leaving a wave in a state that creates excessive immediate lane cost.

**Not to be confused with:**
A high-value emergency response where preparing the wave is impossible or less valuable than the objective.

**Typical evaluation:**
Trade-off decision.

---

### 41. Contesting an Unwinnable Objective

**What it is:**
You contest an objective despite insufficient numbers, resources, position, or information to make the contest realistically favorable.

**Not to be confused with:**
A calculated contest where the objective's value justifies a low-probability fight.

**Typical evaluation:**
Potential mistake.

---

### 42. Failure to Trade Objective

**What it is:**
The enemy takes an objective you cannot contest, but you fail to extract another meaningful resource elsewhere.

**Not to be confused with:**
Being unable to trade because no meaningful alternative exists.

**Typical evaluation:**
Potential macro error.

---

### 43. Objective Tunnel Vision

**What it is:**
You continue pursuing the objective after its strategic value has diminished or the situation has changed enough that another option is better.

**Not to be confused with:**
Finishing a high-value objective because abandoning it would produce an even worse state.

**Typical evaluation:**
Decision adaptation failure.

---

# VIII. Mid-Game Map Assignment

### 44. Wrong Side-Lane Assignment

**What it is:**
You occupy a side lane where your champion or current game state is poorly suited for the resulting pressure/risk.

**Not to be confused with:**
Taking a difficult side lane because the team composition or objective setup requires it.

**Typical evaluation:**
Requires team-state context.

---

### 45. Side-Lane With No Exit

**What it is:**
You push a side lane without a safe route back to your team or without accounting for likely enemy collapse.

**Not to be confused with:**
Deliberately drawing multiple enemies because your team is exploiting the opposite side.

**Typical evaluation:**
Potential strategic mistake.

---

### 46. Side-Lane Greed Before Objective

**What it is:**
You continue farming a side lane too long and become late to an important upcoming objective or team fight.

**Not to be confused with:**
Taking an intentional side-lane trade because your team can safely delay or contest the objective without you.

**Typical evaluation:**
Very important for later-game decision analysis.

---

### 47. Grouping When Side-Lane Value Is Higher

**What it is:**
You repeatedly group for low-value mid-map activity while a side lane offers substantially more guaranteed resources or pressure.

**Not to be confused with:**
Grouping because your champion is essential for an imminent fight or because side-lane absence would expose your team to a decisive loss.

**Typical evaluation:**
Potential macro inefficiency.

---

# IX. Positioning Decisions

### 48. Frontline Position Without Need

**What it is:**
You stand in a position where you are unnecessarily exposed to enemy engage or burst.

**Not to be confused with:**
Taking forward space deliberately to threaten the enemy and create room for teammates.

**Typical evaluation:**
Depends on threat, vision, cooldowns, and team position.

---

### 49. Too Far From the Action

**What it is:**
You position so far away that you cannot meaningfully respond to a fight or protect a teammate despite having reason to be nearby.

**Not to be confused with:**
Maintaining distance to preserve a crucial damage source or avoid unavoidable enemy engage.

**Typical evaluation:**
Potential positioning mistake.

---

### 50. Entering Fog Without a Necessary Reason

**What it is:**
You move into an area where the enemy can be present without sufficient information or strategic justification.

**Not to be confused with:**
Using fog intentionally to create pressure or ambush when the expected value justifies the risk.

**Typical evaluation:**
Potential information/positioning error.

---

# X. Objective-Cost / Trade-Off Decisions

These are particularly important because they prevent the system from labeling every lost resource as a mistake.

### 51. Correct Resource Trade

**What it is:**
You intentionally sacrifice one resource to secure a more valuable resource elsewhere.

**Examples:**

```text
lose wave → secure dragon
lose plates → kill enemy carry
lose CS → save jungler
give turret → win major fight elsewhere
```

**Not to be confused with:**
Losing the first resource without obtaining meaningful compensation.

**Typical evaluation:**
Potentially good decision.

---

### 52. Bad Resource Trade

**What it is:**
You sacrifice a meaningful resource for an outcome whose value is lower or whose probability was too poor.

**Not to be confused with:**
A failed attempt where the decision was reasonable given the information available.

**Typical evaluation:**
Requires expected-value reasoning rather than outcome-only judgment.

---

### 53. Outcome-Validated Hindsight

**What it is:**
Judging the quality of a decision solely from whether the resulting play succeeded or failed.

**Not to be confused with:**
Using outcome as one part of evaluating the decision.

**Typical evaluation:**
**Analytical error.**

This one is especially important for your system because your project explicitly wants to avoid "you died, therefore bad." 

---

# XI. Adaptation / State-Recognition Decisions

### 54. Failure to Adapt After Lane State Changes

**What it is:**
The matchup or game state changes materially, but you continue applying the same strategy that was appropriate earlier.

**Not to be confused with:**
Maintaining the same strategy because the underlying state has not actually changed.

**Typical evaluation:**
Potential strategic rigidity.

---

### 55. Ignoring Opponent's Win Condition

**What it is:**
You make decisions that directly enable the opponent's strongest path to winning the matchup or game.

**Not to be confused with:**
Accepting that win condition temporarily because preventing it costs even more.

**Typical evaluation:**
Requires matchup/domain knowledge.

---

### 56. Playing Your Champion, Not the Game State

**What it is:**
You follow a habitual champion pattern—push, roam, fight, farm, split—without adapting to the actual game.

**Not to be confused with:**
Using a champion's established identity because it genuinely matches the current state.

**Typical evaluation:**
High-value conceptual category.

---

# XII. Advantage Conversion

This is one of the most important categories for your project's "why did the numbers happen?" objective.

### 57. Lane Advantage Not Converted

**What it is:**
You establish a meaningful CS/XP/gold/health/priority advantage but fail to convert it into further pressure, resources, or map influence.

**Not to be confused with:**
Holding an advantage safely because forcing conversion would introduce unnecessary risk.

**Typical evaluation:**
Potential missed opportunity.

---

### 58. Kill With No Conversion

**What it is:**
You kill the opposing mid laner but fail to convert the resulting window into meaningful wave, plates, vision, objective, recall, or map value.

**Not to be confused with:**
Being unable to convert because the enemy respawn timing, wave state, or external threats prevent it.

**Typical evaluation:**
Useful separate category because a kill is an opportunity, not the endpoint.

---

### 59. Lead Overextension

**What it is:**
You become stronger than the opponent and use that advantage to take increasingly unnecessary risks until the lead is lost.

**Not to be confused with:**
Using a lead aggressively to deny resources and accelerate the game.

**Typical evaluation:**
Potentially one of the most important recurring-player-pattern labels.

---

# XIII. Defensive / Losing-State Decisions

### 60. Fighting to Recover a Lost Lane

**What it is:**
You repeatedly force trades or all-ins in an unfavorable lane because you are trying to immediately erase the deficit.

**Not to be confused with:**
Taking a calculated fight because the alternative is an even worse long-term state.

**Typical evaluation:**
Common losing-state error.

---

### 61. Refusing to Give Up a Resource

**What it is:**
You contest a wave, plate, objective, or position that should strategically be conceded, resulting in disproportionate risk.

**Not to be confused with:**
Contesting because the enemy cannot actually punish you or because the resource is strategically critical.

**Typical evaluation:**
Potential mistake.

---

### 62. Passive When Recovery Window Exists

**What it is:**
You are behind, but a legitimate recovery opportunity appears and you fail to take it.

**Not to be confused with:**
Playing safely because the apparent opportunity is actually unreliable.

**Typical evaluation:**
Potential missed opportunity.

---

# XIV. Information / Uncertainty Decisions

These deserve their own category because later you want the system to reason about **what the player could reasonably have known**, not just what the replay reveals retrospectively.

### 63. Information Ignored

**What it is:**
Relevant information was available to the player—for example enemy position, missing summoner spell, wave condition, or objective timing—but the subsequent decision appears inconsistent with it.

**Not to be confused with:**
Information that existed in the game but was not reasonably available to the player.

**Typical evaluation:**
Very valuable future category.

---

### 64. Reasonable Decision Under Uncertainty

**What it is:**
The player chooses an action that carries risk, but the information available at the time reasonably supported that decision.

**Not to be confused with:**
A lucky outcome from an objectively unsupported decision.

**Typical evaluation:**
Positive/neutral label that protects the system from hindsight bias.

---

### 65. Information-Deficit Decision

**What it is:**
The player makes a decision in an information-poor situation where multiple outcomes were plausible.

**Not to be confused with:**
A decision where the necessary information was clearly available but ignored.

**Typical evaluation:**
Usually should reduce confidence in a negative verdict.

---

# XV. Meta-Decisions

These are not individual in-game actions, but recurring behavioral patterns that could become particularly useful in your Season 16 analysis.

### 66. Habitual Push

**What it is:**
The player repeatedly pushes waves regardless of matchup or map context.

**Not to be confused with:**
A champion/game plan that genuinely benefits from frequent pushing.

---

### 67. Habitual Roam

**What it is:**
The player repeatedly leaves lane because roaming is part of their normal pattern, even when the current opportunity is poor.

**Not to be confused with:**
A consistently effective roaming identity supported by appropriate wave setup.

---

### 68. Habitual Fight

**What it is:**
The player repeatedly takes skirmishes simply because combat is available rather than because the state makes fighting valuable.

**Not to be confused with:**
A champion/game plan built around consistently contesting fights.

---

### 69. Farm-First Overinvestment

**What it is:**
The player repeatedly prioritizes CS even when the marginal farm value is lower than an available map opportunity.

**Not to be confused with:**
A deliberate scaling strategy where farming is the correct response.

---

### 70. Action Bias

**What it is:**
The player repeatedly feels compelled to make something happen even when waiting, holding wave, resetting, or conceding is strategically better.

**Not to be confused with:**
A high-agency playstyle that deliberately accepts calculated risk.

---

# The catalogue's deeper structure

I would actually organize these into a hierarchy rather than leaving 70 flat entries:

```text
MID-LANER DECISION
│
├── Lane / Wave
│   ├── farm
│   ├── push
│   ├── freeze
│   ├── crash
│   ├── reset
│   └── wave sacrifice
│
├── Combat
│   ├── trade
│   ├── all-in
│   ├── skirmish
│   └── disengage
│
├── Movement
│   ├── roam
│   ├── follow
│   ├── rotate
│   └── return
│
├── Information
│   ├── vision
│   ├── enemy tracking
│   ├── uncertainty
│   └── information usage
│
├── Objectives
│   ├── contest
│   ├── concede
│   ├── trade
│   └── setup
│
├── Resources
│   ├── gold
│   ├── XP
│   ├── HP/mana
│   └── cooldowns
│
├── Positioning
│   ├── lane
│   ├── river
│   ├── jungle
│   └── teamfight
│
└── Adaptation
    ├── recognize state
    ├── change plan
    ├── convert advantage
    └── recover deficit
```

That hierarchy is more important than the exact number of labels.

---

# One major recommendation: don't make "Mistake" the catalogue's primary unit

I think your example points toward something better.

Instead of:

```text
GREEDY FARM, LATE TO SKIRMISH
```

being simply:

```text
mistake = true
```

I'd make the underlying record conceptually:

```text
Decision:
    FARM

Context:
    nearby skirmish

Alternative:
    ROTATE

Trade-off:
    wave value vs skirmish value

Observed choice:
    CONTINUE_FARMING

Outcome:
    arrived late

Evaluation:
    BAD_TRADEOFF

Reason:
    skirmish value > retained lane value

Confidence:
    ...
```

Then **"Greedy Farm, Late to Early Skirmish"** becomes a human-readable label for that pattern.

This is much more powerful because the same action can be good or bad.

```text
CONTINUE FARMING
```

can produce:

```text
GOOD RESOURCE TRADE
```

or:

```text
GREEDY FARM, LATE TO SKIRMISH
```

depending on context.

That is exactly the kind of distinction your project needs.

Riot's own explanation of the mid-lane changes supports this general framing: roaming has an opportunity cost because synchronized waves make the lane resources you leave behind matter. ([League of Legends][1])

---

# What I would put into your domain documentation

I would **not immediately put all 70 entries into `wave-mechanics.md` or `roaming-and-map-movement.md`**.

This deserves its own document:

```text
docs/domain/
└── mid-laner-decision-catalogue.md
```

Then:

```text
wave-mechanics.md
    → what waves do

roaming-and-map-movement.md
    → what roaming/movement means

lane-phase.md
    → lane/trade/resource concepts

mid-laner-decision-catalogue.md
    → recognizable decisions and decision patterns
```

The catalogue should link to the underlying mechanic rather than redefining it.

For example:

```markdown
## Greedy Farm, Late to Early Skirmish

See:
- wave mechanics → wave opportunity cost
- roaming → rotation conditions
- objectives → fight value

Decision pattern:
...
```

That preserves your **one canonical home per fact** rule.

---

## Most important next step

I would **not yet treat the 70 labels above as the final taxonomy**. They are a research-backed **candidate catalogue**.

The next useful step is to turn this into a more rigorous specification with columns like:

| Field                     | Purpose                                 |
| ------------------------- | --------------------------------------- |
| `decision_id`             | Stable identifier                       |
| `name`                    | Human-readable label                    |
| `category`                | Wave / Roam / Combat / Objective / etc. |
| `decision_type`           | What action/choice it describes         |
| `preconditions`           | What must be true                       |
| `alternative`             | What another reasonable choice was      |
| `cost`                    | What was sacrificed                     |
| `potential_payoff`        | What could be gained                    |
| `bad_pattern`             | When it becomes a mistake               |
| `not_confused_with`       | Similar but legitimate decisions        |
| `required_game_knowledge` | Domain concepts needed                  |
| `required_data`           | Data needed to evaluate it              |
| `evaluation_notes`        | How humans should judge it              |
| `patch_sensitive`         | Yes/No                                  |
| `status`                  | Candidate / verified / needs research   |

That would turn the catalogue from a list of coaching tips into something your eventual analysis engine can actually reason over.

And importantly, **that catalogue itself should remain domain knowledge rather than pretending to be an implementation spec**. The current project architecture already gives us exactly the separation needed: domain documents define what the concepts mean, `DATA_AUDIT` determines what the data can observe, and `ANALYSIS_SPEC` later defines how those concepts are operationalized.

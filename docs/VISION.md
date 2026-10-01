# LoL Mid-Lane Analytics Project — Project Definition and Starting Direction

> **L3 Archive** · the user's 2026-08-29 project definition, kept word for word below · owner: the user · update: never; changes go into `.claude/CLAUDE.md` or `ROADMAP.md`
> Where this file and `.claude/CLAUDE.md` differ, CLAUDE.md wins. For example, building the dashboard scaffold first was decided on 2026-10-01.

## 1. Project Purpose

The project is a **personal mid-lane performance analysis and improvement system for League of Legends**.

The primary purpose is not to build a generic LoL statistics dashboard, a champion database, or a prediction system.

The project should answer:

> **"Given one of my games, what happened in my mid lane, what decisions did I make, how good were those decisions, and what I could be done differently?"**

The secondary purpose is:

> **"Across my Season 16 mid-lane games, what are my actual strengths, weaknesses, champion tendencies, and recurring patterns?"**

The long-term purpose is:

> **"How does my play compare with high-level professional mid laners in equivalent matchups and situations, and what can I learn from those differences?"**

The project should therefore prioritize **usefulness for one player's actual improvement** over generic statistics or portfolio-oriented complexity.

---

# 2. Core Scope

The project has three major levels.

## Level 1 — Single-Match Analysis

This is the **core of the project and must be implemented first**.

The system evaluates one completed match, with the analysis restricted to the player's **mid-lane experience and decisions**.

The analysis should cover:

### 2.1 Overall performance

Evaluate performance throughout the game, including:

- CS performance
- CS/min
- XP and level progression
- gold progression
- gold/min
- damage dealt
- damage taken
- deaths and death timing
- KDA
- item progression
- build path
- rune choice
- skill order
- resource usage where data is available
- laning performance
- transition from laning phase into mid game
- side-laning/grouping
- team fighting
- skirmishing
- positioning
- objective participation
- roaming

The goal is not simply to report numbers.

The system should attempt to explain **why the numbers occurred**.

For example:

> "You were down 14 CS at 10:00."

is less useful than:

> "You lost approximately one wave during your first recall cycle, then remained in lane while the opposing mid had a completed component advantage."

The latter is closer to the project's intended value.

---

## 3. Laning-Phase Analysis

The primary laning window is:

**Game start → 14:00**

The system should attempt to reconstruct the state of the mid lane throughout this period.

Important dimensions include:

### 3.1 CSing

Compare the player and opponent on:

- CS
- CS/min
- CS differential
- missed opportunities
- CS timing
- wave-by-wave CS outcomes where possible

### 3.2 XP

Compare:

- XP
- level timing
- level advantages
- missed XP
- level-up timing relative to trades and fights

Important situations include:

- first level-2 timing
- level-3 timing
- level-6 timing
- level advantages during fights
- losing XP while roaming or recalling

### 3.3 Gold

Compare:

- total gold
- gold differential
- gold/min
- recall timing
- item completion timing
- component advantages
- purchase efficiency

The system should distinguish between:

- gold lead caused by CS
- gold lead caused by kills
- gold lead caused by plates
- gold lead caused by roaming
- gold lead caused by opponent mistakes

rather than treating all gold differences equally.

### 3.4 Wave State

Where the underlying data permits, analyze:

- neutral wave
- push
- slow push
- fast push
- crash
- bounce
- freeze
- wave accumulation
- wave timing relative to recalls
- wave timing relative to roams
- wave timing relative to objectives

The system must clearly distinguish:

**observed data**, **derived state**, and **assumed/reconstructed state**.

It must never present a reconstructed wave state as if Riot directly supplied it.

### 3.5 Trading

Trading analysis is **optional for the initial implementation** because it requires considerably more state information, also need to track those information continuos and comprehensively (might be frame-by-frame).

Potential inputs include:

- player HP
- opponent HP
- current/max mana or other resources where relevant
- level
- CS
- XP
- wave state
- cooldowns where obtainable
- summoner spells
- items
- champion matchup
- jungle pressure
- nearby support/jungle influence
- damage taken
- damage dealt
- positional context

The eventual objective is to analyze questions such as:

> Was this trade favorable?

> Was the trade necessary?

> Did the player trade while having a wave advantage?

> Was the opponent vulnerable because of cooldown/resource state?

> Did an external player enter the lane and invalidate what otherwise would have been a good trade?

This capability should **not** block the initial version of the project.

---

# 4. Decision-Making Analysis

This is more important than producing a large statistics table.

The system should identify significant decisions and evaluate their context.

Examples:

### Laning decisions

- trade
- all-in
- push
- hold wave
- recall
- stay in lane
- contest CS
- give CS
- contest level advantage
- concede wave
- roam
- follow roam
- punish opponent roam
- ward
- deny vision

### Mid-game decisions

- roam
- side-lane assignment
- grouping
- objective contest
- objective concession
- reset/recall
- jungle interaction
- skirmish participation
- team fight positioning
- pushing side lane
- abandoning side lane
- entering fog
- contesting vision

The system should ultimately answer:

> **What decision was available?**

> **What decision did I make?**

> **What information/state existed at that moment?**

> **What was the likely consequence?**

> **Was the decision reasonable given the available information?**

The project should avoid simplistic hindsight such as:

> "You died, therefore the decision was bad."

A bad outcome does not automatically imply a bad decision.

---

# 5. External Lane Pressure

A major requirement is to avoid analyzing the mid laner in isolation.

The system should detect or account for situations where another player affects mid lane.

Examples:

- enemy jungle gank
- allied jungle assistance
- support roam
- enemy support roam
- top/bot roam into mid
- objective pressure forcing movement
- jungle skirmish affecting mid priority

This distinction is important because:

> A mid-lane outcome can be caused by a mid-lane decision, or by external pressure.

Therefore the analysis should attempt to distinguish:

**self-caused state**

from

**externally influenced state**.

This becomes especially important for evaluating trades, deaths, wave decisions, and lane pressure.

---

# 6. Single-Match Output

The final single-match report should not merely be a collection of charts.

It should have a hierarchy such as:

### Match Summary

Overall performance and major conclusions.

### Laning Phase

A chronological reconstruction of the first 14 minutes.

### Major Decisions

A timeline of important decisions and their context.

### Mistakes

High-confidence mistakes supported by data.

### Good Decisions

Important decisions that should be reinforced.

### Recurring Patterns

Patterns observed within the match.

### Improvement Recommendations

Concrete actions the player can apply in future games.

The system should distinguish between:

- **fact**
- **derived observation**
- **interpretation**
- **recommendation**
- **uncertainty**

---

# 7. Level 2 — Season-Level Player Statistics

Once single-match analysis is reliable, the system should analyze the player's complete **Season 16  mid-lane dataset ****(Season 16 is the current season, not the fixed one)**.

The analysis should include:

### Basic statistics

- number of games
- wins
- losses
- win rate
- average game duration
- average KDA
- average CS/min
- average gold/min
- average damage
- average damage taken

### Champion pool

- champions played
- games per champion
- win rate per champion
- average performance per champion
- matchup frequency
- champion-specific strengths/weaknesses

### Champion performance

"Best champion" should **not** simply mean highest win rate.

The project should account for:

- games played
- matchup diversity
- laning performance
- CS/min
- CS differential
- gold/min
- gold differential
- damage dealt
- damage taken
- game outcome
- strength of opponents/matchups where possible

The system should prevent a champion with:

> 2 games, 100% win rate

from automatically being considered better than:

> 40 games, 62% win rate

This requires a clearly defined weighting methodology.

---

# 8. Matchup-Level Statistics

The next layer should aggregate performance by matchup.

For example:

> Player: Ahri\
> Opponent: LeBlanc

Aggregate all relevant mid-lane games and measure:

- games
- wins
- losses
- win rate
- CS difference @ 10
- CS difference @ 14
- gold difference @ 10
- gold difference @ 14
- XP difference
- first recall timing
- first death timing
- kill participation
- damage
- laning pressure
- common build paths

The project should eventually be able to answer:

> "Against which matchup am I consistently losing lane even when the game outcome varies?"

That is more valuable than simply asking:

> "What is my win rate against LeBlanc?"

---

# 9. Level 3 — Pro Comparison / "PROmoted"

The name is temporary.

This is the long-term scaling layer.

The goal is to compare the player's decisions with high-level professional mid laners in equivalent situations.

Initial target players:

- Faker
- Chovy
- ShowMaker
- Bdd
- Zeka
- Caps
- Knight
- Rookie

The comparison should be **matchup-specific and situation-specific**, rather than simply comparing aggregate statistics.

For a given matchup, collect a sufficiently large sample of professional games and analyze:

### Pre-game

- champion matchup
- runes
- summoners
- skill setup

### Early lane

- level-up decisions
- first wave interaction
- first recall
- wave management
- trading patterns
- CS prioritization

### Mid game

- roam timing
- reset timing
- objective movement
- side-laning
- grouping
- itemization
- fight selection
- positioning

The system should attempt to answer:

> "What do elite players consistently do in this matchup?"

and then:

> "How does my behavior differ?"

The final output should not simply say:

> "Chovy has better CS."

It should attempt to identify the underlying decision pattern:

> "In this matchup, professional players tend to preserve the wave before the first reset, whereas you frequently clear the wave immediately and reveal yourself on the map."

---

# 10. Professional Comparison Must Be Patch-Aware

This is a fundamental requirement.

Professional examples cannot simply be treated as timeless "correct gameplay."

League changes continuously through champion buffs/nerfs, item changes, system changes, and other balance adjustments. Riot's official patch history demonstrates this ongoing change.

Therefore every professional analysis should carry:

- patch
- date
- game version
- champion versions
- item versions
- rune versions
- relevant systemic rules

A professional game from one patch should **not automatically be treated as directly applicable** to a later patch.

The system should therefore distinguish:

### Timeless principles

Examples:

- maintain a favorable reset
- avoid unnecessary deaths
- synchronize recalls with wave states

from:

### Patch-specific conclusions

Examples:

- exact item breakpoint
- specific champion ability interaction
- wave timing affected by a system change
- matchup-specific optimal build

---

# 11. Data Architecture Principle

The project should maintain a clear distinction between:

### Raw facts

What Riot or another legitimate source actually provides.

### Derived facts

Values calculated from raw data.

### Domain interpretation

Human/game-knowledge interpretation of those facts.

### Recommendations

Actions suggested to the player.

For example:

```text
RAW
player CS at 10:00 = 72
opponent CS at 10:00 = 64

DERIVED
CS differential = +8

INTERPRETATION
player achieved a meaningful early CS advantage

CONTEXT
opponent spent 35 seconds away from lane

RECOMMENDATION
evaluate whether the player converted the temporary lane advantage
into a useful reset/roam/objective action
```

This separation is mandatory because the project is intended to explain decisions, not merely generate numbers.

---

# 12. Data Provenance and Confidence

Every important analytical field should have provenance.

For example:

```text
source = Riot Match-V5
confidence = high
```

or:

```text
source = derived from Match-V5
confidence = high
```

or:

```text
source = manually annotated gameplay
confidence = high
```

or:

```text
source = reconstructed wave state
confidence = medium
```

The project must never silently convert an approximation into a fact.

---

# 13. Patch and Version Management

Every dataset should be associated with a patch/version.

At minimum:

```text
match_id
game_datetime
patch
region
queue
player
champion
opponent_champion
```

For derived mechanics, store the relevant ruleset/version as well.

This is necessary because the meaning of historical data can change when the underlying game rules change.

---

# 14. How to Start

Do NOT start by trying to solve the entire project.

Start in this order:

## Phase 0 — Data Audit

Before implementing analysis, determine exactly what data is available.

For each desired metric, record:

```text
field
source
exact API path
raw / derived
availability
resolution
limitations
patch sensitivity
```

The objective is to eliminate assumptions such as:

> "The timeline probably contains wave information."

Every important field needs a verified source.

---

# Phase 1 — Single-Match Data Contract

Choose **one match**.

Build a complete representation of everything that can currently be obtained for that match.

Do not build sophisticated analysis yet.

Produce:

```text
match metadata
participants
mid laners
timeline
events
items
runes
levels
CS
gold
XP
positions
objectives
kills/deaths
wards
turrets
```

Then explicitly mark unavailable information.

---

# Phase 2 — Basic Single-Match Analysis

Implement only high-confidence measurements first:

- laning CS
- CS/min
- gold
- XP
- deaths
- kills
- items
- damage
- damage taken
- level timings
- recall timing where reliably available
- objective participation
- roaming events where reliably derivable

The first milestone is:

> **Given one match ID, generate a trustworthy mid-lane match report.**

Not an ML system.

Not a wave simulator.

Not pro comparison.

Just a correct single-match analysis.

---

# Phase 3 — Decision Timeline

Once the basic measurements are trustworthy, create a chronological event timeline.

For example:

```text
00:00 — lane begins
01:32 — level advantage
02:14 — trade
03:01 — wave state changes
04:10 — recall
05:03 — returns to lane
06:20 — opponent roams
06:35 — player follows
08:14 — jungle pressure
09:02 — first major reset
...
```

The objective is to turn raw match data into **game situations**.

---

# Phase 4 — Wave / Lane-State Reconstruction

Only after the available data has been fully audited should the project attempt detailed wave analysis.

For every wave-related field, explicitly classify it as:

```text
A = directly available
B = deterministically derived
C = unavailable
```

If C-level information is required, identify a separate legitimate acquisition method instead of inventing the field.

Wave state should therefore be treated as a **data-acquisition problem first**, and an analysis problem second.

---

# Phase 5 — Decision Evaluation

Once enough state exists, define rules for evaluating decisions.

For example:

```text
Situation
→ available information
→ player's action
→ expected objective
→ consequence
→ evaluation
```

The rules should be explicit and inspectable.

Avoid opaque "good/bad" scores without explaining why.

---

# Phase 6 — Season-Level Aggregation

After single-match analysis is trustworthy, aggregate the same underlying facts across Season 16.

This prevents the season dashboard from becoming a separate data system with conflicting definitions.

Single-match metrics and season metrics should share the same canonical definitions.

---

# Phase 7 — Pro Comparison

Only after the player-analysis layer is stable should professional comparison begin.

The first version should probably focus on **one matchup at a time**, not all matchups.

For example:

```text
My champion
+
Opponent champion
+
Patch range
+
Professional sample
```

Then compare:

- lane setup
- early wave handling
- recall
- itemization
- skill order
- movement
- roam timing
- objective decisions
- side-lane behavior

The system should explicitly separate:

```text
What professionals did
from
Why they may have done it
from
Whether the same decision is appropriate for the user's situation
```

---

# 15. Definition of Success

The project is successful when it can take a single completed match and produce something substantially more useful than a normal statistics site.

The ideal output is not:

> "You had 7.4 CS/min."

It is closer to:

> "You were +9 CS at 10:00, but the advantage came primarily from the opponent's two early roams. You converted the resulting lane priority into only one meaningful reset and spent the next wave contesting an unnecessary trade. Your strongest improvement opportunity is converting temporary lane priority into better reset timing rather than taking additional low-value trades."

The project should gradually move toward this level of explanation.

---

# 16. Non-Goals for the Beginning

Do not initially attempt to:

- analyze every champion
- analyze every lane
- analyze every game mode
- build a general LoL knowledge engine
- solve perfect wave reconstruction immediately
- analyze every professional matchup
- create a universal "best play" system
- optimize the UI before the analytical definitions are stable

The project should remain:

> **Mid-only → single-match-first → explain decisions → aggregate later → professional comparison last.**

The core principle is:

> **Build a trustworthy reconstruction of what happened before attempting to judge why it happened.**

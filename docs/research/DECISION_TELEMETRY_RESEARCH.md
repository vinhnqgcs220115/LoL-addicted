# Decision Telemetry Research

Can the PARTIAL and NOT OBSERVABLE entries in `docs/ANALYSIS_SPEC.md` be made more
actionable using Riot data sources beyond the historical Match-V5 corpus?

**Researched 2026-09-15.** Sources are labelled with the provenance scheme in section 10.
Nothing here has been used to change `ANALYSIS_SPEC.md`; recommendations are in section 11.

---

## 1. Executive summary

**The Live Client Data API does not upgrade a single PARTIAL or NOT OBSERVABLE entry to
BUILDABLE.** It is, for the specific judgements this catalogue needs, weaker than the
Match-V5 timeline the project already has.

Four findings drive that conclusion, each from Riot's own published schema:

1. **No coordinates for anybody.** `playerlist[].position` is a lane/role string
   (`"MIDDLE"`), not an x/y pair. Match-V5 gives x/y per minute for all ten players; the
   Live Client API gives none at all.
2. **`allPlayers` carries no health, no mana, no gold.** Only `activePlayer` exposes
   `championStats` and `currentGold`. **Enemy resource state is never available**, at any
   resolution, from any documented Riot source.
3. **`/activeplayerabilities` exposes ability *levels*, not casts and not cooldowns.** The
   sample response carries `abilityLevel`, `displayName`, `id`, `rawDescription`,
   `rawDisplayName` and nothing else.
4. **`/eventdata` has eleven event types, none positional, none carrying damage** — and it
   is a strict subset of what Match-V5 already provides. No item purchases, no ward events,
   no skill level-ups, no turret plates.

**Minion-level data exists in no Riot source.** Not Match-V5, not Live Client, not the
Replay API. The single minion-related datum anywhere is the Live Client `MinionsSpawning`
event, which is one timing anchor, not wave state.

**The Replay API is a camera and video controller, not a telemetry source.** Its documented
surface is `/game`, `/playback`, `/render`, `/recording`, `/sequence` — playback seeking,
render properties, and video capture.

**The one genuine future gain is narrow but real:** polling the Live Client API while
playing would record *your own* health, mana, gold and combat stats at sub-second
resolution instead of once per minute. That improves the ability to *locate* a trade in
time. It does not supply enemy state, casts, or cooldowns, so it cannot *evaluate* one.

**Therefore wave state and trading remain human-review problems.** Both are visible to a
person watching a replay and reachable by manual annotation. Neither is reachable as
structured Riot telemetry, historically or in future.

---

## 2. Riot source inventory

### 2.1 Match-V5 — `OFFICIAL_DOCUMENTED`, historical

The project backbone. Capabilities are measured empirically over the whole corpus in
`docs/DATA_AUDIT.md` rather than taken from documentation.

- Per-minute participant frames for all ten players: position, gold, current gold, CS,
  jungle CS, XP, level, `championStats` (health, mana, armour, MR, AD, AP, move speed) and
  `damageStats` split physical/magic/true including `totalDamageDoneToChampions`.
  Measured presence: 100%, zero nulls, corpus-wide.
- Twenty event types at millisecond timestamps. Five carry position: `CHAMPION_KILL`,
  `CHAMPION_SPECIAL_KILL`, `BUILDING_KILL`, `ELITE_MONSTER_KILL`,
  `TURRET_PLATE_DESTROYED`.
- `CHAMPION_KILL` carries `victimDamageReceived` (100% of kills) and `victimDamageDealt`
  (92.8%; absence is semantic — the victim dealt nothing) with per-source attribution:
  `participantId`, `type`, `spellName`, `spellSlot`, and a physical/magic/true split.
- **Frame interval is 60000 ms on 825 of 825 matches.** Uniform, measured.

Limitations, measured: no minion data of any kind; no ability casts; no cooldowns;
`WARD_PLACED` carries `creatorId`, `timestamp`, `type`, `wardType` and **no position**; no
non-lethal damage as discrete events; no visibility state; no recall event.

### 2.2 Live Client Data API — `OFFICIAL_DOCUMENTED`, live-only, local

Base `https://127.0.0.1:2999/liveclientdata/`. Runs on the player's own machine during a
game. **Not a historical source** — it cannot be applied to any game already in
`data/raw/`.

Documented endpoints: `/allgamedata`, `/activeplayer`, `/activeplayername`,
`/activeplayerabilities`, `/activeplayerrunes`, `/playerlist`, `/playerscores`,
`/playersummonerspells`, `/playermainrunes`, `/playeritems`, `/eventdata`, `/gamestats`.

**What it gives about the active player only:**
`activePlayer.currentGold`, `activePlayer.level`, `activePlayer.fullRunes`, and
`activePlayer.championStats` — `currentHealth`, `maxHealth`, `resourceValue`,
`resourceMax`, `resourceType`, `attackDamage`, `abilityPower`, `armor`, `magicResist`,
`moveSpeed`, `abilityHaste`, `cooldownReduction`, `attackSpeed`, `critChance`, penetration
and lethality values, `healthRegenRate`, `resourceRegenRate`, `lifeSteal`, `spellVamp`,
`tenacity`, `attackRange`.

**What it gives about every player** (`playerlist[]` / `allPlayers[]`): `championName`,
`rawChampionName`, `isBot`, `isDead`, `respawnTimer`, `items[]`, `level`, `position`,
`runes`, `scores` (`assists`, `creepScore`, `deaths`, `kills`, `wardScore`), `skinID`,
`summonerSpells`, `team`, `riotId`.

**Critical limitations, from the published schema:**

- `position` is a **lane/role string**, e.g. `"MIDDLE"`. **No x/y coordinates exist for any
  player.**
- `allPlayers` entries carry **no health, no mana, no gold**. Enemy resource state is
  unavailable.
- `/activeplayerabilities` carries `abilityLevel` per slot. **No cooldown values, no cast
  events.**
- `/eventdata` events carry `EventID`, `EventName`, `EventTime` plus a few per-type fields.
  The complete documented set is: `GameStart`, `MinionsSpawning`, `FirstBrick`,
  `TurretKilled`, `InhibKilled`, `DragonKill`, `HeraldKill`, `BaronKill`, `ChampionKill`,
  `Multikill`, `Ace`. Participants are identified by **name string**, not participant id.
  **No event carries a position. No event carries damage.**
- No ward events, no item-purchase events, no skill-level-up events, no turret plates.

**Provenance conflict, recorded deliberately.** A third-party article
(`buildzcrank.com`, `THIRD_PARTY`) states the Live Client Data API exposes "ability
cooldowns." Riot's own sample response for `/activeplayerabilities` does not contain any
cooldown field. **The official schema governs.** If cooldown state matters later, it needs
the empirical test in section 9, not a citation to a blog.

**Support status.** Riot documents this API on the Developer Portal. The separate *League
Client* (LCU) API is explicitly unsupported for third-party use; these are different
surfaces and should not be conflated. Riot policy also states products "must not use or
incorporate information not present in the game client that would give players a
competitive edge" — relevant to any live overlay, not to post-game analysis of one's own
recorded data.

### 2.3 Replay API — `OFFICIAL_DOCUMENTED`, local, not telemetry

Base `https://127.0.0.1:2999/replay/`. Documented endpoints: `/game` (client process
info), `/playback` (GET/POST pause state and seek time), `/render` (GET/POST render
properties), `/recording` (GET/POST video capture with codec and filepath), `/sequence`
(GET/POST keyframe sequences).

Riot's page describes these behaviourally and **does not publish field schemas** for
`/render`, `/playback` or `/sequence`. Treat any specific render field as `UNKNOWN` until
tested.

**It is a camera and video controller.** No endpoint returns positions, minions, wards,
damage, casts, or visibility state. It can drive the client to *render* a moment — and a
replay renders without fog of war — but that produces **pixels for a human**, not
structured data. This is the distinction the project must hold: replay-visible ≠ Replay API
field.

Its legitimate value here is **automating human review**: seek to a timestamp, record a
clip. That makes a manual-annotation workflow cheap, which matters for wave and trading.

### 2.4 Data Dragon — `OFFICIAL_DOCUMENTED`, static

Patch-versioned champion, item, spell and rune data plus assets. Already used by the
project. Supplies item costs and ability metadata for interpreting purchases and skill
order. Contains no match telemetry.

---

## 3. Decision coverage matrix

`M5` = historical Match-V5. `LCD` = Live Client Data (future games only). `RPL` =
replay/video for human viewing. `MAN` = manual annotation.

| # | Decision | M5 | LCD | RPL | MAN | Final status | Missing input |
|---|---|---|---|---|---|---|---|
| 2 | Abandoning Valuable Wave for Low-Value Action | partial | no gain | yes | yes | PARTIAL | wave state |
| 3 | Shove Without a Purpose | partial | no gain | yes | yes | PARTIAL | wave state |
| 4 | Roam Without Wave Setup | partial | no gain | yes | yes | PARTIAL | wave state |
| 6 | Missed Crash | no | no | yes | yes | REPLAY_MANUAL_ONLY | minion positions |
| 7 | Unnecessary Crash | no | no | yes | yes | REPLAY_MANUAL_ONLY | minion positions |
| 8 | Failed Freeze Maintenance | no | no | yes | yes | REPLAY_MANUAL_ONLY | minion positions |
| 9 | Refusing to Break Freeze | no | no | yes | yes | REPLAY_MANUAL_ONLY | minion positions |
| 10 | Poor Reset Timing | partial | minor gain | yes | yes | PARTIAL | wave state |
| 11 | Greedy Stay for One More Wave | partial | minor gain | yes | yes | PARTIAL | wave state, intent |
| 12 | Wrong Wave Investment | no | minor gain | yes | yes | REPLAY_MANUAL_ONLY | cast targets |
| 13 | No-Roam When High-Value Window | partial | no gain | yes | yes | PARTIAL | domain rule |
| 14 | Low-Probability Roam | partial | no gain | yes | yes | PARTIAL | domain rule |
| 15 | Wrong Roam Target | partial | no gain | yes | yes | PARTIAL | domain rule |
| 19 | Blind Follow | partial | no gain | yes | yes | PARTIAL (rename) | vision state |
| 21 | Ignoring Enemy Jungler Information | partial | no gain | yes | yes | PARTIAL (rename) | vision state |
| 24 | Forced Jungle Fight From Bad Lane State | partial | no gain | yes | yes | PARTIAL | wave state |
| 25 | Failure to Exploit Enemy Jungle Absence | partial | no gain | yes | yes | PARTIAL | domain rule |
| 26 | Bad Trade on Minion Disadvantage | no | no | yes | yes | REPLAY_MANUAL_ONLY | minions, casts |
| 27 | Trade Without Resource Advantage | no | partial gain | yes | yes | REPLAY_MANUAL_ONLY | enemy HP/mana |
| 28 | Missing Advantage Window | no | no | yes | yes | REPLAY_MANUAL_ONLY | cooldowns, summoners |
| 29 | Extended Trade After Win Condition | no | partial gain | yes | yes | REPLAY_MANUAL_ONLY | enemy HP, casts |
| 30 | Fight Without Exit Condition | no | no | yes | yes | REPLAY_MANUAL_ONLY | cooldowns, intent |
| 31 | Blind Push | partial | no gain | yes | yes | PARTIAL (rename) | vision state |
| 34 | Staying on a Known Dangerous Side | partial | no gain | yes | yes | PARTIAL (rename) | vision state |
| 36 | Recall Before Immediate Value | partial | minor gain | yes | yes | PARTIAL | wave state |
| 38 | Delayed Power-Spike Conversion | partial | no gain | yes | yes | PARTIAL | domain rule |
| 40 | Objective Fight Without Lane Preparation | partial | no gain | yes | yes | PARTIAL | wave state |
| 43 | Objective Tunnel Vision | partial | no gain | yes | yes | PARTIAL | domain rule |

**Zero entries change to BUILDABLE.** Twelve move from the undifferentiated
`NOT OBSERVABLE` label to `REPLAY_MANUAL_ONLY`, which is a more accurate name for the same
availability, not an upgrade.

The `Missing input` column separates three genuinely different blockers, which the current
single `NOT OBSERVABLE` label hides:

- **wave state / minions** — no source at all; replay-visual only
- **vision state** — no source at all; *and not recoverable from replay either*, because a
  replay shows what happened, not what the player could see at the time
- **domain rule** — the data exists; what is missing is a threshold the player must define

That third group is important: entries 13, 14, 15, 25, 38, 43 are **not blocked by
telemetry**. They are blocked by an undefined domain rule. Those are the cheapest to
unblock and they require no new data source at all.

---

## 4. Wave-state investigation

**Is minion position available?** No. Not in Match-V5 (measured over the whole corpus, zero
minion paths in `docs/data_audit.json`), not in the Live Client Data API (no minion object
in any documented endpoint), not in the Replay API (no telemetry endpoints at all).

**Is minion state available?** No. The only minion-related datum in any Riot source is the
Live Client `MinionsSpawning` event — a single wave-timing anchor with no composition, no
position, no per-wave tracking.

**Can wave state be reconstructed reliably?** No, and the temporal resolution point is
independent of the data point. A wave crosses the lane in roughly 30 seconds. The Match-V5
frame interval is 60 seconds. Even if minion positions existed at frame resolution, a full
push-and-bounce cycle could occur invisibly between two consecutive frames. **Wave state
fails on both axes — the entity is absent and the sampling rate is too coarse.**

**Weak proxies that exist, and what they are not.** CS deltas per minute, gold rate,
position relative to static tower coordinates, and time since last CS are all observable.
They correlate loosely with wave behaviour. **None of them observes a wave.** A player
gaining 14 CS in one minute may have crashed a stacked wave, or cleared two normal waves
under tower, or taken a jungle camp. The proxy cannot separate these. Any use must be
labelled a weak proxy with the ambiguity named, per the project's existing PARTIAL rule.

**Strongest defensible approach:** treat wave state as a **human-annotation input**.
Automatic analysis identifies a candidate minute; a person opens the replay at that
timestamp and records the wave state as an annotation. The Replay API's `/playback` seek
and `/recording` endpoints make that workflow cheap to automate — the *navigation* is
automatable even though the *observation* is not.

---

## 5. Trading investigation

| Required input | Match-V5 | Live Client Data | Verdict |
|---|---|---|---|
| Non-lethal damage events | absent — `victimDamageReceived` exists only on `CHAMPION_KILL` | absent — no damage in any event | **No source** |
| Ability cast events | absent | absent — `/activeplayerabilities` is levels only | **No source** |
| Cooldown state | absent | **not established** — no cooldown field in the official sample; a third-party claim conflicts and is not authoritative | **NOT ESTABLISHED**, needs the section 9 test |
| Own resource state at trade instant | 60s frames only | **available at polling frequency** via `activePlayer.championStats` | **Live-only gain** |
| Enemy resource state | 60s frames only | **absent** — `allPlayers` has no health or mana | **Regression; M5 is better** |
| Summoner availability over time | which spells only | which spells only | **No source** |
| Combat sequencing | kill events only | `ChampionKill` events only, by name, no position | **No source** |
| Target interactions | kill attribution only | absent | **No source** |

**Conclusion.** Live Client Data does not solve trading. It improves exactly one input —
the active player's own resource curve — from 60-second to sub-second resolution. That is
enough to **detect and time** a trade (a health drop of 300 over 400 ms), and not remotely
enough to **evaluate** one, because the opponent's health, both players' cooldowns, and
every ability cast remain absent.

Note the asymmetry: for enemy resource state, **Match-V5 is strictly better than the Live
Client API**, because the 60-second frame at least contains enemy health. Adopting the Live
Client API as a trading source would lose information.

Replay and manual annotation remain the only route to per-trade evaluation.

---

## 6. Vision and ward investigation

Four distinct concepts that must never collapse into one another:

| Concept | Availability |
|---|---|
| **Ward placement** — that a ward was placed, by whom, when, what type | Match-V5 `WARD_PLACED`: `creatorId`, `timestamp`, `type`, `wardType`. Measured 167,420 occurrences, 100% present |
| **Ward location** — where the ward was | **No source.** `WARD_PLACED` carries no position. Live Client has no ward events at all, only a `wardScore` aggregate |
| **Vision state** — what area was lit for a team at time t | **No source in any Riot API** |
| **Player knowledge** — what the player actually saw and registered | **Not observable in principle**, and *not recoverable from replay either* — a replay plays without fog of war, so it shows what happened, not what was visible to that player at that moment |

That last row deserves emphasis because it is the one place where replay annotation does
**not** rescue an entry. Wave state is replay-recoverable; vision state largely is not,
since the replay viewer sees more than the player did. A careful annotator can partially
reconstruct it by reasoning about ward timings and camera, but that is inference, not
observation, and should be labelled as such.

**Consequences the project must hold:**

- "A ward was placed" ≠ "the ward gave useful vision."
- "The enemy jungler was 618 units away" ≠ "the player could see the enemy jungler."
- "The enemy jungler was nearby" ≠ "the player ignored available information."

Every entry whose label contains *blind*, *known*, or *ignoring* asserts player knowledge
and is therefore currently unsupportable as worded. Section 11 recommends renaming them.

---

## 7. Historical versus future collection

### Historical corpus — games already in `data/raw/`

Match-V5 only, permanently. No later tooling can add resolution to a game already played.
Everything in `docs/DATA_AUDIT.md` is the ceiling, forever, for these games.

### Future games — if a live collector runs while playing

Adds, and only this:

- Active player's `championStats` and `currentGold` at polling frequency (sub-second)
- All players' `isDead`, `respawnTimer`, `items`, `level`, `scores` at polling frequency
- Eleven coarse game events with float timestamps

Does **not** add: any coordinates, enemy health or mana, ability casts, cooldowns, minions,
wards, vision.

**Net assessment:** the only judgement class this improves is trade *localisation* for the
player's own resource curve. Given the cost — building, running and maintaining a live
collector, plus a schema that must keep two heterogeneous sources honest — this is **not
recommended as a near-term investment**. It is worth revisiting only if per-trade timing
becomes the binding constraint after the Match-V5 layer is fully exploited.

### Replay-assisted review

Available for **both** historical and future games, subject to replay availability — Riot
replays are patch-locked and will not launch on a later client. This is a hard practical
limit: a replay must be reviewed while its patch is current. **That makes replay annotation
a rolling, perishable opportunity, not a backfill option.**

For the existing corpus spanning 15.18 to 16.17, only current-patch games remain
reviewable. Annotation cannot be applied retroactively to the historical corpus.

---

## 8. Recommended architecture

The research justifies source tiers, but a smaller set than proposed:

```text
TIER 1  HISTORICAL_RIOT        Match-V5 + Data Dragon
        Backbone. Every game. Automatic. The only tier that scales.

TIER 2  HUMAN_ANNOTATION       Replay-assisted, current-patch only
        Wave state, trade detail. Perishable. Never backfillable.

(DEFERRED)  SUPPLEMENTAL_LIVE  Live Client Data
        Justified only if trade localisation becomes binding.
        Adds no coordinates, no enemy state, no casts.
```

The proposed four-tier model collapses to two active tiers plus one deferred, because the
research shows the live tier currently buys almost nothing. Building a schema to
accommodate it now would be speculative.

**The two-tier analysis design is sound and should be preserved:**

Tier 1 detects candidate decision points automatically and reports what it can see. Where
judgement requires an unobservable input, it emits a **review target**, not a verdict:

```text
08:42 candidate decision point
  Observable: enemy jungler 618 units away; you pushed to enemy tower range;
              CS +6 that minute; no ally within 3000 units
  Missing:    wave state, vision state
  Verdict:    not justified
  Review:     08:42-09:05
```

That output is honest, useful, and shippable today. It is also the natural hand-off into
Tier 2 annotation.

---

## 9. Empirical test plan

Only needed to resolve one genuine `NOT ESTABLISHED` question: **does the Live Client Data
API expose any cooldown-like state?**

Everything else in this document is settled by Riot's published schema and does not need
testing.

**Test.** Start a Practice Tool game. Poll at 250 ms for five minutes:

```text
/liveclientdata/allgamedata
/liveclientdata/activeplayer
/liveclientdata/activeplayerabilities
/liveclientdata/playerlist
/liveclientdata/eventdata
```

Cast each ability and use a summoner spell at recorded wall-clock times. Then diff
consecutive responses and record **every JSON path that changes**.

**Specifically check whether any field tracks:** ability availability or cooldown remaining;
summoner spell availability; a cast having occurred; any per-player coordinate; any enemy
health or mana value.

**Recording rule.** Any field found this way is `OFFICIAL_OBSERVED`, never
`OFFICIAL_DOCUMENTED`. Store raw responses as evidence under `docs/research/`. An
undocumented field may change or vanish without notice and must not become load-bearing.

**Not yet run.** This test requires a running game client and is out of scope for a
research task.

---

## 10. Provenance of every claim in this document

| Label | Applies to |
|---|---|
| `OFFICIAL_DOCUMENTED` | Live Client endpoint list and sample fields; Replay API endpoint list; Data Dragon — Riot Developer Portal, `developer.riotgames.com/docs/lol`, and the published samples `static.developer.riotgames.com/docs/lol/liveclientdata_events.json` and `liveclientdata_sample.json` |
| `OFFICIAL_OBSERVED` | All Match-V5 capability claims — measured over 825 corpus pairs by `scripts/audit_raw_fields.py`, recorded in `docs/DATA_AUDIT.md` and `docs/data_audit.json`. Stronger than documentation for this purpose |
| `THIRD_PARTY` | The "Live Client exposes ability cooldowns" claim (`buildzcrank.com`). **Contradicted by the official sample. Not relied upon** |
| `DERIVED` | The coverage matrix verdicts in section 3 — reasoning over the two sources above |
| `UNKNOWN` | Replay API `/render`, `/playback`, `/sequence` field schemas — endpoints documented behaviourally, fields not published |
| `NOT ESTABLISHED` | Live Client cooldown state — see section 9 |

---

## 11. Recommended changes to `ANALYSIS_SPEC.md`

Not applied. Each is a discrete decision.

### 11.1 Add one verdict state, not five

The proposed six-state taxonomy is more than the evidence supports — `FUTURE_COLLECTABLE`
would be empty, since no entry is unblocked by live collection.

**Recommended minimal change:** split the current `NOT OBSERVABLE` into two.

```text
BUILDABLE             Historical Match-V5 is sufficient.
PARTIAL               Action observable; a load-bearing judgement input is missing.
REPLAY_MANUAL_ONLY    No structured source; a human can observe it in a replay,
                      subject to patch-locking.
NOT OBSERVABLE        No defensible source identified, including replay.
```

Twelve current `NOT OBSERVABLE` entries become `REPLAY_MANUAL_ONLY`. Vision-state entries
stay `PARTIAL` but with the rename below, because replay does not restore player knowledge.

### 11.2 Add a `Missing input` column

Section 3's matrix separates *wave state*, *vision state* and *undefined domain rule*.
These are three different problems with three different fixes and the single
`NOT OBSERVABLE` label conceals that. The six domain-rule entries (13, 14, 15, 25, 38, 43)
need no new data at all — only a threshold the player defines.

### 11.3 Rename four entries that assert player knowledge

Current wording claims something the data cannot support. Suggested reformulations keep the
observable half and name the missing half, per the project's existing PARTIAL rule:

| # | Current | Recommended |
|---|---|---|
| 19 | Blind Follow | Followed enemy mid rotation — vision state unknown |
| 21 | Ignoring Enemy Jungler Information | Acted with enemy jungler at known distance — player knowledge unknown |
| 31 | Blind Push | Pushed into exposed position with enemy proximity — visibility unknown |
| 34 | Staying on a Known Dangerous Side | Objectively exposed position |

Entry 34's rename matters most: *known* and *dangerous* are two separate claims, and the
data supports only a weak form of the second.

### 11.4 Record the source tiers from section 8

Two active tiers plus one deferred. Do not build schema for the live tier yet.

### 11.5 Do not rename inferred recall

`ITEM_PURCHASED` timestamps stay an observed purchase. Recall stays derived. Live Client
polling would not change this — it exposes no recall event either.

---

## 12. What this research did not change

- No application code, schema, collector, or dashboard was touched.
- `docs/ANALYSIS_SPEC.md` is unmodified; section 11 is a proposal.
- The catalogue entries remain `status: candidate`, unverified by the player.
- Sections VIII-XV of the catalogue remain unclassified, outside the laning scope.

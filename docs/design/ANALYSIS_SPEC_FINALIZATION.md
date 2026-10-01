# ANALYSIS_SPEC finalization proposal

Concrete changes proposed to `docs/ANALYSIS_SPEC.md`. **Not applied.** Each is a separate
decision. Rationale and full context: `docs/design/PROJECT_SYSTEM_DESIGN.html`.

---

## 1. Adopt a four-state availability model

Replace the current three states. Adds one state; does not adopt the six-state taxonomy
proposed earlier, because `FUTURE_COLLECTABLE` would be empty — the telemetry research
established that Live Client Data upgrades no entry.

```text
BUILDABLE             Historical Match-V5 supports detection and evaluation.
PARTIAL               Action observable; a load-bearing judgement input is missing.
REPLAY_MANUAL_ONLY    No structured source; a human can observe it in a replay.
                      Patch-locked and therefore perishable.
NOT_OBSERVABLE        No defensible source identified, replay included.
```

Twelve entries move from `NOT OBSERVABLE` to `REPLAY_MANUAL_ONLY`: the five wave entries
(#6, 7, 8, 9, 12), the five trading entries (#26–30), and the two ward-location entries
(#32, 33). This is a more accurate name for the same availability, not an upgrade.

Vision-state entries stay `PARTIAL` rather than moving, because a replay plays without fog
of war and therefore does not restore what the player could see.

---

## 2. Add a `missing_input` classification

The single `NOT OBSERVABLE` label conceals three different problems with three different
fixes. This is the highest-value change in this proposal.

| Class | Meaning | Fix |
|---|---|---|
| `telemetry_missing` | The entity is absent from all Riot sources | Replay annotation, or never |
| `information_state_missing` | What the player could see. Absent from telemetry **and** not recoverable from replay | None — reword the claim |
| `domain_rule_missing` | The data exists; a threshold is undefined | **User defines it. No new data needed** |

**Six entries turn out to be blocked only by a missing domain rule** — #13, #14, #15, #25,
#38, #43. They need no telemetry at all, only a number the player decides. These are the
cheapest unblocks in the catalogue and were invisible under the old single label.

---

## 3. Rename four entries that assert player knowledge

Current names claim something the data cannot support. The replacements keep the observable
half and name the missing half, consistent with the existing PARTIAL rule.

| # | Current | Recommended |
|---|---|---|
| 19 | Blind Follow | Followed enemy mid rotation — vision state unknown |
| 21 | Ignoring Enemy Jungler Information | Acted with enemy jungler at known distance — player knowledge unknown |
| 31 | Blind Push | Pushed into exposed position with enemy proximity — visibility unknown |
| 34 | Staying on a Known Dangerous Side | Objectively exposed position |

Entry 34 matters most: *known* and *dangerous* are two separate claims and the data
supports only a weak form of the second.

---

## 4. Add the Decision Record as the spec's core unit

`ANALYSIS_SPEC.md` currently classifies entries but does not define what an entry *produces*.
Add the record shape, so that availability and confidence have somewhere to live:

```text
DecisionRecord
  decision_id, match_id, t_start_ms, t_end_ms
  catalogue_entry, catalogue_version
  category, context, options, observed_choice, consequence, cost
  evaluation      good | bad | tradeoff | not_justified
  confidence      high | medium | low
  availability    BUILDABLE | PARTIAL | REPLAY_MANUAL_ONLY | NOT_OBSERVABLE
  missing_inputs[]  telemetry | information_state | domain_rule
  evidence[]      facts, each traceable to a canonical row
  rule_version, domain_version
```

`evaluation = not_justified` is what a PARTIAL or REPLAY_MANUAL_ONLY entry emits instead of
a verdict, paired with a review target timestamp range.

---

## 5. Record the source tiers

Two active tiers plus one deferred, from the telemetry research:

```text
TIER 1  HISTORICAL_RIOT    Match-V5 + Data Dragon. Backbone, every game, automatic.
TIER 2  HUMAN_ANNOTATION   Replay-assisted, current-patch only. Perishable, never backfillable.
DEFERRED  SUPPLEMENTAL_LIVE  Live Client Data. Adds no coordinates, no enemy state, no casts.
```

Do not build schema for the deferred tier.

---

## 6. Leave unchanged

- **The PARTIAL shipping rule.** A PARTIAL entry ships only with its missing half named.
  This survives intact and becomes load-bearing for the whole product.
- **Inferred recall stays inferred.** `ITEM_PURCHASED` proves a purchase. Live Client
  polling would not change this — it exposes no recall event either.
- **The observable primitives list in §1.** Measured, accurate, unchanged.
- **Catalogue entries remain `status: candidate`.** Nothing here verifies them.

---

## 7. Decisions still required from the user

1. Verify the catalogue — all 70 entries are unverified candidates. The 13 BUILDABLE ones
   are the priority, since those are what would be built first.
2. Define the six domain thresholds in §2 above.
3. Adopt or reject the four-state model and the missing-input classification.

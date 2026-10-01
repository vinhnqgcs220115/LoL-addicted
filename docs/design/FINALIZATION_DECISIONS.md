# Finalization decisions

The concise record of what is locked, what is proposed, and what is waiting on the player.

**Companions.** `PROJECT_SYSTEM_DESIGN.html` is the visual system blueprint.
`ANALYSIS_SPEC_FINALIZATION.md` is the proposed delta to `docs/ANALYSIS_SPEC.md`.
`CATALOGUE_REVIEW.md` is the per-entry review sheet.
`docs/ANALYSIS_SPEC.md` remains the operative contract until a delta is accepted.

**Status vocabulary**

```text
DECIDED                 locked; implementation may assume it
PROPOSED                recommended, not yet accepted
REQUIRES_USER_DECISION  a product or threshold call that is not mine to make
REQUIRES_DOMAIN_REVIEW  needs game knowledge to confirm
DEFERRED                deliberately out of scope, with a reason
```

Last reconciled against the repository: **2026-09-16**.

---

## 1. Reconciliation findings — blueprint versus repository

Five material discrepancies found. The first two change the plan.

| # | Finding | Effect |
|---|---|---|
| 1 | **`src/mapping.py` already implements minimap projection.** `position_to_fraction` and `add_position_marker`, bounds 0–14850, covered by `tests/test_mapping.py`. The blueprint said the map asset was unused — true, but the *projection utility is already written and tested*, and only the wiring is missing. | Map evidence (block 5) is cheaper than estimated. Reuse, do not rewrite. |
| 2 | **Objective spawn timers are empirically derivable.** Earliest observed kill across 825 games bounds spawn from above: Void Grubs 8:04, Herald 15:14, Baron 20:15, Dragon 5:24, Atakhan 20:14. | Removes a hand-maintained patch-sensitive constant from entries #39, #41, #42. Those are no longer blocked on domain review. |
| 3 | **`GAME_MECHANICS.md` documents three objectives; the corpus contains five.** Dragon and Atakhan (113 games) are absent from the domain doc. | Domain gap. <span>REQUIRES_DOMAIN_REVIEW</span> |
| 4 | **`.claude/CONTEXT.md` says "Phase 4 complete"** (dated 2026-08-12) under the *old* phase numbering, which conflicts with the roadmap here. | Stale state. Must be rewritten when P1 lands, not before. |
| 5 | **`binomial_significance`, `wilson_interval`, `classify_winrate` are pure functions** with no DB coupling. `classify_winrate` already documents that `Skill-based` is withheld pending a minimum effect size — a pre-existing unresolved user decision. | Reusable as-is. Links directly to the multiple-comparison policy below. |

### Objective timing evidence

Earliest observed kill is an **upper bound on spawn**, not a measurement of it, and this is
pooled across 24 patches. For patch-aware use it must be computed per patch. Stated that way
it is still strictly better than a hand-maintained constant, because it is re-derivable.

| Objective | Games | Earliest kill | 5th pct | Median |
|---|---|---|---|---|
| Dragon | 810 | 5:24 | 5:43 | 7:26 |
| Void Grubs (`HORDE`) | 809 | 8:04 | 8:09 | 8:31 |
| Rift Herald | 774 | 15:14 | 15:22 | 16:13 |
| Atakhan | 113 | 20:14 | 20:24 | 21:10 |
| Baron Nashor | 638 | 20:15 | 20:39 | 23:56 |

---

## 2. Product

| Decision | Status |
|---|---|
| Per-game is a **decision reconstruction**; it is the primary product | **DECIDED** |
| Per-season is a **pattern index over the same DecisionRecords**, not a parallel statistics engine | **DECIDED** |
| A season pattern that cannot drill down to real DecisionRecords is not presented as a pattern | **DECIDED** |
| Statistics are supporting context, never the headline | **DECIDED** |
| Product flow `pattern → games → game → decision → evidence` is a first-class acceptance requirement | **DECIDED** |

---

## 3. Per-game contract

| Decision | Status |
|---|---|
| Seven blocks: verdict header · lane phase 0–14 · decision timeline · key decisions · map evidence · review queue · reference stats | **DECIDED** |
| Only blocks 1–2 above the fold; block 7 collapsed by default | **DECIDED** |
| Lane phase compares against the **actual lane opponent**, never the player's own season average | **DECIDED** |
| Lane-activity proxies are labelled as proxies; wave state is never implied | **DECIDED** |
| Map layers bind to the selected timeline window; never all layers at once | **DECIDED** |
| Map rendering reuses `src/mapping.py` | **DECIDED** (finding 1) |

---

## 4. Decision model

| Decision | Status |
|---|---|
| `DecisionRecord` is the primary internal analytical contract | **DECIDED** |
| Every evidence item traceable to a canonical row; no opaque "bad decision" | **DECIDED** |
| Four availability states: `BUILDABLE` · `PARTIAL` · `REPLAY_MANUAL_ONLY` · `NOT_OBSERVABLE` | **PROPOSED** — delta to `ANALYSIS_SPEC.md` |
| Three missing-input classes: `telemetry_missing` · `information_state_missing` · `domain_rule_missing` | **PROPOSED** |
| `evaluation = not_justified` plus a review-target range replaces a verdict when a load-bearing input is absent | **PROPOSED** |
| A `PARTIAL` record ships **only** with its missing half named in the output | **DECIDED** — pre-existing rule, preserved |
| No fifth or sixth availability state; `FUTURE_COLLECTABLE` stays rejected | **DECIDED** |

---

## 5. Catalogue

| Decision | Status |
|---|---|
| All 70 entries are `status: candidate`; none is domain truth | **DECIDED** |
| No rule is implemented against an unverified entry | **DECIDED** |
| Entries are not "verified" using general LoL knowledge, mine or any model's | **DECIDED** |
| Review structure delivered as `CATALOGUE_REVIEW.md` | **DECIDED** |
| Which entries are real coaching concepts for this player | **REQUIRES_DOMAIN_REVIEW** |
| Proposed merges (#17→#16, #23→#1) and the #37 demotion to REVIEW_ONLY | **PROPOSED** |
| Sections VIII–XV (entries 44–70) stay unclassified | **DEFERRED** — outside laning scope |

---

## 6. Six threshold decisions

**These need no new data.** The telemetry exists; a number is missing. Do not let me pick
these — a threshold that changes a conclusion is a product decision.

| # | Concept | What the threshold controls | Observable inputs | Stricter → | Looser → | Suggested rule type |
|---|---|---|---|---|---|---|
| 13 | high-value window | when staying in lane is flagged | fight size, distance, objective proximity, ally count | few flags, high confidence | many flags, noisy | fight size **and** distance, not either alone |
| 14 | low-probability roam | when a roam is judged poor | distance, ally/enemy counts, HP/mana, enemy jungler location | only disasters flagged | punishes reasonable gambles | feasibility factors, **never a fabricated probability** |
| 15 | wrong roam target | how two destinations compare | all-lane states, travel time, enemy positions | rarely fires | second-guesses constantly | comparison shown, "wrong" withheld |
| 25 | exploitable jungle absence | what counts as using the window | jungler distance, your action, resources gained | misses real misses | flags every absence | minimum distance **and** a minimum window length |
| 38 | power-spike conversion | what counts as converting | item completion time, subsequent aggression, CS/plate rate | misses soft conversions | flags normal play | a window after completion, action within it |
| 43 | objective redirection | when persistence becomes tunnel vision | your proximity over time, objective state changes | rarely fires | punishes commitment | requires an observable state change first |

Also unresolved and of the same kind:

| Item | Where | Status |
|---|---|---|
| Mid-corridor width — currently an invented `MID_LANE_CORRIDOR_WIDTH = 2500` in `src/features.py` | affects #16, #17 | **REQUIRES_USER_DECISION** |
| "At the fight" proximity radius | affects #20, #22, #41 | **REQUIRES_USER_DECISION** — suggest deriving from observed fight spread rather than choosing a number |
| Minimum interesting effect size — already blocking `Skill-based` per `classify_winrate` | affects champion/matchup verdicts | **REQUIRES_USER_DECISION**, pre-existing |

---

## 7. Multiple-comparison policy

**Unresolved and load-bearing.** Testing 39 champions at *p* < 0.05 produces roughly two
false verdicts by chance. The only champion currently clearing the uncorrected threshold
does **not** survive correction.

**Smallest defensible recommendation** `PROPOSED` — three tiers of language, not a heavier
statistical framework:

| Tier | Qualifies when | Language permitted |
|---|---|---|
| **Verdict** | Survives multiplicity control across the whole family tested — Benjamini–Hochberg at *q* = 0.10 | "above / below your baseline" |
| **Lead** | Passes uncorrected *p* < 0.05 but not corrected | "worth watching — not yet separable from chance" |
| **Descriptive** | Everything else | count, rate, interval. **No inferential claim** |

Benjamini–Hochberg needs only a sort over p-values `binomial_significance` already computes,
so it adds no dependency. Bonferroni is the stricter alternative and would currently yield
zero verdicts.

**REQUIRES_USER_DECISION** — three acceptable answers: adopt the tiers; go descriptive-only
on the champion page and drop inferential language entirely; or accept uncorrected results
provided they are labelled leads. The one unacceptable outcome is shipping uncorrected
p-values as verdicts.

---

## 8. Degenerate games

| Decision | Status |
|---|---|
| **No global remake threshold.** Each analysis declares its own required window; exclusions trace to the analysis that required them | **DECIDED** |
| Implementation is a per-query `frame_count >= N` predicate, not a pipeline-level filter | **DECIDED** |
| Canonical layer retains all games, including the 13 remakes and 3 early surrenders | **DECIDED** |

A 14-minute laning analysis excludes different games than a 20-minute objective analysis —
correctly, and without an invented constant.

---

## 9. Data architecture and database

| Decision | Status |
|---|---|
| Six layers: RAW · CANONICAL · DERIVED · DECISION · ANALYSIS · PRESENTATION | **DECIDED** |
| Domain knowledge enters at the DECISION layer through versioned rules — never inside parsers | **DECIDED** |
| Participant-long canonical schema: `matches` · `participants` · `frames` · `events` · `kill_damage` | **DECIDED** |
| Derived and decision tables: `lane_state` · `decisions` · `decision_evidence` · `annotations` | **DECIDED** |
| Canonical frame identity `(match_id, frame_index, participant_id)` + `timestamp_ms`; "minute" is an interpretation derived at query time | **DECIDED** |
| **No `puuid`, `summonerName` or `summonerId` for any participant.** `is_subject` suffices | **DECIDED** |
| `participantId = 0` is a sentinel meaning "no participant" and never joins to a slot | **DECIDED** |
| Full event payload retained in `events.detail` even where structured extraction is partial | **DECIDED** |
| Corpus size enumerated at run time; **no count is ever an architectural assumption** | **DECIDED** |
| Every derived value carries `availability_class`, `derivation_method`, `confidence` | **DECIDED** |
| Versioned: `game_version` · `season` · `catalogue_version` · `rule_version` · `domain_version` | **DECIDED** |

---

## 10. Dashboard

| Decision | Status |
|---|---|
| Streamlit stays; the defect is information architecture, not framework | **DECIDED** |
| Five pages: Overview · Games · Game Review · Patterns · Champions | **DECIDED** |
| Matchups merges into Champions | **DECIDED** |
| Patterns means **named recurring decision patterns**, never clusters | **DECIDED** |
| Every transition in the drill path is clickable; never manual re-filtering | **DECIDED** |
| Every visualization declares question, source, inferable, not-inferable, next action | **DECIDED** |
| No business logic in `dashboard/` | **DECIDED** |
| Cut: cluster distribution, cluster heatmap, gold-trajectory-by-cluster, win-rate-by-patch, time-of-day, CS-advantage scatter | **DECIDED** |
| Visual UI audit of the rebuilt app | **DEFERRED** to P4 — more useful against the rebuild than against a known absence |

---

## 11. K-Means

**DECIDED — deprecated.** Remove `src/models.py`, `models/cluster_centroids.json`,
`cluster_labels`, `tests/test_models.py`, and the Patterns tab bound to them.

Five independent grounds: answers no user question · IDs permute on every refresh ·
three of nine features collinear at r = 0.75–0.82 · silhouette 0.193 with clusters
recovering game outcome rather than behaviour across three feature sets and *k* = 2…8 ·
a numeric cluster ID cannot be traced to evidence, which the decision model requires.

Retiring it also dissolves the cluster-ID permutation issue rather than answering it.

---

## 12. Replay and annotation

| Decision | Status |
|---|---|
| Manual annotation is a distinct evidence source; `source = MANUAL_ANNOTATION`, never `riot` | **DECIDED** |
| Annotations append-only, permanent, patch-stamped; a correction is a new row | **DECIDED** |
| Review targets emitted for `REPLAY_MANUAL_ONLY` decisions | **DECIDED** |
| Replay review is patch-locked and **cannot backfill** the historical corpus | **DECIDED** |
| Review queue prioritises current-patch games | **DECIDED** |
| Annotation capture UI | **DEFERRED** to P6 — schema slot and target emission come first |

---

## 13. Privacy and publication

| Decision | Status |
|---|---|
| Publication is an explicit allow-list transformation, never a database copy | **DECIDED** |
| No PUUID or account identifiers in the public artefact | **DECIDED** |
| `game_datetime` truncated to midnight UTC; consumers use `>=` so filtering is unaffected | **DECIDED** |
| Annotations and reviewer notes private by default | **DECIDED** |
| Publication assertions run against the built artefact | **DECIDED** |
| **Should Game Review be public at all?** | **REQUIRES_USER_DECISION** |

The open decision, unchanged: a public dated game list plus both champions plus a death
sequence is the most identifying artefact this project would ship. Options are (A) keep Game
Review local-only and publish season aggregates, (B) publish with coarsened identifiers,
(C) accept the risk explicitly. **Blocks P5 publication, nothing earlier.**

---

## 14. Testing

| Layer | What it protects | Status |
|---|---|---|
| RAW | corpus pairing, duplicates, malformed files | **DECIDED** — audit script exists |
| CANONICAL | parser correctness; participant-mapping invariant over the full corpus | **DECIDED** |
| DERIVED | formulas, invariants, edge cases | **DECIDED** |
| DECISION | synthetic scenarios **and** hand-labelled real examples; rules fire when they should and stay silent when they should not | **DECIDED** — the most important tests in the project |
| ANALYSIS | no claim exceeds evidence; PARTIAL always names its gap | **DECIDED** |
| DASHBOARD | render smoke test, drill-path reachability | **DECIDED** |
| PUBLICATION | no identifiers, no precise timestamps, allow-list enforced | **DECIDED** |

**Software correctness and analytical correctness are independent.** A green suite proves
the code runs; only a human reading a generated report against a replay proves it describes
the right game.

---

## 15. Roadmap

Ordering confirmed against the repository. Unchanged from the blueprint.

| Phase | Goal | Blocked by |
|---|---|---|
| **P0** | Corpus audit | — **complete** |
| **P1** | Canonical schema, rebuild from all valid pairs | nothing |
| **P2** | Derived layer + text match report | P1 |
| **P3** | Decision engine | P2 **and** catalogue verification **and** thresholds |
| **P4** | Game Review page | P3 |
| **P5** | Season, patterns, publication | P4 **and** the privacy decision |
| **P6** | Review loop and annotation capture | P5 |

**P1 and P2 are unblocked and can begin immediately.** They depend on no user decision —
canonical parsing carries no domain interpretation, and the text report exposes only
measured values. Everything from P3 onward waits on the catalogue.

---

## 16. What the next coding session should do

```text
P1 · Canonical representation

  Rewrite  src/processor.py to the participant-long schema
  Rebuild  DuckDB from every valid pair enumerated at run time
  Delete   src/models.py · models/cluster_centroids.json · tests/test_models.py
  Quarantine  the Level-2 half of tests/test_features.py, restore in P5
  Keep     src/collector.py · src/mapping.py · src/archetypes.py untouched

  Gate     participant-mapping invariant over every participant in every valid
           pair, zero mismatches. Pre-verified 8,250/8,250 on the current corpus
  Exit     surviving suite green · ruff clean · one-match completeness dump
           marking unavailable fields explicitly · counts recorded in CONTEXT.md
           as dated observations

  Non-goals  no analysis · no UI · no decision rules · no CONTEXT.md phase
             rewrite until the rebuild actually lands
```

---

## 17. Open items, consolidated

| Item | Status | Blocks |
|---|---|---|
| Verify catalogue entries — 13 BUILDABLE first | REQUIRES_DOMAIN_REVIEW | P3 |
| Six thresholds (#13, 14, 15, 25, 38, 43) | REQUIRES_USER_DECISION | P3 for those entries |
| Mid-corridor width; "at the fight" radius | REQUIRES_USER_DECISION | P3 for #16, 17, 20, 22, 41 |
| Multiple-comparison policy | REQUIRES_USER_DECISION | Champions page in P5 |
| Minimum interesting effect size (`Skill-based`) | REQUIRES_USER_DECISION | Champions page in P5 |
| Public Game Review policy | REQUIRES_USER_DECISION | P5 publication |
| Objectives absent from `GAME_MECHANICS.md` — Dragon, Atakhan | REQUIRES_DOMAIN_REVIEW | domain docs, not code |
| Accept the four-state model and missing-input classes | PROPOSED | `ANALYSIS_SPEC.md` delta |
| `docs/domain/` does not exist yet | REQUIRES_DOMAIN_REVIEW | domain layer |
| `.claude/CONTEXT.md` stale phase claim | DECIDED — rewrite when P1 lands | — |

**Nothing in this document has been applied to `ANALYSIS_SPEC.md`, the database, the
dashboard, or any application code.**

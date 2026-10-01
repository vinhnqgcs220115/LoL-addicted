# Session journal

> **L1 Working** · what each session did and decided · owner: Claude writes, the user reads · update: add one entry at the top at the end of every session; never edit an old entry, correct it in a new one

Entry format, newest first, at most about 10 lines:

```text
## YYYY-MM-DD · <focus>
- Done: <ROADMAP task IDs>
- In progress: <task IDs, and where work stopped>
- DECISION (<who>): <what was decided, and why>   ← if it changes scope, edit CLAUDE.md too
- Parked: <idea>                                  ← also goes in the ROADMAP parking lot
- Next: <first step for the next session>
```

No counts or metrics in this file. Query them, or cite the commit that measured them.

---

## 2026-10-01 · Docs refactor
- Done:
  - Docs reorganized into levels L0–L3 (map in CLAUDE.md).
  - `AGENTS.md` removed; `PRODUCT.md` became `ROADMAP.md`.
  - The 08-29 definition moved to `docs/VISION.md`.
  - The decision catalogue was saved verbatim to `docs/domain/`.
  - The old docs are kept at tag `pre-docs-refactor`.
- DECISION (user): the M1 dashboard scaffold comes before per-game work, time-boxed.
- DECISION (user): public identity is fine. The Riot ID and rank go on the live app, and the anonymization rules are dropped.
- DECISION (user): there is a collect button on the live app too. It is its own track, M1b, which starts once you have a non-expiring Riot key.
- DECISION (user): K-Means is retired in M1.8.
- DECISION (user): season = patch major, and stats cover the current season only. The 0–14 min per-game window is temporary.
- Next: M1.1.

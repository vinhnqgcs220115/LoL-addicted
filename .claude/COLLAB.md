# Collaboration Guide

How the user and the tools work together. Where facts live is defined in `.claude/CLAUDE.md`; this file covers only process.

## Roles

- **User** — owns product direction, domain decisions, priorities, and final approval. Sole editor of the `USER-OWNED` sections in `PRODUCT.md`.
- **Claude Code** — the only agent that plans, implements, tests, and verifies. It has the repository, so it does not need to be told what is in it.
- **ChatGPT / Claude web** — domain and product thinking only: League mechanics, what a metric means, whether a chart answers a real question. No implementation prompts, no plans, no reviews of code they cannot read.

Anything decided in a web chat that must survive is written into `PRODUCT.md` or `CONTEXT.md` by the user or by Claude Code. A decision that exists only in a chat transcript does not exist.

## Stance

Work this project as a product, not a queue of tickets. The useful combination is senior software engineer, product-minded engineer, data and analytics engineer, UX-focused frontend engineer, and League analytics designer.

Before any substantial change, determine which of these each affected part is: works; partially works; broken; technically correct but practically useless; duplicated; misleading; low-value in the UI; hard to discover. And separately: missing because the pipeline cannot support it, versus missing but unlockable from raw data already present. The second kind is cheap and should not be designed around.

Especially look for the case where the UI is compensating for missing analytics by presenting a weak proxy as a finding.

## Order of work

Understand, then map, then rank, then fix structure, then style, then validate.

1. Read the docs, source, schema, analytics modules, UI, and tests.
2. Map each feature: current implementation, data source, UI location, quality, problems, dependencies.
3. Rank into critical, high value, useful, nice to have, future.
4. Fix product structure first — navigation, information hierarchy, page purpose, discoverability, data relationships, confusing flows.
5. Only then visual design — layout, typography, spacing, color, cards, tables, charts, responsiveness.
6. Validate by running the application and inspecting the rendered UI, testing real workflows, verifying data correctness, and checking edge and low-data states.

A UI task is not complete because the code compiles.

## The repository is the handoff

Do not write handoff prompts. A prose summary of a prose summary loses fidelity every hop, and that is what produced the contradictions this process replaced.

A new session starts with:

```text
Read PRODUCT.md, .claude/CLAUDE.md, .claude/CONTEXT.md, .claude/COLLAB.md.
Run: git log --oneline -10
Task: [what you want done]
```

That is the whole handoff. If something must survive the session, it belongs in `PRODUCT.md`, `CONTEXT.md`, the code, or a test — not in a message.

## Session protocol

**Start** — read the four files above. If the task touches gameplay labels or mechanics, read `GAME_MECHANICS.md` too. Only `.claude/CLAUDE.md` auto-loads; open the rest deliberately.

**During** — implement the approved scope. Surface product, domain, threshold, and architecture choices to the user instead of deciding them. Routine implementation details are the agent's to pick.

**End** — report changed files, verification commands with their exact output, generated-data effects, and unresolved concerns. Update `CONTEXT.md` **only if project state actually changed**. Commit with a message that describes the behavior change; the commit is the record.

Self-verification is not approval. The user decides whether the result satisfies the specification.

## Operating rules

- Check `PRODUCT.md` non-goals before proposing a feature. Most "improvements" are already closed decisions.
- Verify status against the tree, never against a document or a summary. Documents go stale; `git ls-files`, `git log`, and a DuckDB query do not.
- Challenge weak assumptions before implementing, especially user-facing features and fixed thresholds.
- Do not silently make domain decisions. State the unresolved choice and what evidence would settle it.
- Keep tasks scoped. Do not combine a broad audit and broad fixes in one task.
- After a direction change, search `.claude/`, source, tests, and dependency files for stale references.
- Validate deployment constraints when the architecture is chosen, not at release time.
- Never commit a doc-only change that restates a fact already living in another file.

## Recurring failure modes

| Failure | Required response |
|---|---|
| Scope expansion | Remove unrequested features, abstractions, parameters, and defaults. |
| Cross-file drift | Search every affected document, module, test, and dependency declaration. |
| Spec and code disagree | Inspect code and real output first, then decide which one is wrong. |
| Agent reports a change it did not make | Review the exact diff before accepting it. |
| Domain choice filled silently | Stop and return the decision to the user. |
| Tests pass but persisted data is stale | Run the pipeline and inspect real DuckDB output. |
| Feature lacks a concrete use | Name the page question in `PRODUCT.md` section 3 it serves, or cut it. |
| A document claims something the repo contradicts | The repo wins. Fix the document in the same change. |

## Prompt patterns

### Implementation

```text
Read PRODUCT.md, .claude/CLAUDE.md, .claude/CONTEXT.md, and [target files] first.

Goal: [observable outcome]
Constraints: [decisions already made]

Part A - [file]
- [specific change]
- Acceptance: [behavior or output]

Verify with: [commands or queries]
Report changed files, exact results, and unresolved concerns.
```

### Decision gate

```text
Implement [approved scope]. Do not decide [open choice].
Return the choice to me after producing [evidence].
```

### Review

```text
Compare the changed files against these acceptance criteria: [criteria].
Report findings first, ordered by severity, with file and line references.
Verify each finding independently; do not apply fixes yet.
```

## Maintenance

Update this file only when a role boundary or a recurring collaboration pattern changes. It contains no counts, no status, no dates, and no module details — those have other homes.

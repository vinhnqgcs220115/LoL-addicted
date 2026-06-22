# Collaboration Guide

This file defines how decisions, implementation, review, and handoffs work. Stable engineering rules belong in `CLAUDE.md`; current plans, metrics, and decisions belong in `CONTEXT.md`; implementation details belong in code and tests. Do not duplicate them here.

## Roles

- **User**: owns product direction, domain decisions, priorities, and final approval.
- **Reviewer/planner**: challenges assumptions, checks architecture and product utility, maintains specifications, and prepares scoped implementation prompts. In the split-agent workflow, this is typically Claude web and it does not edit implementation code.
- **Coding agent**: implements the approved scope, adds or updates tests, runs verification, and reports exact changes and outputs. It may choose routine implementation details but must surface product, domain, threshold, and architecture decisions.

Self-verification is required, but it is not final approval. The user or an independent reviewer decides whether the result satisfies the specification.

## Workflow

1. User and reviewer agree on the problem, intended user action, constraints, and acceptance criteria.
2. Reviewer checks the proposal against `CLAUDE.md`, `CONTEXT.md`, and relevant code before writing an implementation prompt.
3. Coding agent reads the named files, implements only the approved scope, and runs the required checks.
4. Coding agent reports changed files, verification commands, exact results, and unresolved concerns.
5. Reviewer compares the implementation with the acceptance criteria and returns numbered findings ordered by severity.
6. Required fixes go back to the coding agent as a new scoped task.
7. A phase closes only when acceptance criteria and relevant tests pass, production-like data is verified when applicable, and `CONTEXT.md` reflects the result.

Direct user-to-agent work is allowed. The same decision gates, verification, and review requirements still apply.

## Operating Rules

- Read `CLAUDE.md`, `CONTEXT.md`, and the target files before proposing or implementing changes.
- Challenge weak assumptions before implementation, especially for user-facing features and fixed thresholds.
- Do not silently make domain decisions. State the unresolved choice and what evidence is needed.
- Keep tasks scoped. Do not combine broad audits and broad fixes in one agent prompt.
- Verify actual code and output; do not rely on an agent's claim that something was changed.
- After a direction change, search `.claude/`, affected source files, tests, and dependency files for stale references.
- Check changed function signatures for unused parameters and orphaned helpers.
- Validate deployment constraints when deployment architecture is chosen, not at release time.
- Update `CONTEXT.md` whenever phase status, measured data, or an architectural decision changes.

## Recurring Failure Modes

| Failure | Required response |
|---|---|
| Scope expansion | Remove unrequested features, abstractions, parameters, and defaults. |
| Cross-file drift | Search every affected document, source module, test, and dependency declaration. |
| Spec and code disagree | Inspect code and real output first; then decide whether code or documentation is wrong. |
| Agent reports a different implementation | Review the exact diff or changed snippet before accepting it. |
| Domain choice filled silently | Stop and return the decision to the user. |
| Tests pass but persisted data is stale | Run the relevant pipeline and inspect real DuckDB output. |
| Feature lacks a concrete use | Define what the user does with the output before implementation. |
| Session context is lost | Record non-obvious rationale in `CONTEXT.md` and produce a factual handoff. |

## Prompt Patterns

### Implementation

```text
Read CLAUDE.md, CONTEXT.md, and [target files] before changing anything.

Goal: [observable outcome]
Constraints: [boundaries and decisions already made]

Part A - [file]
- [specific change]
- Acceptance: [behavior or output]

Part B - [file]
- [specific change]
- Acceptance: [behavior or output]

Verify with: [commands or queries]
Report changed files, exact results, and unresolved concerns.
```

### Consistency Sweep

```text
Search .claude/, affected source files, tests, and dependencies for [old concept].
List every occurrence first, then update only confirmed stale references.
```

### Decision Gate

```text
Implement [approved scope]. Do not decide [open choice].
Return the choice to me after producing [evidence or output].
```

### Review

```text
Compare the changed files with these acceptance criteria: [criteria].
Report findings first, ordered by severity, with file and line references.
Verify each finding independently; do not apply fixes yet.
```

### Session Close

```text
Produce a factual handoff: files changed, behavior changed, verification results,
current phase status, and open items. Update CONTEXT.md when its state changed.
```

## Maintenance

Update this file only when a recurring collaboration pattern or role boundary changes. Do not add current data counts, model constants, agent versions, module workflows, or temporary phase details; those have more authoritative homes.

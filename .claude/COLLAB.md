# How we work

> **L2 Reference** · roles and collaboration rules · owner: the user · update: only when a role or a working pattern changes

## Roles

- **User: player and product owner.**
  - Uses the dashboard, judges whether it helps, and raises the concerns and problems they hit.
  - Owns direction, priorities, domain knowledge, thresholds and final approval.
- **Claude Code: main engineer.**
  - Plans, implements, tests and verifies in the repository.
  - Turns the user's concerns into ROADMAP tasks.
  - Surfaces product, domain, threshold and architecture choices instead of deciding them.
- **Claude (web): researcher and tie-breaker.**
  - Brought in when a problem stays unsolved, or when the user and Claude Code can't agree.
  - It has no access to the repository, so give it the specific question and the facts it needs, not the whole project.

## Rules

- **The repo is the memory.** A decision made in a web chat counts only once it is written into the repo:
  - CLAUDE.md for scope;
  - ROADMAP for tasks;
  - CONTEXT for the record.

  The decision catalogue once existed only in a chat transcript. This rule stops that from happening again.
- **Self-verification is not approval.** Claude Code reports what changed and how it was checked; the user decides whether it meets the need.
- **The repo beats the docs.** Check status against the code, git and the data, never against a summary or a handoff message.
- **One task at a time.** Never mix a broad audit with broad fixes in the same session.
- **After a direction change,** fix stale references in the docs, code, tests and config in the same change.

## Raising a concern (user → Claude Code)

Say what you saw, where it was, and what you expected. Claude Code reproduces it first. Then it either fixes the problem inside the current task or adds it to the ROADMAP.

## Escalating to Claude (web)

Take one concrete question, with the facts it needs pasted in. Bring the conclusion back and have Claude Code record it.

# Team Conventions

> Layer 2 context artifact. These are the working agreements the team has adopted.
> Version: 0.1.0 | Last updated: 2026-03-05

## Task Structure

Every task (regardless of tool: Jira, Notion, GitHub Issues) follows this structure:

```
Title: [ACTION] [SUBJECT] — [CONTEXT]
Example: "Fix flaky deploy pipeline for trading-api service"

Description:
- Background: what's happening and why it matters
- Acceptance criteria: specific, verifiable conditions for done
- Effort estimate: small / medium / large
- Assignee: one owner, others are collaborators
- Priority: P1 (blocking) / P2 (this sprint) / P3 (backlog)
```

## Effort Sizing

| Size   | Duration     | Examples |
|--------|--------------|---------|
| small  | < 1 day      | Config change, quick fix, documentation update |
| medium | 1–3 days     | New alert rule, pipeline step, script refactor |
| large  | 3+ days      | New infrastructure component, migration, new service |

When uncertain between two sizes, choose the larger.

## Priority Levels

| Priority | Meaning | SLA |
|----------|---------|-----|
| P1 | Production blocked or security risk | Immediate, same day |
| P2 | Sprint commitment | This sprint (within 2 weeks) |
| P3 | Backlog / nice-to-have | No SLA, reviewed in sprint planning |

## Acceptance Criteria Rules

- Must be verifiable (not "should work better")
- Written as: "Given X, when Y, then Z" or "The [thing] must [measurable condition]"
- Minimum 1 criterion per task
- Do NOT write criteria that duplicate the description

## Git Branching

```
feature/<ticket-id>-short-description
fix/<ticket-id>-short-description
chore/<ticket-id>-short-description
```

Commits follow Conventional Commits: `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`

## Definition of Done

A task is done when:
1. Code/change is in main (or deployed, for infra)
2. Acceptance criteria are verified
3. Relevant documentation is updated
4. If production: monitoring shows stable metrics for 30 minutes post-deploy

## What Goes in Backlog vs Park

- **Backlog**: actionable, effort estimated, has potential owner
- **Park (notes/)**: observation, idea, or dependency on external event
- Parked notes are reviewed in sprint planning — not lost, not forgotten

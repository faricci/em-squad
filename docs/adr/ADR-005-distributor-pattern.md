# ADR-005: Pluggable Distributor over Hardcoded Output

**Status:** active
**Date:** 2026-03-07
**Author:** Fabiano Ricci

---

## Context

After an agent produces a decision, that decision needs to go somewhere: a task file,
Notion, GitHub Issues, a Slack message. The target varies by team, by phase, and by
agent type.

Hardcoding output logic inside each agent module couples the agent's reasoning to its
output destination. Adding a new output channel would require editing every agent.

---

## Decision

Output is handled by **pluggable distributors** — a separate module layer decoupled from
agents. Each agent declares its distributor in `agents.yaml`. The orchestrator resolves
and calls the distributor after a successful agent run.

```
src/distributors/
├── base.py       → Distributor protocol (Python Protocol class)
└── markdown.py   → Default: writes to output/ directory
```

The distributor receives the agent's result and the agent's registry entry. It is
responsible for all side effects: file writes, API calls, notifications.

**Current implementation:** `MarkdownDistributor`
- `park` → `output/backlog.md` (running log) + `memory/notes/<slug>.md`
- `task` / `assign` → `output/tasks.md` (running log)

**Planned:** `NotionDistributor`, `GitHubDistributor` — swap by changing one line in `agents.yaml`.

---

## Consequences

### Positive
- Agents are pure reasoning modules — zero output side effects
- Swapping output channel requires no code change in agents or orchestrator
- Multiple agents can share the same distributor
- Easy to test agents without triggering real output (swap in a NullDistributor)

### Negative / Trade-offs
- Distributor must understand the agent's result type — thin coupling remains
- Adding a new output channel requires implementing the Distributor protocol

---

## Alternatives Considered

| Option | Reason Rejected |
|--------|----------------|
| Each agent writes its own output | Couples reasoning to I/O; duplicates output logic; hard to swap channels |
| Single global output function | Not extensible; can't support per-agent distributor configuration |
| Event bus / message queue | Overkill for a single-user CLI tool at current scale |

---

## References

- Distributor protocol: `src/distributors/base.py`
- Default distributor: `src/distributors/markdown.py`
- Registry configuration: `agents.yaml` (distributor field per agent)
- Related ADRs: ADR-001 (Orchestrator)

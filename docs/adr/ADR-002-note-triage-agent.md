# ADR-002: Note Triage — Three-Way Decision (Park / Task / Assign)

**Status:** active
**Date:** 2026-03-07
**Author:** Fabiano Ricci

---

## Context

Raw EM notes are unstructured and heterogeneous. Some are vague ideas, some are urgent
incidents, some have clear owners, some are still half-formed thoughts. The triage agent
needed a decision model that maps cleanly onto how an EM actually processes notes.

The simplest model is binary: actionable vs. not actionable. But this ignores a critical
distinction in real EM workflow: actionable-but-no-clear-owner is fundamentally different
from actionable-with-a-clear-owner. The former requires EM judgment before it becomes a
task. The latter can be suggested to the EM for one-click confirmation.

---

## Decision

The Note Triage Agent uses a **three-way decision model**:

- **Park** — not actionable yet. Idea, observation, or future consideration.
  Stored in `memory/notes/` with tags and timestamp. No task created.

- **Task** — actionable but owner is unclear, workload is uncertain, or the decision
  involves trade-offs the EM must resolve. Produces a structured task definition for the
  EM to assign manually.

- **Assign** — actionable AND a clear owner match exists in the team roster based on
  skill/domain alignment. Produces a task definition with a suggested owner for EM
  confirmation (human-in-the-loop required — the agent never assigns unilaterally).

The distinction between task and assign is driven by the team roster and routing rules
in `context/agent-directives.md`.

---

## Consequences

### Positive
- Matches real EM mental model — eliminates the need for a second manual pass
- Assign decisions accelerate workflow without removing human oversight
- Park decisions preserve information that would otherwise be lost
- Three-way split enables meaningful eval metrics (decision accuracy, owner accuracy separately)

### Negative / Trade-offs
- "Task vs assign" boundary is fuzzy and model-dependent — requires EM calibration over time
- Owner suggestions can be wrong; this is tracked via eval runner and promoted to agent-directives.md
- Notes that span multiple actionable items are not split (deferred — see open questions in contract)

---

## Alternatives Considered

| Option | Reason Rejected |
|--------|----------------|
| Binary: actionable / not-actionable | Loses the owner-clarity signal; EM still has to triage all actionable notes manually |
| Four-way: add "urgent" category | Premature; urgency can be inferred from effort + content; adds eval complexity without clear benefit |
| Free-form output (no fixed decision enum) | Not machine-readable; breaks downstream distribution; can't compute accuracy metrics |

---

## References

- Contract: `contracts/note-triage-agent.yaml`
- Skill prompt: `skills/note-triage/skill.md`
- Agent directives (routing rules): `context/agent-directives.md`
- Eval criteria: `evals/triage-accuracy.md`
- Related ADRs: ADR-001 (Orchestrator), ADR-004 (Memory Architecture)

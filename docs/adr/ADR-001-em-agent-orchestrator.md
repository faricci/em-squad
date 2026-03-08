# ADR-001: EM Agent as Multi-Agent Orchestrator

**Status:** active
**Date:** 2026-03-07
**Author:** Fabiano Ricci

---

## Context

The EM Agent framework needed a top-level controller. The key design question was whether
to build a single monolithic agent that handles all EM responsibilities (triage, onboarding,
pattern detection, distribution) or a multi-agent orchestrator that delegates to specialized
sub-agents.

Engineering managers deal with a wide range of heterogeneous inputs: notes from standups,
CI/CD alerts, onboarding requests, retrospective observations, and budget signals. A single
agent handling all of these would require an enormous, brittle system prompt that conflates
unrelated concerns.

The 5-layer CDLC matrix the framework is built on implies separation of concerns at each
layer. Layer 4 (Orchestration) should route inputs — not execute them.

---

## Decision

The EM Agent is implemented as a **multi-agent orchestrator**. It:
- Holds no domain intelligence itself
- Reads the agent registry (`agents.yaml`) to discover available sub-agents
- Routes each input to the appropriate sub-agent based on type
- Applies C-DAD validation (pre-run + post-run) uniformly across all agents
- Delegates distribution to pluggable distributors

Sub-agents are autonomous modules, each with their own contract, skill prompt, and Python
entry function.

---

## Consequences

### Positive
- Sub-agents are independently testable, replaceable, and deployable
- Adding a new capability requires no changes to the orchestrator (registry-driven)
- Each sub-agent's scope is bounded by its contract — no scope creep across agents
- The orchestrator's C-DAD validation is a uniform enforcement point

### Negative / Trade-offs
- More files and moving parts for a small team (mitigated by the Onboarding Agent)
- Inter-agent communication (when one agent's output feeds another) requires an explicit
  handoff protocol (deferred to Phase 4)
- No shared state between sub-agents within a single orchestrator run

---

## Alternatives Considered

| Option | Reason Rejected |
|--------|----------------|
| Monolithic agent with one large system prompt | Prompt becomes unmanageable; concerns conflate; impossible to eval individual capabilities |
| LangGraph / LangChain agent graph | Framework lock-in; overkill for current scale; hides the architecture behind abstractions |
| One Python class with method dispatch | Doesn't enforce contract boundaries; harder to extend without modifying the class |

---

## References

- Contract: `contracts/em-agent.yaml`
- Registry: `agents.yaml`
- Orchestrator: `src/orchestrator.py`
- Related ADRs: ADR-002 (Note Triage), ADR-003 (Onboarding), ADR-005 (Distributor)

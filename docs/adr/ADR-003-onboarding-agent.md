# ADR-003: Onboarding Agent — Artifact Generation at Onboarding Time

**Status:** active
**Date:** 2026-03-07
**Author:** Fabiano Ricci

---

## Context

Adding a new agent to em-squad requires creating three coordinated artifacts: a C-DAD
contract YAML, a Python module skeleton, and a registry entry in `agents.yaml`. Doing this
manually is error-prone — fields can be omitted, naming conventions can drift, and the
contract may not be internally consistent.

The question was: how should the framework lower the barrier to adding new agents while
maintaining contract governance?

---

## Decision

An **Onboarding Agent** generates all three artifacts from a natural-language description.
It:
1. Parses the description into structured agent intent
2. Generates a valid C-DAD contract YAML (using note-triage-agent.yaml as template)
3. Generates a Python skeleton (using note_triage.py as template)
4. Produces the `agents.yaml` registry entry
5. Returns all artifacts for EM review — **never writes files automatically**

The EM reviews all artifacts before confirming. On confirmation, `squad.py` writes the
files and registers the agent. The Onboarding Agent is itself a sub-agent, registered in
`agents.yaml` and governed by a contract.

---

## Consequences

### Positive
- New agents can be added in minutes, not hours
- Generated artifacts follow the framework's conventions by construction
- Human-in-the-loop review prevents bad agents from being silently registered
- The onboarding agent itself is an example of recursive framework application

### Negative / Trade-offs
- Generated skeleton is a stub — the EM still needs to implement the agent's logic
- Generated contract may need editing (fields like open_questions need human judgment)
- The onboarding agent's quality depends on the template contract and skeleton it references

---

## Alternatives Considered

| Option | Reason Rejected |
|--------|----------------|
| Manual artifact creation with a written guide | Error-prone; no enforcement of required fields; slow |
| CLI scaffold command (cookiecutter-style) | No AI reasoning about the agent's purpose; produces generic boilerplate |
| Fully autonomous agent creation (no EM review) | Violates the human-in-the-loop principle central to C-DAD governance |

---

## References

- Contract: `contracts/onboarding-agent.yaml`
- Agent module: `src/agents/onboarding.py`
- Template contract: `contracts/note-triage-agent.yaml`
- Template skeleton: `src/agents/note_triage.py`
- Related ADRs: ADR-001 (Orchestrator)

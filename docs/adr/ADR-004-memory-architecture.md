# ADR-004: Memory Architecture — Hot / Cold / Audit Layers

**Status:** active
**Date:** 2026-03-07
**Author:** Fabiano Ricci

---

## Context

AI agents need access to different kinds of information with different access patterns:
- Always-on rules that govern behavior (routing, effort calibration)
- Historical decisions for context recall
- An immutable audit trail for governance and pattern detection

A flat context injection — dumping everything into every prompt — would be expensive,
noisy, and would hit token limits as history grows.

---

## Decision

Three formal memory layers with distinct access patterns:

### Hot Memory — `context/agent-directives.md`
- **Always loaded** — injected into every agent call
- Contains routing rules, effort calibration, EM preferences
- Human-editable markdown — behavior change without code change
- Small by design (< 2KB target)
- Future: auto-promoted from EM corrections (L5 → L4 vertical promotion)

### Cold Memory — `memory/history/*.jsonl`
- **On-demand retrieval** — only when relevant
- Grows unbounded; one file per day
- Indexed with **BM25** (Okapi BM25 via `rank-bm25`) for Phase 2
  - Zero API cost, deterministic, no server
  - Returns top-K entries matching the current note
- Park decisions excluded from search (not useful for recall)
- Phase 5 upgrade path: LanceDB (embedded, MIT license) for semantic vector search
  when corpus exceeds ~10K decisions

### Audit Memory — `memory/history/*.jsonl`
- Same files as cold memory, different semantic role
- **Immutable append-only log** — `audit_log(agent_id, input, output)` called by every agent
- `agent_id` field enables multi-agent traceability
- Primary input to the vertical promotion detector

---

## Consequences

### Positive
- Token efficiency: cold memory only injected when relevant (top-3, not all history)
- Governance: audit log is the ground truth for all agent decisions
- Separation: behavior rules (hot) are decoupled from history (cold)
- Upgrade path: BM25 → LanceDB is a single-module swap when scale requires it

### Negative / Trade-offs
- BM25 is keyword-based — misses semantic similarity (e.g., "pipeline" ≠ "CI/CD" unless both appear)
- Hot memory must be kept small manually — no automatic size enforcement
- Single JSONL file per day creates a read bottleneck as history grows

---

## Alternatives Considered

| Option | Reason Rejected |
|--------|----------------|
| Inject full history into every prompt | Token cost grows linearly with history; noisy context degrades quality |
| Redis / vector DB from day one | Operational overhead for a single-user CLI tool; premature |
| Separate hot memory into a DB table | Over-engineered; markdown is readable, editable, and diff-able by humans |
| No cold memory (only hot rules) | Loses the recall signal; can't detect recurring patterns without history |

---

## References

- Memory engine: `src/context_engine/memory.py`
- Hot memory file: `context/agent-directives.md`
- Cold/Audit storage: `memory/history/`
- LanceDB upgrade path documented in ARCHITECTURE.md
- Related ADRs: ADR-001 (Orchestrator), ADR-002 (Note Triage)

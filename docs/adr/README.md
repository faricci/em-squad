# Architecture Decision Records

This directory contains ADRs for the em-agent-framework. Each ADR captures why a significant
architectural decision was made, what alternatives were considered, and what trade-offs were accepted.

ADRs are linked from their corresponding C-DAD contracts via the `provenance.adr` field.

---

## Index

| ADR | Title | Status | Date | Summary |
|-----|-------|--------|------|---------|
| [0000](0000-adr-template.md) | ADR Template | — | — | Blank template for new ADRs |
| [001](ADR-001-em-agent-orchestrator.md) | EM Agent as Multi-Agent Orchestrator | active | 2026-03-07 | Why multi-agent over monolithic; registry-driven routing |
| [002](ADR-002-note-triage-agent.md) | Note Triage — Three-Way Decision | active | 2026-03-07 | Why park/task/assign over binary actionable/not-actionable |
| [003](ADR-003-onboarding-agent.md) | Onboarding Agent — Artifact Generation | active | 2026-03-07 | Why generate contract+skeleton+registry at onboarding time |
| [004](ADR-004-memory-architecture.md) | Memory Architecture — Hot/Cold/Audit | active | 2026-03-07 | Three-layer memory; BM25 now, LanceDB upgrade path |
| [005](ADR-005-distributor-pattern.md) | Pluggable Distributor Pattern | active | 2026-03-07 | Why decoupled distributors over hardcoded output per agent |

---

## Contract Linkage

| Contract | Linked ADR |
|----------|-----------|
| `contracts/em-agent.yaml` | ADR-001 |
| `contracts/note-triage-agent.yaml` | ADR-002 |
| `contracts/onboarding-agent.yaml` | ADR-003 |
| (framework-level) | ADR-004, ADR-005 |

# Lessons — em-agent-framework

> Patterns captured after corrections. Reviewed at session start.

---

## L001 — Documentation drifts from code without a governance rule

**When:** Phase 2 implementation (memory architecture, BM25, distributor).
**What happened:** Multiple incongruences accumulated between ARCHITECTURE.md/README.md
and the actual codebase:
- `memory/hot/rules.md` classified as Layer 1 (immutable) but was mutable
- Cold memory described as "keyword-based" after BM25 upgrade
- Python module responsibilities listed were stale
- Onboarding Agent missing from hierarchy diagram
- README project structure missing new directories and modules

**Root cause:** ARCHITECTURE.md and README.md have no contract enforcement.
Code changes don't trigger doc updates automatically — it requires discipline.

**Rule:** After any file creation/move/rename or responsibility change, update
ARCHITECTURE.md (layer mapping) and README.md (project structure) in the same session.
Codified in `/workspace/CLAUDE.md` under "Documentation Integrity".

---

## L002 — "memory/" is not the right home for active context artifacts

**When:** Naming review of `memory/hot/rules.md`.
**What happened:** The file was placed under `memory/` because it felt like "memory",
but `memory/` in this framework means past decisions (Layer 1, immutable history).
Hot memory is a living, human-edited governance artifact — it belongs in `context/`.

**Rule:** `memory/` = past (JSONL logs, parked notes, observations).
`context/` = present (team structure, conventions, agent directives).
When creating a new context artifact, default to `context/` unless it is append-only history.

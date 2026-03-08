# Architecture: The 5-Layer CDLC Matrix

> This framework is a recursive application of the CDLC (Context Development Lifecycle)
> originally defined by Patrick Debois (Tessl). The 5-layer model and vertical promotion
> mechanism are original contributions by Fabiano Ricci.

---

## The 5×4 Matrix

Each layer of the system runs its own CDLC cycle. Layers promote signals upward
and governance downward.

```
              Generate          Evaluate            Distribute          Observe

Layer 5       Prompt,           Response correct?   Extract insight →   Recurring patterns,
Session       in-chat context   Accept/correct/     template, summary,  repeated corrections
                                reject?             rules promoted up   across sessions

Layer 4       Agent personas,   Better output       Reusable patterns   Recurring errors,
Orchestrator  checkpoints,      with rules?         cross-team          scope creep
              instructions

Layer 3       Skill packages,   Skill works in      Registry,           Adoption, forks,
Packaging     tiles             other contexts?     versioning,         degradation
                                                    dependency mgmt

Layer 2       Living contracts: Contracts self-     Executable          Drift detection:
Context       intent + ownership validate at        agreements that     code diverges from
Infra.        + rules + open    runtime vs real     adapt cross-system  intent codified in
              questions         data + human        with ownership      contract
                                feedback

Layer 1       Versioned,        Data integrity,     Replication,        Retention, pruning,
Persistence   immutable storage recovery            branching, snapshot aging
```

---

## Vertical Promotion Mechanism

**Upward (signal rises):**
- L5 → L4: Repeated correction becomes an instruction rule
- L4 → L3: Stable instruction pattern packaged as a skill
- L3 → L2: Skill reveals a domain invariant → structured artifact
- L2 → L1: Critical invariant versioned with retention policy

**Downward (governance descends):**
- L1 → L2: Data drift detected → artifact flagged for update
- L2 → L3: Invariant changed → dependent skills invalidated
- L3 → L4: Skill updated → agent instructions may behave differently
- L4 → L5: Updated instructions → agent behavior changes in sessions

**Key insight:** A single prompt correction, if the system has promotion mechanisms,
can become a governed organizational asset.

---

## How This Framework Maps to the Matrix

### Layer 1 — Persistence
- `memory/history/YYYY-MM-DD.jsonl` — immutable, append-only audit log (every agent writes here via `audit_log()`)
- `memory/notes/` — parked notes (raw input preserved, written by distributor)
- `memory/observations/` — promoted patterns (written by human or future automation)

### Layer 2 — Context Infrastructure
- `agents.yaml` — Agent Registry: single source of truth for all registered agents
- `contracts/*.yaml` — C-DAD contracts (intent + ownership + validation + open questions)
- `context/team-roster.md` — living artifact, updated when team changes
- `context/team-conventions.md` — working agreements that govern task structure
- `context/agent-directives.md` — agent directives: routing rules, effort calibration, EM preferences (mutable, human-edited, always loaded into agent context)

### Layer 3 — Packaging
- `skills/note-triage/` — Tessl-compatible skill: `skill.md` (prompt) + `skill.yaml` (metadata)
- `skills/onboarding/` — Tessl-compatible skill for the Onboarding Agent (same structure)
- Skills are versioned, reusable, and can be published to tessl.io/registry

### Layer 4 — Orchestration
- `src/orchestrator.py` — EM Agent: runs agents with C-DAD validation (lifecycle + pre-run + post-run) + distribution hooks
- `squad.py` — Interactive CLI: action menu (Run Agent / Run Evals / Detect Promotions / Close Task)
- `src/agents/note_triage.py` — Note Triage Agent: implements the triage contract
- `src/agents/onboarding.py` — Onboarding Agent: generates new agent artifacts from description
- `src/context_engine/validator.py` — C-DAD runtime validator (lifecycle check, pre-run context sources, post-run output schema)
- `src/context_engine/promoter.py` — Vertical promotion detector: scans JSONL history, proposes L5→L4 rules, applies to agent-directives.md
- `src/evals/runner.py` — Eval runner: runs fixture notes through triage, collects EM corrections, reports accuracy
- `src/distributors/markdown.py` — Default distributor: writes to `output/tasks.md` + `output/backlog.md`
- Each agent has a contract that defines its scope, boundaries, and validation rules

### Layer 5 — Session
- Each run of the orchestrator is a complete CDLC cycle:
  - **Generate:** raw note input
  - **Evaluate:** Claude API assesses actionability, effort, ownership
  - **Distribute:** decision written to task output and memory
  - **Observe:** JSONL log enables pattern detection across sessions

---

## Technology Choices

### What is Python and why

Python handles only **deterministic plumbing** — zero LLM reasoning lives here:
- `loader.py` — contract-driven context loader: reads `context_sources` from the agent contract, assembles a `ContextBundle(sources, skill_prompt)` for any agent; `load_note_triage_context()` is a thin backward-compatible wrapper
- `memory.py` — hot/cold/audit memory engine (BM25 search, audit log, daily summary)
- `validator.py` — C-DAD runtime validation (pre-run context sources, post-run output schema)
- `note_triage.py` — calls Claude API with enriched context (hot + cold memory), parses JSON response
- `orchestrator.py` — runs agents with validation + distribution hooks; programmatic API entry point
- `distributors/markdown.py` — writes triage decisions to `output/tasks.md` and `output/backlog.md`; also writes `output/tasks.jsonl` (status=open/closed) for task lifecycle tracking

### What is markdown and why

The **intelligence** lives in markdown files — not in Python:
- `skills/note-triage/skill.md` — the agent's system prompt, loaded at runtime
- `contracts/*.yaml` — define agent scope, boundaries, validation rules
- `context/*.md` — team roster, conventions, domain knowledge

This separation means you can change agent behavior by editing a markdown file.
No code change, no redeploy. The Python layer never needs to change unless the
I/O contract changes.

### What is YAML and why

YAML for contracts and skill metadata — structured enough for machines to parse,
readable enough for humans to maintain without tooling.

---

## Memory Architecture

Three formal memory layers govern how agents access context and past decisions.

### Hot Memory (`context/agent-directives.md`)
- Small, always loaded — injected into every agent's context before the API call
- Contains: routing rules, effort calibration patterns, team shortcuts, EM preferences
- Human-editable markdown — no code change required to adjust behavior
- Future: auto-promoted from L5 corrections (when the EM edits a decision, the pattern rises to a rule)

### Cold Memory (`memory/history/*.jsonl`)
- Grows unbounded — every past triage decision is stored here
- Accessed only when relevant: `search_cold_memory()` pulls top-K entries matching the current note
- Phase 2 indexer: **BM25** (Okapi BM25, `rank-bm25`) — scores by term frequency + document length normalization, zero API cost
- Injected as "Related past decisions" context block in the agent prompt
- Routing rule: park decisions are skipped during search (not useful for recall)
- Phase 5 upgrade path: LanceDB (MIT, embedded, no server) for semantic vector search when corpus exceeds ~10K decisions

### Audit Memory (`memory/history/*.jsonl`)
- Same files as cold memory, formalized as an immutable audit log
- Every agent calls `audit_log(agent_id, input, output)` — the `agent_id` field enables multi-agent traceability
- Replaces per-agent `_persist()` functions — one generic function, all agents

### Memory Engine (`src/context_engine/memory.py`)
```
load_hot_memory()                     → str (rules.md content)
search_cold_memory(query, top_k=3)    → list[dict] (past task/assign decisions)
format_cold_memory_context(entries)   → str (markdown context block)
audit_log(agent_id, input, output)    → None (appends to JSONL)
today_summary()                       → dict (counts for daily CLI panel)
```

---

## C-DAD: Contract-Driven AI Development

> Concept by **Enrico Piovesan** — [C-DAD White Paper](https://it.scribd.com/document/991003633/Contract-Driven-AI-Development-C-DAD-White-Paper)

Each agent has a contract (in `contracts/`) that encodes:
- **Intent** — why this agent exists
- **Ownership** — who is responsible
- **Lifecycle** — `draft | active | deprecated | retired` (explicit state, machine-readable)
- **Provenance** — author, published date, ADR link
- **Validation rules** — how to verify correctness
- **Open questions** — what's still uncertain

Contracts are not static documents. They evolve as patterns are promoted upward.
A routing rule that starts as an EM correction (L5) can become a contract invariant (L2).

**Phase 3 additions:**
- ADR documents (`docs/adr/`) — 5 retroactive ADRs covering every major architectural decision.
  Linked from each contract's `provenance.adr` field. See `docs/adr/README.md` for the index.
- Contract lifecycle enforcement — `validate_lifecycle()` in `validator.py` blocks `draft`/`retired`
  contracts, warns on `deprecated`. Called before every agent run.
- Eval runner — `src/evals/runner.py` with gold-standard fixtures (`evals/fixtures/notes.jsonl`),
  EM correction loop, and accuracy report (classification + owner + no-note-loss).
- Vertical promotion detector — `src/context_engine/promoter.py` scans JSONL history for
  routing and effort patterns, proposes rules to the EM, and appends approved rules to
  `context/agent-directives.md` with an observations log.

---

## Pluggable Distributor

The "Distribute" step is decoupled from agents. Every agent declares a `distributor` in `agents.yaml`.
The orchestrator resolves and calls it after each successful run.

```
src/distributors/
├── base.py       → Distributor Protocol (interface)
└── markdown.py   → Default: writes to output/ directory
```

Phase 2 baseline: `MarkdownDistributor`
- `park`   → `output/backlog.md` (running log) + `memory/notes/<slug>.md` (individual file)
- `task`   → `output/tasks.md` (running log) + `output/tasks.jsonl` (status=open)
- `assign` → `output/tasks.md` (running log) + `output/tasks.jsonl` (status=open)
- Task lifecycle: `output/tasks.jsonl` records `{id, date, decision, note, owner, effort, status}` — status transitions `open → closed` via the CLI Close Task action

Phase 3 planned: `NotionDistributor`, `GitHubDistributor` — swap by changing one line in `agents.yaml`.

---

## Agent Hierarchy

```
                         EM Agent (Orchestrator)
                                  │
          ┌───────────┬───────────┼───────────┬───────────┐
          │           │           │           │           │
    Note Triage   Onboarding  DevOps Agent  Dev Agent  QA Agent
      Agent         Agent      (planned)   (planned)  (planned)
    (Phase 1)    (Phase 1)
```

---

## What "Technology-Agnostic" Means Here

- Contracts are YAML — readable by any agent, any runtime
- Skills are Markdown + YAML — no framework lock-in (Tessl-compatible)
- Context files are Markdown — editable by humans, readable by agents
- History is JSONL — importable into any database when scale requires it
- The orchestrator uses the Claude API, but contracts and skills survive model changes
- Swapping the Python layer for another language requires changing only 3 files

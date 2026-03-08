# EM Agent Framework

> *To Anna, Domenico, and Giulia:*
> *the best team I could ever have to achieve my goals.*

---

An Engineering Manager Agent built on the 5-layer CDLC matrix — a multi-agent system
where a lead EM agent orchestrates sub-agents that mirror the roles of a real engineering team.

Built with Claude Code, Claude API, and a contract-driven approach (C-DAD).

---

## What It Does

**Today (Phase 1):** Takes a raw EM note and triages it into a structured decision:
- **Park** — not actionable yet, store in backlog
- **Task** — actionable, needs EM to assign
- **Assign** — actionable, agent suggests an owner from the team roster

```bash
python squad.py
# → Select Note Triage
# → Enter your note: The deploy pipeline has been flaky for 3 days. Anna keeps manually retrying.
```

```
📋  Decision: TASK

Reasoning: The pipeline flakiness is clearly actionable and impacting team productivity.
Anna is the primary CI/CD owner but her current workload should be verified before assigning.
Assigning would require EM confirmation given the impact on the team.

Effort:    medium
Owner:     Anna (pending EM confirmation)

Acceptance Criteria:
  1. Pipeline succeeds without manual intervention for 10 consecutive runs
  2. Root cause identified and documented

Logged: memory/history/2026-03-06.jsonl
```

---

## Architecture

The framework maps to the 5-layer CDLC matrix (Patrick Debois, 2024):

```
Layer 5 — Session:       Each note triage is a Generate → Evaluate → Distribute → Observe cycle
Layer 4 — Orchestration: EM Agent routes inputs to sub-agents, reviews outputs
Layer 3 — Packaging:     Skills (note-triage, team-routing) are versioned, reusable packages
Layer 2 — Context Infra: Contracts (C-DAD), team roster, conventions are living artifacts
Layer 1 — Persistence:   Immutable JSONL history, parked notes, promoted observations
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for the complete matrix and vertical promotion model.

---

## Project Structure

```
em-agent-framework/
├── agents.yaml             # Agent registry — single source of truth
├── squad.py                # Interactive CLI entry point
├── contracts/              # C-DAD contracts for each agent
├── skills/                 # Tessl-compatible skill packages
├── context/                # Layer 2 artifacts: team roster, conventions, agent directives
├── memory/
│   ├── history/            # Immutable audit log — JSONL, per day (Layer 1)
│   ├── notes/              # Parked notes (Layer 1)
│   └── observations/       # Promoted patterns (Layer 1)
├── output/                 # Distributor output: tasks.md, backlog.md
├── docs/adr/               # Architecture Decision Records (5 retroactive ADRs)
├── evals/
│   ├── fixtures/           # Gold-standard test notes (10 seeded fixtures)
│   └── results/            # Eval run results (JSONL, per day)
├── requirements.txt
└── src/
    ├── orchestrator.py     # Agent runner: C-DAD validation + distribution hooks
    ├── agents/
    │   ├── note_triage.py
    │   └── onboarding.py
    ├── context_engine/
    │   ├── loader.py
    │   ├── registry.py     # Registry loader (reads agents.yaml)
    │   ├── memory.py       # Hot/Cold/Audit memory engine (BM25 search)
    │   ├── validator.py    # C-DAD runtime validator (lifecycle + pre/post-run)
    │   └── promoter.py     # Vertical promotion detector (L5 → L4)
    ├── evals/
    │   └── runner.py       # Eval runner: fixtures → triage → EM review → accuracy report
    └── distributors/
        ├── base.py         # Distributor protocol (interface)
        └── markdown.py     # Default: writes to output/
```

## Agent Convention

Every agent in em-squad requires three artifacts:
1. `contracts/<id>-agent.yaml` — C-DAD contract with all required fields
2. `src/agents/<id>.py` — Python module with a single public entry function
3. Entry in `agents.yaml` — with id, name, description, module, entry, input_prompt, output_type

Use the **Onboard New Agent** option in `squad.py` to generate all three from a plain-English description.

**Design principle:** The intelligence lives in markdown (`skills/`, `contracts/`, `context/`).
Python handles only deterministic plumbing: file I/O, API calls, JSON parsing, persistence.

---

## Setup

```bash
cd em-agent-framework
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your_key_here
```

## Usage

```bash
# Interactive CLI (recommended)
python squad.py

# Programmatic API
python src/orchestrator.py note-triage "Your note here"
```

## Customize for Your Team

1. Edit `context/team-roster.md` — replace placeholder team members with your team
2. Edit `context/team-conventions.md` — update effort sizing and task conventions
3. Update `contracts/note-triage-agent.yaml` — adjust validation targets for your context

No code changes needed — the agent reads context at runtime.

---

## Roadmap

- **Phase 1 (done):** Note Triage Agent, Onboarding Agent, contracts, context files, history log
- **Phase 2 (done):** Memory architecture (Hot/Cold/Audit, BM25), C-DAD runtime validation, pluggable distributor
- **Phase 3 (done):** Framework completion — 5 ADRs (`docs/adr/`), contract lifecycle enforcement (draft/deprecated/retired), eval runner with 10 fixture notes and EM correction loop, vertical promotion detector (JSONL scan → rule proposal → agent-directives.md)
- **Phase 4:** Agent import — read existing EM assistant capabilities, translate into framework-compliant agents (contract + skill + Python skeleton + registry entry)
- **Phase 5:** Templatization — setup wizard, remove personal context, framework usable by any EM team. Followed by a real-use branch (2+ weeks) to field-test before publication. Bugs found → fix on main branch.
- **Phase 6:** Publication — Tessl skill registry → GitHub README polish → Medium article

---

## Attribution

- **CDLC (4 stages):** Patrick Debois / Tessl — [tessl.io/blog](https://tessl.io/blog/context-development-lifecycle-better-context-for-ai-coding-agents/)
- **5-layer recursive CDLC model:** Fabiano Aricci (this framework)
- **"Everything is Context" paper:** arXiv 2512.05470
- **C-DAD (Contract-Driven AI Development):** Enrico Piovesan — [White Paper on Scribd](https://it.scribd.com/document/991003633/Contract-Driven-AI-Development-C-DAD-White-Paper)

## License

Code: MIT | Documentation & contracts: CC BY 4.0

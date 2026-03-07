# EM Agent — Agent Directives

> Layer 2 context artifact. Always injected into every agent's system context.
> Edit it to calibrate routing, effort, and search behavior.
> Version: 0.2.0 | Last updated: 2026-03-07

---

## Routing Rules

- If the note mentions a specific team member by name → lean toward assign
- If the note contains "explore", "idea", "maybe", "consider", "someday" → lean toward park
- Pipeline/CI/CD notes → likely owner is Anna (DevOps lead)
- Monitoring, alerting, dashboard notes → likely owner is Domenico
- Internal tooling, API, scripting notes → likely owner is Domenico
- Cloud architecture, security, FinOps notes → likely owner is Giulia
- If note is vague or has no clear owner → prefer task over assign

---

## Effort Calibration

- Anything involving k8s cluster changes → large (minimum)
- Terraform changes to existing infra → medium
- Alert rule changes → small
- Dashboard work → medium
- New service or migration → large
- Config change, doc update → small
- When uncertain between two sizes → choose the larger

---

## Search Rules (Cold Memory)

- Always search cold memory for task and assign decisions
- Skip cold memory search for park decisions (not useful for recall)
- Top-K = 3 most recent relevant entries
- Search terms: use the main subject of the note (infra name, person, technology)

---

## EM Preferences

- Acceptance criteria must be specific and verifiable — never generic
- Preserve the original note verbatim — do not paraphrase or summarize
- Effort estimates should reflect uncertainty: when in doubt, size up
- If Giulia is suggested as owner, verify it requires cloud/security depth — otherwise prefer Anna or Domenico

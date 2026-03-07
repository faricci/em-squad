# Eval: Triage Accuracy

> Layer 3 eval definition for the Note Triage skill.
> Eval runner: manual (Phase 1) → automated (Phase 3).

## What We're Measuring

### Eval 1: Classification Accuracy (actionable vs park)

**Target:** >90% match between agent decision and EM's actual decision

**Method:**
1. Run 20 real notes through the agent
2. EM records their actual decision independently
3. Compare: did agent decide park when EM said park? task/assign when EM said actionable?
4. Track in a simple table below

**Current baseline:** not yet established

| Note # | Agent Decision | EM Decision | Match? | Notes |
|--------|---------------|-------------|--------|-------|
| ...    | ...           | ...         | ...    | ...   |

---

### Eval 2: Assignee Accuracy

**Target:** >70% match between suggested_owner and EM's chosen assignee

**Method:**
1. For all `assign` decisions, record suggested_owner
2. EM records who they actually assigned the task to
3. Compare

**Current baseline:** not yet established

| Note # | Suggested Owner | Actual Assignee | Match? | Mismatch Reason |
|--------|----------------|----------------|--------|-----------------|
| ...    | ...            | ...            | ...    | ...             |

---

### Eval 3: No Note Loss

**Target:** 100% — every input has a persisted output

**Method:** Automated check — count inputs vs records in memory/history/

```bash
# Count notes submitted (track manually or via wrapper)
# Count records in today's history
wc -l memory/history/$(date +%Y-%m-%d).jsonl
```

---

## Promotion Trigger

When any eval falls below target for 5+ consecutive runs:
→ Review skill.md and update agent instructions (L5 → L4 promotion)
→ Log pattern in memory/observations/ with timestamp

## Retrospective Notes

_Add observations here after each batch of evals._

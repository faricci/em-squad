import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Literal

import anthropic

from src.context_engine.loader import load_note_triage_context
from src.context_engine.memory import (
    audit_log,
    format_cold_memory_context,
    load_hot_memory,
    search_cold_memory,
)

Decision = Literal["park", "task", "assign"]
Effort = Literal["small", "medium", "large"] | None


@dataclass
class TriageDecision:
    decision: Decision
    reasoning: str
    effort: Effort
    suggested_owner: str | None
    acceptance_criteria: list[str]
    related_context: list[str]
    original_note: str
    timestamp: str


def triage_note(raw_note: str) -> TriageDecision:
    """
    Note Triage Agent — implements contracts/note-triage-agent.yaml.

    CDLC mapping:
        Generate  → raw note is captured context from the EM
        Evaluate  → Claude assesses actionability, effort, ownership
        Distribute → decision written to task output and memory (via orchestrator)
        Observe   → every decision appended to memory/history/ (Layer 1)
    """
    client = anthropic.Anthropic()
    context = load_note_triage_context()
    hot_memory = load_hot_memory()
    cold_entries = search_cold_memory(raw_note)
    cold_memory_ctx = format_cold_memory_context(cold_entries)

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=context.skill_prompt,
        messages=[{"role": "user", "content": _build_user_message(raw_note, context, hot_memory, cold_memory_ctx)}],
    )

    raw_output = next(b.text for b in response.content if b.type == "text")
    decision = _parse_decision(raw_output, raw_note)
    audit_log("note-triage", raw_note, asdict(decision))
    return decision


def _build_user_message(note: str, context, hot_memory: str, cold_memory_ctx: str) -> str:
    return (
        f"## Hot Memory (always active)\n\n{hot_memory}\n\n"
        f"---\n\n## Team Roster\n\n{context.sources.get('context/team-roster.md', '')}\n\n"
        f"---\n\n## Team Conventions\n\n{context.sources.get('context/team-conventions.md', '')}\n\n"
        f"---\n\n## Related Past Decisions\n\n{cold_memory_ctx}\n\n"
        f"---\n\n## Note to Triage\n\n{note}"
    )


def _parse_decision(raw_output: str, original_note: str) -> TriageDecision:
    cleaned = raw_output.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"Agent returned invalid JSON:\n{raw_output}") from e

    if data.get("decision") not in ("park", "task", "assign"):
        raise ValueError(f"Invalid decision value: {data.get('decision')}")

    return TriageDecision(
        decision=data["decision"],
        reasoning=data.get("reasoning", ""),
        effort=data.get("effort"),
        suggested_owner=data.get("suggested_owner"),
        acceptance_criteria=data.get("acceptance_criteria", []),
        related_context=data.get("related_context", []),
        original_note=data.get("original_note", original_note),
        timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat()),
    )



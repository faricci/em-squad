import json
from dataclasses import dataclass
from pathlib import Path

import anthropic

ROOT = Path(__file__).parent.parent.parent


@dataclass
class OnboardingResult:
    agent_id: str
    contract_yaml: str
    python_skeleton: str
    registry_entry: dict
    summary: str


def onboard_agent(description: str) -> OnboardingResult:
    """
    Onboarding Agent — implements contracts/onboarding-agent.yaml.

    CDLC mapping:
        Generate  → natural language description from the EM
        Evaluate  → Claude generates contract, skeleton, registry entry
        Distribute → artifacts returned for EM review (no files written here)
        Observe   → caller logs the onboarding event to memory/history/
    """
    client = anthropic.Anthropic()
    system_prompt = _build_system_prompt()
    user_message = _build_user_message(description)

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )

    raw_output = next(b.text for b in response.content if b.type == "text")
    return _parse_result(raw_output)


def _build_system_prompt() -> str:
    skill_text = (ROOT / "skills" / "onboarding" / "skill.md").read_text(encoding="utf-8")
    return skill_text + "\n\n---\n\n" + _build_dynamic_context()


def _build_dynamic_context() -> str:
    contract = (ROOT / "contracts" / "onboarding-agent.yaml").read_text(encoding="utf-8")
    note_triage_contract = (ROOT / "contracts" / "note-triage-agent.yaml").read_text(encoding="utf-8")
    note_triage_py = (ROOT / "src" / "agents" / "note_triage.py").read_text(encoding="utf-8")
    registry = (ROOT / "agents.yaml").read_text(encoding="utf-8")

    return (
        f"## Your contract (what governs you)\n\n{contract}\n\n"
        f"---\n\n## Reference: existing contract template (note-triage-agent.yaml)\n\n{note_triage_contract}\n\n"
        f"---\n\n## Reference: existing Python agent template (note_triage.py)\n\n{note_triage_py}\n\n"
        f"---\n\n## Current registry (agents.yaml) — check for duplicate IDs\n\n{registry}"
    )


def _build_user_message(description: str) -> str:
    return f"## Agent Description\n\n{description}"


def _parse_result(raw_output: str) -> OnboardingResult:
    cleaned = raw_output.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"Onboarding agent returned invalid JSON:\n{raw_output}") from e

    required = ("agent_id", "contract_yaml", "python_skeleton", "registry_entry", "summary")
    missing = [f for f in required if f not in data]
    if missing:
        raise ValueError(f"Onboarding result missing fields: {missing}")

    return OnboardingResult(
        agent_id=data["agent_id"],
        contract_yaml=data["contract_yaml"],
        python_skeleton=data["python_skeleton"],
        registry_entry=data["registry_entry"],
        summary=data["summary"],
    )

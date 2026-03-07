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
    contract = (ROOT / "contracts" / "onboarding-agent.yaml").read_text(encoding="utf-8")
    note_triage_contract = (ROOT / "contracts" / "note-triage-agent.yaml").read_text(encoding="utf-8")
    note_triage_py = (ROOT / "src" / "agents" / "note_triage.py").read_text(encoding="utf-8")
    registry = (ROOT / "agents.yaml").read_text(encoding="utf-8")

    return f"""You are the Onboarding Agent for the em-squad EM Agent Framework.

Your job is to generate three artifacts for a new agent based on a natural language description:
1. A C-DAD contract YAML file
2. A Python module skeleton
3. An agents.yaml registry entry

## Your contract (what governs you)

{contract}

---

## Reference: existing contract template (note-triage-agent.yaml)

{note_triage_contract}

---

## Reference: existing Python agent template (note_triage.py)

{note_triage_py}

---

## Current registry (agents.yaml) — check for duplicate IDs

{registry}

---

## Output format

Respond with valid JSON only. No markdown, no explanation outside the JSON block.

```json
{{
  "agent_id": "kebab-case-id",
  "contract_yaml": "full YAML content as a string",
  "python_skeleton": "full Python module content as a string",
  "registry_entry": {{
    "id": "kebab-case-id",
    "name": "Human Readable Name",
    "description": "One-line description",
    "contract": "contracts/<id>-agent.yaml",
    "module": "src.agents.<id_underscored>",
    "entry": "function_name",
    "input_prompt": "Prompt shown to user in the CLI:",
    "output_type": "type_string"
  }},
  "summary": "Human-readable description of what was created and why"
}}
```

## Conventions to follow

- agent_id: kebab-case (e.g. retro-summarizer)
- module: src.agents.<id with hyphens replaced by underscores> (e.g. src.agents.retro_summarizer)
- entry function: snake_case verb + noun (e.g. summarize_retro)
- The Python skeleton must define the entry function and return a dataclass result
- The contract must include all required C-DAD fields: name, version, purpose, owner, layer,
  responsibilities, boundaries, output_schema, validation, context_sources, open_questions,
  cdlc_mapping, promotion_rules
- Do not include any narrative or explanation outside the JSON block
"""


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

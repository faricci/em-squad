from pathlib import Path
from dataclasses import dataclass, field

import yaml

ROOT = Path(__file__).parent.parent.parent


@dataclass
class ContextBundle:
    sources: dict[str, str]
    skill_prompt: str


def _read(relative_path: str) -> str:
    path = ROOT / relative_path
    if not path.exists():
        raise FileNotFoundError(f"Context file not found: {path}")
    return path.read_text(encoding="utf-8")


def load_agent_context(contract_path: str, skill_path: str) -> ContextBundle:
    """
    Contract-driven context loader.
    Reads context_sources from the agent contract and loads each file.
    Directories (e.g. memory/history/) are skipped — loaded on demand via memory.py.
    Layer 2 → Layer 4 bridge: assembles context bundle for any registered agent.
    """
    contract_data = yaml.safe_load(_read(contract_path))
    source_paths = contract_data.get("contract", {}).get("context_sources", [])
    sources = {}
    for rel_path in source_paths:
        full_path = ROOT / rel_path
        if full_path.is_file():
            sources[rel_path] = full_path.read_text(encoding="utf-8")
    return ContextBundle(sources=sources, skill_prompt=_read(skill_path))


def load_note_triage_context() -> ContextBundle:
    """
    Loads context files required by the Note Triage Agent.
    Thin wrapper over load_agent_context — kept for zero breakage risk.
    """
    return load_agent_context(
        "contracts/note-triage-agent.yaml",
        "skills/note-triage/skill.md",
    )


def history_path() -> Path:
    """Immutable append-only decision logs — Layer 1."""
    path = ROOT / "memory" / "history"
    path.mkdir(parents=True, exist_ok=True)
    return path


def notes_path() -> Path:
    """Parked notes directory."""
    path = ROOT / "memory" / "notes"
    path.mkdir(parents=True, exist_ok=True)
    return path

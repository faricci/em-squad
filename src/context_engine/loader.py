from pathlib import Path
from dataclasses import dataclass

ROOT = Path(__file__).parent.parent.parent


@dataclass
class ContextBundle:
    team_roster: str
    team_conventions: str
    skill_prompt: str


def _read(relative_path: str) -> str:
    path = ROOT / relative_path
    if not path.exists():
        raise FileNotFoundError(f"Context file not found: {path}")
    return path.read_text(encoding="utf-8")


def load_note_triage_context() -> ContextBundle:
    """
    Loads context files required by the Note Triage Agent.
    Layer 2 → Layer 4 bridge: structured context artifacts assembled for the agent.
    """
    return ContextBundle(
        team_roster=_read("context/team-roster.md"),
        team_conventions=_read("context/team-conventions.md"),
        skill_prompt=_read("skills/note-triage/skill.md"),
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

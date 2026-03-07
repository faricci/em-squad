from dataclasses import dataclass
from pathlib import Path

import yaml

ROOT = Path(__file__).parent.parent.parent
REGISTRY_PATH = ROOT / "agents.yaml"


@dataclass
class AgentEntry:
    id: str
    name: str
    description: str
    contract: str
    module: str
    entry: str
    input_prompt: str
    output_type: str
    distributor: str = "markdown"


def load_registry() -> list[AgentEntry]:
    """Load all agents from agents.yaml."""
    data = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))
    return [AgentEntry(**a) for a in data["agents"]]


def get_agent(agent_id: str) -> AgentEntry:
    """Return a single agent by id. Raises KeyError if not found."""
    agents = {a.id: a for a in load_registry()}
    if agent_id not in agents:
        raise KeyError(f"Agent '{agent_id}' not found in registry.")
    return agents[agent_id]


def append_agent(entry: AgentEntry) -> None:
    """Append a new agent entry to agents.yaml."""
    data = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))
    existing_ids = {a["id"] for a in data["agents"]}
    if entry.id in existing_ids:
        raise ValueError(f"Agent id '{entry.id}' already exists in registry.")
    data["agents"].append({
        "id": entry.id,
        "name": entry.name,
        "description": entry.description,
        "contract": entry.contract,
        "module": entry.module,
        "entry": entry.entry,
        "input_prompt": entry.input_prompt,
        "output_type": entry.output_type,
        "distributor": entry.distributor,
    })
    REGISTRY_PATH.write_text(yaml.dump(data, default_flow_style=False, allow_unicode=True), encoding="utf-8")

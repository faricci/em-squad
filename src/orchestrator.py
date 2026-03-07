#!/usr/bin/env python3
"""
EM Agent Orchestrator — programmatic API entry point.

Usage:
    python src/orchestrator.py <agent_id> "Your input here"
    python src/orchestrator.py note-triage "The deploy pipeline is broken"

Interactive CLI:
    python squad.py
"""
import importlib
import sys
from dataclasses import asdict
from typing import Any

from src.context_engine.registry import get_agent
from src.context_engine.validator import validate_pre_run, validate_post_run
from src.distributors.markdown import MarkdownDistributor


def run(agent_id: str, user_input: str) -> Any:
    """Run an agent by id with C-DAD validation and distribution."""
    agent = get_agent(agent_id)

    # Pre-run: verify all contract context sources exist on disk
    validate_pre_run(agent.contract)

    # Run agent
    module = importlib.import_module(agent.module)
    fn = getattr(module, agent.entry)
    result = fn(user_input)

    # Post-run: verify output shape matches contract schema
    try:
        output_dict = asdict(result)
    except TypeError:
        output_dict = vars(result) if hasattr(result, "__dict__") else {}

    validate_post_run(agent.contract, output_dict)

    # Distribute
    distributor = _load_distributor(getattr(agent, "distributor", "markdown") or "markdown")
    distributor.distribute(result, agent)

    return result


def _load_distributor(name: str):
    if name == "markdown":
        return MarkdownDistributor()
    raise ValueError(f"Unknown distributor: '{name}'. Available: markdown")


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: python src/orchestrator.py <agent_id> \"Your input\"", file=sys.stderr)
        print("       python src/orchestrator.py note-triage \"Note text\"", file=sys.stderr)
        print("\nFor interactive mode: python squad.py", file=sys.stderr)
        sys.exit(1)

    agent_id = sys.argv[1]
    user_input = " ".join(sys.argv[2:])

    if not user_input.strip():
        print("Error: no input provided.", file=sys.stderr)
        sys.exit(1)

    result = run(agent_id, user_input)
    print(result)


if __name__ == "__main__":
    main()

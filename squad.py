#!/usr/bin/env python3
"""
squad.py — Interactive CLI for em-squad.

Usage:
    python squad.py
"""
import sys
from pathlib import Path

import questionary
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from src.context_engine.memory import today_summary
from src.context_engine.registry import AgentEntry, append_agent, load_registry
from src.orchestrator import run as run_agent

console = Console()


def main() -> None:
    console.print()
    console.print(Panel.fit("[bold]em-squad[/bold]", border_style="dim"))
    console.print()

    summary = today_summary()
    if summary["total"] > 0:
        console.print(
            f"[dim]Today: {summary['total']} decision{'s' if summary['total'] != 1 else ''}  "
            f"({summary['park']} park · {summary['task']} task · {summary['assign']} assign)[/dim]"
        )
        console.print()

    agents = load_registry()
    choices = [questionary.Choice(title=a.name, value=a) for a in agents]

    agent: AgentEntry = questionary.select(
        "Select agent:",
        choices=choices,
    ).ask()

    if agent is None:
        sys.exit(0)

    console.print()
    user_input = questionary.text(agent.input_prompt).ask()

    if user_input is None or not user_input.strip():
        console.print("[yellow]No input provided. Exiting.[/yellow]")
        sys.exit(0)

    console.print()
    console.print("[dim]Running...[/dim]")
    console.print()

    result = run_agent(agent.id, user_input.strip())

    if agent.output_type == "triage":
        _render_triage(result)
    elif agent.output_type == "onboarding":
        _render_onboarding(result, agent)
    else:
        console.print(result)


def _render_triage(d) -> None:
    icons = {"park": "Archive", "task": "Task", "assign": "Assign"}
    colors = {"park": "blue", "task": "yellow", "assign": "green"}
    color = colors.get(d.decision, "white")

    console.print(Panel(
        f"[bold {color}]{d.decision.upper()}[/bold {color}]\n\n{d.reasoning}",
        title=f"[bold]Decision: {icons.get(d.decision, d.decision)}[/bold]",
        border_style=color,
    ))

    details = Text()
    if d.effort:
        details.append(f"Effort:  {d.effort}\n", style="dim")
    if d.suggested_owner:
        details.append(f"Owner:   {d.suggested_owner} ", style="dim")
        details.append("(pending EM confirmation)\n", style="italic dim")
    if details:
        console.print(details)

    if d.acceptance_criteria:
        console.print("[bold]Acceptance Criteria[/bold]")
        for i, c in enumerate(d.acceptance_criteria, 1):
            console.print(f"  {i}. {c}")
        console.print()

    if d.related_context:
        console.print("[bold]Related Context[/bold]")
        for r in d.related_context:
            console.print(f"  - {r}")
        console.print()

    today = d.timestamp.split("T")[0]
    console.print(f"[dim]Logged:  memory/history/{today}.jsonl[/dim]")
    if d.decision == "park":
        slug = d.timestamp.replace(":", "-").replace(".", "-")
        console.print(f"[dim]Parked:  memory/notes/{slug}.md[/dim]")
        console.print(f"[dim]Output:  output/backlog.md[/dim]")
    else:
        console.print(f"[dim]Output:  output/tasks.md[/dim]")


def _render_onboarding(result, agent: AgentEntry) -> None:
    console.print(Panel(
        result.summary,
        title=f"[bold]New Agent: {result.agent_id}[/bold]",
        border_style="cyan",
    ))

    console.print()
    console.print("[bold]Contract preview[/bold] (contracts/{}-agent.yaml)".format(result.agent_id))
    console.print(Syntax(result.contract_yaml, "yaml", theme="monokai", line_numbers=False))

    console.print()
    console.print("[bold]Python skeleton preview[/bold] (src/agents/{}.py)".format(
        result.agent_id.replace("-", "_")
    ))
    console.print(Syntax(result.python_skeleton, "python", theme="monokai", line_numbers=False))

    console.print()
    confirmed = questionary.confirm(
        "Write these files to disk?",
        default=False,
    ).ask()

    if not confirmed:
        console.print("[yellow]Aborted. No files written.[/yellow]")
        return

    _write_onboarding_files(result)


def _write_onboarding_files(result) -> None:
    from src.context_engine.registry import AgentEntry

    contract_path = ROOT / "contracts" / f"{result.agent_id}-agent.yaml"
    module_id = result.agent_id.replace("-", "_")
    skeleton_path = ROOT / "src" / "agents" / f"{module_id}.py"

    contract_path.write_text(result.contract_yaml, encoding="utf-8")
    console.print(f"[green]Written:[/green] contracts/{result.agent_id}-agent.yaml")

    skeleton_path.write_text(result.python_skeleton, encoding="utf-8")
    console.print(f"[green]Written:[/green] src/agents/{module_id}.py")

    entry = result.registry_entry
    new_agent = AgentEntry(
        id=entry["id"],
        name=entry["name"],
        description=entry["description"],
        contract=entry["contract"],
        module=entry["module"],
        entry=entry["entry"],
        input_prompt=entry["input_prompt"],
        output_type=entry["output_type"],
    )
    append_agent(new_agent)
    console.print(f"[green]Registered:[/green] {result.agent_id} added to agents.yaml")
    console.print()
    console.print("[bold green]Done.[/bold green] Run [bold]python squad.py[/bold] to use your new agent.")


if __name__ == "__main__":
    main()

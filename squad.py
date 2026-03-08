#!/usr/bin/env python3
"""
squad.py — Interactive CLI for em-squad.

Usage:
    python squad.py
"""
import json
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

_ACTION_RUN_AGENT = "Run Agent"
_ACTION_RUN_EVALS = "Run Evals"
_ACTION_PROMOTIONS = "Detect Promotions"
_ACTION_CLOSE_TASK = "Close Task"


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

    action = questionary.select(
        "What would you like to do?",
        choices=[
            _ACTION_RUN_AGENT,
            _ACTION_RUN_EVALS,
            _ACTION_PROMOTIONS,
            _ACTION_CLOSE_TASK,
        ],
    ).ask()

    if action is None:
        sys.exit(0)

    if action == _ACTION_RUN_EVALS:
        _run_evals()
        return

    if action == _ACTION_PROMOTIONS:
        _run_promotions()
        return

    if action == _ACTION_CLOSE_TASK:
        _run_close_task()
        return

    # Default: run agent
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


def _run_evals() -> None:
    from src.evals.runner import run_eval
    run_eval(console, interactive=True)


def _run_promotions() -> None:
    from src.context_engine.promoter import detect_promotions, apply_promotion

    console.print()
    console.print("[dim]Scanning history for promotion candidates...[/dim]")
    candidates = detect_promotions(min_occurrences=3)

    if not candidates:
        console.print("[yellow]No promotion candidates found. Run more notes to build history.[/yellow]")
        return

    console.print(f"\nFound [bold]{len(candidates)}[/bold] candidate(s).\n")

    applied = 0
    skipped = 0

    for i, candidate in enumerate(candidates, 1):
        console.print(f"[bold]Candidate {i}/{len(candidates)}[/bold] — {candidate['pattern_type']}")
        console.print(f"Proposed rule: [cyan]{candidate['proposed_rule']}[/cyan]")
        console.print(f"Section: [dim]{candidate['section']}[/dim]")
        console.print("Evidence:")
        for note in candidate["evidence"][:3]:
            console.print(f"  [dim]· {note[:100]}[/dim]")
        console.print()

        confirm = questionary.confirm("Apply this rule to agent-directives.md?", default=False).ask()
        if confirm is None:
            break
        if confirm:
            apply_promotion(candidate["proposed_rule"], candidate["section"])
            console.print("[green]Applied.[/green]")
            applied += 1
        else:
            console.print("[dim]Skipped.[/dim]")
            skipped += 1
        console.print()

    console.print(f"[bold]Done.[/bold] Applied: {applied} · Skipped: {skipped}")
    if applied > 0:
        console.print("[dim]Rules written to context/agent-directives.md[/dim]")
        console.print("[dim]Log written to memory/observations/[/dim]")


def _run_close_task() -> None:
    tasks_jsonl = ROOT / "output" / "tasks.jsonl"
    if not tasks_jsonl.exists():
        console.print("[yellow]No tasks found. Run Note Triage first.[/yellow]")
        return

    records = []
    for line in tasks_jsonl.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    open_tasks = [r for r in records if r.get("status") == "open"]
    if not open_tasks:
        console.print("[yellow]No open tasks found.[/yellow]")
        return

    choices = [
        questionary.Choice(
            title=f"[{r['date']}] {r['decision'].upper()} — {r['note'][:60]}",
            value=r,
        )
        for r in open_tasks
    ]

    selected = questionary.select("Select task to close:", choices=choices).ask()
    if selected is None:
        return

    for r in records:
        if r["id"] == selected["id"]:
            r["status"] = "closed"

    tasks_jsonl.write_text(
        "\n".join(json.dumps(r) for r in records) + "\n",
        encoding="utf-8",
    )
    console.print(f"[green]Closed:[/green] {selected['note'][:60]}")
    console.print(f"[dim]Updated: output/tasks.jsonl[/dim]")


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

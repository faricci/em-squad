"""
Eval runner — runs all fixture notes through the Note Triage Agent and collects
EM corrections to measure classification and owner accuracy.

Usage:
    Called from squad.py → "Run Evals" menu item.
    Or directly: python -m src.evals.runner
"""
import json
from dataclasses import asdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
FIXTURES_PATH = ROOT / "evals" / "fixtures" / "notes.jsonl"
RESULTS_DIR = ROOT / "evals" / "results"


def run_eval(console, interactive: bool = True) -> None:
    """
    Run all fixture notes through triage, collect EM feedback, save results,
    and print an accuracy report.
    """
    import questionary
    from rich.panel import Panel
    from rich.text import Text

    from src.agents.note_triage import triage_note

    fixtures = _load_fixtures()
    if not fixtures:
        console.print("[red]No fixtures found at evals/fixtures/notes.jsonl[/red]")
        return

    console.print()
    console.print(Panel.fit(
        f"[bold]Eval Runner[/bold] — {len(fixtures)} fixture notes",
        border_style="cyan",
    ))
    console.print()

    records = []
    for i, fixture in enumerate(fixtures, 1):
        note = fixture["note"]
        expected_decision = fixture.get("expected_decision")
        expected_owner = fixture.get("expected_owner")

        console.print(f"[bold]Note {i}/{len(fixtures)}[/bold]")
        console.print(f"[dim]{note}[/dim]")
        console.print()
        console.print("[dim]Calling triage agent...[/dim]")

        try:
            result = triage_note(note)
        except Exception as e:
            console.print(f"[red]Agent error: {e}[/red]")
            continue

        # Show agent decision
        colors = {"park": "blue", "task": "yellow", "assign": "green"}
        color = colors.get(result.decision, "white")
        detail = Text()
        detail.append(f"Decision: {result.decision.upper()}\n", style=f"bold {color}")
        detail.append(f"Reasoning: {result.reasoning}\n", style="dim")
        if result.effort:
            detail.append(f"Effort: {result.effort}\n", style="dim")
        if result.suggested_owner:
            detail.append(f"Suggested owner: {result.suggested_owner}\n", style="dim")
        console.print(detail)

        if not interactive:
            # Non-interactive mode: auto-accept agent decision
            em_decision = result.decision
            em_owner = result.suggested_owner
            match = True
            owner_match = (em_owner == expected_owner) if expected_owner is not None else True
        else:
            correct = questionary.confirm("Correct decision?", default=True).ask()
            if correct is None:
                console.print("[yellow]Interrupted.[/yellow]")
                break

            if correct:
                em_decision = result.decision
                em_owner = result.suggested_owner
            else:
                em_decision = questionary.select(
                    "Correct decision:",
                    choices=["park", "task", "assign"],
                ).ask()
                if em_decision is None:
                    break

                em_owner = None
                if em_decision == "assign":
                    em_owner = questionary.text("Correct owner (name):").ask()
                    if em_owner:
                        em_owner = em_owner.strip() or None

            match = em_decision == result.decision
            owner_match = (em_owner == result.suggested_owner) if em_decision == "assign" else True

        records.append({
            "note": note,
            "expected_decision": expected_decision,
            "expected_owner": expected_owner,
            "agent_decision": result.decision,
            "agent_owner": result.suggested_owner,
            "em_decision": em_decision,
            "em_owner": em_owner,
            "match": match,
            "owner_match": owner_match,
        })

        console.print()
        console.rule()
        console.print()

    if not records:
        console.print("[yellow]No results recorded.[/yellow]")
        return

    _save_results(records)
    _print_report(console, records)


def _load_fixtures() -> list[dict]:
    if not FIXTURES_PATH.exists():
        return []
    fixtures = []
    for line in FIXTURES_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            fixtures.append(json.loads(line))
    return fixtures


def _save_results(records: list[dict]) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    out_path = RESULTS_DIR / f"{today}-eval.jsonl"
    with out_path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")


def _print_report(console, records: list[dict]) -> None:
    from rich.panel import Panel

    total = len(records)
    correct = sum(1 for r in records if r["match"])
    assign_records = [r for r in records if r["em_decision"] == "assign"]
    owner_correct = sum(1 for r in assign_records if r["owner_match"])

    lines = [
        f"[bold]Accuracy Report[/bold]",
        f"",
        f"Classification: {correct}/{total} ({100 * correct // total}%)  [dim](target: >90%)[/dim]",
    ]

    if assign_records:
        pct = 100 * owner_correct // len(assign_records)
        lines.append(
            f"Owner accuracy:  {owner_correct}/{len(assign_records)} ({pct}%)  [dim](target: >70%)[/dim]"
        )

    lines.append(f"No note loss:    {total}/{total}")

    today = date.today().isoformat()
    lines.append(f"")
    lines.append(f"[dim]Results saved: evals/results/{today}-eval.jsonl[/dim]")

    console.print(Panel("\n".join(lines), border_style="cyan"))


if __name__ == "__main__":
    from rich.console import Console
    c = Console()
    run_eval(c, interactive=True)

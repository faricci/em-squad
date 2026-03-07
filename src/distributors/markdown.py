"""
markdown.py — Default file-based distributor.

park   → output/backlog.md (append) + memory/notes/<slug>.md
task   → output/tasks.md (append)
assign → output/tasks.md (append)
"""

from pathlib import Path
from typing import Any

ROOT = Path(__file__).parent.parent.parent


class MarkdownDistributor:
    def distribute(self, result: Any, agent: Any) -> str:
        if agent.output_type != "triage":
            return "no-op: distributor only handles triage output"

        output_dir = ROOT / "output"
        output_dir.mkdir(parents=True, exist_ok=True)

        decision = result.decision
        ts = result.timestamp
        note = result.original_note
        owner = result.suggested_owner or "unassigned"
        effort = result.effort or "—"

        if decision == "park":
            return self._distribute_park(result, output_dir, ts, note)
        else:
            return self._distribute_task(decision, output_dir, ts, note, owner, effort)

    def _distribute_park(self, result: Any, output_dir: Path, ts: str, note: str) -> str:
        # Append to output/backlog.md
        backlog = output_dir / "backlog.md"
        _ensure_header(
            backlog,
            "# Backlog — Parked Notes\n\n"
            "| Date | Note | Reasoning |\n"
            "|------|------|-----------|\n",
        )
        date_str = ts[:10]
        reasoning_short = result.reasoning[:100].replace("|", "\\|")
        note_short = note[:80].replace("|", "\\|")
        with backlog.open("a", encoding="utf-8") as f:
            f.write(f"| {date_str} | {note_short} | {reasoning_short} |\n")

        # Write individual memory note
        slug = ts.replace(":", "-").replace(".", "-")
        notes_dir = ROOT / "memory" / "notes"
        notes_dir.mkdir(parents=True, exist_ok=True)
        note_file = notes_dir / f"{slug}.md"
        content = (
            f"# Parked Note\n\n"
            f"**Date:** {ts}\n"
            f"**Tags:** parked\n\n"
            f"## Original Note\n\n{note}\n\n"
            f"## Reasoning\n\n{result.reasoning}\n\n"
            f"## Related Context\n\n"
            + "\n".join(f"- {r}" for r in result.related_context)
            + "\n"
        )
        note_file.write_text(content, encoding="utf-8")

        return f"Parked → output/backlog.md + memory/notes/{slug}.md"

    def _distribute_task(
        self,
        decision: str,
        output_dir: Path,
        ts: str,
        note: str,
        owner: str,
        effort: str,
    ) -> str:
        tasks = output_dir / "tasks.md"
        _ensure_header(
            tasks,
            "# Tasks\n\n"
            "| Date | Decision | Owner | Effort | Note |\n"
            "|------|----------|-------|--------|------|\n",
        )
        date_str = ts[:10]
        note_short = note[:80].replace("|", "\\|")
        with tasks.open("a", encoding="utf-8") as f:
            f.write(
                f"| {date_str} | {decision.upper()} | {owner} | {effort} | {note_short} |\n"
            )

        return "Distributed → output/tasks.md"


def _ensure_header(path: Path, header: str) -> None:
    """Write header if file is new or empty."""
    if not path.exists() or path.stat().st_size == 0:
        path.write_text(header, encoding="utf-8")

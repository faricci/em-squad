"""
promoter.py — Vertical Promotion Detector (L5 → L4).

Scans JSONL history for recurring patterns that are not yet captured in
context/agent-directives.md. Proposes new routing rules and effort calibrations
for EM approval. On approval, appends the rule to agent-directives.md and logs
to memory/observations/.

Usage:
    Called from squad.py → "Detect Promotions" menu item.
"""
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
HISTORY_DIR = ROOT / "memory" / "history"
DIRECTIVES_PATH = ROOT / "context" / "agent-directives.md"
OBSERVATIONS_DIR = ROOT / "memory" / "observations"

_SECTION_ROUTING = "## Routing Rules"
_SECTION_EFFORT = "## Effort Calibration"


def detect_promotions(min_occurrences: int = 3) -> list[dict]:
    """
    Scan all JSONL history. Return candidate promotions:

    - routing_rule: suggested_owner X appears >= min_occurrences times for assign decisions
      with no matching rule already in agent-directives.md.
    - effort_calibration: a keyword cluster dominates with a specific effort level
      >= min_occurrences times with no matching rule already in agent-directives.md.

    Returns a list of candidate dicts:
        {
            "pattern_type": "routing_rule" | "effort_calibration",
            "proposed_rule": str,
            "section": str,         # section header in agent-directives.md
            "evidence": list[str],  # sample notes that support the pattern
        }
    """
    entries = _load_history()
    existing_directives = DIRECTIVES_PATH.read_text(encoding="utf-8") if DIRECTIVES_PATH.exists() else ""

    candidates = []
    candidates.extend(_detect_routing_rules(entries, existing_directives, min_occurrences))
    candidates.extend(_detect_effort_calibration(entries, existing_directives, min_occurrences))
    return candidates


def apply_promotion(proposed_rule: str, section: str) -> None:
    """
    Append proposed_rule under the named section in context/agent-directives.md.
    Log the promotion to memory/observations/YYYY-MM-DD-promotions.md.
    """
    _append_to_directives(proposed_rule, section)
    _log_observation(proposed_rule, section)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_history() -> list[dict]:
    entries = []
    if not HISTORY_DIR.exists():
        return entries
    for jsonl_file in sorted(HISTORY_DIR.glob("*.jsonl")):
        for line in jsonl_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries


def _detect_routing_rules(entries: list[dict], existing: str, min_occ: int) -> list[dict]:
    """Find owners that appear frequently in assign decisions but have no routing rule."""
    owner_notes: dict[str, list[str]] = {}

    for entry in entries:
        output = entry.get("output", {})
        if output.get("decision") != "assign":
            continue
        owner = output.get("suggested_owner")
        if not owner:
            continue
        note = entry.get("input", "")
        owner_notes.setdefault(owner, []).append(note)

    candidates = []
    for owner, notes in owner_notes.items():
        if len(notes) < min_occ:
            continue
        # Check if a routing rule for this owner already exists
        pattern = re.compile(rf"\b{re.escape(owner)}\b", re.IGNORECASE)
        if pattern.search(existing):
            continue
        proposed = f"- Notes mentioning {owner}'s domain → suggest {owner} as owner"
        candidates.append({
            "pattern_type": "routing_rule",
            "proposed_rule": proposed,
            "section": _SECTION_ROUTING,
            "evidence": notes[:5],
        })
    return candidates


def _detect_effort_calibration(entries: list[dict], existing: str, min_occ: int) -> list[dict]:
    """Find keyword clusters with a dominant effort level not already in directives."""
    # Simple keyword extraction: top 2 non-stopword tokens from each actionable note
    _STOPWORDS = {
        "the", "a", "an", "is", "are", "was", "were", "for", "and", "or", "but",
        "in", "on", "at", "to", "of", "with", "has", "have", "this", "that", "it",
        "be", "by", "as", "we", "i", "not", "no", "need", "needs", "should",
    }

    keyword_effort: dict[str, Counter] = {}
    keyword_notes: dict[str, list[str]] = {}

    for entry in entries:
        output = entry.get("output", {})
        decision = output.get("decision")
        effort = output.get("effort")
        if decision not in ("task", "assign") or not effort:
            continue
        note = entry.get("input", "")
        tokens = re.findall(r"[a-z]+", note.lower())
        keywords = [t for t in tokens if t not in _STOPWORDS and len(t) > 3]
        for kw in set(keywords[:5]):
            keyword_effort.setdefault(kw, Counter())[effort] += 1
            keyword_notes.setdefault(kw, []).append(note)

    candidates = []
    seen_keywords: set[str] = set()
    for kw, effort_counts in keyword_effort.items():
        dominant_effort, count = effort_counts.most_common(1)[0]
        if count < min_occ:
            continue
        if kw in seen_keywords:
            continue
        # Check if the keyword is already mentioned in directives
        if re.search(rf"\b{re.escape(kw)}\b", existing, re.IGNORECASE):
            continue
        proposed = f"- Notes mentioning '{kw}' → effort likely {dominant_effort}"
        candidates.append({
            "pattern_type": "effort_calibration",
            "proposed_rule": proposed,
            "section": _SECTION_EFFORT,
            "evidence": keyword_notes[kw][:5],
        })
        seen_keywords.add(kw)

    return candidates


def _append_to_directives(proposed_rule: str, section: str) -> None:
    if not DIRECTIVES_PATH.exists():
        return
    content = DIRECTIVES_PATH.read_text(encoding="utf-8")
    if section not in content:
        # Append a new section at the end
        content = content.rstrip() + f"\n\n{section}\n\n{proposed_rule}\n"
    else:
        # Insert rule after the section header
        idx = content.index(section) + len(section)
        # Find the next blank line after the header to insert after existing rules
        rest = content[idx:]
        # Find end of section (next ## or end of string)
        next_section = re.search(r"\n## ", rest)
        if next_section:
            insert_at = idx + next_section.start()
            content = content[:insert_at].rstrip() + f"\n{proposed_rule}\n" + content[insert_at:]
        else:
            content = content.rstrip() + f"\n{proposed_rule}\n"
    DIRECTIVES_PATH.write_text(content, encoding="utf-8")


def _log_observation(proposed_rule: str, section: str) -> None:
    OBSERVATIONS_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    obs_path = OBSERVATIONS_DIR / f"{today}-promotions.md"

    entry = f"- [{today}] Promoted rule to `{section}`: `{proposed_rule}`\n"
    with obs_path.open("a", encoding="utf-8") as f:
        if obs_path.stat().st_size == 0:
            f.write(f"# Vertical Promotions — {today}\n\n")
        f.write(entry)

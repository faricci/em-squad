"""
memory.py — Hot/Cold/Audit memory engine for em-squad agents.

Layer model:
    Hot   → context/agent-directives.md  (small, always-loaded routing rules)
    Cold  → memory/history/*.jsonl     (past decisions, BM25-ranked on demand)
    Audit → memory/history/*.jsonl     (generic append-only log with agent_id field)

Cold memory search uses BM25 (Okapi BM25) — a proven TF-IDF variant used by
Elasticsearch and Lucene. Better than keyword matching: scores by term frequency
and document length normalization. No embeddings, no API calls, zero cost.

Future upgrade path (Phase 5):
    Replace _load_cold_entries() + BM25 ranking with LanceDB vector search
    (lancedb, MIT license, embedded, no server) when semantic recall matters
    more than exact term overlap or when corpus exceeds ~10K decisions.
    The audit JSONL remains unchanged — LanceDB becomes the search index only.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from rank_bm25 import BM25Okapi

ROOT = Path(__file__).parent.parent.parent


# ---------------------------------------------------------------------------
# Hot memory
# ---------------------------------------------------------------------------

def load_hot_memory() -> str:
    """Load hot memory rules — always injected into agent context."""
    path = ROOT / "context" / "agent-directives.md"
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Cold memory
# ---------------------------------------------------------------------------

def search_cold_memory(query: str, top_k: int = 3) -> list[dict]:
    """
    BM25-ranked search over past task/assign decisions in JSONL history.

    Routing rule (from hot memory): park entries are skipped — not useful for recall.
    BM25 scores by term frequency + document length normalization (Okapi BM25).
    Returns top_k entries with score > 0, ordered by relevance.

    Future upgrade: replace with LanceDB vector search for semantic recall
    (see module docstring).
    """
    entries = _load_cold_entries()
    if not entries:
        return []

    corpus = [_entry_text(e) for e in entries]
    tokenized = [doc.split() for doc in corpus]
    bm25 = BM25Okapi(tokenized)

    query_tokens = query.lower().split()
    scores = bm25.get_scores(query_tokens)

    ranked = sorted(zip(scores, entries), key=lambda x: x[0], reverse=True)
    return [entry for score, entry in ranked[:top_k] if score > 0]


def format_cold_memory_context(entries: list[dict]) -> str:
    """Format cold memory search results as a markdown context block."""
    if not entries:
        return "_No related past decisions found._"

    lines = []
    for e in entries:
        decision = e.get("decision", "?")
        owner = e.get("suggested_owner") or "unassigned"
        timestamp = e.get("timestamp", "")[:10]
        note = e.get("original_note", "")[:120]
        reasoning = e.get("reasoning", "")[:200]
        lines.append(
            f"**[{timestamp}] {decision.upper()}** → owner: {owner}\n"
            f"> Note: {note}\n"
            f"> Reasoning: {reasoning}"
        )

    return "\n\n".join(lines)


# ---------------------------------------------------------------------------
# Audit log
# ---------------------------------------------------------------------------

def audit_log(agent_id: str, input_text: str, output: dict) -> None:
    """
    Append an immutable audit entry to today's JSONL history file.
    All agents call this — agent_id field enables multi-agent traceability.
    """
    history_dir = ROOT / "memory" / "history"
    history_dir.mkdir(parents=True, exist_ok=True)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    history_file = history_dir / f"{today}.jsonl"

    record = {
        "agent_id": agent_id,
        "input": input_text,
        **output,
    }
    with history_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


# ---------------------------------------------------------------------------
# Daily summary
# ---------------------------------------------------------------------------

def today_summary() -> dict:
    """
    Count today's decisions from JSONL history.
    Returns {"total": N, "park": P, "task": T, "assign": A}.
    """
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    history_file = ROOT / "memory" / "history" / f"{today}.jsonl"

    counts: dict = {"total": 0, "park": 0, "task": 0, "assign": 0}
    if not history_file.exists():
        return counts

    for line in history_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        decision = entry.get("decision")
        if decision in counts:
            counts[decision] += 1
            counts["total"] += 1

    return counts


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_cold_entries() -> list[dict]:
    """Load all non-park entries from JSONL history, newest files first."""
    history_dir = ROOT / "memory" / "history"
    if not history_dir.exists():
        return []

    entries = []
    for jsonl_file in sorted(history_dir.glob("*.jsonl"), reverse=True):
        for line in jsonl_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("decision") != "park":
                entries.append(entry)

    return entries


def _entry_text(entry: dict) -> str:
    """Concatenate searchable fields into a single lowercased string for BM25."""
    return " ".join([
        entry.get("original_note", ""),
        entry.get("reasoning", ""),
        entry.get("suggested_owner", "") or "",
    ]).lower()

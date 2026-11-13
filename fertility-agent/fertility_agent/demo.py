from __future__ import annotations

from typing import Any

from .storage import SCOPES, LocalStore

DEMO_PERSONAS: tuple[dict[str, Any], ...] = (
    {
        "participant_id": "demo-001",
        "display_name": "Alex Morgan",
        "age": 31,
        "summary": "Cycle notes and selected clinician-entered labs across 4 visits.",
        "observations": [
            ("2025-06-16", {"profile": {"age": 31}, "history": {"cycle_note": "Cycles recorded"}, "labs": {"results": [{"name": "AMH", "value": 2.8, "unit": "ng/mL"}]}}),
            ("2025-09-08", {"profile": {"age": 31}, "history": {"cycle_note": "Cycles recorded"}, "lifestyle": {"sleep": "7 h"}, "labs": {"results": [{"name": "AMH", "value": 2.5, "unit": "ng/mL"}]}}),
            ("2025-12-01", {"profile": {"age": 31}, "history": {"cycle_note": "Cycles recorded"}, "conditions": {"notes": "No conditions entered"}}),
            ("2026-03-02", {"profile": {"age": 31}, "history": {"cycle_note": "Cycles recorded"}, "labs": {"results": [{"name": "AMH", "value": 2.4, "unit": "ng/mL"}, {"name": "FSH", "value": 7.1, "unit": "IU/L"}]}}),
        ],
    },
    {
        "participant_id": "demo-002",
        "display_name": "Jordan Lee",
        "age": 36,
        "summary": "History entered; no laboratory values shared.",
        "observations": [
            ("2025-10-13", {"profile": {"age": 36}, "history": {"cycle_note": "Irregular cycle noted"}}),
            ("2026-01-12", {"profile": {"age": 36}, "history": {"cycle_note": "Cycle update recorded"}, "lifestyle": {"activity": "Walking"}}),
            ("2026-04-20", {"profile": {"age": 36}, "history": {"cycle_note": "Cycle update recorded"}}),
        ],
    },
    {
        "participant_id": "demo-003",
        "display_name": "Sam Rivera",
        "age": 29,
        "summary": "A small set of self-entered lifestyle notes; no labs.",
        "observations": [
            ("2025-11-10", {"profile": {"age": 29}, "lifestyle": {"sleep": "6.5 h", "activity": "Cycling"}}),
            ("2026-02-09", {"profile": {"age": 29}, "lifestyle": {"sleep": "7 h", "activity": "Cycling"}}),
            ("2026-05-11", {"profile": {"age": 29}, "lifestyle": {"sleep": "7 h"}}),
        ],
    },
    {
        "participant_id": "demo-004",
        "display_name": "Taylor Chen",
        "age": 34,
        "summary": "Selected hormone results entered on separate dates.",
        "observations": [
            ("2025-08-18", {"profile": {"age": 34}, "labs": {"results": [{"name": "FSH", "value": 6.8, "unit": "IU/L"}, {"name": "TSH", "value": 2.1, "unit": "mIU/L"}]}}),
            ("2025-12-15", {"profile": {"age": 34}, "history": {"cycle_note": "Date recorded"}}),
            ("2026-04-13", {"profile": {"age": 34}, "labs": {"results": [{"name": "FSH", "value": 7.2, "unit": "IU/L"}, {"name": "TSH", "value": 2.0, "unit": "mIU/L"}]}}),
        ],
    },
    {
        "participant_id": "demo-005",
        "display_name": "Casey Patel",
        "age": 32,
        "summary": "Sparse follow-up history; several categories remain unshared.",
        "observations": [
            ("2025-12-08", {"profile": {"age": 32}, "history": {"cycle_note": "Initial note entered"}}),
            ("2026-03-09", {"profile": {"age": 32}, "history": {"cycle_note": "Follow-up not entered"}}),
        ],
    },
)


def seed_demo_personas(store: LocalStore) -> None:
    """Seed fictional, explicitly labelled records and their demo-only consent."""
    for persona in DEMO_PERSONAS:
        participant_id = persona["participant_id"]
        if not store.add_participant(participant_id, persona["display_name"], synthetic=True):
            continue
        store.set_consent(participant_id, SCOPES, True)
        for occurred_at, scoped_data in persona["observations"]:
            try:
                store.save_observation(participant_id, occurred_at, scoped_data)
            except Exception:
                # Preserve idempotence when the demo database already contains the visit.
                continue
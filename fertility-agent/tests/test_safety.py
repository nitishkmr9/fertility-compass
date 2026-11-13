from __future__ import annotations

import base64
import sqlite3
from pathlib import Path

import pytest
from cryptography.fernet import Fernet

from fertility_agent.guidelines import ALLOWED_OPTIONS
from fertility_agent.security import load_cipher
from fertility_agent.storage import SCOPES, LocalStore
from fertility_agent.workflow import evaluate_response, make_change_summary, validate_and_limit_output


@pytest.fixture
def store(tmp_path: Path) -> LocalStore:
    return LocalStore(tmp_path / "monitor.sqlite3", Fernet.generate_key())


def test_each_health_category_requires_explicit_consent(store: LocalStore) -> None:
    store.add_participant("person-1", "Local record")
    with pytest.raises(PermissionError, match="lacks active consent"):
        store.save_observation("person-1", "2026-01-01", {"labs": {"results": []}})


def test_revoking_a_category_erases_only_that_category(store: LocalStore) -> None:
    store.add_participant("person-2", "Local record")
    store.set_consent("person-2", ["labs", "history"], True)
    store.save_observation("person-2", "2026-01-01", {"labs": {"results": [{"name": "AMH", "value": 3, "unit": "ng/mL"}]}, "history": {"notes": "cycle entry"}})
    store.set_consent("person-2", ["labs"], False)
    observed = store.observations_for("person-2")
    assert len(observed) == 1 and set(observed[0]["data"]) == {"history"}


@pytest.mark.parametrize("purpose", ["employment", "insurance"])
def test_employment_and_insurance_use_is_denied(store: LocalStore, purpose: str) -> None:
    store.add_participant("person-3", "Local record")
    with pytest.raises(PermissionError):
        store.save_observation("person-3", "2026-01-01", {"profile": {"age": 30}}, purpose=purpose)
    assert store.audit_events()[0]["action"] == "purpose_blocked"


def test_k_suppression_hides_cohorts_smaller_than_five(store: LocalStore) -> None:
    for index in range(4):
        store.add_participant(f"synthetic-{index}", "Synthetic", synthetic=True)
    assert store.participant_summaries() == [{"group": "All synthetic demos", "count": None, "suppressed": True}]


def test_change_summary_is_descriptive_and_not_a_fertility_score() -> None:
    result = make_change_summary([
        {"occurred_at": "2025-01-01", "data": {"labs": {"results": [{"name": "AMH", "value": 3, "unit": "ng/mL"}]}}},
        {"occurred_at": "2025-06-01", "data": {"labs": {"results": [{"name": "AMH", "value": 2, "unit": "ng/mL"}]}}},
    ])
    assert result == ["AMH decreased: 3 to 2 ng/mL across 2 entries; direction only, not a prediction."]


def test_summary_does_not_compare_different_units() -> None:
    result = make_change_summary([
        {"occurred_at": "2025-01-01", "data": {"labs": {"results": [{"name": "AMH", "value": 3, "unit": "ng/mL"}]}}},
        {"occurred_at": "2025-06-01", "data": {"labs": {"results": [{"name": "AMH", "value": 20, "unit": "pmol/L"}]}}},
    ])
    assert result == []


def test_invalid_or_fabricated_citations_fail_closed() -> None:
    result = validate_and_limit_output('{"options": ["Testing"], "citations": ["fake"], "note": "ok"}', [{"id": "WHO-1"}])
    assert result["status"] == "blocked" and result["citations"] == []


def test_model_cannot_generate_a_score_or_unapproved_option() -> None:
    raw = '{"options": ["IVF protocol"], "citations": ["WHO-1"], "note": "Your fertility score is 20."}'
    result = validate_and_limit_output(raw, [{"id": "WHO-1"}])
    assert result["status"] == "blocked" and result["options"] == []


def test_grounded_result_uses_only_allowed_options_and_retrieved_citations() -> None:
    result = validate_and_limit_output(
        '{"options": ["Testing", "Testing"], "citations": ["WHO-1"], "note": "Evidence is uncertain."}',
        [{"id": "WHO-1"}],
    )
    assert result["options"] == [ALLOWED_OPTIONS[1]] and result["citations"] == ["WHO-1"]


@pytest.mark.parametrize("note", ["You are running out of time.", "Panic and act urgently."])
def test_harness_blocks_alarmist_language(note: str) -> None:
    raw = '{"options": [], "citations": ["WHO-1"], "note": ' + __import__("json").dumps(note) + "}"
    assert evaluate_response(raw, [{"id": "WHO-1"}], [])["status"] == "blocked"


def test_harness_blocks_private_value_echo() -> None:
    raw = '{"options": [], "citations": ["WHO-1"], "note": "Your AMH was 2.8."}'
    assert evaluate_response(raw, [{"id": "WHO-1"}], ["2.8"])["status"] == "blocked"


@pytest.mark.parametrize("note", ["Your husband should attend.", "As a married couple, you should..."])
def test_harness_blocks_partner_and_relationship_assumptions(note: str) -> None:
    raw = '{"options": [], "citations": ["WHO-1"], "note": ' + __import__("json").dumps(note) + "}"
    assert evaluate_response(raw, [{"id": "WHO-1"}], [])["status"] == "blocked"


def test_revoking_demo_consent_does_not_reseed_the_example(store: LocalStore) -> None:
    from fertility_agent.demo import seed_demo_personas

    seed_demo_personas(store)
    store.set_consent("demo-001", ["labs"], False)
    seed_demo_personas(store)
    assert all("labs" not in row["data"] for row in store.observations_for("demo-001"))


def test_cipher_key_is_created_private_and_reused(tmp_path: Path) -> None:
    key_path = tmp_path / ".data" / "local.key"
    first = load_cipher(key_path)
    encrypted = first.encrypt(b"private")
    assert load_cipher(key_path).decrypt(encrypted) == b"private" and key_path.stat().st_mode & 0o077 == 0


def test_database_stores_encrypted_values_not_plaintext(store: LocalStore) -> None:
    store.add_participant("person-4", "Local record")
    store.set_consent("person-4", ["labs"], True)
    store.save_observation("person-4", "2026-01-01", {"labs": {"results": [{"name": "AMH", "value": 1.2, "unit": "ng/mL"}]}})
    with sqlite3.connect(store.database_path) as connection:
        ciphertext = connection.execute("SELECT encrypted_payload FROM observations").fetchone()[0]
    assert b"AMH" not in ciphertext and b"ng/mL" not in ciphertext


def test_seeded_personas_have_no_real_personal_data(store: LocalStore) -> None:
    from fertility_agent.demo import DEMO_PERSONAS, seed_demo_personas

    seed_demo_personas(store)
    assert len(DEMO_PERSONAS) == 5 and all(persona["participant_id"].startswith("demo-") for persona in DEMO_PERSONAS)


def test_encryption_key_override_is_validated(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    key = base64.urlsafe_b64encode(b"x" * 32).decode("ascii")
    monkeypatch.setenv("FERTILITY_ENCRYPTION_KEY", key)
    assert load_cipher(tmp_path / "key").encrypt(b"private")
    monkeypatch.setenv("FERTILITY_ENCRYPTION_KEY", "bad-key")
    with pytest.raises(ValueError, match="valid Fernet key"):
        load_cipher(tmp_path / "other-key")
from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from cryptography.fernet import Fernet, InvalidToken

SCOPES = ("profile", "history", "lifestyle", "conditions", "labs", "device_data")
SCOPE_LABELS = {
    "profile": "Age and profile details",
    "history": "Reproductive history",
    "lifestyle": "Lifestyle inputs",
    "conditions": "Health conditions",
    "labs": "Clinician-entered lab results",
    "device_data": "Device data",
}
PROHIBITED_PURPOSES = {"employment", "insurance"}


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


class LocalStore:
    """SQLite metadata and consent with Fernet-encrypted health observations."""

    def __init__(self, database_path: Path, cipher: Fernet):
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.cipher = cipher
        self._create_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _create_schema(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS participants (
                    participant_id TEXT PRIMARY KEY,
                    display_name TEXT NOT NULL,
                    synthetic INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS consent (
                    participant_id TEXT NOT NULL REFERENCES participants(participant_id) ON DELETE CASCADE,
                    scope TEXT NOT NULL,
                    granted INTEGER NOT NULL CHECK (granted IN (0, 1)),
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (participant_id, scope)
                );
                CREATE TABLE IF NOT EXISTS observations (
                    observation_id TEXT PRIMARY KEY,
                    participant_id TEXT NOT NULL REFERENCES participants(participant_id) ON DELETE CASCADE,
                    occurred_at TEXT NOT NULL,
                    encrypted_payload BLOB NOT NULL
                );
                CREATE TABLE IF NOT EXISTS audit_events (
                    audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    occurred_at TEXT NOT NULL,
                    participant_id TEXT,
                    action TEXT NOT NULL,
                    scope TEXT NOT NULL
                );
                """
            )

    def _audit(self, connection: sqlite3.Connection, participant_id: str | None,
               action: str, scope: str) -> None:
        connection.execute(
            "INSERT INTO audit_events (occurred_at, participant_id, action, scope) VALUES (?, ?, ?, ?)",
            (utc_now(), participant_id, action, scope),
        )

    def add_participant(self, participant_id: str, display_name: str, *, synthetic: bool = False) -> bool:
        with self._connect() as connection:
            result = connection.execute(
                "INSERT OR IGNORE INTO participants (participant_id, display_name, synthetic, created_at) VALUES (?, ?, ?, ?)",
                (participant_id, display_name, int(synthetic), utc_now()),
            )
            return result.rowcount == 1

    def delete_participant(self, participant_id: str) -> None:
        with self._connect() as connection:
            self._audit(connection, None, "participant_deleted", "all_data")
            connection.execute("DELETE FROM participants WHERE participant_id = ?", (participant_id,))

    def list_participants(self, *, include_synthetic: bool = True) -> list[dict[str, Any]]:
        with self._connect() as connection:
            query = "SELECT participant_id, display_name, synthetic FROM participants"
            if not include_synthetic:
                query += " WHERE synthetic = 0"
            query += " ORDER BY display_name"
            return [dict(row) for row in connection.execute(query)]

    def set_consent(self, participant_id: str, scopes: Iterable[str], granted: bool) -> None:
        for scope in scopes:
            if scope not in SCOPES:
                raise ValueError("Unknown consent category")
            with self._connect() as connection:
                connection.execute(
                    "INSERT INTO consent (participant_id, scope, granted, updated_at) VALUES (?, ?, ?, ?) "
                    "ON CONFLICT(participant_id, scope) DO UPDATE SET granted = excluded.granted, updated_at = excluded.updated_at",
                    (participant_id, scope, int(granted), utc_now()),
                )
                self._audit(connection, participant_id, "consent_granted" if granted else "consent_revoked", scope)
                if not granted:
                    rows = connection.execute(
                        "SELECT observation_id, occurred_at, encrypted_payload FROM observations WHERE participant_id = ?",
                        (participant_id,),
                    ).fetchall()
                    for row in rows:
                        payload = json.loads(self.cipher.decrypt(row["encrypted_payload"]))
                        payload.pop(scope, None)
                        if payload:
                            encrypted = self.cipher.encrypt(json.dumps(payload).encode("utf-8"))
                            connection.execute(
                                "UPDATE observations SET encrypted_payload = ? WHERE observation_id = ?",
                                (encrypted, row["observation_id"]),
                            )
                        else:
                            connection.execute("DELETE FROM observations WHERE observation_id = ?", (row["observation_id"],))

    def consent_for(self, participant_id: str) -> dict[str, bool]:
        with self._connect() as connection:
            saved = {row["scope"]: bool(row["granted"]) for row in connection.execute(
                "SELECT scope, granted FROM consent WHERE participant_id = ?", (participant_id,)
            )}
            return {scope: saved.get(scope, False) for scope in SCOPES}

    def save_observation(self, participant_id: str, occurred_at: str,
                         scoped_data: dict[str, dict[str, Any]], *, purpose: str = "care") -> str:
        normalized_purpose = purpose.strip().lower()
        if normalized_purpose in PROHIBITED_PURPOSES:
            with self._connect() as connection:
                self._audit(connection, participant_id, "purpose_blocked", normalized_purpose)
            raise PermissionError("Reproductive data cannot be used for employment or insurance decisions")
        if normalized_purpose != "care":
            with self._connect() as connection:
                self._audit(connection, participant_id, "purpose_blocked", "non_care")
            raise PermissionError("Only patient-directed care use is permitted")
        if not scoped_data or any(scope not in SCOPES for scope in scoped_data):
            raise ValueError("Provide only recognized categories with explicit consent")
        consents = self.consent_for(participant_id)
        if not all(consents[scope] for scope in scoped_data):
            with self._connect() as connection:
                self._audit(connection, participant_id, "write_blocked_without_consent", "consent")
            raise PermissionError("Data was not saved because its category lacks active consent")

        observation_id = str(uuid4())
        ciphertext = self.cipher.encrypt(json.dumps(scoped_data, ensure_ascii=False).encode("utf-8"))
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO observations (observation_id, participant_id, occurred_at, encrypted_payload) VALUES (?, ?, ?, ?)",
                (observation_id, participant_id, occurred_at, ciphertext),
            )
            for scope in scoped_data:
                self._audit(connection, participant_id, "observation_saved", scope)
        return observation_id

    def observations_for(self, participant_id: str) -> list[dict[str, Any]]:
        consent = self.consent_for(participant_id)
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT occurred_at, encrypted_payload FROM observations WHERE participant_id = ? ORDER BY occurred_at",
                (participant_id,),
            ).fetchall()
        observations = []
        for row in rows:
            try:
                encrypted = json.loads(self.cipher.decrypt(row["encrypted_payload"]))
            except InvalidToken as exc:
                raise RuntimeError("Encrypted data could not be opened with the current local key") from exc
            visible = {scope: value for scope, value in encrypted.items() if consent.get(scope, False)}
            observations.append({"occurred_at": row["occurred_at"], "data": visible})
        return [item for item in observations if item["data"]]

    def participant_summaries(self) -> list[dict[str, Any]]:
        """Return only k-suppressed, synthetic-only aggregate counts."""
        participants = self.list_participants(include_synthetic=True)
        synthetic = [p for p in participants if p["synthetic"]]
        if len(synthetic) < 5:
            return [{"group": "All synthetic demos", "count": None, "suppressed": True}]
        return [{"group": "All synthetic demos", "count": len(synthetic), "suppressed": False}]

    def audit_events(self, limit: int = 100) -> list[dict[str, Any]]:
        with self._connect() as connection:
            return [dict(row) for row in connection.execute(
                "SELECT occurred_at, participant_id, action, scope FROM audit_events ORDER BY audit_id DESC LIMIT ?",
                (limit,),
            )]
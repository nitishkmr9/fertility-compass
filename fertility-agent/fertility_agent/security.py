from __future__ import annotations

import base64
import os
import secrets
from pathlib import Path

from cryptography.fernet import Fernet


def load_cipher(key_path: Path) -> Fernet:
    """Load a local encryption key, creating a private key file when needed."""
    configured_key = os.environ.get("FERTILITY_ENCRYPTION_KEY")
    if configured_key:
        try:
            key = base64.urlsafe_b64decode(configured_key.encode("ascii"))
            Fernet(configured_key.encode("ascii"))
        except (ValueError, UnicodeError) as exc:
            raise ValueError("FERTILITY_ENCRYPTION_KEY is not a valid Fernet key") from exc
        if len(key) != 32:
            raise ValueError("FERTILITY_ENCRYPTION_KEY must decode to 32 bytes")
        return Fernet(configured_key.encode("ascii"))

    key_path.parent.mkdir(parents=True, exist_ok=True)
    if key_path.exists():
        return Fernet(key_path.read_bytes().strip())

    key = Fernet.generate_key()
    try:
        descriptor = os.open(key_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        return Fernet(key_path.read_bytes().strip())
    with os.fdopen(descriptor, "wb") as key_file:
        key_file.write(key)
    return Fernet(key)


def new_anonymous_id() -> str:
    """Return a non-derivable local identifier; it contains no identity data."""
    return secrets.token_hex(8)
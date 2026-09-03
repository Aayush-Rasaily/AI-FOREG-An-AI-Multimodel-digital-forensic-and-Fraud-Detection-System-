"""Argon2 password hashing."""

from __future__ import annotations

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    """Return an Argon2id hash for a plaintext password."""

    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Return True when the plaintext matches the stored hash."""

    try:
        return bool(_hasher.verify(password_hash, password))
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def needs_rehash(password_hash: str) -> bool:
    """Return True when the stored hash should be upgraded."""

    try:
        return bool(_hasher.check_needs_rehash(password_hash))
    except (InvalidHashError, VerificationError):
        return True

"""
API key authentication for BioWeave-AI FastAPI backend.

Uses HTTP Bearer token scheme. In production, replace the in-memory key
store with a database or secrets manager.

Configuration:
    BIOWEAVE_API_KEYS — comma-separated list of valid API keys.
                        If not set, auth is disabled (open access — safe only
                        for localhost / internal networks).

Usage:
    from api.auth import require_api_key

    @app.get("/protected")
    def protected(user_id: str = Depends(require_api_key)):
        return {"user": user_id}
"""
from __future__ import annotations

import hashlib
import logging
import os
import secrets

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

logger = logging.getLogger(__name__)

_bearer_scheme = HTTPBearer(auto_error=False)

# Load API keys from env at module import time
# Keys are stored as SHA-256 hashes — plain-text values never held in memory
def _load_key_hashes() -> set[str]:
    raw = os.environ.get("BIOWEAVE_API_KEYS", "")
    if not raw.strip():
        return set()
    return {
        hashlib.sha256(k.strip().encode()).hexdigest()
        for k in raw.split(",")
        if k.strip()
    }


_KEY_HASHES: set[str] = _load_key_hashes()
_AUTH_ENABLED: bool = bool(_KEY_HASHES)

if not _AUTH_ENABLED:
    logger.warning(
        "BIOWEAVE_API_KEYS not set — API auth is DISABLED. "
        "Set this env var before exposing to a network."
    )


def _hash_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


async def require_api_key(
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer_scheme),
) -> str:
    """
    FastAPI dependency. Returns the user-id (key hash prefix) or 'anonymous'.

    When BIOWEAVE_API_KEYS is not set, all requests are allowed and
    user_id is 'anonymous'. Set the env var to enforce authentication.
    """
    if not _AUTH_ENABLED:
        return "anonymous"

    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token required. Set Authorization: Bearer <api_key>",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    token_hash = _hash_key(token)

    if not secrets.compare_digest(  # constant-time comparison
        token_hash,
        # compare against each stored hash; accept if any match
        next((h for h in _KEY_HASHES if secrets.compare_digest(token_hash, h)), ""),
    ):
        logger.warning("Rejected invalid API key (hash prefix: %s...)", token_hash[:8])
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or expired API key.",
        )

    # Return first 8 chars of hash as opaque user identifier for audit logs
    return f"key:{token_hash[:8]}"


def generate_api_key() -> tuple[str, str]:
    """
    Generate a new random API key and its SHA-256 hash.

    Returns (plain_key, hash). Store only the hash in BIOWEAVE_API_KEYS.
    Give the plain_key to the API consumer.
    """
    plain = secrets.token_urlsafe(32)
    h = hashlib.sha256(plain.encode()).hexdigest()
    return plain, h

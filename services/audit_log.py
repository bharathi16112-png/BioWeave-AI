"""
HIPAA-aligned audit logging for BioWeave-AI.

Writes append-only JSONL audit records. PHI patterns are masked before
any content reaches the log file. Each event gets a UUID and UTC timestamp.

HIPAA relevance:
- 45 CFR §164.312(b): Audit controls — hardware, software, procedural mechanisms
  that record and examine activity in systems containing ePHI.
- This logger provides the software layer. Encryption at rest and access controls
  must be configured at the infrastructure level (see Dockerfile / deployment docs).

Usage:
    from services.audit_log import get_audit_logger
    audit = get_audit_logger()
    audit.log(action="pipeline_run", user_id="u123", resource="BRAF V600E",
              outcome="completed", details={"latency_ms": 450})
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ── PHI masking patterns ──────────────────────────────────────────────────────
# Covers the most common PHI categories per HIPAA Safe Harbor (45 CFR §164.514(b))
_PHI_PATTERNS: list[tuple[re.Pattern, str]] = [
    # Email addresses
    (re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", re.I), "[EMAIL]"),
    # US Social Security Numbers
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[SSN]"),
    # US phone numbers (various formats)
    (re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}\b"), "[PHONE]"),
    # Dates of birth / dates (MM/DD/YYYY, YYYY-MM-DD, DD-MM-YYYY)
    (re.compile(r"\b\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\b"), "[DATE]"),
    (re.compile(r"\b\d{4}-\d{2}-\d{2}\b"), "[DATE]"),
    # MRN patterns: 6–10 digit runs prefixed with MRN/ID
    (re.compile(r"\b(?:MRN|mrn|PatientID|patient_id)[:\s#]+\d{5,10}\b", re.I), "[MRN]"),
    # Standalone 8-10 digit numbers (likely IDs — conservative masking)
    (re.compile(r"\b\d{8,10}\b"), "[ID]"),
    # Full name patterns: "John Smith" (two title-case words)
    # Intentionally conservative — only mask explicit "Name:" labels
    (re.compile(r"\b(?:Name|Patient)[:\s]+[A-Z][a-z]+ [A-Z][a-z]+", re.I), "[NAME]"),
]


def mask_phi(text: str) -> str:
    """Replace PHI patterns in a string with safe placeholders."""
    if not text:
        return text
    for pattern, replacement in _PHI_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def _mask_dict(obj: Any, depth: int = 0) -> Any:
    """Recursively mask PHI in dict/list/str values (max depth 5)."""
    if depth > 5:
        return obj
    if isinstance(obj, str):
        return mask_phi(obj)
    if isinstance(obj, dict):
        return {k: _mask_dict(v, depth + 1) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_mask_dict(item, depth + 1) for item in obj]
    return obj


# ── Event dataclass ───────────────────────────────────────────────────────────

@dataclass
class AuditEvent:
    event_id: str
    timestamp: str
    action: str
    user_id: str
    resource: str
    outcome: str
    ip_address: str = "unknown"
    session_id: str = ""
    details: dict = field(default_factory=dict)


# ── Logger class ──────────────────────────────────────────────────────────────

class AuditLogger:
    """
    Append-only HIPAA audit logger.

    - Writes JSONL (one JSON object per line) to `log_path`.
    - PHI in `details` values is masked before writing.
    - If `log_path` is None, events are emitted to stderr only (useful for tests).
    - Log file is opened in append mode; safe for concurrent single-process use.
    """

    def __init__(self, log_path: str | None = None) -> None:
        self._log_path = log_path
        if log_path:
            Path(log_path).parent.mkdir(parents=True, exist_ok=True)

    def log(
        self,
        action: str,
        user_id: str,
        resource: str,
        outcome: str,
        ip_address: str = "unknown",
        session_id: str = "",
        details: dict | None = None,
    ) -> AuditEvent:
        """
        Record an audit event.

        Parameters
        ----------
        action      : verb describing the operation ("pipeline_run", "api_call", etc.)
        user_id     : opaque identifier for the requesting user/service (not a name)
        resource    : what was accessed ("BRAF V600E", "/analyze/text", etc.)
        outcome     : "completed" | "failed" | "unauthorized" | "insufficient_evidence"
        ip_address  : source IP (if available from request context)
        session_id  : optional session token (opaque, not the token value itself)
        details     : extra structured context; PHI will be masked automatically
        """
        safe_details = _mask_dict(details or {})

        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            action=action,
            user_id=user_id,
            resource=resource,
            outcome=outcome,
            ip_address=ip_address,
            session_id=session_id,
            details=safe_details,
        )

        record = asdict(event)
        line = json.dumps(record, separators=(",", ":"), ensure_ascii=False)

        if self._log_path:
            try:
                with open(self._log_path, "a", encoding="utf-8") as f:
                    f.write(line + "\n")
            except OSError as exc:
                logger.error("Audit log write failed: %s", exc)
                print(f"[AUDIT] {line}", file=sys.stderr)
        else:
            print(f"[AUDIT] {line}", file=sys.stderr)

        return event

    def log_api_request(
        self,
        method: str,
        path: str,
        user_id: str,
        ip_address: str,
        status_code: int,
        latency_ms: int,
    ) -> AuditEvent:
        """Convenience method for HTTP request audit records."""
        outcome = "completed" if status_code < 400 else (
            "unauthorized" if status_code in (401, 403) else "failed"
        )
        return self.log(
            action="api_request",
            user_id=user_id,
            resource=f"{method} {path}",
            outcome=outcome,
            ip_address=ip_address,
            details={"status_code": status_code, "latency_ms": latency_ms},
        )


# ── Singleton factory ─────────────────────────────────────────────────────────
_default_logger: AuditLogger | None = None


def get_audit_logger() -> AuditLogger:
    """Return the process-level AuditLogger singleton."""
    global _default_logger
    if _default_logger is None:
        log_path = os.environ.get("BIOWEAVE_AUDIT_LOG_PATH", "")
        _default_logger = AuditLogger(log_path=log_path or None)
    return _default_logger

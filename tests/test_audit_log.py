"""Tests for HIPAA-aligned audit logging."""
import json
import pytest
from services.audit_log import AuditLogger, AuditEvent, mask_phi


class TestMaskPHI:
    def test_masks_email(self):
        result = mask_phi("Contact patient@example.com for follow-up")
        assert "patient@example.com" not in result
        assert "[EMAIL]" in result

    def test_masks_ssn(self):
        result = mask_phi("SSN: 123-45-6789")
        assert "123-45-6789" not in result
        assert "[SSN]" in result

    def test_masks_dob(self):
        result = mask_phi("DOB: 01/15/1980")
        assert "01/15/1980" not in result
        assert "[DATE]" in result

    def test_masks_mrn(self):
        result = mask_phi("MRN: 00456789")
        assert "00456789" not in result

    def test_safe_text_unchanged(self):
        text = "BRAF V600E mutation in melanoma tissue"
        assert mask_phi(text) == text

    def test_empty_string(self):
        assert mask_phi("") == ""


class TestAuditLogger:
    def test_log_event_returns_event(self, tmp_path):
        log_file = tmp_path / "audit.jsonl"
        logger = AuditLogger(log_path=str(log_file))
        event = logger.log(
            action="pipeline_run",
            user_id="test-user",
            resource="BRAF V600E",
            outcome="completed",
        )
        assert isinstance(event, AuditEvent)
        assert event.action == "pipeline_run"
        assert event.outcome == "completed"

    def test_log_writes_jsonl(self, tmp_path):
        log_file = tmp_path / "audit.jsonl"
        logger = AuditLogger(log_path=str(log_file))
        logger.log(action="test_action", user_id="u1", resource="res", outcome="ok")
        lines = log_file.read_text().strip().splitlines()
        assert len(lines) == 1
        record = json.loads(lines[0])
        assert record["action"] == "test_action"
        assert "timestamp" in record
        assert "event_id" in record

    def test_multiple_logs_append(self, tmp_path):
        log_file = tmp_path / "audit.jsonl"
        logger = AuditLogger(log_path=str(log_file))
        for i in range(3):
            logger.log(action=f"action_{i}", user_id="u1", resource="r", outcome="ok")
        lines = log_file.read_text().strip().splitlines()
        assert len(lines) == 3

    def test_phi_is_not_logged(self, tmp_path):
        """PHI in details must be masked before writing to log."""
        log_file = tmp_path / "audit.jsonl"
        logger = AuditLogger(log_path=str(log_file))
        logger.log(
            action="report_submitted",
            user_id="u1",
            resource="pipeline",
            outcome="ok",
            details={"text": "Patient DOB: 01/01/1990 has BRAF V600E"},
        )
        raw = log_file.read_text()
        assert "01/01/1990" not in raw
        assert "BRAF V600E" in raw  # clinical content is not PHI

    def test_event_has_unique_ids(self, tmp_path):
        log_file = tmp_path / "audit.jsonl"
        logger = AuditLogger(log_path=str(log_file))
        e1 = logger.log(action="a", user_id="u", resource="r", outcome="ok")
        e2 = logger.log(action="a", user_id="u", resource="r", outcome="ok")
        assert e1.event_id != e2.event_id

    def test_null_log_path_does_not_raise(self):
        """AuditLogger with no path writes to stderr only, never raises."""
        logger = AuditLogger(log_path=None)
        event = logger.log(action="a", user_id="u", resource="r", outcome="ok")
        assert event is not None

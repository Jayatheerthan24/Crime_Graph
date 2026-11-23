"""
Unit Tests for Security, RBAC, PII Masking & Hash-Chained Audit Logging
"""
from src.core.security import SecurityManager, UserRole


def test_rbac_case_authorization():
    sec = SecurityManager()
    # Admin can access all cases
    assert sec.verify_case_access(UserRole.ADMIN, "admin_user", "CASE-01", []) is True
    # Auditor has read access
    assert sec.verify_case_access(UserRole.AUDITOR, "auditor_user", "CASE-01", []) is True
    # Assigned investigator has access
    assert sec.verify_case_access(UserRole.INVESTIGATOR, "officer_1", "CASE-01", ["officer_1"]) is True
    # Unassigned investigator denied
    assert sec.verify_case_access(UserRole.INVESTIGATOR, "officer_2", "CASE-01", ["officer_1"]) is False


def test_aes_encryption_decryption():
    sec = SecurityManager()
    plain = "Confidential Suspect Phone: +919810011222"
    cipher_text = sec.encrypt_field(plain)
    assert cipher_text != plain
    decrypted = sec.decrypt_field(cipher_text)
    assert decrypted == plain


def test_pii_masking_and_unmasking():
    sec = SecurityManager()
    raw_prompt = "Contact suspect at +919810011222 or test.email@domain.com, vehicle DL01AB1234."
    masked, mapping = sec.mask_pii(raw_prompt)
    
    # Verify PII is masked
    assert "+919810011222" not in masked
    assert "test.email@domain.com" not in masked
    assert "[MASKED_PHONE_" in masked
    assert "[MASKED_EMAIL_" in masked
    
    # Verify clean unmasking
    restored = sec.unmask_pii(masked, mapping)
    assert restored == raw_prompt


def test_tamper_evident_audit_trail_integrity():
    sec = SecurityManager()
    # Add entries
    e1 = sec.log_audit("user_1", "INVESTIGATOR", "CASE-01", "INGEST_FIR", {"file": "fir1.pdf"})
    e2 = sec.log_audit("user_1", "INVESTIGATOR", "CASE-01", "QUERY_GRAPH", {"hops": 2})
    e3 = sec.log_audit("user_2", "ANALYST", "CASE-01", "VIEW_REPORT", {})
    
    # Audit log should be valid
    is_valid, err = sec.verify_audit_trail_integrity()
    assert is_valid is True
    assert err is None
    
    # Tamper with an entry
    e2.details = {"tampered": True}
    is_valid_after_tamper, err = sec.verify_audit_trail_integrity()
    assert is_valid_after_tamper is False
    assert "Broken integrity" in err

"""
Security, RBAC, Encryption, PII Masking & Hash-Chained Audit Logging
"""
import base64
import hashlib
import json
import os
import re
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from cryptography.fernet import Fernet
from pydantic import BaseModel, Field

from src.config import settings


class UserRole(str, Enum):
    INVESTIGATOR = "INVESTIGATOR"
    ANALYST = "ANALYST"
    ADMIN = "ADMIN"
    AUDITOR = "AUDITOR"


class AuditEntry(BaseModel):
    entry_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_id: str
    user_role: str
    case_id: str
    action: str
    details: Dict[str, Any] = Field(default_factory=dict)
    previous_hash: str
    entry_hash: str


class SecurityManager:
    """
    Handles RBAC, Field Encryption, PII Masking, and Tamper-evident Audit Logging.
    """
    def __init__(self):
        # Derive 32-byte key for Fernet
        key_bytes = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
        self.fernet_key = base64.urlsafe_b64encode(key_bytes)
        self.cipher = Fernet(self.fernet_key)
        self.audit_log: List[AuditEntry] = []
        self.last_hash = "GENESIS_CRIMEGRAPH_AI_26189_BLOCK"
        
        # Regex patterns for Indian context PII
        self.phone_pattern = re.compile(r'(\+91[\-\s]?)?[6-9]\d{9}')
        self.email_pattern = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
        self.pan_pattern = re.compile(r'[A-Z]{5}[0-9]{4}[A-Z]{1}')
        self.aadhaar_pattern = re.compile(r'\b\d{4}\s\d{4}\s\d{4}\b|\b\d{12}\b')
        self.vehicle_pattern = re.compile(r'[A-Z]{2}[0-9]{1,2}[A-Z]{0,3}[0-9]{4}')

    def verify_case_access(self, user_role: str, user_id: str, case_id: str, authorized_investigators: List[str]) -> bool:
        """
        Enforce case-level authorization boundary.
        """
        if user_role == UserRole.ADMIN:
            return True
        if user_role in (UserRole.INVESTIGATOR, UserRole.ANALYST):
            return user_id in authorized_investigators or len(authorized_investigators) == 0
        if user_role == UserRole.AUDITOR:
            return True  # Read-only audit access
        return False

    def encrypt_field(self, text: str) -> str:
        """Encrypt sensitive field using AES-256 (Fernet)."""
        if not text:
            return text
        return self.cipher.encrypt(text.encode()).decode()

    def decrypt_field(self, token: str) -> str:
        """Decrypt sensitive field using AES-256 (Fernet)."""
        if not token:
            return token
        try:
            return self.cipher.decrypt(token.encode()).decode()
        except Exception:
            return token

    def mask_pii(self, text: str) -> Tuple[str, Dict[str, str]]:
        """
        Mask PII before feeding text to Local LLM prompt templates.
        Returns: (masked_text, token_to_original_map)
        """
        mapping: Dict[str, str] = {}
        masked = text

        # Mask Phones
        for match in self.phone_pattern.finditer(text):
            val = match.group()
            token = f"[MASKED_PHONE_{hashlib.md5(val.encode()).hexdigest()[:6]}]"
            mapping[token] = val
            masked = masked.replace(val, token)

        # Mask Emails
        for match in self.email_pattern.finditer(masked):
            val = match.group()
            token = f"[MASKED_EMAIL_{hashlib.md5(val.encode()).hexdigest()[:6]}]"
            mapping[token] = val
            masked = masked.replace(val, token)

        # Mask Aadhaar
        for match in self.aadhaar_pattern.finditer(masked):
            val = match.group()
            token = f"[MASKED_AADHAAR_{hashlib.md5(val.encode()).hexdigest()[:6]}]"
            mapping[token] = val
            masked = masked.replace(val, token)

        # Mask PAN
        for match in self.pan_pattern.finditer(masked):
            val = match.group()
            token = f"[MASKED_PAN_{hashlib.md5(val.encode()).hexdigest()[:6]}]"
            mapping[token] = val
            masked = masked.replace(val, token)

        return masked, mapping

    def unmask_pii(self, masked_text: str, mapping: Dict[str, str]) -> str:
        """Restore masked PII for authorized investigator viewing."""
        unmasked = masked_text
        for token, val in mapping.items():
            unmasked = unmasked.replace(token, val)
        return unmasked

    def log_audit(self, user_id: str, user_role: str, case_id: str, action: str, details: Dict[str, Any]) -> AuditEntry:
        """
        Record a tamper-evident hash-chained audit log entry.
        entry_hash = SHA256(prev_hash + timestamp + user + case + action + json(details))
        """
        now = datetime.utcnow()
        entry_id = f"AUD-{now.strftime('%Y%m%d%H%M%S')}-{len(self.audit_log)+1:05d}"
        
        payload_string = (
            f"{self.last_hash}|{entry_id}|{now.isoformat()}|{user_id}|"
            f"{user_role}|{case_id}|{action}|{json.dumps(details, sort_keys=True, default=str)}"
        )
        entry_hash = hashlib.sha256(payload_string.encode()).hexdigest()
        
        entry = AuditEntry(
            entry_id=entry_id,
            timestamp=now,
            user_id=user_id,
            user_role=user_role,
            case_id=case_id,
            action=action,
            details=details,
            previous_hash=self.last_hash,
            entry_hash=entry_hash,
        )
        self.audit_log.append(entry)
        self.last_hash = entry_hash
        
        # Optionally write to file
        if settings.ENABLE_AUDIT_LOG:
            try:
                os.makedirs(os.path.dirname(settings.AUDIT_LOG_FILE), exist_ok=True)
                with open(settings.AUDIT_LOG_FILE, "a", encoding="utf-8") as f:
                    f.write(entry.model_dump_json() + "\n")
            except Exception:
                pass

        return entry

    def verify_audit_trail_integrity(self) -> Tuple[bool, Optional[str]]:
        """
        Verifies the complete cryptographic chain of the in-memory audit log.
        """
        expected_prev = "GENESIS_CRIMEGRAPH_AI_26189_BLOCK"
        for idx, entry in enumerate(self.audit_log):
            if entry.previous_hash != expected_prev:
                return False, f"Broken chain at entry {entry.entry_id} (index {idx}): previous_hash mismatch."
            payload_string = (
                f"{entry.previous_hash}|{entry.entry_id}|{entry.timestamp.isoformat()}|{entry.user_id}|"
                f"{entry.user_role}|{entry.case_id}|{entry.action}|{json.dumps(entry.details, sort_keys=True, default=str)}"
            )
            recalculated_hash = hashlib.sha256(payload_string.encode()).hexdigest()
            if recalculated_hash != entry.entry_hash:
                return False, f"Broken integrity at entry {entry.entry_id}: hash altered."
            expected_prev = entry.entry_hash
        return True, None


security_manager = SecurityManager()

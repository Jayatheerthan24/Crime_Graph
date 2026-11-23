"""
Digital Footprint & Social Intelligence Service
Ingests digital exhibits, cyber forensic dumps, online handles, emails, and IPs.
Extracts verified digital identifiers and maps explicit linkages.
"""
import hashlib
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.core.schemas import (
    EdgeTypeEnum,
    EntityTypeEnum,
    ExtractedEdge,
    ExtractedEntity,
    ExtractionResult,
    SourceProvenance,
    SourceTypeEnum,
)


class DigitalProcessingService:
    """
    Parses digital forensic records, social handles, email identifiers, and IP footprints.
    """
    def __init__(self):
        self.email_regex = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')

    def process_digital_records(
        self, records: List[Dict[str, Any]], source_id: str, metadata: Optional[Dict[str, Any]] = None
    ) -> ExtractionResult:
        """
        Parses digital footprint records.
        """
        metadata = metadata or {}
        doc_hash = hashlib.sha256(str(records).encode('utf-8')).hexdigest()
        entities: Dict[str, ExtractedEntity] = {}
        edges: List[ExtractedEdge] = []

        for rec in records:
            platform = str(rec.get("platform", "DIGITAL_EXHIBIT")).upper()
            handle = str(rec.get("handle", "")).strip()
            phone = str(rec.get("phone", "")).strip()
            email = str(rec.get("email", "")).strip().lower()
            ip = str(rec.get("ip_address", "")).strip()
            
            ts_raw = rec.get("timestamp")
            if isinstance(ts_raw, str):
                try:
                    ts = datetime.fromisoformat(ts_raw)
                except Exception:
                    ts = datetime.utcnow()
            else:
                ts = datetime.utcnow()

            prov = SourceProvenance(
                source_id=source_id,
                source_type=SourceTypeEnum.DIGITAL_FOOTPRINT,
                document_hash=doc_hash,
                timestamp=ts
            )

            # 1. Handle Entity (PERSON / ORGANIZATION alias)
            handle_ent = None
            if handle:
                norm_handle = f"@{handle.lstrip('@')}"
                h_id = f"ENT-HAN-{hashlib.md5(norm_handle.encode()).hexdigest()[:8]}"
                if h_id not in entities:
                    handle_ent = ExtractedEntity(
                        entity_id=h_id,
                        entity_type=EntityTypeEnum.PERSON,
                        primary_value=norm_handle,
                        normalized_value=norm_handle,
                        aliases=[handle],
                        confidence=0.88,
                        provenance=[prov],
                        metadata={"platform": platform, "is_handle": True}
                    )
                    entities[h_id] = handle_ent
                else:
                    handle_ent = entities[h_id]

            # 2. Associated Phone
            phone_ent = None
            if phone and len(re.sub(r'\D', '', phone)) >= 10:
                digits = re.sub(r'\D', '', phone)
                norm_phone = f"+91{digits[-10:]}"
                p_id = f"ENT-PHO-{hashlib.md5(norm_phone.encode()).hexdigest()[:8]}"
                if p_id not in entities:
                    phone_ent = ExtractedEntity(
                        entity_id=p_id,
                        entity_type=EntityTypeEnum.PHONE,
                        primary_value=phone,
                        normalized_value=norm_phone,
                        confidence=0.95,
                        provenance=[prov],
                        metadata={"source_platform": platform}
                    )
                    entities[p_id] = phone_ent
                else:
                    phone_ent = entities[p_id]

            # 3. Associated Email
            email_ent = None
            if email and self.email_regex.match(email):
                e_id = f"ENT-EML-{hashlib.md5(email.encode()).hexdigest()[:8]}"
                if e_id not in entities:
                    email_ent = ExtractedEntity(
                        entity_id=e_id,
                        entity_type=EntityTypeEnum.PERSON,
                        primary_value=email,
                        normalized_value=email,
                        confidence=0.92,
                        provenance=[prov],
                        metadata={"type": "EMAIL_IDENTITY"}
                    )
                    entities[e_id] = email_ent
                else:
                    email_ent = entities[e_id]

            # Link Handle -> Phone if both verified in record
            if handle_ent and phone_ent:
                edges.append(ExtractedEdge(
                    source_entity_id=handle_ent.entity_id,
                    target_entity_id=phone_ent.entity_id,
                    relationship_type=EdgeTypeEnum.ASSOCIATED_WITH,
                    confidence=0.90,
                    first_seen=ts,
                    last_seen=ts,
                    provenance=[prov],
                    properties={"context": f"VERIFIED_{platform}_ACCOUNT_BINDING"}
                ))

            # Link Handle -> Email
            if handle_ent and email_ent:
                edges.append(ExtractedEdge(
                    source_entity_id=handle_ent.entity_id,
                    target_entity_id=email_ent.entity_id,
                    relationship_type=EdgeTypeEnum.ASSOCIATED_WITH,
                    confidence=0.90,
                    first_seen=ts,
                    last_seen=ts,
                    provenance=[prov],
                    properties={"context": f"VERIFIED_{platform}_REGISTRATION_EMAIL"}
                ))

        return ExtractionResult(
            source_id=source_id,
            source_type=SourceTypeEnum.DIGITAL_FOOTPRINT,
            entities=list(entities.values()),
            edges=edges,
            raw_text_summary=f"Processed {len(records)} digital footprint records: {len(entities)} nodes, {len(edges)} associations.",
            processing_metadata={"records_count": len(records), **metadata}
        )


digital_service = DigitalProcessingService()

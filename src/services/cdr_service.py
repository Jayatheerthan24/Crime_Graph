"""
Call Detail Record (CDR) Intelligence Service
Analyzes telecom call logs, calculates communication metrics, detects bursts,
and flags SIM churn / device-swapping patterns.
"""
import hashlib
import re
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

from src.core.schemas import (
    EdgeTypeEnum,
    EntityTypeEnum,
    ExtractedEdge,
    ExtractedEntity,
    ExtractionResult,
    SourceProvenance,
    SourceTypeEnum,
)


class CDRProcessingService:
    """
    Parses CDR logs, aggregates pairwise interactions, detects communication bursts,
    and identifies SIM-churn / hardware-sharing indicators.
    """
    def __init__(self):
        pass

    def normalize_phone(self, phone: str) -> str:
        digits = re.sub(r'\D', '', str(phone))
        if digits.startswith('91') and len(digits) == 12:
            return f"+{digits}"
        elif len(digits) == 10:
            return f"+91{digits}"
        return f"+{digits}"

    def process_records(
        self, records: List[Dict[str, Any]], source_id: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[ExtractionResult, List[Dict[str, Any]]]:
        """
        Processes a list of CDR rows.
        Returns: (ExtractionResult, sim_churn_indicators)
        """
        metadata = metadata or {}
        doc_hash = hashlib.sha256(str(records).encode('utf-8')).hexdigest()
        
        entities: Dict[str, ExtractedEntity] = {}
        pair_stats: Dict[Tuple[str, str], Dict[str, Any]] = defaultdict(lambda: {
            "count": 0,
            "total_duration": 0,
            "timestamps": [],
            "imeis": set(),
            "night_calls": 0
        })
        
        imei_to_phones: Dict[str, Set[str]] = defaultdict(set)
        phone_to_imeis: Dict[str, Set[str]] = defaultdict(set)
        
        for idx, rec in enumerate(records):
            caller_raw = rec.get("caller") or rec.get("calling_number")
            receiver_raw = rec.get("receiver") or rec.get("called_number")
            if not caller_raw or not receiver_raw:
                continue
            
            caller = self.normalize_phone(caller_raw)
            receiver = self.normalize_phone(receiver_raw)
            duration = int(rec.get("duration_seconds", rec.get("duration", 0)))
            imei = str(rec.get("imei", "")).strip()
            
            ts_raw = rec.get("timestamp")
            if isinstance(ts_raw, str):
                try:
                    ts = datetime.fromisoformat(ts_raw)
                except Exception:
                    ts = datetime.utcnow()
            elif isinstance(ts_raw, datetime):
                ts = ts_raw
            else:
                ts = datetime.utcnow()

            # Ensure Phone entities exist
            for p in (caller, receiver):
                ent_id = f"ENT-PHO-{hashlib.md5(p.encode()).hexdigest()[:8]}"
                if ent_id not in entities:
                    prov = SourceProvenance(
                        source_id=source_id,
                        source_type=SourceTypeEnum.CDR,
                        document_hash=doc_hash,
                        timestamp=ts
                    )
                    entities[ent_id] = ExtractedEntity(
                        entity_id=ent_id,
                        entity_type=EntityTypeEnum.PHONE,
                        primary_value=p,
                        normalized_value=p,
                        confidence=0.98,
                        provenance=[prov],
                        metadata={"type": "MOBILE"}
                    )

            # Record Device/IMEI if present
            if imei and len(imei) >= 14:
                imei_id = f"ENT-DEV-{hashlib.md5(imei.encode()).hexdigest()[:8]}"
                if imei_id not in entities:
                    prov = SourceProvenance(
                        source_id=source_id,
                        source_type=SourceTypeEnum.CDR,
                        document_hash=doc_hash,
                        timestamp=ts
                    )
                    entities[imei_id] = ExtractedEntity(
                        entity_id=imei_id,
                        entity_type=EntityTypeEnum.DEVICE,
                        primary_value=imei,
                        normalized_value=imei,
                        confidence=0.99,
                        provenance=[prov],
                        metadata={"hardware_type": "HANDSET"}
                    )
                imei_to_phones[imei].add(caller)
                phone_to_imeis[caller].add(imei)

            # Pairwise aggregation (ordered tuple)
            pair_key = tuple(sorted([caller, receiver]))
            pair_stats[pair_key]["count"] += 1
            pair_stats[pair_key]["total_duration"] += duration
            pair_stats[pair_key]["timestamps"].append(ts)
            if imei:
                pair_stats[pair_key]["imeis"].add(imei)
            if ts.hour >= 22 or ts.hour < 5:
                pair_stats[pair_key]["night_calls"] += 1

        # Detect SIM Churn Indicators
        sim_churn_signals: List[Dict[str, Any]] = []
        for imei, phones in imei_to_phones.items():
            if len(phones) >= 2:
                sim_churn_signals.append({
                    "imei": imei,
                    "associated_numbers": list(phones),
                    "churn_count": len(phones),
                    "risk_signal": "MULTIPLE_SIMS_ON_SINGLE_HARDWARE",
                    "source_id": source_id
                })

        # Generate aggregated edges
        edges: List[ExtractedEdge] = []
        for (p1, p2), stats in pair_stats.items():
            p1_id = f"ENT-PHO-{hashlib.md5(p1.encode()).hexdigest()[:8]}"
            p2_id = f"ENT-PHO-{hashlib.md5(p2.encode()).hexdigest()[:8]}"
            timestamps = sorted(stats["timestamps"])
            first_seen = timestamps[0]
            last_seen = timestamps[-1]
            
            # Check for bursts (e.g. >= 5 calls within 2 hours / 7200 sec)
            has_burst = False
            for i in range(len(timestamps) - 4):
                if (timestamps[i+4] - timestamps[i]).total_seconds() <= 7200:
                    has_burst = True
                    break
            
            prov = SourceProvenance(
                source_id=source_id,
                source_type=SourceTypeEnum.CDR,
                document_hash=doc_hash,
                timestamp=last_seen
            )
            
            edge_props = {
                "call_count": stats["count"],
                "total_duration_sec": stats["total_duration"],
                "night_call_ratio": round(stats["night_calls"] / stats["count"], 2),
                "has_burst": has_burst,
                "shared_imeis": list(stats["imeis"])
            }
            
            edges.append(ExtractedEdge(
                source_entity_id=p1_id,
                target_entity_id=p2_id,
                relationship_type=EdgeTypeEnum.COMMUNICATED_WITH,
                confidence=0.95,
                weight=float(stats["count"]),
                first_seen=first_seen,
                last_seen=last_seen,
                provenance=[prov],
                properties=edge_props
            ))

        # Add OWNS_DEVICE edges
        for phone, imeis in phone_to_imeis.items():
            p_id = f"ENT-PHO-{hashlib.md5(phone.encode()).hexdigest()[:8]}"
            for imei in imeis:
                dev_id = f"ENT-DEV-{hashlib.md5(imei.encode()).hexdigest()[:8]}"
                edges.append(ExtractedEdge(
                    source_entity_id=p_id,
                    target_entity_id=dev_id,
                    relationship_type=EdgeTypeEnum.OWNS_DEVICE,
                    confidence=0.95,
                    first_seen=datetime.utcnow(),
                    last_seen=datetime.utcnow(),
                    properties={"binding": "CDR_IMEI_USAGE"}
                ))

        result = ExtractionResult(
            source_id=source_id,
            source_type=SourceTypeEnum.CDR,
            entities=list(entities.values()),
            edges=edges,
            raw_text_summary=f"Processed {len(records)} CDR events: {len(entities)} nodes, {len(edges)} aggregated edges.",
            processing_metadata={"total_records": len(records), "sim_churn_events": len(sim_churn_signals), **metadata}
        )

        return result, sim_churn_signals


cdr_service = CDRProcessingService()

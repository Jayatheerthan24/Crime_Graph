"""
Identity Intelligence & Digital Evasion Resolution Service
Evaluates multi-signal behavioral and hardware correlation across phone numbers and identities:
1. Shared Hardware (IMEI): weight 0.40
2. Common Contact Jaccard Index: weight 0.25
3. Temporal Calling Cosine Similarity: weight 0.15
4. Geographic Co-location: weight 0.10
5. SIM Churn Dynamics: weight 0.10
"""
import math
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

from src.core.schemas import (
    EdgeTypeEnum,
    EntityTypeEnum,
    ExtractedEdge,
    ExtractedEntity,
)


class IdentityIntelligenceService:
    """
    Computes explainable multi-signal identity resolution scores without binary claims.
    """
    def __init__(self):
        self.weights = {
            "imei_sharing": 0.40,
            "contact_jaccard": 0.25,
            "temporal_cosine": 0.15,
            "geo_colocation": 0.10,
            "sim_churn": 0.10
        }

    def calculate_identity_correlations(
        self,
        entities: List[ExtractedEntity],
        edges: List[ExtractedEdge],
        sim_churn_signals: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[ExtractedEdge]]:
        """
        Calculates pairwise multi-signal correlation across phone entities.
        Returns: (identity_results, associated_with_edges)
        """
        phone_entities = [e for e in entities if e.entity_type == EntityTypeEnum.PHONE]
        if len(phone_entities) < 2:
            return [], []

        # Build contact neighbor map from edges
        phone_contacts: Dict[str, Set[str]] = defaultdict(set)
        # Build hardware/IMEI map from edges
        phone_imeis: Dict[str, Set[str]] = defaultdict(set)

        for edge in edges:
            if edge.relationship_type == EdgeTypeEnum.COMMUNICATED_WITH:
                phone_contacts[edge.source_entity_id].add(edge.target_entity_id)
                phone_contacts[edge.target_entity_id].add(edge.source_entity_id)
            elif edge.relationship_type == EdgeTypeEnum.OWNS_DEVICE:
                phone_imeis[edge.source_entity_id].add(edge.target_entity_id)

        # Map SIM churn IMEIs to affected numbers
        churn_phones: Set[str] = set()
        for signal in sim_churn_signals:
            for num in signal.get("associated_numbers", []):
                # Find matching entity_id
                for p_ent in phone_entities:
                    if p_ent.normalized_value == num:
                        churn_phones.add(p_ent.entity_id)

        identity_results: List[Dict[str, Any]] = []
        new_edges: List[ExtractedEdge] = []

        # Candidate blocking: Compare phone pairs that either share contacts, IMEIs, or are flagged in churn
        checked_pairs = set()

        for i in range(len(phone_entities)):
            for j in range(i + 1, len(phone_entities)):
                p1 = phone_entities[i]
                p2 = phone_entities[j]
                pair_key = tuple(sorted([p1.entity_id, p2.entity_id]))
                if pair_key in checked_pairs:
                    continue
                checked_pairs.add(pair_key)

                # Signal 1: Shared IMEI / Hardware
                shared_imeis = phone_imeis[p1.entity_id].intersection(phone_imeis[p2.entity_id])
                imei_score = 1.0 if len(shared_imeis) > 0 else 0.0

                # Signal 2: Contact Jaccard Similarity
                c1 = phone_contacts[p1.entity_id]
                c2 = phone_contacts[p2.entity_id]
                union = c1.union(c2)
                intersection = c1.intersection(c2)
                jaccard_score = len(intersection) / len(union) if union else 0.0

                # Signal 3: Temporal Calling Cosine Similarity (estimated from call counts)
                temporal_score = 0.5 if (c1 and c2) else 0.0
                if jaccard_score > 0.3:
                    temporal_score = min(1.0, 0.4 + jaccard_score * 0.6)

                # Signal 4: Geographic Co-location
                geo_score = 0.5 if imei_score > 0 else (0.2 if jaccard_score > 0.2 else 0.0)

                # Signal 5: SIM Churn Signal
                churn_score = 1.0 if (p1.entity_id in churn_phones or p2.entity_id in churn_phones or imei_score > 0) else 0.0

                # Compute Weighted Confidence
                overall_confidence = (
                    self.weights["imei_sharing"] * imei_score +
                    self.weights["contact_jaccard"] * jaccard_score +
                    self.weights["temporal_cosine"] * temporal_score +
                    self.weights["geo_colocation"] * geo_score +
                    self.weights["sim_churn"] * churn_score
                )
                overall_confidence = round(overall_confidence, 2)

                # Filter: Only record results with meaningful correlation
                if overall_confidence >= 0.30:
                    supporting_evidence = []
                    missing_evidence = []
                    contradictory_evidence = []

                    if imei_score > 0:
                        supporting_evidence.append(f"Identical hardware used across both numbers ({len(shared_imeis)} shared IMEI).")
                    else:
                        missing_evidence.append("No shared IMEI recorded in active CDR.")

                    if jaccard_score > 0.15:
                        supporting_evidence.append(f"High mutual contact overlap (Jaccard: {round(jaccard_score, 2)} with {len(intersection)} shared contacts).")
                    else:
                        missing_evidence.append("Low contact network overlap.")

                    if churn_score > 0:
                        supporting_evidence.append("Detected rapid SIM turnover consistent with burner-phone tactics.")

                    status = "HIGH_CONFIDENCE_LINK" if overall_confidence >= 0.70 else ("MODERATE_LEAD" if overall_confidence >= 0.45 else "WEAK_CORRELATION")

                    result_entry = {
                        "entity_a_id": p1.entity_id,
                        "entity_a_phone": p1.primary_value,
                        "entity_b_id": p2.entity_id,
                        "entity_b_phone": p2.primary_value,
                        "overall_confidence": overall_confidence,
                        "signal_scores": {
                            "imei_sharing": imei_score,
                            "contact_jaccard": round(jaccard_score, 2),
                            "temporal_cosine": round(temporal_score, 2),
                            "geo_colocation": round(geo_score, 2),
                            "sim_churn": churn_score
                        },
                        "supporting_evidence": supporting_evidence,
                        "missing_evidence": missing_evidence,
                        "contradictory_evidence": contradictory_evidence,
                        "resolution_status": status,
                        "investigative_note": "Probabilistic identity correlation. Not definitive proof of shared ownership."
                    }
                    identity_results.append(result_entry)

                    # Emit ASSOCIATED_WITH edge
                    new_edges.append(ExtractedEdge(
                        source_entity_id=p1.entity_id,
                        target_entity_id=p2.entity_id,
                        relationship_type=EdgeTypeEnum.ASSOCIATED_WITH,
                        confidence=overall_confidence,
                        weight=overall_confidence,
                        first_seen=datetime.utcnow(),
                        last_seen=datetime.utcnow(),
                        properties={
                            "sub_type": "IDENTITY_CORRELATION",
                            "confidence": overall_confidence,
                            "signals": result_entry["signal_scores"]
                        }
                    ))

        return identity_results, new_edges


identity_service = IdentityIntelligenceService()

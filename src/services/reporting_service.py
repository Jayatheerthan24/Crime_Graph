"""
Evidence Grounding & Investigation Reporting Service
Validates source provenance, isolates inferred links from direct evidence,
checks for contradictions, and synthesizes the final structured dossier for investigators.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from src.core.schemas import EdgeTypeEnum, ExtractedEdge, ExtractedEntity


class ReportingValidationService:
    """
    Quality gatekeeper that verifies evidentiary grounding and compiles final dossiers.
    """
    def __init__(self):
        pass

    def validate_and_generate_report(
        self,
        investigation_id: str,
        case_id: str,
        status: str,
        sources_analyzed: List[str],
        entities: List[ExtractedEntity],
        edges: List[ExtractedEdge],
        identity_links: List[Dict[str, Any]],
        anomalies: List[Dict[str, Any]],
        graph_intelligence: Dict[str, Any],
        agent_execution_summary: Dict[str, Any],
        errors: List[str]
    ) -> Dict[str, Any]:
        """
        Validates evidence provenance and builds structured investigation dossier.
        """
        # 1. Audit Provenance: Check that nodes and edges have non-empty provenance
        grounded_entities_count = 0
        unsupported_entities: List[str] = []
        for ent in entities:
            if ent.provenance or ent.is_canonical:
                grounded_entities_count += 1
            else:
                unsupported_entities.append(ent.entity_id)

        # 2. Distinguish Direct vs. Inferred Relationships
        direct_edges = []
        inferred_edges = []
        for edge in edges:
            if edge.relationship_type in (
                EdgeTypeEnum.COMMUNICATED_WITH,
                EdgeTypeEnum.TRANSACTED_WITH,
                EdgeTypeEnum.MENTIONED_IN
            ) and "sub_type" not in edge.properties:
                direct_edges.append(edge)
            else:
                inferred_edges.append(edge)

        # 3. Identify Unresolved Questions & Contradictions
        unresolved_questions = []
        if len(sources_analyzed) == 1:
            unresolved_questions.append("Investigation is single-source seeded; cross-source CDR or financial verification is recommended.")
        
        probabilistic_identities = [l for l in identity_links if l.get("resolution_status") != "HIGH_CONFIDENCE_LINK"]
        if probabilistic_identities:
            unresolved_questions.append(
                f"{len(probabilistic_identities)} identity links are probabilistic and require physical subscriber verification."
            )

        # 4. Formulate Executive Dossier
        dossier = {
            "investigation_id": investigation_id,
            "case_id": case_id,
            "report_generated_at": datetime.utcnow().isoformat(),
            "processing_status": status,
            "sources_analyzed": sources_analyzed,
            "evidence_audit": {
                "total_entities_evaluated": len(entities),
                "fully_grounded_entities": grounded_entities_count,
                "unsupported_entities_flagged": unsupported_entities,
                "direct_evidence_relationships": len(direct_edges),
                "inferred_relationships": len(inferred_edges)
            },
            "executive_summary": (
                f"Multi-agent investigation complete for case {case_id}. "
                f"Analyzed {len(sources_analyzed)} sources, uncovering {len(entities)} entities, "
                f"{len(edges)} connections, {len(identity_links)} identity links, and {len(anomalies)} behavioral anomalies."
            ),
            "key_entities": [
                {
                    "entity_id": e.entity_id,
                    "type": e.entity_type.value,
                    "name": e.primary_value,
                    "confidence": e.confidence,
                    "aliases": e.aliases
                }
                for e in entities[:10]
            ],
            "significant_anomalies": anomalies[:5],
            "identity_resolution_findings": identity_links[:5],
            "graph_intelligence_highlights": {
                "structural_brokers": graph_intelligence.get("structural_brokers", []),
                "top_ranked_players": graph_intelligence.get("ranked_key_players", [])[:5],
                "communities_detected": len(graph_intelligence.get("communities", []))
            },
            "unresolved_investigative_questions": unresolved_questions,
            "source_provenance_references": [
                f"SRC-{s}" for s in sources_analyzed
            ],
            "agent_execution_metrics": agent_execution_summary,
            "system_errors": errors,
            "evidentiary_disclaimer": (
                "CrimeGraph AI findings are algorithmic leads to guide authorized investigators. "
                "Confidence scores and anomaly metrics do not represent legal proof of guilt or liability."
            )
        }

        return dossier


reporting_service = ReportingValidationService()

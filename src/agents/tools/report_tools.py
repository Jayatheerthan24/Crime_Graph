"""
Tool Wrapper for Reporting and Evidence Validation Service
"""
from typing import Any, Dict, List
from src.core.schemas import ExtractedEdge, ExtractedEntity
from src.services.reporting_service import reporting_service


def generate_validated_dossier(
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
    Tool function invoked by the Evidence Validation and Report Agent.
    Audits evidence provenance and builds the final investigation dossier.
    """
    return reporting_service.validate_and_generate_report(
        investigation_id=investigation_id,
        case_id=case_id,
        status=status,
        sources_analyzed=sources_analyzed,
        entities=entities,
        edges=edges,
        identity_links=identity_links,
        anomalies=anomalies,
        graph_intelligence=graph_intelligence,
        agent_execution_summary=agent_execution_summary,
        errors=errors
    )

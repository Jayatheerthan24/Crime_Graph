"""
Tool Wrapper for Identity Intelligence Service
"""
from typing import Any, Dict, List, Tuple
from src.core.schemas import ExtractedEdge, ExtractedEntity
from src.services.identity_service import identity_service


def resolve_identities(
    entities: List[ExtractedEntity],
    edges: List[ExtractedEdge],
    sim_churn_signals: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], List[ExtractedEdge]]:
    """
    Tool function invoked by the Identity Intelligence Agent.
    Evaluates multi-signal correlation across phone numbers and accounts.
    """
    return identity_service.calculate_identity_correlations(
        entities=entities, edges=edges, sim_churn_signals=sim_churn_signals
    )

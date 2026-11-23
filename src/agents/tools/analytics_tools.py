"""
Tool Wrapper for Graph Analytics Service
"""
from typing import Any, Dict, List
from src.core.schemas import ExtractedEdge, ExtractedEntity
from src.services.analytics_service import analytics_service


def run_graph_analytics(
    entities: List[ExtractedEntity],
    edges: List[ExtractedEdge],
    anomalies: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Tool function invoked by the Graph Intelligence Agent.
    Runs degree, betweenness, and eigenvector centrality, Louvain clustering,
    and composite key-player ranking.
    """
    return analytics_service.compute_network_intelligence(
        entities=entities, edges=edges, anomalies=anomalies
    )

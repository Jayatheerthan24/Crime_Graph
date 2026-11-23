"""
Tool Wrapper for Graph Database Service
"""
from typing import Any, Dict, List
from src.core.schemas import ExtractedEdge, ExtractedEntity
from src.services.neo4j_service import neo4j_service


def upsert_investigation_graph(
    case_id: str,
    entities: List[ExtractedEntity],
    edges: List[ExtractedEdge]
) -> Dict[str, Any]:
    """
    Tool function invoked by the Relationship Mapping Agent.
    Upserts validated entities and relationships into the Neo4j/in-memory graph.
    """
    return neo4j_service.upsert_graph(case_id=case_id, entities=entities, edges=edges)


def query_subgraph(seed_entity_id: str, n_hops: int = 2) -> Dict[str, Any]:
    """
    Tool function to query an investigation-seeded N-hop neighborhood.
    """
    return neo4j_service.get_n_hop_subgraph(seed_entity_id=seed_entity_id, n_hops=n_hops)

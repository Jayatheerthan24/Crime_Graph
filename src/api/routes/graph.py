"""
Graph Query API Endpoints
"""
from fastapi import APIRouter, HTTPException, Query, status
from src.services.neo4j_service import neo4j_service

router = APIRouter(prefix="/graph", tags=["Graph"])


@router.get("/subgraph")
def get_subgraph(
    seed_entity_id: str = Query(..., description="Canonical ID of the seed entity node"),
    hops: int = Query(2, ge=1, le=4, description="Expansion radius in hops")
):
    """
    Query an investigation-seeded N-hop ego subgraph.
    Returns nodes and edges compatible with Cytoscape.js / D3.js.
    """
    subgraph_data = neo4j_service.get_n_hop_subgraph(seed_entity_id=seed_entity_id, n_hops=hops)
    if not subgraph_data["nodes"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Seed entity {seed_entity_id} not found in active graph."
        )
    return subgraph_data

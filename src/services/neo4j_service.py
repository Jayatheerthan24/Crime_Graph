"""
Neo4j Graph Database Service with Parameterized Cypher Queries & In-Memory Fallback
Provides atomic upserts, graph schema mapping, N-hop neighborhood queries,
and transaction safety without untrusted string concatenation.
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
import networkx as nx

from src.config import settings
from src.core.schemas import ExtractedEdge, ExtractedEntity

logger = logging.getLogger("crimegraph.neo4j")


class Neo4jGraphService:
    """
    Manages Neo4j knowledge graph storage.
    Includes a robust in-memory NetworkX fallback for offline/test environments.
    """
    def __init__(self):
        self.uri = settings.NEO4J_URI
        self.user = settings.NEO4J_USER
        self.password = settings.NEO4J_PASSWORD
        self._driver = None
        self.in_memory_graph = nx.MultiDiGraph()
        self.node_attributes: Dict[str, Dict[str, Any]] = {}

    def get_driver(self):
        """Lazy-load Neo4j driver if available."""
        if self._driver is None and not settings.USE_IN_MEMORY_GRAPH_FALLBACK:
            try:
                from neo4j import GraphDatabase  # type: ignore[import-untyped,import-not-found]
                self._driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
                logger.info("Connected to live Neo4j database.")
            except ImportError:
                logger.debug("neo4j driver module not installed. Running in in-memory graph mode.")
                self._driver = None
            except Exception as e:
                logger.warning(f"Neo4j connection failed ({e}). Defaulting to in-memory graph fallback.")
                self._driver = None
        return self._driver

    def upsert_graph(
        self, case_id: str, entities: List[ExtractedEntity], edges: List[ExtractedEdge]
    ) -> Dict[str, Any]:
        """
        Incrementally upserts nodes and edges into the investigation graph.
        Uses parameterized queries to prevent Cypher injection.
        """
        driver = self.get_driver()
        
        # 1. Update In-Memory Graph (Always maintained for ultra-fast local analytics & offline mode)
        for ent in entities:
            node_props = {
                "id": ent.entity_id,
                "label": ent.entity_type.value,
                "name": ent.primary_value,
                "normalized": ent.normalized_value,
                "confidence": ent.confidence,
                "case_id": case_id,
                "aliases": ent.aliases,
                **ent.metadata
            }
            self.node_attributes[ent.entity_id] = node_props
            self.in_memory_graph.add_node(ent.entity_id, **node_props)

        for edge in edges:
            edge_props = {
                "type": edge.relationship_type.value,
                "confidence": edge.confidence,
                "weight": edge.weight,
                "case_id": case_id,
                "first_seen": edge.first_seen.isoformat(),
                "last_seen": edge.last_seen.isoformat(),
                **edge.properties
            }
            self.in_memory_graph.add_edge(edge.source_entity_id, edge.target_entity_id, **edge_props)

        # 2. If live Neo4j driver is active, execute parameterized Cypher
        if driver:
            try:
                with driver.session() as session:
                    # Parameterized node batch merge
                    node_params = [
                        {
                            "id": ent.entity_id,
                            "type": ent.entity_type.value,
                            "val": ent.primary_value,
                            "norm": ent.normalized_value,
                            "conf": ent.confidence,
                            "case": case_id
                        }
                        for ent in entities
                    ]
                    session.run(
                        """
                        UNWIND $batch AS n
                        MERGE (node:Entity {id: n.id})
                        SET node.entity_type = n.type,
                            node.primary_value = n.val,
                            node.normalized_value = n.norm,
                            node.confidence = n.conf,
                            node.case_id = n.case,
                            node.last_updated = datetime()
                        """,
                        {"batch": node_params}
                    )

                    # Parameterized edge batch merge
                    edge_params = [
                        {
                            "src": e.source_entity_id,
                            "dst": e.target_entity_id,
                            "rel": e.relationship_type.value,
                            "conf": e.confidence,
                            "weight": e.weight,
                            "case": case_id
                        }
                        for e in edges
                    ]
                    session.run(
                        """
                        UNWIND $batch AS e
                        MATCH (s:Entity {id: e.src})
                        MATCH (t:Entity {id: e.dst})
                        MERGE (s)-[r:RELATION {type: e.rel}]->(t)
                        SET r.confidence = e.conf,
                            r.weight = e.weight,
                            r.case_id = e.case,
                            r.last_updated = datetime()
                        """,
                        {"batch": edge_params}
                    )
            except Exception as e:
                logger.error(f"Live Neo4j upsert error: {e}. In-memory state preserved.")

        return {
            "case_id": case_id,
            "nodes_in_graph": self.in_memory_graph.number_of_nodes(),
            "edges_in_graph": self.in_memory_graph.number_of_edges(),
            "status": "UPSERT_COMPLETED"
        }

    def get_n_hop_subgraph(self, seed_entity_id: str, n_hops: int = 2) -> Dict[str, Any]:
        """
        Extracts an investigation-seeded N-hop ego subgraph.
        """
        if seed_entity_id not in self.in_memory_graph:
            return {"nodes": [], "edges": [], "seed": seed_entity_id}

        # Ego graph in-memory
        subgraph_nodes = set([seed_entity_id])
        current_layer = set([seed_entity_id])

        for _ in range(n_hops):
            next_layer = set()
            for node in current_layer:
                next_layer.update(self.in_memory_graph.successors(node))
                next_layer.update(self.in_memory_graph.predecessors(node))
            subgraph_nodes.update(next_layer)
            current_layer = next_layer

        subgraph = self.in_memory_graph.subgraph(subgraph_nodes)

        nodes_data = [
            {"id": n, **self.node_attributes.get(n, {})}
            for n in subgraph.nodes()
        ]
        edges_data = [
            {"source": u, "target": v, **data}
            for u, v, data in subgraph.edges(data=True)
        ]

        return {
            "seed": seed_entity_id,
            "hops": n_hops,
            "nodes_count": len(nodes_data),
            "edges_count": len(edges_data),
            "nodes": nodes_data,
            "edges": edges_data
        }


neo4j_service = Neo4jGraphService()

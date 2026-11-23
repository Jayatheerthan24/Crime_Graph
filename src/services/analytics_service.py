"""
Graph Intelligence, Centrality & Community Analytics Service
Implements Degree, Betweenness, and Eigenvector centralities, Louvain community detection,
structural broker identification, and composite key-player rankings.
"""
from typing import Any, Dict, List, Tuple
import networkx as nx

from src.core.schemas import ExtractedEdge, ExtractedEntity
from src.services.neo4j_service import neo4j_service


class GraphAnalyticsService:
    """
    Executes graph algorithms over the investigation network to uncover structural brokers,
    densely connected cells, and influential network coordinators.
    """
    def __init__(self):
        pass

    def compute_network_intelligence(
        self,
        entities: List[ExtractedEntity],
        edges: List[ExtractedEdge],
        anomalies: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Runs graph analytics algorithms on the investigation graph.
        Returns: {centrality_metrics, communities, structural_brokers, ranked_key_players}
        """
        # Build undirected graph for community detection & centrality
        G = nx.Graph()
        
        # Add all nodes
        entity_lookup = {e.entity_id: e for e in entities}
        for ent in entities:
            G.add_node(ent.entity_id, label=ent.entity_type.value, name=ent.primary_value)

        # Add edges with weights
        for edge in edges:
            w = edge.weight if edge.weight > 0 else 1.0
            if G.has_edge(edge.source_entity_id, edge.target_entity_id):
                G[edge.source_entity_id][edge.target_entity_id]["weight"] += w
            else:
                G.add_edge(edge.source_entity_id, edge.target_entity_id, weight=w)

        if G.number_of_nodes() == 0:
            return {
                "total_nodes": 0,
                "total_edges": 0,
                "ranked_key_players": [],
                "structural_brokers": [],
                "communities": []
            }

        # 1. Degree Centrality
        degree_dict = nx.degree_centrality(G)

        # 2. Betweenness Centrality (identifies bottleneck structural brokers)
        betweenness_dict = nx.betweenness_centrality(G, weight="weight") if G.number_of_nodes() > 2 else {n: 0.0 for n in G.nodes()}

        # 3. Eigenvector Centrality (influence from high-degree neighbors)
        try:
            eigen_dict = nx.eigenvector_centrality(G, max_iter=500, weight="weight")
        except Exception:
            eigen_dict = degree_dict

        # 4. Community Detection (using greedy modularity communities)
        communities_raw = list(nx.community.greedy_modularity_communities(G))
        node_to_community: Dict[str, int] = {}
        community_summaries: List[Dict[str, Any]] = []

        for comm_id, comm_nodes in enumerate(communities_raw):
            node_names = [entity_lookup[n].primary_value for n in comm_nodes if n in entity_lookup]
            for n in comm_nodes:
                node_to_community[n] = comm_id
            community_summaries.append({
                "community_id": comm_id,
                "size": len(comm_nodes),
                "sample_members": node_names[:5]
            })

        # 5. Anomaly weights by entity
        entity_anomaly_weights = {e.entity_id: 0.0 for e in entities}
        for anom in anomalies:
            src = anom.get("source_entity_id")
            dst = anom.get("target_entity_id")
            score = anom.get("anomaly_score", 0.0)
            if src in entity_anomaly_weights:
                entity_anomaly_weights[src] += score
            if dst in entity_anomaly_weights:
                entity_anomaly_weights[dst] += score

        # 6. Composite Key-Player Scoring
        # Composite = 0.35 * Betweenness + 0.25 * Degree + 0.20 * Eigenvector + 0.20 * AnomalyWeight
        key_players: List[Dict[str, Any]] = []
        structural_brokers: List[Dict[str, Any]] = []

        for node_id in G.nodes():
            ent = entity_lookup.get(node_id)
            if not ent:
                continue

            deg = degree_dict.get(node_id, 0.0)
            btw = betweenness_dict.get(node_id, 0.0)
            eig = eigen_dict.get(node_id, 0.0)
            anom_w = min(1.0, entity_anomaly_weights.get(node_id, 0.0))

            composite_score = round(0.35 * btw + 0.25 * deg + 0.20 * eig + 0.20 * anom_w, 3)

            rationale_parts = []
            if btw > 0.15:
                rationale_parts.append("High betweenness bridging separate network sub-clusters.")
                structural_brokers.append({
                    "entity_id": node_id,
                    "name": ent.primary_value,
                    "betweenness": round(btw, 3),
                    "community_id": node_to_community.get(node_id, 0)
                })
            if deg > 0.3:
                rationale_parts.append("Dense immediate contact hub.")
            if anom_w > 0.5:
                rationale_parts.append("Involved in multiple high-severity behavioral anomalies.")
            if not rationale_parts:
                rationale_parts.append("Standard network participant.")

            key_players.append({
                "entity_id": node_id,
                "name": ent.primary_value,
                "entity_type": ent.entity_type.value,
                "composite_rank_score": composite_score,
                "metrics": {
                    "degree_centrality": round(deg, 3),
                    "betweenness_centrality": round(btw, 3),
                    "eigenvector_centrality": round(eig, 3),
                    "anomaly_influence": round(anom_w, 2),
                    "community_id": node_to_community.get(node_id, 0)
                },
                "structural_rationale": " ".join(rationale_parts),
                "investigative_priority": "CRITICAL_HUB" if composite_score >= 0.50 else ("KEY_INTERMEDIARY" if composite_score >= 0.30 else "PERIPHERAL")
            })

        key_players.sort(key=lambda x: x["composite_rank_score"], reverse=True)

        return {
            "total_nodes": G.number_of_nodes(),
            "total_edges": G.number_of_edges(),
            "density": round(nx.density(G), 3),
            "communities": community_summaries,
            "structural_brokers": structural_brokers,
            "ranked_key_players": key_players[:10],
            "disclaimer": "Graph rankings represent structural network prominence and investigative leads; they do NOT constitute proof of guilt."
        }


analytics_service = GraphAnalyticsService()

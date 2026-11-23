"""
Agent 10: Graph Intelligence Agent Implementation
"""
from typing import Any, Dict, List, Tuple
from src.agents.base_agent import BaseAgent
from src.agents.registry import agent_registry
from src.agents.state import SharedInvestigationState
from src.agents.tools.analytics_tools import run_graph_analytics


class GraphIntelligenceAgent(BaseAgent):
    """
    Agent responsible for running Graph Data Science algorithms,
    detecting communities, identifying structural brokers, and ranking key players.
    """
    def __init__(self):
        super().__init__(
            name="GRAPH_INTELLIGENCE_AGENT",
            description="Computes graph centrality, Louvain communities, and structural key-player rankings.",
            system_prompt="Analyze network topology and structural brokers without conflating centrality with guilt."
        )

    def _execute(
        self, state: SharedInvestigationState, input_data: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], List[str], float]:
        if not state.consolidated_entities:
            raise ValueError(f"No entities available for graph analytics in case {state.case_id}.")

        # Invoke graph analytics tool
        intelligence = run_graph_analytics(
            entities=state.consolidated_entities,
            edges=state.consolidated_edges,
            anomalies=state.anomaly_results
        )

        state.graph_intelligence = intelligence

        evidence_refs = [
            f"KEY_PLAYER:{kp['name']}(rank={kp['composite_rank_score']})"
            for kp in intelligence.get("ranked_key_players", [])[:3]
        ]

        output = {
            "communities_identified": len(intelligence.get("communities", [])),
            "structural_brokers_count": len(intelligence.get("structural_brokers", [])),
            "top_key_players": intelligence.get("ranked_key_players", [])[:5],
            "disclaimer": intelligence.get("disclaimer")
        }

        return output, evidence_refs, 0.95


# Register singleton instance
graph_agent = GraphIntelligenceAgent()
agent_registry.register(graph_agent)

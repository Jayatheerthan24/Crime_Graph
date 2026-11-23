"""
Agent 8: Relationship Mapping Agent Implementation
"""
from typing import Any, Dict, List, Tuple
from src.agents.base_agent import BaseAgent
from src.agents.registry import agent_registry
from src.agents.state import SharedInvestigationState
from src.agents.tools.graph_tools import upsert_investigation_graph


class RelationshipMappingAgent(BaseAgent):
    """
    Agent responsible for translating validated entities and edges
    into parameterized Neo4j graph structures and maintaining graph state.
    """
    def __init__(self):
        super().__init__(
            name="RELATIONSHIP_MAPPING_AGENT",
            description="Builds and updates the investigation relationship graph using parameterized transactional upserts.",
            system_prompt="Map entities and relationships into the graph store idempotently without Cypher injection."
        )

    def _execute(
        self, state: SharedInvestigationState, input_data: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], List[str], float]:
        if not state.consolidated_entities:
            raise ValueError(f"No consolidated entities available to map for case {state.case_id}.")

        # Invoke graph upsert tool
        upsert_summary = upsert_investigation_graph(
            case_id=state.case_id,
            entities=state.consolidated_entities,
            edges=state.consolidated_edges
        )

        state.graph_summary = upsert_summary

        evidence_refs = [
            f"GRAPH:nodes_{upsert_summary['nodes_in_graph']}:edges_{upsert_summary['edges_in_graph']}"
        ]

        output = {
            "case_id": state.case_id,
            "nodes_upserted": len(state.consolidated_entities),
            "edges_upserted": len(state.consolidated_edges),
            "graph_summary": upsert_summary
        }

        return output, evidence_refs, 0.98


# Register singleton instance
relationship_agent = RelationshipMappingAgent()
agent_registry.register(relationship_agent)

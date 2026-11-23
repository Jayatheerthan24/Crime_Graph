"""
Agent 6: Entity Validation and Resolution Agent Implementation
"""
from typing import Any, Dict, List, Tuple
from src.agents.base_agent import BaseAgent
from src.agents.registry import agent_registry
from src.agents.state import SharedInvestigationState
from src.agents.tools.entity_tools import consolidate_and_resolve_entities


class EntityResolutionAgent(BaseAgent):
    """
    Agent responsible for collecting extractions across all sources,
    normalizing values, merging exact identifiers, and flagging fuzzy ambiguities.
    """
    def __init__(self):
        super().__init__(
            name="ENTITY_RESOLUTION_AGENT",
            description="Consolidates entities across sources, merges exact identifiers, and flags probabilistic matches.",
            system_prompt="Consolidate entities without auto-merging uncertain names; preserve aliases and audit provenance."
        )

    def _execute(
        self, state: SharedInvestigationState, input_data: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], List[str], float]:
        if not state.source_extractions:
            raise ValueError(f"No source extractions found in state for case {state.case_id}.")

        # Invoke entity resolution tool
        canonical_entities, consolidated_edges, ambiguous_matches = consolidate_and_resolve_entities(
            source_extractions=state.source_extractions
        )

        # Store in shared investigation state
        state.consolidated_entities = canonical_entities
        state.consolidated_edges = consolidated_edges
        state.ambiguous_entities = ambiguous_matches

        evidence_refs = [f"SOURCES:{','.join(state.source_extractions.keys())}"]

        output = {
            "total_canonical_entities": len(canonical_entities),
            "total_consolidated_edges": len(consolidated_edges),
            "ambiguous_matches_count": len(ambiguous_matches),
            "ambiguous_matches": ambiguous_matches,
            "requires_review": len([m for m in ambiguous_matches if m.get("tier") == "PROBABILISTIC"]) > 0
        }

        return output, evidence_refs, 0.95


# Register singleton instance
entity_resolution_agent = EntityResolutionAgent()
agent_registry.register(entity_resolution_agent)

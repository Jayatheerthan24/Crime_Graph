"""
Agent 7: Identity Intelligence Agent Implementation
"""
from typing import Any, Dict, List, Tuple
from src.agents.base_agent import BaseAgent
from src.agents.registry import agent_registry
from src.agents.state import SharedInvestigationState
from src.agents.tools.identity_tools import resolve_identities


class IdentityIntelligenceAgent(BaseAgent):
    """
    Agent responsible for uncovering hidden links between digital identities
    using multi-signal hardware, behavioral, and contact analysis.
    """
    def __init__(self):
        super().__init__(
            name="IDENTITY_INTELLIGENCE_AGENT",
            description="Computes multi-signal identity links (IMEI, Jaccard, timing cosine, SIM churn).",
            system_prompt="Identify identity correlation signals with explainable confidence; avoid binary claims of identity."
        )

    def _execute(
        self, state: SharedInvestigationState, input_data: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], List[str], float]:
        if not state.consolidated_entities:
            raise ValueError(f"No consolidated entities available in state for case {state.case_id}.")

        # Invoke identity resolution tool
        identity_results, candidate_edges = resolve_identities(
            entities=state.consolidated_entities,
            edges=state.consolidated_edges,
            sim_churn_signals=state.sim_churn_signals
        )

        # Store results in shared investigation state
        state.identity_links = identity_results
        # Append candidate edges into consolidated edges
        state.consolidated_edges.extend(candidate_edges)

        evidence_refs = [
            f"LINK:{res['entity_a_phone']}<->{res['entity_b_phone']}(conf={res['overall_confidence']})"
            for res in identity_results
        ]

        output = {
            "identity_links_evaluated": len(identity_results),
            "high_confidence_links": len([r for r in identity_results if r["overall_confidence"] >= 0.70]),
            "identity_correlations": identity_results
        }

        avg_conf = (
            sum(r["overall_confidence"] for r in identity_results) / len(identity_results)
            if identity_results else 1.0
        )

        return output, evidence_refs, avg_conf


# Register singleton instance
identity_agent = IdentityIntelligenceAgent()
agent_registry.register(identity_agent)

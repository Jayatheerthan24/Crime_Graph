"""
Agent 3: CDR Intelligence Agent Implementation
"""
from typing import Any, Dict, List, Tuple
from src.agents.base_agent import BaseAgent
from src.agents.registry import agent_registry
from src.agents.state import SharedInvestigationState
from src.agents.tools.cdr_tools import process_cdr_data


class CDRIntelligenceAgent(BaseAgent):
    """
    Agent responsible for ingesting telecom records, calculating communication
    velocity and timing distributions, and identifying SIM churn.
    """
    def __init__(self):
        super().__init__(
            name="CDR_INTELLIGENCE_AGENT",
            description="Analyzes Call Detail Records (CDRs), aggregates communications, and detects SIM churn.",
            system_prompt="Analyze call frequency, burst patterns, and hardware bindings without assuming guilt."
        )

    def _execute(
        self, state: SharedInvestigationState, input_data: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], List[str], float]:
        source_id = input_data.get("source_id", f"CDR-{state.case_id}")
        records = input_data.get("records", [])
        metadata = input_data.get("metadata", {})

        if not records:
            raise ValueError(f"CDR source {source_id} contains empty records list.")

        # Invoke CDR processing tool
        extraction_result, sim_churn_signals = process_cdr_data(
            source_id=source_id, records=records, metadata=metadata
        )

        # Store in investigation state
        state.add_source_extraction(extraction_result)
        if sim_churn_signals:
            state.sim_churn_signals.extend(sim_churn_signals)

        evidence_refs = [f"{source_id}:records_{len(records)}"]
        
        output = {
            "source_id": source_id,
            "records_processed": len(records),
            "phone_nodes_extracted": len(extraction_result.entities),
            "aggregated_edges_count": len(extraction_result.edges),
            "sim_churn_alerts_count": len(sim_churn_signals),
            "sim_churn_details": sim_churn_signals[:3]
        }

        return output, evidence_refs, 0.95


# Register singleton instance
cdr_agent = CDRIntelligenceAgent()
agent_registry.register(cdr_agent)

"""
Agent 5: Digital Footprint Intelligence Agent Implementation
"""
from typing import Any, Dict, List, Tuple
from src.agents.base_agent import BaseAgent
from src.agents.registry import agent_registry
from src.agents.state import SharedInvestigationState
from src.agents.tools.social_tools import process_digital_footprint


class DigitalFootprintAgent(BaseAgent):
    """
    Agent responsible for ingesting social and digital forensic footprints,
    extracting unique handles, and identifying explicit account links.
    """
    def __init__(self):
        super().__init__(
            name="DIGITAL_FOOTPRINT_AGENT",
            description="Analyzes digital forensic footprints, social profiles, and online handles.",
            system_prompt="Map digital associations based on verified identifiers without conflating identical display names."
        )

    def _execute(
        self, state: SharedInvestigationState, input_data: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], List[str], float]:
        source_id = input_data.get("source_id", f"DIG-{state.case_id}")
        records = input_data.get("records", [])
        metadata = input_data.get("metadata", {})

        if not records:
            raise ValueError(f"Digital footprint source {source_id} contains empty records list.")

        # Invoke digital footprint tool
        extraction_result = process_digital_footprint(
            source_id=source_id, records=records, metadata=metadata
        )

        # Store in shared investigation state
        state.add_source_extraction(extraction_result)

        evidence_refs = [f"{source_id}:exhibits_{len(records)}"]
        
        output = {
            "source_id": source_id,
            "digital_records_analyzed": len(records),
            "digital_nodes_extracted": len(extraction_result.entities),
            "associations_mapped": len(extraction_result.edges)
        }

        return output, evidence_refs, 0.90


# Register singleton instance
digital_agent = DigitalFootprintAgent()
agent_registry.register(digital_agent)

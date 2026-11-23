"""
Agent 2: FIR Intelligence Agent Implementation
"""
from typing import Any, Dict, List, Tuple
from src.agents.base_agent import BaseAgent
from src.agents.registry import agent_registry
from src.agents.state import SharedInvestigationState
from src.agents.tools.fir_tools import extract_fir_intelligence


class FIRIntelligenceAgent(BaseAgent):
    """
    Agent responsible for analyzing unstructured FIRs, extracting grounded entities,
    and returning confidence-scored intelligence.
    """
    def __init__(self):
        super().__init__(
            name="FIR_INTELLIGENCE_AGENT",
            description="Analyzes FIRs and complaints, extracts entities with offsets, and maps incident relations.",
            system_prompt="Extract entities and event relationships grounded in verbatim FIR evidence without hallucination."
        )

    def _execute(
        self, state: SharedInvestigationState, input_data: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], List[str], float]:
        source_id = input_data.get("source_id", f"FIR-{state.case_id}")
        content = input_data.get("content", "")
        metadata = input_data.get("metadata", {})

        if not content:
            raise ValueError(f"FIR source {source_id} contains empty content.")

        # Invoke FIR processing tool
        extraction_result = extract_fir_intelligence(source_id=source_id, content=content, metadata=metadata)
        
        # Add to shared investigation state
        state.add_source_extraction(extraction_result)

        evidence_refs = [f"{source_id}:char_{e.provenance[0].character_offsets}" for e in extraction_result.entities if e.provenance]
        
        output = {
            "source_id": source_id,
            "entities_extracted": len(extraction_result.entities),
            "edges_mapped": len(extraction_result.edges),
            "summary": extraction_result.raw_text_summary,
            "entity_ids": [e.entity_id for e in extraction_result.entities]
        }
        
        # Calculate aggregate confidence
        avg_confidence = (
            sum(e.confidence for e in extraction_result.entities) / len(extraction_result.entities)
            if extraction_result.entities else 1.0
        )

        return output, evidence_refs, avg_confidence


# Register singleton instance
fir_agent = FIRIntelligenceAgent()
agent_registry.register(fir_agent)

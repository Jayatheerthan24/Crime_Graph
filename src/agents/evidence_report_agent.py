"""
Agent 11: Evidence Validation and Report Agent Implementation
"""
from typing import Any, Dict, List, Tuple
from src.agents.base_agent import BaseAgent
from src.agents.registry import agent_registry
from src.agents.state import SharedInvestigationState
from src.agents.tools.report_tools import generate_validated_dossier


class EvidenceReportAgent(BaseAgent):
    """
    Agent responsible for quality assurance, verifying provenance,
    isolating direct vs. inferred claims, and formatting the final investigation dossier.
    """
    def __init__(self):
        super().__init__(
            name="EVIDENCE_REPORT_AGENT",
            description="Audits provenance, validates fact grounding, and synthesizes the final intelligence dossier.",
            system_prompt="Produce an objective, evidence-grounded intelligence report without unproven conclusions."
        )

    def _execute(
        self, state: SharedInvestigationState, input_data: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], List[str], float]:
        agent_exec_summary = {
            k: {"status": v.status.value, "time_ms": v.processing_time_ms}
            for k, v in state.agent_results.items()
        }

        # Invoke report validation tool
        report = generate_validated_dossier(
            investigation_id=state.investigation_id,
            case_id=state.case_id,
            status=state.status.value,
            sources_analyzed=list(state.source_extractions.keys()),
            entities=state.consolidated_entities,
            edges=state.consolidated_edges,
            identity_links=state.identity_links,
            anomalies=state.anomaly_results,
            graph_intelligence=state.graph_intelligence,
            agent_execution_summary=agent_exec_summary,
            errors=state.errors
        )

        state.validation_report = report

        evidence_refs = [
            f"DOSSIER:{state.investigation_id}:sources_{len(state.source_extractions)}"
        ]

        output = {
            "investigation_id": state.investigation_id,
            "case_id": state.case_id,
            "dossier": report,
            "validation_passed": len(report["evidence_audit"]["unsupported_entities_flagged"]) == 0
        }

        return output, evidence_refs, 0.99


# Register singleton instance
report_agent = EvidenceReportAgent()
agent_registry.register(report_agent)

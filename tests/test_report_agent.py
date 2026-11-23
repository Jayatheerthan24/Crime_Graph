"""
Unit Tests for Evidence Validation & Report Agent (Agent 11)
"""
from src.agents.fir_agent import fir_agent
from src.agents.entity_resolution_agent import entity_resolution_agent
from src.agents.relationship_agent import relationship_agent
from src.agents.evidence_report_agent import report_agent
from src.agents.schemas import AgentStatusEnum


def test_evidence_report_agent(sample_investigation_state, synthetic_fir_text):
    fir_agent.run(sample_investigation_state, {"source_id": "FIR-01", "content": synthetic_fir_text})
    entity_resolution_agent.run(sample_investigation_state, {})
    relationship_agent.run(sample_investigation_state, {})
    
    # Run Agent 11
    result = report_agent.run(sample_investigation_state, {})
    assert result.status == AgentStatusEnum.SUCCESS
    assert sample_investigation_state.validation_report is not None
    
    dossier = sample_investigation_state.validation_report
    assert dossier["investigation_id"] == sample_investigation_state.investigation_id
    assert dossier["case_id"] == sample_investigation_state.case_id
    assert "evidence_audit" in dossier
    assert "executive_summary" in dossier
    assert "evidentiary_disclaimer" in dossier

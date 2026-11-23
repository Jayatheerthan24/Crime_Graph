"""
Unit Tests for Entity Resolution & Identity Intelligence Agents (Agents 6 & 7)
"""
from src.agents.fir_agent import fir_agent
from src.agents.cdr_agent import cdr_agent
from src.agents.entity_resolution_agent import entity_resolution_agent
from src.agents.identity_agent import identity_agent
from src.agents.schemas import AgentStatusEnum
from src.core.schemas import EdgeTypeEnum, EntityTypeEnum


def test_entity_resolution_agent(sample_investigation_state, synthetic_fir_text, synthetic_cdr_records):
    # Ingest sources into state
    fir_agent.run(sample_investigation_state, {"source_id": "FIR-01", "content": synthetic_fir_text})
    cdr_agent.run(sample_investigation_state, {"source_id": "CDR-01", "records": synthetic_cdr_records})
    
    # Run Agent 6
    result = entity_resolution_agent.run(sample_investigation_state, {})
    
    assert result.status == AgentStatusEnum.SUCCESS
    assert len(sample_investigation_state.consolidated_entities) > 0
    assert len(sample_investigation_state.consolidated_edges) > 0
    
    # Verify phone +919810011222 from FIR and CDR was merged to same canonical node
    phone_nodes = [
        e for e in sample_investigation_state.consolidated_entities
        if e.entity_type == EntityTypeEnum.PHONE and "+919810011222" in e.normalized_value
    ]
    assert len(phone_nodes) == 1
    # Check that provenance includes both FIR and CDR
    src_types = {p.source_type for p in phone_nodes[0].provenance}
    assert len(src_types) >= 2


def test_identity_intelligence_agent(sample_investigation_state, synthetic_cdr_records):
    # Ingest CDR to produce shared hardware / SIM churn
    cdr_agent.run(sample_investigation_state, {"source_id": "CDR-01", "records": synthetic_cdr_records})
    entity_resolution_agent.run(sample_investigation_state, {})
    
    # Run Agent 7
    result = identity_agent.run(sample_investigation_state, {})
    
    assert result.status == AgentStatusEnum.SUCCESS
    assert len(sample_investigation_state.identity_links) >= 1
    
    # Check that top link has high hardware sharing score
    top_link = sample_investigation_state.identity_links[0]
    assert top_link["signal_scores"]["imei_sharing"] == 1.0
    assert top_link["overall_confidence"] >= 0.40
    assert "supporting_evidence" in top_link
    assert "missing_evidence" in top_link
    assert "contradictory_evidence" in top_link

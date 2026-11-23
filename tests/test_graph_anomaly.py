"""
Unit Tests for Graph, Anomaly & Intelligence Agents (Agents 8 - 10)
"""
from src.agents.fir_agent import fir_agent
from src.agents.cdr_agent import cdr_agent
from src.agents.financial_agent import financial_agent
from src.agents.entity_resolution_agent import entity_resolution_agent
from src.agents.identity_agent import identity_agent
from src.agents.relationship_agent import relationship_agent
from src.agents.anomaly_agent import anomaly_agent
from src.agents.graph_intelligence_agent import graph_agent
from src.agents.schemas import AgentStatusEnum
from src.services.neo4j_service import neo4j_service


def test_relationship_mapping_agent(
    sample_investigation_state, synthetic_fir_text, synthetic_cdr_records
):
    fir_agent.run(sample_investigation_state, {"source_id": "FIR-01", "content": synthetic_fir_text})
    cdr_agent.run(sample_investigation_state, {"source_id": "CDR-01", "records": synthetic_cdr_records})
    entity_resolution_agent.run(sample_investigation_state, {})
    
    # Run Agent 8
    result = relationship_agent.run(sample_investigation_state, {})
    assert result.status == AgentStatusEnum.SUCCESS
    assert sample_investigation_state.graph_summary["nodes_in_graph"] > 0
    assert sample_investigation_state.graph_summary["edges_in_graph"] > 0


def test_anomaly_investigation_agent(
    sample_investigation_state, synthetic_cdr_records, synthetic_financial_transactions
):
    cdr_agent.run(sample_investigation_state, {"source_id": "CDR-01", "records": synthetic_cdr_records})
    financial_agent.run(sample_investigation_state, {"source_id": "FIN-01", "transactions": synthetic_financial_transactions})
    entity_resolution_agent.run(sample_investigation_state, {})
    identity_agent.run(sample_investigation_state, {})
    relationship_agent.run(sample_investigation_state, {})
    
    # Run Agent 9
    result = anomaly_agent.run(sample_investigation_state, {})
    assert result.status == AgentStatusEnum.SUCCESS
    assert len(sample_investigation_state.anomaly_results) > 0
    
    rule_names = {a["rule_name"] for a in sample_investigation_state.anomaly_results}
    # Call burst and circular transactions should be detected
    assert "CALL_BURST_ANOMALY" in rule_names or "CIRCULAR_TRANSACTION_ANOMALY" in rule_names
    assert "investigator_briefing" in result.output


def test_graph_intelligence_agent(
    sample_investigation_state, synthetic_fir_text, synthetic_cdr_records
):
    fir_agent.run(sample_investigation_state, {"source_id": "FIR-01", "content": synthetic_fir_text})
    cdr_agent.run(sample_investigation_state, {"source_id": "CDR-01", "records": synthetic_cdr_records})
    entity_resolution_agent.run(sample_investigation_state, {})
    relationship_agent.run(sample_investigation_state, {})
    anomaly_agent.run(sample_investigation_state, {})
    
    # Run Agent 10
    result = graph_agent.run(sample_investigation_state, {})
    assert result.status == AgentStatusEnum.SUCCESS
    intel = sample_investigation_state.graph_intelligence
    assert "ranked_key_players" in intel
    assert "communities" in intel
    assert len(intel["ranked_key_players"]) > 0
    # Check disclaimer
    assert "guilt" in intel["disclaimer"].lower()

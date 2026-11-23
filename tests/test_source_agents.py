"""
Unit Tests for Source Intelligence Agents (Agents 2 - 5)
"""
from src.agents.fir_agent import fir_agent
from src.agents.cdr_agent import cdr_agent
from src.agents.financial_agent import financial_agent
from src.agents.digital_footprint_agent import digital_agent
from src.agents.schemas import AgentStatusEnum
from src.core.schemas import EntityTypeEnum, SourceTypeEnum


def test_fir_intelligence_agent(sample_investigation_state, synthetic_fir_text):
    input_data = {
        "source_id": "TEST-FIR-01",
        "content": synthetic_fir_text
    }
    result = fir_agent.run(sample_investigation_state, input_data)
    
    assert result.status == AgentStatusEnum.SUCCESS
    assert result.output["entities_extracted"] > 0
    assert "TEST-FIR-01" in sample_investigation_state.source_extractions
    
    extraction = sample_investigation_state.source_extractions["TEST-FIR-01"]
    types = {e.entity_type for e in extraction.entities}
    assert EntityTypeEnum.PERSON in types
    assert EntityTypeEnum.PHONE in types
    assert EntityTypeEnum.VEHICLE in types
    assert EntityTypeEnum.BANK_ACCOUNT in types


def test_cdr_intelligence_agent(sample_investigation_state, synthetic_cdr_records):
    input_data = {
        "source_id": "TEST-CDR-01",
        "records": synthetic_cdr_records
    }
    result = cdr_agent.run(sample_investigation_state, input_data)
    
    assert result.status == AgentStatusEnum.SUCCESS
    assert result.output["records_processed"] == len(synthetic_cdr_records)
    assert result.output["sim_churn_alerts_count"] >= 1
    assert len(sample_investigation_state.sim_churn_signals) >= 1
    
    # Check that burst was flagged in CDR edges
    extraction = sample_investigation_state.source_extractions["TEST-CDR-01"]
    burst_edges = [e for e in extraction.edges if e.properties.get("has_burst")]
    assert len(burst_edges) >= 1


def test_financial_intelligence_agent(sample_investigation_state, synthetic_financial_transactions):
    input_data = {
        "source_id": "TEST-FIN-01",
        "transactions": synthetic_financial_transactions
    }
    result = financial_agent.run(sample_investigation_state, input_data)
    
    assert result.status == AgentStatusEnum.SUCCESS
    assert result.output["transactions_analyzed"] == 3
    # Synthetic transactions ACC111 -> ACC222 -> ACC333 -> ACC111 form a circular loop!
    assert result.output["circular_cycles_detected"] >= 1
    
    extraction = sample_investigation_state.source_extractions["TEST-FIN-01"]
    assert len(extraction.entities) == 3


def test_digital_footprint_agent(sample_investigation_state, synthetic_digital_records):
    input_data = {
        "source_id": "TEST-DIG-01",
        "records": synthetic_digital_records
    }
    result = digital_agent.run(sample_investigation_state, input_data)
    
    assert result.status == AgentStatusEnum.SUCCESS
    assert result.output["digital_records_analyzed"] == 1
    
    extraction = sample_investigation_state.source_extractions["TEST-DIG-01"]
    assert len(extraction.entities) >= 2  # Handle, Phone, Email

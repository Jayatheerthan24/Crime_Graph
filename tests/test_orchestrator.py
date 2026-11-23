"""
Unit Tests for Master Orchestrator Agent (Agent 1)
Tests state machine transitions: PENDING -> RUNNING -> VALIDATING -> GRAPH_PROCESSING -> ANALYSIS -> COMPLETED
"""
from src.agents.orchestrator import orchestrator_agent
from src.agents.schemas import InvestigationStatusEnum
from src.core.schemas import InvestigationRequest


def test_orchestrator_state_machine_happy_path(full_synthetic_investigation_request):
    final_state = orchestrator_agent.execute_investigation(full_synthetic_investigation_request)
    
    # Assert final status is COMPLETED or REQUIRES_REVIEW (if ambiguous)
    assert final_state.status in (InvestigationStatusEnum.COMPLETED, InvestigationStatusEnum.REQUIRES_REVIEW)
    assert len(final_state.source_extractions) == 4
    assert len(final_state.consolidated_entities) > 0
    assert len(final_state.consolidated_edges) > 0
    assert len(final_state.agent_results) >= 8
    assert final_state.validation_report is not None
    
    # Verify state transitions were recorded in checkpoints
    statuses_in_checkpoints = [cp["status"] for cp in final_state.checkpoints]
    assert "RUNNING" in statuses_in_checkpoints
    assert "VALIDATING" in statuses_in_checkpoints
    assert "GRAPH_PROCESSING" in statuses_in_checkpoints
    assert "ANALYSIS" in statuses_in_checkpoints


def test_orchestrator_failure_recovery_on_missing_sources():
    empty_request = InvestigationRequest(
        case_id="TEST-EMPTY-CASE",
        investigator_id="INV-01",
        source_documents=[]
    )
    final_state = orchestrator_agent.execute_investigation(empty_request)
    assert final_state.status == InvestigationStatusEnum.FAILED
    assert len(final_state.errors) > 0


def test_orchestrator_partial_completion():
    partial_request = InvestigationRequest(
        case_id="TEST-PARTIAL-CASE",
        investigator_id="INV-01",
        source_documents=[
            {
                "source_type": "FIR",
                "source_id": "VALID-FIR",
                "content": "Complainant: Sunita. Accused: Vikram phone +919811122233."
            },
            {
                # Invalid empty CDR source
                "source_type": "CDR",
                "source_id": "BROKEN-CDR",
                "records": []
            }
        ]
    )
    final_state = orchestrator_agent.execute_investigation(partial_request)
    # The valid FIR proceeds while the broken CDR is isolated, resulting in PARTIALLY_COMPLETED or REQUIRES_REVIEW
    assert final_state.status in (InvestigationStatusEnum.PARTIALLY_COMPLETED, InvestigationStatusEnum.REQUIRES_REVIEW, InvestigationStatusEnum.COMPLETED)
    assert "VALID-FIR" in final_state.source_extractions

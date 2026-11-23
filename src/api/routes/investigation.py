"""
Investigation Orchestration API Endpoints
"""
from typing import Any, Dict
from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from src.core.schemas import InvestigationRequest
from src.agents.orchestrator import orchestrator_agent
from src.agents.state import SharedInvestigationState

router = APIRouter(prefix="/investigations", tags=["Investigations"])

# In-memory investigation state store (backed by database/redis in cluster deployments)
active_investigations: Dict[str, SharedInvestigationState] = {}


@router.post("/trigger", status_code=status.HTTP_202_ACCEPTED)
def trigger_investigation(request: InvestigationRequest, background_tasks: BackgroundTasks):
    """
    Triggers an authorized multi-agent investigation workflow.
    Executes through the Master Orchestrator state machine.
    """
    state = SharedInvestigationState(case_id=request.case_id)
    active_investigations[state.investigation_id] = state
    # Also index by case_id for convenient lookup
    active_investigations[request.case_id] = state

    # Execute orchestrator workflow
    def run_workflow():
        orchestrator_agent.execute_investigation(request=request, state=state)

    background_tasks.add_task(run_workflow)

    return {
        "message": "Investigation successfully initialized and dispatched to Master Orchestrator.",
        "investigation_id": state.investigation_id,
        "case_id": request.case_id,
        "status": state.status.value,
        "current_stage": state.current_stage
    }


@router.get("/{investigation_id}/status")
def get_investigation_status(investigation_id: str):
    """Retrieve real-time investigation state, agent progress, and checkpoints."""
    state = active_investigations.get(investigation_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investigation {investigation_id} not found."
        )
    return state.to_dict()


@router.get("/{investigation_id}/report")
def get_investigation_report(investigation_id: str):
    """Retrieve final validated intelligence dossier."""
    state = active_investigations.get(investigation_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investigation {investigation_id} not found."
        )
    if not state.validation_report:
        return {
            "status": state.status.value,
            "message": "Investigation report is still compiling or pending execution.",
            "current_stage": state.current_stage
        }
    return state.validation_report


@router.get("/{case_id}/anomalies")
def get_case_anomalies(case_id: str):
    """Retrieve behavioral anomalies detected for a case."""
    state = active_investigations.get(case_id)
    if not state:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Case {case_id} not found.")
    return {
        "case_id": case_id,
        "anomalies_count": len(state.anomaly_results),
        "anomalies": state.anomaly_results
    }


@router.get("/{case_id}/identities")
def get_case_identities(case_id: str):
    """Retrieve multi-signal identity links for a case."""
    state = active_investigations.get(case_id)
    if not state:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Case {case_id} not found.")
    return {
        "case_id": case_id,
        "identity_links_count": len(state.identity_links),
        "identity_links": state.identity_links
    }

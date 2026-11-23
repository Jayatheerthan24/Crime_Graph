"""
End-to-End System Tests using FastAPI TestClient
Tests investigation triggering, status polling, dossier retrieval, and graph querying.
"""
from fastapi.testclient import TestClient
from src.api.main import app
from src.agents.schemas import InvestigationStatusEnum

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"
    assert data["total_registered_agents"] == 11
    assert data["audit_trail_intact"] is True


def test_end_to_end_investigation_lifecycle(full_synthetic_investigation_request):
    payload = full_synthetic_investigation_request.model_dump()
    
    # 1. Trigger Investigation
    response = client.post("/api/v1/investigations/trigger", json=payload)
    assert response.status_code == 202
    data = response.json()
    assert "investigation_id" in data
    inv_id = data["investigation_id"]

    # 2. Query Status
    status_resp = client.get(f"/api/v1/investigations/{inv_id}/status")
    assert status_resp.status_code == 200
    state_data = status_resp.json()
    assert state_data["case_id"] == full_synthetic_investigation_request.case_id

    # 3. Query Report
    report_resp = client.get(f"/api/v1/investigations/{inv_id}/report")
    assert report_resp.status_code == 200

    # 4. Query Anomalies
    anom_resp = client.get(f"/api/v1/investigations/{full_synthetic_investigation_request.case_id}/anomalies")
    assert anom_resp.status_code == 200

    # 5. Query Identities
    id_resp = client.get(f"/api/v1/investigations/{full_synthetic_investigation_request.case_id}/identities")
    assert id_resp.status_code == 200


def test_subgraph_query_404():
    response = client.get("/api/v1/graph/subgraph?seed_entity_id=NON_EXISTENT_SEED&hops=2")
    assert response.status_code == 404

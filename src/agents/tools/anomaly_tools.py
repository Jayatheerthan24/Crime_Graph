"""
Tool Wrapper for Anomaly Engine Service
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from src.core.schemas import ExtractedEdge
from src.services.anomaly_service import anomaly_service


def run_anomaly_detection(
    edges: List[ExtractedEdge],
    identity_links: List[Dict[str, Any]],
    sim_churn_signals: List[Dict[str, Any]],
    incident_date: Optional[datetime] = None
) -> List[Dict[str, Any]]:
    """
    Tool function invoked by the Anomaly Investigation Agent.
    Executes CallBurstRule, CircularTransactionRule, SharedIdentityCrossCaseRule,
    SuddenUncontextualizedConnectionRule, and SIMChurnRule.
    """
    return anomaly_service.evaluate_all(
        edges=edges,
        identity_links=identity_links,
        sim_churn_signals=sim_churn_signals,
        incident_date=incident_date
    )

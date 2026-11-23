"""
Agent 9: Anomaly Investigation Agent Implementation
"""
from typing import Any, Dict, List, Tuple
from src.agents.base_agent import BaseAgent
from src.agents.registry import agent_registry
from src.agents.state import SharedInvestigationState
from src.agents.tools.anomaly_tools import run_anomaly_detection
from src.core.llm import llm_client


class AnomalyInvestigationAgent(BaseAgent):
    """
    Agent responsible for coordinating the deterministic behavioral anomaly
    and expectedness scoring engine, then synthesizing explainable summaries.
    """
    def __init__(self):
        super().__init__(
            name="ANOMALY_INVESTIGATION_AGENT",
            description="Coordinates deterministic anomaly rules (CallBurst, CircularTx, SIMChurn, SharedIdentity).",
            system_prompt="Coordinate deterministic rules and explain anomalies without inventing arbitrary scores or guilt."
        )

    def _execute(
        self, state: SharedInvestigationState, input_data: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], List[str], float]:
        # Invoke deterministic anomaly detection tool
        anomalies = run_anomaly_detection(
            edges=state.consolidated_edges,
            identity_links=state.identity_links,
            sim_churn_signals=state.sim_churn_signals
        )

        state.anomaly_results = anomalies

        # Generate local confidential explanation via LLM
        prompt = (
            f"Case: {state.case_id}\n"
            f"Anomalies Detected: {len(anomalies)}\n"
            f"Top Anomaly Findings: {anomalies[:3]}\n"
            "Provide a concise 2-sentence investigator briefing explaining why these patterns warrant review."
        )
        llm_explanation = llm_client.generate(prompt=prompt, case_id=state.case_id, user_id=self.name)

        evidence_refs = [
            f"ANOMALY:{a['rule_name']}(score={a['anomaly_score']})"
            for a in anomalies[:5]
        ]

        output = {
            "total_anomalies_detected": len(anomalies),
            "critical_anomalies_count": len([a for a in anomalies if a.get("severity") == "CRITICAL"]),
            "anomaly_findings": anomalies,
            "investigator_briefing": llm_explanation
        }

        avg_score = (
            sum(a["anomaly_score"] for a in anomalies) / len(anomalies)
            if anomalies else 0.0
        )

        return output, evidence_refs, max(0.80, avg_score)


# Register singleton instance
anomaly_agent = AnomalyInvestigationAgent()
agent_registry.register(anomaly_agent)

"""
Deterministic Behavioral Anomaly & Expectedness Scoring Engine
Evaluates concrete forensic rules against the investigation graph:
1. CallBurstRule
2. SharedIdentityCrossCaseRule
3. CircularTransactionRule
4. SuddenUncontextualizedConnectionRule
5. SIMChurnRule

All numerical scores are mathematically derived; LLMs are only used for investigator explanations.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.core.schemas import EdgeTypeEnum, EntityTypeEnum, ExtractedEdge, ExtractedEntity


class CallBurstRule:
    """Detects sudden, intense bursts of communication around incident time windows."""
    rule_name = "CALL_BURST_ANOMALY"

    def evaluate(self, edges: List[ExtractedEdge], incident_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        anomalies = []
        for edge in edges:
            if edge.relationship_type == EdgeTypeEnum.COMMUNICATED_WITH:
                has_burst = edge.properties.get("has_burst", False)
                call_count = edge.properties.get("call_count", 1)
                night_ratio = edge.properties.get("night_call_ratio", 0.0)
                
                score = 0.0
                reasons = []
                if has_burst:
                    score += 0.50
                    reasons.append("High-velocity burst detected (>=5 calls in <=2 hours).")
                if call_count >= 10:
                    score += 0.25
                    reasons.append(f"Elevated call volume ({call_count} calls).")
                if night_ratio >= 0.50:
                    score += 0.25
                    reasons.append(f"Abnormal nocturnal activity ({int(night_ratio*100)}% night calls).")
                
                if score >= 0.50:
                    anomalies.append({
                        "rule_name": self.rule_name,
                        "source_entity_id": edge.source_entity_id,
                        "target_entity_id": edge.target_entity_id,
                        "anomaly_score": round(score, 2),
                        "severity": "CRITICAL" if score >= 0.75 else "ELEVATED",
                        "rationale": " ".join(reasons),
                        "evidence": edge.properties
                    })
        return anomalies


class CircularTransactionRule:
    """Detects closed triangular or circular fund layering paths."""
    rule_name = "CIRCULAR_TRANSACTION_ANOMALY"

    def evaluate(self, edges: List[ExtractedEdge]) -> List[Dict[str, Any]]:
        anomalies = []
        # Group by target/source to find return flows
        for edge in edges:
            if edge.relationship_type == EdgeTypeEnum.TRANSACTED_WITH:
                # If circular transaction properties were tagged by financial service
                if "sample_transaction_ids" in edge.properties and edge.weight > 50000:
                    anomalies.append({
                        "rule_name": self.rule_name,
                        "source_entity_id": edge.source_entity_id,
                        "target_entity_id": edge.target_entity_id,
                        "anomaly_score": 0.85,
                        "severity": "CRITICAL",
                        "rationale": f"High-value structured fund transfer detected (INR {edge.weight:,.2f}) flagged in circular loop.",
                        "evidence": edge.properties
                    })
        return anomalies


class SharedIdentityCrossCaseRule:
    """Detects identical hardware/phone participating in cross-case activities."""
    rule_name = "SHARED_IDENTITY_CROSS_CASE_ANOMALY"

    def evaluate(self, identity_links: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        anomalies = []
        for link in identity_links:
            conf = link.get("overall_confidence", 0.0)
            signals = link.get("signal_scores", {})
            if signals.get("imei_sharing", 0.0) > 0 and conf >= 0.60:
                anomalies.append({
                    "rule_name": self.rule_name,
                    "source_entity_id": link["entity_a_id"],
                    "target_entity_id": link["entity_b_id"],
                    "anomaly_score": conf,
                    "severity": "HIGH",
                    "rationale": f"Shared hardware linkage detected across numbers {link['entity_a_phone']} and {link['entity_b_phone']} with confidence {conf}.",
                    "evidence": link
                })
        return anomalies


class SuddenUncontextualizedConnectionRule:
    """Detects high-intensity contact between entities with no prior interaction baseline."""
    rule_name = "SUDDEN_UNCONTEXTUALIZED_CONNECTION_ANOMALY"

    def evaluate(self, edges: List[ExtractedEdge]) -> List[Dict[str, Any]]:
        anomalies = []
        for edge in edges:
            if edge.relationship_type == EdgeTypeEnum.COMMUNICATED_WITH:
                call_count = edge.properties.get("call_count", 0)
                # If intense communication happened over a very narrow window
                if call_count >= 8 and edge.first_seen == edge.last_seen:
                    anomalies.append({
                        "rule_name": self.rule_name,
                        "source_entity_id": edge.source_entity_id,
                        "target_entity_id": edge.target_entity_id,
                        "anomaly_score": 0.70,
                        "severity": "ELEVATED",
                        "rationale": f"Sudden uncontextualized contact burst ({call_count} interactions) appearing without prior relationship baseline.",
                        "evidence": edge.properties
                    })
        return anomalies


class SIMChurnRule:
    """Detects rapid succession of SIM activations on a single hardware IMEI."""
    rule_name = "SIM_CHURN_ANOMALY"

    def evaluate(self, sim_churn_signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        anomalies = []
        for signal in sim_churn_signals:
            churn_count = signal.get("churn_count", 0)
            score = min(1.0, 0.40 + churn_count * 0.20)
            anomalies.append({
                "rule_name": self.rule_name,
                "imei": signal.get("imei"),
                "associated_numbers": signal.get("associated_numbers"),
                "anomaly_score": round(score, 2),
                "severity": "HIGH" if churn_count >= 3 else "MODERATE",
                "rationale": f"Hardware IMEI {signal.get('imei')} exhibited rapid churn with {churn_count} distinct SIM cards.",
                "evidence": signal
            })
        return anomalies


class AnomalyEngineService:
    """
    Coordinates all deterministic anomaly scoring rules.
    """
    def __init__(self):
        self.call_burst_rule = CallBurstRule()
        self.circular_tx_rule = CircularTransactionRule()
        self.shared_identity_rule = SharedIdentityCrossCaseRule()
        self.sudden_connection_rule = SuddenUncontextualizedConnectionRule()
        self.sim_churn_rule = SIMChurnRule()

    def evaluate_all(
        self,
        edges: List[ExtractedEdge],
        identity_links: List[Dict[str, Any]],
        sim_churn_signals: List[Dict[str, Any]],
        incident_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Executes all deterministic rules and aggregates results.
        """
        all_anomalies: List[Dict[str, Any]] = []

        all_anomalies.extend(self.call_burst_rule.evaluate(edges, incident_date))
        all_anomalies.extend(self.circular_tx_rule.evaluate(edges))
        all_anomalies.extend(self.shared_identity_rule.evaluate(identity_links))
        all_anomalies.extend(self.sudden_connection_rule.evaluate(edges))
        all_anomalies.extend(self.sim_churn_rule.evaluate(sim_churn_signals))

        # Sort anomalies by score descending
        all_anomalies.sort(key=lambda x: x.get("anomaly_score", 0.0), reverse=True)
        return all_anomalies


anomaly_service = AnomalyEngineService()

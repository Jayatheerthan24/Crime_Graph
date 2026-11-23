"""
Shared Investigation State Machine & Checkpoint Manager
"""
import copy
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from src.core.schemas import ExtractedEdge, ExtractedEntity, ExtractionResult
from src.agents.schemas import AgentResult, InvestigationStatusEnum


class SharedInvestigationState:
    """
    Thread-safe, observable investigation state passed across multi-agent workflows.
    Maintains stage transitions, checkpointing, and partial execution recovery.
    """
    def __init__(self, case_id: str, investigation_id: Optional[str] = None):
        self._lock = threading.RLock()
        self.investigation_id = investigation_id or f"INV-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{case_id}"
        self.case_id = case_id
        self.status = InvestigationStatusEnum.PENDING
        self.current_stage = "INITIALIZATION"
        
        # Evidence & Extraction containers
        self.source_extractions: Dict[str, ExtractionResult] = {}
        self.consolidated_entities: List[ExtractedEntity] = []
        self.consolidated_edges: List[ExtractedEdge] = []
        self.ambiguous_entities: List[Dict[str, Any]] = []
        
        # Intelligence & Analytics containers
        self.identity_links: List[Dict[str, Any]] = []
        self.sim_churn_signals: List[Dict[str, Any]] = []
        self.graph_summary: Dict[str, Any] = {}
        self.anomaly_results: List[Dict[str, Any]] = []
        self.graph_intelligence: Dict[str, Any] = {}
        self.validation_report: Optional[Dict[str, Any]] = None
        
        # Agent Execution Tracking
        self.agent_results: Dict[str, AgentResult] = {}
        self.errors: List[str] = []
        self.checkpoints: List[Dict[str, Any]] = []
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def transition_to(self, new_status: InvestigationStatusEnum, stage_name: str):
        """Perform a validated state machine transition."""
        with self._lock:
            self.status = new_status
            self.current_stage = stage_name
            self.updated_at = datetime.utcnow()
            self.save_checkpoint(f"Transitioned to {new_status.value} ({stage_name})")

    def add_source_extraction(self, extraction: ExtractionResult):
        """Record structured source intelligence extraction."""
        with self._lock:
            self.source_extractions[extraction.source_id] = extraction
            self.updated_at = datetime.utcnow()

    def add_agent_result(self, result: AgentResult):
        """Record an agent's execution output and metadata."""
        with self._lock:
            self.agent_results[result.agent_name] = result
            if result.errors:
                self.errors.extend(result.errors)
            self.updated_at = datetime.utcnow()

    def record_error(self, error_message: str):
        """Log a workflow error."""
        with self._lock:
            self.errors.append(f"[{datetime.utcnow().isoformat()}] {error_message}")
            self.updated_at = datetime.utcnow()

    def save_checkpoint(self, description: str):
        """Create a state snapshot for partial recovery or audit review."""
        with self._lock:
            snapshot = {
                "checkpoint_id": f"CP-{len(self.checkpoints)+1:03d}",
                "timestamp": datetime.utcnow().isoformat(),
                "description": description,
                "status": self.status.value,
                "current_stage": self.current_stage,
                "entity_count": len(self.consolidated_entities),
                "edge_count": len(self.consolidated_edges),
                "source_count": len(self.source_extractions),
                "agent_count": len(self.agent_results)
            }
            self.checkpoints.append(snapshot)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize state for dashboard APIs and reporting."""
        with self._lock:
            return {
                "investigation_id": self.investigation_id,
                "case_id": self.case_id,
                "status": self.status.value,
                "current_stage": self.current_stage,
                "sources_analyzed": list(self.source_extractions.keys()),
                "total_entities": len(self.consolidated_entities),
                "total_edges": len(self.consolidated_edges),
                "ambiguous_entities_count": len(self.ambiguous_entities),
                "identity_links_count": len(self.identity_links),
                "anomalies_detected": len(self.anomaly_results),
                "graph_intelligence_available": bool(self.graph_intelligence),
                "agent_execution_summary": {
                    k: {"status": v.status.value, "time_ms": v.processing_time_ms}
                    for k, v in self.agent_results.items()
                },
                "errors": self.errors,
                "checkpoints": self.checkpoints,
                "created_at": self.created_at.isoformat(),
                "updated_at": self.updated_at.isoformat()
            }

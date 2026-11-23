"""
Abstract Base Agent Definition
Provides standard execution lifecycle, validation, provenance tracking, and error handling.
"""
import abc
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from src.core.security import security_manager
from src.agents.schemas import AgentResult, AgentStatusEnum
from src.agents.state import SharedInvestigationState


class BaseAgent(abc.ABC):
    """
    Abstract base class for all CrimeGraph AI agents.
    Enforces standardized execution, safety boundaries, error reporting, and timing.
    """
    def __init__(self, name: str, description: str, system_prompt: Optional[str] = None):
        self.name = name
        self.description = description
        self.system_prompt = system_prompt or f"You are {name}, a specialized intelligence agent."

    def run(self, state: SharedInvestigationState, input_data: Dict[str, Any]) -> AgentResult:
        """
        Public execution wrapper with timing, audit logging, and defensive error isolation.
        """
        execution_id = f"EXEC-{self.name}-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')[:17]}"
        start_time = time.perf_counter()
        
        # Log execution initiation
        security_manager.log_audit(
            user_id="ORCHESTRATOR",
            user_role="SYSTEM_AGENT",
            case_id=state.case_id,
            action=f"AGENT_EXECUTE_START_{self.name}",
            details={"execution_id": execution_id, "input_keys": list(input_data.keys())}
        )
        
        errors: List[str] = []
        output: Dict[str, Any] = {}
        evidence_references: List[str] = []
        confidence: float = 1.0
        status: AgentStatusEnum = AgentStatusEnum.RUNNING

        try:
            output, evidence_references, confidence = self._execute(state, input_data)
            status = AgentStatusEnum.SUCCESS if not errors else AgentStatusEnum.PARTIAL
        except Exception as exc:
            status = AgentStatusEnum.FAILED
            err_msg = f"{self.name} execution failed: {str(exc)}"
            errors.append(err_msg)
            state.record_error(err_msg)
            output = {"error": str(exc), "stage": state.current_stage}
            confidence = 0.0

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        result = AgentResult(
            agent_name=self.name,
            execution_id=execution_id,
            case_id=state.case_id,
            status=status,
            input_reference=str(input_data.get("source_id", "INVESTIGATION_CONTEXT")),
            output=output,
            evidence_references=evidence_references,
            confidence=confidence,
            errors=errors,
            processing_time_ms=elapsed_ms
        )

        state.add_agent_result(result)
        
        # Audit log execution conclusion
        security_manager.log_audit(
            user_id="ORCHESTRATOR",
            user_role="SYSTEM_AGENT",
            case_id=state.case_id,
            action=f"AGENT_EXECUTE_END_{self.name}",
            details={"execution_id": execution_id, "status": status.value, "time_ms": elapsed_ms}
        )

        return result

    @abc.abstractmethod
    def _execute(
        self, state: SharedInvestigationState, input_data: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], List[str], float]:
        """
        Domain-specific agent logic implemented by subclasses.
        Returns: (output_dict, evidence_references, confidence_score)
        """
        pass

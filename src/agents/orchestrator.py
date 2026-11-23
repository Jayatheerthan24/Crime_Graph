"""
Agent 1: Master Orchestrator Agent Implementation
Coordinates multi-agent execution, manages the workflow state machine:
PENDING -> RUNNING -> VALIDATING -> GRAPH_PROCESSING -> ANALYSIS -> COMPLETED
Executes parallel source agents, ensures failure isolation, checkpointing, and idempotency.
"""
import concurrent.futures
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.core.schemas import InvestigationRequest
from src.core.security import security_manager
from src.agents.base_agent import BaseAgent
from src.agents.registry import agent_registry
from src.agents.schemas import (
    AgentStatusEnum,
    ExecutionPlan,
    ExecutionStage,
    InvestigationStatusEnum,
)
from src.agents.state import SharedInvestigationState

# Import all agents so they are auto-registered in agent_registry
import src.agents.fir_agent
import src.agents.cdr_agent
import src.agents.financial_agent
import src.agents.digital_footprint_agent
import src.agents.entity_resolution_agent
import src.agents.identity_agent
import src.agents.relationship_agent
import src.agents.anomaly_agent
import src.agents.graph_intelligence_agent
import src.agents.evidence_report_agent

logger = logging.getLogger("crimegraph.orchestrator")


class MasterOrchestratorAgent(BaseAgent):
    """
    Central Coordinator for CrimeGraph AI.
    Builds the execution plan, coordinates parallel source processing,
    and manages state transitions across all 11 agents.
    """
    def __init__(self):
        super().__init__(
            name="MASTER_ORCHESTRATOR_AGENT",
            description="Coordinates multi-agent investigation workflow, manages state transitions and error recovery.",
            system_prompt="Coordinate specialized intelligence agents across strict investigation boundaries with complete auditability."
        )

    def execute_investigation(
        self, request: InvestigationRequest, state: Optional[SharedInvestigationState] = None
    ) -> SharedInvestigationState:
        """
        Executes the full end-to-end multi-agent investigation workflow.
        """
        state = state or SharedInvestigationState(case_id=request.case_id)
        
        # 1. State: PENDING -> RUNNING (Initial Inspection & Plan Formulation)
        state.transition_to(InvestigationStatusEnum.RUNNING, "SOURCE_EXTRACTION")
        security_manager.log_audit(
            user_id=request.investigator_id,
            user_role=request.investigator_role,
            case_id=request.case_id,
            action="INVESTIGATION_ORCHESTRATION_START",
            details={"sources_count": len(request.source_documents), "priority": request.priority}
        )

        plan = self._build_execution_plan(request)
        had_optional_failure = False

        try:
            # 2. Stage 1: Parallel Source Intelligence Extraction
            source_tasks = self._dispatch_source_agents(request, state)
            if not source_tasks["success"] and source_tasks["mandatory_failed"]:
                err = source_tasks.get("error", "Source extraction failed: No recognizable source documents.")
                state.record_error(err)
                state.transition_to(InvestigationStatusEnum.FAILED, "SOURCE_EXTRACTION_FATAL")
                return state
            if source_tasks.get("had_partial_failures"):
                had_optional_failure = True

            # Check if any sources were successfully extracted
            if not state.source_extractions:
                state.record_error("No source documents could be extracted.")
                state.transition_to(InvestigationStatusEnum.FAILED, "NO_VALID_SOURCES")
                return state

            # 3. State: RUNNING -> VALIDATING (Entity Resolution & Identity Intelligence)
            state.transition_to(InvestigationStatusEnum.VALIDATING, "ENTITY_AND_IDENTITY_RESOLUTION")
            
            # Execute Agent 6: Entity Resolution Agent
            ent_agent = agent_registry.get("ENTITY_RESOLUTION_AGENT")
            if ent_agent:
                ent_res = ent_agent.run(state, {"source_extractions_count": len(state.source_extractions)})
                if ent_res.status == AgentStatusEnum.FAILED:
                    state.transition_to(InvestigationStatusEnum.FAILED, "ENTITY_RESOLUTION_FAILED")
                    return state

            # Execute Agent 7: Identity Intelligence Agent
            id_agent = agent_registry.get("IDENTITY_INTELLIGENCE_AGENT")
            if id_agent:
                id_res = id_agent.run(state, {"entities_count": len(state.consolidated_entities)})
                if id_res.status == AgentStatusEnum.FAILED:
                    had_optional_failure = True

            # 4. State: VALIDATING -> GRAPH_PROCESSING (Relationship Mapping)
            state.transition_to(InvestigationStatusEnum.GRAPH_PROCESSING, "RELATIONSHIP_GRAPH_CONSTRUCTION")
            rel_agent = agent_registry.get("RELATIONSHIP_MAPPING_AGENT")
            if rel_agent:
                rel_res = rel_agent.run(state, {"entities_count": len(state.consolidated_entities)})
                if rel_res.status == AgentStatusEnum.FAILED:
                    state.transition_to(InvestigationStatusEnum.FAILED, "GRAPH_CONSTRUCTION_FAILED")
                    return state

            # 5. State: GRAPH_PROCESSING -> ANALYSIS (Anomaly Scoring & Graph Intelligence)
            state.transition_to(InvestigationStatusEnum.ANALYSIS, "ANOMALY_AND_GRAPH_INTELLIGENCE")
            
            # Execute Agent 9: Anomaly Investigation Agent
            anom_agent = agent_registry.get("ANOMALY_INVESTIGATION_AGENT")
            if anom_agent:
                anom_res = anom_agent.run(state, {"edges_count": len(state.consolidated_edges)})
                if anom_res.status == AgentStatusEnum.FAILED:
                    had_optional_failure = True

            # Execute Agent 10: Graph Intelligence Agent
            graph_agent = agent_registry.get("GRAPH_INTELLIGENCE_AGENT")
            if graph_agent:
                graph_res = graph_agent.run(state, {"entities_count": len(state.consolidated_entities)})
                if graph_res.status == AgentStatusEnum.FAILED:
                    had_optional_failure = True

            # 6. Stage 4: Evidence Grounding & Final Intelligence Report Generation
            report_agent = agent_registry.get("EVIDENCE_REPORT_AGENT")
            if report_agent:
                rep_res = report_agent.run(state, {"investigation_id": state.investigation_id})
                if rep_res.status == AgentStatusEnum.FAILED:
                    state.record_error("Evidence report agent failed to generate final dossier.")

            # 7. Final State Transition
            has_probabilistic_review = len([
                m for m in state.ambiguous_entities if m.get("tier") == "PROBABILISTIC"
            ]) > 0

            if has_probabilistic_review:
                final_status = InvestigationStatusEnum.REQUIRES_REVIEW
            elif had_optional_failure:
                final_status = InvestigationStatusEnum.PARTIALLY_COMPLETED
            else:
                final_status = InvestigationStatusEnum.COMPLETED

            state.transition_to(final_status, "WORKFLOW_CONCLUDED")

        except Exception as e:
            logger.error(f"Fatal orchestration failure in case {request.case_id}: {e}", exc_info=True)
            state.record_error(f"Fatal orchestration error: {str(e)}")
            state.transition_to(InvestigationStatusEnum.FAILED, "ORCHESTRATOR_FATAL_EXCEPTION")

        # Conclude Audit Log
        security_manager.log_audit(
            user_id=request.investigator_id,
            user_role=request.investigator_role,
            case_id=request.case_id,
            action="INVESTIGATION_ORCHESTRATION_END",
            details={
                "final_status": state.status.value,
                "entities_count": len(state.consolidated_entities),
                "edges_count": len(state.consolidated_edges),
                "anomalies_count": len(state.anomaly_results)
            }
        )

        return state

    def _build_execution_plan(self, request: InvestigationRequest) -> ExecutionPlan:
        """Determines the execution stages based on available source types."""
        plan_id = f"PLAN-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{request.case_id}"
        stages = [
            ExecutionStage(
                stage_name="PARALLEL_SOURCE_EXTRACTION",
                agents=["FIR_INTELLIGENCE_AGENT", "CDR_INTELLIGENCE_AGENT", "FINANCIAL_INTELLIGENCE_AGENT", "DIGITAL_FOOTPRINT_AGENT"],
                is_parallel=True,
                is_mandatory=True
            ),
            ExecutionStage(
                stage_name="ENTITY_AND_IDENTITY_RESOLUTION",
                agents=["ENTITY_RESOLUTION_AGENT", "IDENTITY_INTELLIGENCE_AGENT"],
                is_parallel=False,
                is_mandatory=True
            ),
            ExecutionStage(
                stage_name="GRAPH_CONSTRUCTION",
                agents=["RELATIONSHIP_MAPPING_AGENT"],
                is_parallel=False,
                is_mandatory=True
            ),
            ExecutionStage(
                stage_name="ANOMALY_AND_ANALYTICS",
                agents=["ANOMALY_INVESTIGATION_AGENT", "GRAPH_INTELLIGENCE_AGENT"],
                is_parallel=False,
                is_mandatory=False
            ),
            ExecutionStage(
                stage_name="EVIDENCE_VALIDATION_AND_REPORTING",
                agents=["EVIDENCE_REPORT_AGENT"],
                is_parallel=False,
                is_mandatory=True
            )
        ]
        return ExecutionPlan(plan_id=plan_id, case_id=request.case_id, stages=stages)

    def _dispatch_source_agents(
        self, request: InvestigationRequest, state: SharedInvestigationState
    ) -> Dict[str, Any]:
        """
        Executes source intelligence agents in parallel using thread pools.
        """
        tasks: List[Tuple[BaseAgent, Dict[str, Any]]] = []

        for doc in request.source_documents:
            doc_type = str(doc.get("source_type", "")).upper()
            source_id = doc.get("source_id", f"SRC-{doc_type}-{len(tasks)+1}")
            
            if doc_type in ("FIR", "COMPLAINT", "PDF"):
                agent = agent_registry.get("FIR_INTELLIGENCE_AGENT")
                if agent:
                    tasks.append((agent, {"source_id": source_id, "content": doc.get("content", ""), "metadata": doc}))
            elif doc_type in ("CDR", "CALL_RECORDS"):
                agent = agent_registry.get("CDR_INTELLIGENCE_AGENT")
                if agent:
                    tasks.append((agent, {"source_id": source_id, "records": doc.get("records", []), "metadata": doc}))
            elif doc_type in ("FINANCIAL", "BANK", "TRANSACTIONS"):
                agent = agent_registry.get("FINANCIAL_INTELLIGENCE_AGENT")
                if agent:
                    tasks.append((agent, {"source_id": source_id, "transactions": doc.get("transactions", []), "metadata": doc}))
            elif doc_type in ("DIGITAL", "SOCIAL", "CYBER"):
                agent = agent_registry.get("DIGITAL_FOOTPRINT_AGENT")
                if agent:
                    tasks.append((agent, {"source_id": source_id, "records": doc.get("records", []), "metadata": doc}))

        if not tasks:
            return {"success": False, "mandatory_failed": True, "error": "No recognizable source documents."}

        had_partial_failures = False
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(4, len(tasks))) as executor:
            futures = {
                executor.submit(agent.run, state, inp): agent.name
                for agent, inp in tasks
            }
            for future in concurrent.futures.as_completed(futures):
                ag_name = futures[future]
                try:
                    res = future.result()
                    if res.status == AgentStatusEnum.FAILED:
                        had_partial_failures = True
                except Exception as exc:
                    had_partial_failures = True
                    state.record_error(f"Source agent {ag_name} execution threw exception: {exc}")

        return {"success": True, "mandatory_failed": False, "had_partial_failures": had_partial_failures}

    def _execute(
        self, state: SharedInvestigationState, input_data: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], List[str], float]:
        """Wrapper required by BaseAgent."""
        req = InvestigationRequest(**input_data)
        updated_state = self.execute_investigation(request=req, state=state)
        return updated_state.to_dict(), [f"CASE:{state.case_id}"], 1.0


# Register singleton instance
orchestrator_agent = MasterOrchestratorAgent()
agent_registry.register(orchestrator_agent)

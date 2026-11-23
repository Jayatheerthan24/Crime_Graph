"""
Multi-Agent Communication & Task Schemas
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AgentStatusEnum(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"


class InvestigationStatusEnum(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    VALIDATING = "VALIDATING"
    GRAPH_PROCESSING = "GRAPH_PROCESSING"
    ANALYSIS = "ANALYSIS"
    COMPLETED = "COMPLETED"
    PARTIALLY_COMPLETED = "PARTIALLY_COMPLETED"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"
    FAILED = "FAILED"


class TaskAssignment(BaseModel):
    task_id: str
    agent_name: str
    case_id: str
    input_reference: str
    input_data: Dict[str, Any] = Field(default_factory=dict)
    dependencies: List[str] = Field(default_factory=list)
    status: AgentStatusEnum = AgentStatusEnum.PENDING
    retry_count: int = 0
    max_retries: int = 2
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AgentResult(BaseModel):
    agent_name: str
    execution_id: str
    case_id: str
    status: AgentStatusEnum
    input_reference: str
    output: Dict[str, Any] = Field(default_factory=dict)
    evidence_references: List[str] = Field(default_factory=list)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    errors: List[str] = Field(default_factory=list)
    processing_time_ms: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ExecutionStage(BaseModel):
    stage_name: str
    agents: List[str]
    is_parallel: bool = False
    is_mandatory: bool = True
    completed: bool = False


class ExecutionPlan(BaseModel):
    plan_id: str
    case_id: str
    stages: List[ExecutionStage] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)

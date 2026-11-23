"""
Core Shared Data Contracts for CrimeGraph AI
Strict Pydantic V2 schemas used across all agents and services.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field


class SourceTypeEnum(str, Enum):
    FIR = "FIR"
    CDR = "CDR"
    FINANCIAL = "FINANCIAL"
    DIGITAL_FOOTPRINT = "DIGITAL_FOOTPRINT"
    MANUAL_EVIDENCE = "MANUAL_EVIDENCE"


class EntityTypeEnum(str, Enum):
    PERSON = "PERSON"
    PHONE = "PHONE"
    BANK_ACCOUNT = "BANK_ACCOUNT"
    VEHICLE = "VEHICLE"
    LOCATION = "LOCATION"
    ORGANIZATION = "ORGANIZATION"
    DEVICE = "DEVICE"


class EdgeTypeEnum(str, Enum):
    COMMUNICATED_WITH = "COMMUNICATED_WITH"
    TRANSACTED_WITH = "TRANSACTED_WITH"
    ASSOCIATED_WITH = "ASSOCIATED_WITH"
    MENTIONED_IN = "MENTIONED_IN"
    LOCATED_AT = "LOCATED_AT"
    OPERATES = "OPERATES"
    OWNS_DEVICE = "OWNS_DEVICE"
    POTENTIAL_DUPLICATE = "POTENTIAL_DUPLICATE"


class ResolutionTierEnum(str, Enum):
    EXACT_IDENTIFIER = "EXACT_IDENTIFIER"      # e.g., Same Phone, Account, IMEI
    STRONGLY_SUPPORTED = "STRONGLY_SUPPORTED"  # High token match + context
    PROBABILISTIC = "PROBABILISTIC"            # Similarity 80-94%, flagged for review
    UNRESOLVED = "UNRESOLVED"                  # Kept distinct (<80%)


class SourceProvenance(BaseModel):
    source_id: str
    source_type: SourceTypeEnum
    document_hash: str
    page_number: Optional[int] = None
    character_offsets: Optional[Tuple[int, int]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    snippet: Optional[str] = None


class ExtractedEntity(BaseModel):
    entity_id: str
    entity_type: EntityTypeEnum
    primary_value: str
    normalized_value: str
    aliases: List[str] = Field(default_factory=list)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    provenance: List[SourceProvenance] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    resolution_tier: Optional[ResolutionTierEnum] = None
    is_canonical: bool = True
    canonical_id: Optional[str] = None


class ExtractedEdge(BaseModel):
    source_entity_id: str
    target_entity_id: str
    relationship_type: EdgeTypeEnum
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    weight: float = 1.0
    first_seen: datetime = Field(default_factory=datetime.utcnow)
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    provenance: List[SourceProvenance] = Field(default_factory=list)
    properties: Dict[str, Any] = Field(default_factory=dict)


class ExtractionResult(BaseModel):
    source_id: str
    source_type: SourceTypeEnum
    entities: List[ExtractedEntity] = Field(default_factory=list)
    edges: List[ExtractedEdge] = Field(default_factory=list)
    raw_text_summary: Optional[str] = None
    processing_metadata: Dict[str, Any] = Field(default_factory=dict)


class CaseSchema(BaseModel):
    case_id: str
    title: str
    incident_date: Optional[datetime] = None
    description: str
    status: str = "ACTIVE"
    assigned_investigator: str
    authorized_sources: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class InvestigationRequest(BaseModel):
    case_id: str
    investigator_id: str
    investigator_role: str = "INVESTIGATOR"
    source_documents: List[Dict[str, Any]] = Field(default_factory=list)
    priority: str = "NORMAL"
    notes: Optional[str] = None

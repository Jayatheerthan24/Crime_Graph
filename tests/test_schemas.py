"""
Unit Tests for Pydantic V2 Schemas & Data Contracts
"""
from datetime import datetime
import pytest
from pydantic import ValidationError

from src.core.schemas import (
    EdgeTypeEnum,
    EntityTypeEnum,
    ExtractedEdge,
    ExtractedEntity,
    ExtractionResult,
    InvestigationRequest,
    SourceProvenance,
    SourceTypeEnum,
)
from src.agents.schemas import AgentResult, AgentStatusEnum, TaskAssignment


def test_source_provenance_validation():
    prov = SourceProvenance(
        source_id="SRC-001",
        source_type=SourceTypeEnum.FIR,
        document_hash="abc123hash",
        character_offsets=(10, 25),
        snippet="Sample snippet"
    )
    assert prov.source_id == "SRC-001"
    assert prov.source_type == SourceTypeEnum.FIR
    assert prov.character_offsets == (10, 25)


def test_extracted_entity_schema():
    ent = ExtractedEntity(
        entity_id="ENT-PER-12345678",
        entity_type=EntityTypeEnum.PERSON,
        primary_value="Rajesh Kumar",
        normalized_value="Rajesh Kumar",
        aliases=["Raju"],
        confidence=0.95
    )
    assert ent.entity_id == "ENT-PER-12345678"
    assert ent.confidence == 0.95
    assert ent.is_canonical is True


def test_extracted_edge_schema():
    edge = ExtractedEdge(
        source_entity_id="ENT-01",
        target_entity_id="ENT-02",
        relationship_type=EdgeTypeEnum.COMMUNICATED_WITH,
        confidence=0.90,
        weight=5.0
    )
    assert edge.relationship_type == EdgeTypeEnum.COMMUNICATED_WITH
    assert edge.weight == 5.0


def test_agent_result_schema():
    res = AgentResult(
        agent_name="FIR_INTELLIGENCE_AGENT",
        execution_id="EXEC-001",
        case_id="CASE-01",
        status=AgentStatusEnum.SUCCESS,
        input_reference="SRC-FIR-01",
        output={"entities_found": 3},
        evidence_references=["SRC-FIR-01:char_10_25"],
        confidence=0.95,
        processing_time_ms=12.5
    )
    assert res.status == AgentStatusEnum.SUCCESS
    assert res.processing_time_ms == 12.5

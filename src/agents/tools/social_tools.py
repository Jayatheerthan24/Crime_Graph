"""
Tool Wrapper for Digital Footprint Processing Service
"""
from typing import Any, Dict, List, Optional
from src.core.schemas import ExtractionResult
from src.services.digital_service import digital_service


def process_digital_footprint(
    source_id: str,
    records: List[Dict[str, Any]],
    metadata: Optional[Dict[str, Any]] = None
) -> ExtractionResult:
    """
    Tool function invoked by the Digital Footprint Intelligence Agent.
    Extracts digital identifiers and explicit account associations.
    """
    return digital_service.process_digital_records(
        records=records, source_id=source_id, metadata=metadata
    )

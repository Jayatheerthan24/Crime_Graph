"""
Tool Wrapper for CDR Processing Service
"""
from typing import Any, Dict, List, Optional, Tuple
from src.core.schemas import ExtractionResult
from src.services.cdr_service import cdr_service


def process_cdr_data(
    source_id: str,
    records: List[Dict[str, Any]],
    metadata: Optional[Dict[str, Any]] = None
) -> Tuple[ExtractionResult, List[Dict[str, Any]]]:
    """
    Tool function invoked by the CDR Intelligence Agent.
    Aggregates call records, computes statistics, detects bursts and churn.
    """
    return cdr_service.process_records(records=records, source_id=source_id, metadata=metadata)

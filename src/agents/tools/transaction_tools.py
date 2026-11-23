"""
Tool Wrapper for Financial Processing Service
"""
from typing import Any, Dict, List, Optional, Tuple
from src.core.schemas import ExtractionResult
from src.services.financial_service import financial_service


def process_financial_transactions(
    source_id: str,
    transactions: List[Dict[str, Any]],
    metadata: Optional[Dict[str, Any]] = None
) -> Tuple[ExtractionResult, List[Dict[str, Any]]]:
    """
    Tool function invoked by the Financial Intelligence Agent.
    Aggregates fund transfers, computes volume, detects circular layering.
    """
    return financial_service.process_transactions(
        transactions=transactions, source_id=source_id, metadata=metadata
    )

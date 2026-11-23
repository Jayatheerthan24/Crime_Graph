"""
Tool Wrapper for FIR Processing Service
"""
from typing import Any, Dict, Optional
from src.core.schemas import ExtractionResult
from src.services.fir_service import fir_service


def extract_fir_intelligence(
    source_id: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None
) -> ExtractionResult:
    """
    Tool function invoked by the FIR Intelligence Agent.
    Accepts raw text or OCR string, extracts entities and relationships.
    """
    return fir_service.process_text(text=content, source_id=source_id, metadata=metadata)

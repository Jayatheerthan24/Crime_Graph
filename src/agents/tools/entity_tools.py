"""
Tool Wrapper for Entity Validation and Resolution Service
"""
from typing import Any, Dict, List, Tuple
from src.core.schemas import ExtractedEdge, ExtractedEntity, ExtractionResult
from src.services.resolution_service import resolution_service


def consolidate_and_resolve_entities(
    source_extractions: Dict[str, ExtractionResult]
) -> Tuple[List[ExtractedEntity], List[ExtractedEdge], List[Dict[str, Any]]]:
    """
    Tool function invoked by the Entity Validation and Resolution Agent.
    Normalizes entities, performs exact identifier deduplication, and flags ambiguous fuzzy matches.
    """
    return resolution_service.consolidate_extractions(extractions=source_extractions)

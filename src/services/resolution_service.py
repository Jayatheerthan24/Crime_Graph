"""
Entity Validation and Resolution Service
Consolidates entities across FIR, CDR, Financial, and Digital sources.
Implements 4-tier match taxonomy using RapidFuzz, merges exact identifiers,
flags probabilistic ambiguities for investigator review, and normalizes edge references.
"""
import hashlib
from collections import defaultdict
from typing import Any, Dict, List, Set, Tuple
from rapidfuzz import fuzz

from src.core.schemas import (
    EdgeTypeEnum,
    EntityTypeEnum,
    ExtractedEdge,
    ExtractedEntity,
    ExtractionResult,
    ResolutionTierEnum,
)


class EntityResolutionService:
    """
    Deduplicates and canonicalizes entities across disparate forensic evidence sources.
    """
    def __init__(self, fuzzy_threshold_strong: float = 95.0, fuzzy_threshold_probabilistic: float = 80.0):
        self.strong_thresh = fuzzy_threshold_strong
        self.prob_thresh = fuzzy_threshold_probabilistic

    def consolidate_extractions(
        self, extractions: Dict[str, ExtractionResult]
    ) -> Tuple[List[ExtractedEntity], List[ExtractedEdge], List[Dict[str, Any]]]:
        """
        Consolidates all entities and edges from source extractions.
        Returns: (consolidated_entities, consolidated_edges, ambiguous_matches)
        """
        raw_entities: List[ExtractedEntity] = []
        raw_edges: List[ExtractedEdge] = []

        for ext in extractions.values():
            raw_entities.extend(ext.entities)
            raw_edges.extend(ext.edges)

        # 1. Exact Identifier Deduplication (Group by entity_type + normalized_value)
        exact_groups: Dict[Tuple[EntityTypeEnum, str], List[ExtractedEntity]] = defaultdict(list)
        for ent in raw_entities:
            key = (ent.entity_type, ent.normalized_value)
            exact_groups[key].append(ent)

        canonical_entities: List[ExtractedEntity] = []
        old_id_to_canonical_id: Dict[str, str] = {}

        for (ent_type, norm_val), group in exact_groups.items():
            # Canonical entity is the first or the one with highest confidence
            primary = sorted(group, key=lambda x: x.confidence, reverse=True)[0]
            canonical_id = f"CAN-{ent_type.value[:3]}-{hashlib.md5(norm_val.encode()).hexdigest()[:8]}"
            
            # Aggregate all aliases & provenance
            all_aliases: Set[str] = set()
            all_provenance = []
            merged_meta = {}
            for g in group:
                all_aliases.update(g.aliases)
                if g.primary_value != norm_val:
                    all_aliases.add(g.primary_value)
                all_provenance.extend(g.provenance)
                merged_meta.update(g.metadata)
                old_id_to_canonical_id[g.entity_id] = canonical_id

            canonical_entity = ExtractedEntity(
                entity_id=canonical_id,
                entity_type=ent_type,
                primary_value=primary.primary_value,
                normalized_value=norm_val,
                aliases=sorted(list(all_aliases)),
                confidence=round(sum(g.confidence for g in group) / len(group), 2),
                provenance=all_provenance,
                metadata=merged_meta,
                resolution_tier=ResolutionTierEnum.EXACT_IDENTIFIER if len(group) > 1 else None,
                is_canonical=True,
                canonical_id=canonical_id
            )
            canonical_entities.append(canonical_entity)

        # 2. Fuzzy Cross-Matching for Person entities
        ambiguous_matches: List[Dict[str, Any]] = []
        duplicate_edges: List[ExtractedEdge] = []
        persons = [e for e in canonical_entities if e.entity_type == EntityTypeEnum.PERSON]
        
        for i in range(len(persons)):
            for j in range(i + 1, len(persons)):
                p1 = persons[i]
                p2 = persons[j]
                # Compare primary values and aliases using token sort ratio
                score = fuzz.token_sort_ratio(p1.normalized_value.lower(), p2.normalized_value.lower())
                
                if score >= self.strong_thresh:
                    # Strongly supported match -> Suggest merge or link strongly
                    ambiguous_matches.append({
                        "entity_a_id": p1.entity_id,
                        "entity_a_name": p1.primary_value,
                        "entity_b_id": p2.entity_id,
                        "entity_b_name": p2.primary_value,
                        "similarity_score": round(score / 100.0, 2),
                        "tier": ResolutionTierEnum.STRONGLY_SUPPORTED.value,
                        "action": "AUTO_LINKED_AS_ALIASED_PERSON"
                    })
                    duplicate_edges.append(ExtractedEdge(
                        source_entity_id=p1.entity_id,
                        target_entity_id=p2.entity_id,
                        relationship_type=EdgeTypeEnum.POTENTIAL_DUPLICATE,
                        confidence=round(score / 100.0, 2),
                        properties={"match_tier": ResolutionTierEnum.STRONGLY_SUPPORTED.value, "similarity": score}
                    ))
                elif score >= self.prob_thresh:
                    # Probabilistic match -> NEVER auto-merge, flag for human investigator review!
                    ambiguous_matches.append({
                        "entity_a_id": p1.entity_id,
                        "entity_a_name": p1.primary_value,
                        "entity_b_id": p2.entity_id,
                        "entity_b_name": p2.primary_value,
                        "similarity_score": round(score / 100.0, 2),
                        "tier": ResolutionTierEnum.PROBABILISTIC.value,
                        "action": "FLAGGED_FOR_INVESTIGATOR_REVIEW"
                    })
                    duplicate_edges.append(ExtractedEdge(
                        source_entity_id=p1.entity_id,
                        target_entity_id=p2.entity_id,
                        relationship_type=EdgeTypeEnum.POTENTIAL_DUPLICATE,
                        confidence=round(score / 100.0, 2),
                        properties={"match_tier": ResolutionTierEnum.PROBABILISTIC.value, "requires_review": True}
                    ))

        # 3. Rewrite Edge Source and Target IDs to Canonical IDs
        consolidated_edges: List[ExtractedEdge] = []
        seen_edges = set()
        
        for edge in raw_edges + duplicate_edges:
            new_src = old_id_to_canonical_id.get(edge.source_entity_id, edge.source_entity_id)
            new_dst = old_id_to_canonical_id.get(edge.target_entity_id, edge.target_entity_id)
            
            if new_src == new_dst:
                # Avoid self-referential edges caused by merging
                continue
                
            edge_key = (new_src, new_dst, edge.relationship_type)
            if edge_key in seen_edges:
                continue
            seen_edges.add(edge_key)

            consolidated_edges.append(ExtractedEdge(
                source_entity_id=new_src,
                target_entity_id=new_dst,
                relationship_type=edge.relationship_type,
                confidence=edge.confidence,
                weight=edge.weight,
                first_seen=edge.first_seen,
                last_seen=edge.last_seen,
                provenance=edge.provenance,
                properties=edge.properties
            ))

        return canonical_entities, consolidated_edges, ambiguous_matches


resolution_service = EntityResolutionService()

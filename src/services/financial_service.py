"""
Financial Transaction Intelligence Service
Analyzes bank statements, UPI logs, and ledger feeds.
Aggregates fund transfers, computes velocity, and detects circular transaction cycles.
"""
import hashlib
import re
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import networkx as nx

from src.core.schemas import (
    EdgeTypeEnum,
    EntityTypeEnum,
    ExtractedEdge,
    ExtractedEntity,
    ExtractionResult,
    SourceProvenance,
    SourceTypeEnum,
)


class FinancialProcessingService:
    """
    Parses transaction records, aggregates fund flows, and identifies layering loops.
    """
    def __init__(self):
        pass

    def normalize_account(self, acct: str) -> str:
        clean = re.sub(r'\s+', '', str(acct)).upper()
        return clean

    def process_transactions(
        self, transactions: List[Dict[str, Any]], source_id: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[ExtractionResult, List[Dict[str, Any]]]:
        """
        Processes financial transaction records.
        Returns: (ExtractionResult, circular_transfer_cycles)
        """
        metadata = metadata or {}
        doc_hash = hashlib.sha256(str(transactions).encode('utf-8')).hexdigest()

        entities: Dict[str, ExtractedEntity] = {}
        pair_transfers: Dict[Tuple[str, str], Dict[str, Any]] = defaultdict(lambda: {
            "count": 0,
            "total_amount": 0.0,
            "channels": set(),
            "tx_ids": [],
            "timestamps": []
        })

        # Directed graph for cycle detection
        dg = nx.DiGraph()

        for tx in transactions:
            src = self.normalize_account(tx.get("source_account") or tx.get("sender_account", ""))
            dst = self.normalize_account(tx.get("target_account") or tx.get("receiver_account", ""))
            if not src or not dst or src == dst:
                continue

            amount = float(tx.get("amount", 0.0))
            channel = str(tx.get("channel", "UPI")).upper()
            tx_id = str(tx.get("transaction_id", tx.get("tx_id", "")))
            
            ts_raw = tx.get("timestamp") or tx.get("date")
            if isinstance(ts_raw, str):
                try:
                    ts = datetime.fromisoformat(ts_raw)
                except Exception:
                    ts = datetime.utcnow()
            elif isinstance(ts_raw, datetime):
                ts = ts_raw
            else:
                ts = datetime.utcnow()

            # Create Bank Account entities
            for acct in (src, dst):
                ent_id = f"ENT-ACC-{hashlib.md5(acct.encode()).hexdigest()[:8]}"
                if ent_id not in entities:
                    prov = SourceProvenance(
                        source_id=source_id,
                        source_type=SourceTypeEnum.FINANCIAL,
                        document_hash=doc_hash,
                        timestamp=ts
                    )
                    entities[ent_id] = ExtractedEntity(
                        entity_id=ent_id,
                        entity_type=EntityTypeEnum.BANK_ACCOUNT,
                        primary_value=acct,
                        normalized_value=acct,
                        confidence=0.98,
                        provenance=[prov],
                        metadata={"account_type": "SAVINGS_OR_CURRENT"}
                    )

            # Pairwise aggregation (directed: src -> dst)
            pair_key = (src, dst)
            pair_transfers[pair_key]["count"] += 1
            pair_transfers[pair_key]["total_amount"] += amount
            pair_transfers[pair_key]["channels"].add(channel)
            if tx_id:
                pair_transfers[pair_key]["tx_ids"].append(tx_id)
            pair_transfers[pair_key]["timestamps"].append(ts)

            # Add to graph
            if dg.has_edge(src, dst):
                dg[src][dst]["weight"] += amount
                dg[src][dst]["count"] += 1
            else:
                dg.add_edge(src, dst, weight=amount, count=1)

        # Detect Simple Directed Cycles (Layering / Circular Transactions)
        circular_cycles: List[Dict[str, Any]] = []
        try:
            cycles = list(nx.simple_cycles(dg))
            for cycle in cycles:
                # We focus on non-trivial cycles (2 to 5 hops)
                if 2 <= len(cycle) <= 5:
                    cycle_edges = list(zip(cycle, cycle[1:] + [cycle[0]]))
                    min_volume = min(dg[u][v]["weight"] for u, v in cycle_edges)
                    circular_cycles.append({
                        "cycle_path": cycle + [cycle[0]],
                        "hops": len(cycle),
                        "estimated_laundered_volume": min_volume,
                        "risk_level": "HIGH" if min_volume > 100000 else "MEDIUM",
                        "rule": "CIRCULAR_TRANSACTION_CYCLE"
                    })
        except Exception:
            pass

        # Generate ExtractedEdge items
        edges: List[ExtractedEdge] = []
        for (src, dst), stats in pair_transfers.items():
            src_id = f"ENT-ACC-{hashlib.md5(src.encode()).hexdigest()[:8]}"
            dst_id = f"ENT-ACC-{hashlib.md5(dst.encode()).hexdigest()[:8]}"
            timestamps = sorted(stats["timestamps"])
            first_seen = timestamps[0]
            last_seen = timestamps[-1]

            prov = SourceProvenance(
                source_id=source_id,
                source_type=SourceTypeEnum.FINANCIAL,
                document_hash=doc_hash,
                timestamp=last_seen
            )

            edge_props = {
                "transaction_count": stats["count"],
                "total_transferred_amount": round(stats["total_amount"], 2),
                "channels": list(stats["channels"]),
                "sample_transaction_ids": stats["tx_ids"][:5]
            }

            edges.append(ExtractedEdge(
                source_entity_id=src_id,
                target_entity_id=dst_id,
                relationship_type=EdgeTypeEnum.TRANSACTED_WITH,
                confidence=0.98,
                weight=round(stats["total_amount"], 2),
                first_seen=first_seen,
                last_seen=last_seen,
                provenance=[prov],
                properties=edge_props
            ))

        result = ExtractionResult(
            source_id=source_id,
            source_type=SourceTypeEnum.FINANCIAL,
            entities=list(entities.values()),
            edges=edges,
            raw_text_summary=f"Processed {len(transactions)} transactions: {len(entities)} accounts, {len(edges)} fund paths.",
            processing_metadata={"circular_cycles_detected": len(circular_cycles), **metadata}
        )

        return result, circular_cycles


financial_service = FinancialProcessingService()

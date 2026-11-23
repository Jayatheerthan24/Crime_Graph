"""
Agent 4: Financial Intelligence Agent Implementation
"""
from typing import Any, Dict, List, Tuple
from src.agents.base_agent import BaseAgent
from src.agents.registry import agent_registry
from src.agents.state import SharedInvestigationState
from src.agents.tools.transaction_tools import process_financial_transactions


class FinancialIntelligenceAgent(BaseAgent):
    """
    Agent responsible for analyzing bank records, UPI transactions,
    detecting circular layering patterns, and building transaction edges.
    """
    def __init__(self):
        super().__init__(
            name="FINANCIAL_INTELLIGENCE_AGENT",
            description="Analyzes financial transactions, detects circular transfers, and maps fund flows.",
            system_prompt="Trace transaction flows and identify circular layering without inferring unproven ownership."
        )

    def _execute(
        self, state: SharedInvestigationState, input_data: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], List[str], float]:
        source_id = input_data.get("source_id", f"FIN-{state.case_id}")
        transactions = input_data.get("transactions", [])
        metadata = input_data.get("metadata", {})

        if not transactions:
            raise ValueError(f"Financial source {source_id} contains empty transactions list.")

        # Invoke financial processing tool
        extraction_result, circular_cycles = process_financial_transactions(
            source_id=source_id, transactions=transactions, metadata=metadata
        )

        # Store in shared investigation state
        state.add_source_extraction(extraction_result)

        evidence_refs = [f"{source_id}:txs_{len(transactions)}"]
        
        output = {
            "source_id": source_id,
            "transactions_analyzed": len(transactions),
            "accounts_identified": len(extraction_result.entities),
            "fund_edges_mapped": len(extraction_result.edges),
            "circular_cycles_detected": len(circular_cycles),
            "cycles": circular_cycles
        }

        return output, evidence_refs, 0.98


# Register singleton instance
financial_agent = FinancialIntelligenceAgent()
agent_registry.register(financial_agent)

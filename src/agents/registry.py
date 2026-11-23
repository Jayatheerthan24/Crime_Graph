"""
Agent Registry Subsystem
"""
from typing import Dict, List, Optional
from src.agents.base_agent import BaseAgent


class AgentRegistry:
    """
    Central repository for registering, discovering, and dispatching specialized agents.
    """
    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}

    def register(self, agent: BaseAgent):
        """Register an agent instance."""
        self._agents[agent.name] = agent

    def get(self, name: str) -> Optional[BaseAgent]:
        """Retrieve an agent by name."""
        return self._agents.get(name)

    def has_agent(self, name: str) -> bool:
        """Check if an agent is registered."""
        return name in self._agents

    def list_agents(self) -> List[str]:
        """List all registered agent names."""
        return list(self._agents.keys())


agent_registry = AgentRegistry()

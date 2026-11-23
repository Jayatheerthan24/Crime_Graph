"""
Health & Diagnostic Routes
"""
from fastapi import APIRouter
from src.agents.registry import agent_registry
from src.core.security import security_manager

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
def health_check():
    """Returns system status, registered agents, and audit log health."""
    audit_valid, audit_err = security_manager.verify_audit_trail_integrity()
    return {
        "status": "HEALTHY",
        "system": "CrimeGraph AI Multi-Agent System",
        "registered_agents": agent_registry.list_agents(),
        "total_registered_agents": len(agent_registry.list_agents()),
        "audit_trail_intact": audit_valid,
        "audit_trail_error": audit_err
    }

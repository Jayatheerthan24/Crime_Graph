"""
Application Configuration
"""
import os
from typing import List
from pydantic import BaseModel, Field

class Settings(BaseModel):
    APP_NAME: str = "CrimeGraph AI"
    APP_VERSION: str = "2.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")
    
    # API Settings
    API_PREFIX: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = int(os.getenv("PORT", 8000))
    CORS_ORIGINS: List[str] = ["*"]
    
    # Security & Encryption
    SECRET_KEY: str = os.getenv("SECRET_KEY", "nexora-crimegraph-ai-sih26189-super-secret-key-32b")
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "bXlzdGVyaW91cy1zZWNyZXQta2V5LTMyeHgtY3JpbWU=") # Base64 32 bytes
    ENABLE_AUDIT_LOG: bool = True
    AUDIT_LOG_FILE: str = os.getenv("AUDIT_LOG_FILE", "logs/audit_trail.jsonl")
    
    # Neo4j Settings
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "crimegraph_secret")
    USE_IN_MEMORY_GRAPH_FALLBACK: bool = True
    
    # Local LLM / Ollama Settings
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.2:latest")
    OLLAMA_TIMEOUT_SECONDS: int = int(os.getenv("OLLAMA_TIMEOUT_SECONDS", 15))
    ALLOW_MOCK_LLM_FALLBACK: bool = True
    
    # Agent Execution Settings
    MAX_PARALLEL_SOURCE_AGENTS: int = 4
    AGENT_TIMEOUT_SECONDS: int = 30
    DEFAULT_CONFIDENCE_THRESHOLD: float = 0.65

settings = Settings()

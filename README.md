# CrimeGraph AI — Multi-Agent Criminal Network Intelligence System

**Problem Statement ID:** SIH26189  
**Organization:** National Crime Records Bureau (NCRB) – Women Safety Division, Ministry of Home Affairs  
**Team:** NEXORA (Team ID: 151)  
**Theme:** Blockchain & Cybersecurity  

---

## 1. System Overview

**CrimeGraph AI** is an investigation-seeded multi-agent criminal network intelligence system. Starting from an active FIR, suspect identifier, phone number, or bank account, the system builds outward across forensic datasets (FIRs, CDRs, Bank Transactions, and Digital Footprints), resolves identities resistant to evasion (SIM churn, hardware sharing), evaluates behavioral deviations using deterministic rules, and generates an auditable, evidence-grounded intelligence dossier for law enforcement investigators.

---

## 2. Multi-Agent Architecture (11 Specialized Agents)

The system is coordinated by a Master Orchestrator Agent delegating tasks to 10 specialized intelligence agents:

| Agent # | Agent Name | Core Responsibility |
|---|---|---|
| **Agent 1** | `MASTER_ORCHESTRATOR_AGENT` | Manages state machine: `PENDING` → `RUNNING` → `VALIDATING` → `GRAPH_PROCESSING` → `ANALYSIS` → `COMPLETED` |
| **Agent 2** | `FIR_INTELLIGENCE_AGENT` | Extracts grounded entities (Persons, Vehicles, Phones, Accounts) with text offsets from FIRs. |
| **Agent 3** | `CDR_INTELLIGENCE_AGENT` | Ingests Call Detail Records, computes communication frequency, burst velocities, and SIM churn alerts. |
| **Agent 4** | `FINANCIAL_INTELLIGENCE_AGENT`| Traces fund flows across accounts, detects high-velocity spikes and circular layering loops ($A \to B \to C \to A$). |
| **Agent 5** | `DIGITAL_FOOTPRINT_AGENT` | Ingests social profiles, online handles, email identifiers, and IP exhibit bindings. |
| **Agent 6** | `ENTITY_RESOLUTION_AGENT` | 4-tier match taxonomy (Exact, Strongly Supported, Probabilistic, Unresolved) using RapidFuzz string metrics. |
| **Agent 7** | `IDENTITY_INTELLIGENCE_AGENT` | Multi-signal correlation: IMEI (40%), Contact Jaccard (25%), Timing Cosine (15%), Geo (10%), SIM Churn (10%). |
| **Agent 8** | `RELATIONSHIP_MAPPING_AGENT` | Transactional, parameterized Cypher graph construction in Neo4j (with in-memory NetworkX fallback). |
| **Agent 9** | `ANOMALY_INVESTIGATION_AGENT` | Deterministic behavioral rules: `CallBurstRule`, `SharedIdentityCrossCaseRule`, `CircularTransactionRule`, `SIMChurnRule`. |
| **Agent 10** | `GRAPH_INTELLIGENCE_AGENT` | Network topology analytics: Degree, Betweenness (structural brokers), Eigenvector, and Louvain community detection. |
| **Agent 11** | `EVIDENCE_REPORT_AGENT` | Provenance grounding audit, direct vs. inferred edge isolation, and final executive dossier generation. |

---

## 3. Directory Structure

```
crimegraph/
├── AGENT_ARCHITECTURE_AUDIT.md     # Phase 1 architectural audit & module blueprint
├── requirements.txt                # System dependencies
├── README.md                       # Documentation & runbook
├── src/
│   ├── config.py                   # Central settings, encryption keys, Neo4j & Ollama configs
│   ├── core/                       # Core system models & security boundaries
│   │   ├── schemas.py              # Pydantic V2 schemas (ExtractedEntity, ExtractedEdge, etc.)
│   │   ├── security.py             # RBAC, AES-256 field encryption, PII masking, hash-chained audit logging
│   │   └── llm.py                  # Local confidential Ollama client with deterministic offline fallback
│   ├── services/                   # Domain processing & analytics engines
│   │   ├── fir_service.py          # FIR parser & entity offset extractor
│   │   ├── cdr_service.py          # CDR parser, burst detection, SIM churn tracking
│   │   ├── financial_service.py    # Transaction parser & circular cycle detection
│   │   ├── digital_service.py      # Social & cyber exhibit normalizer
│   │   ├── resolution_service.py   # RapidFuzz 4-tier entity deduplication
│   │   ├── identity_service.py     # Multi-signal identity correlation engine
│   │   ├── neo4j_service.py        # Parameterized Cypher graph builder & in-memory graph
│   │   ├── anomaly_service.py      # Deterministic scoring engine (CallBurst, CircularTx, etc.)
│   │   ├── analytics_service.py    # Centrality (Betweenness, Degree, Eigen) & Louvain clustering
│   │   └── reporting_service.py    # Provenance validator & dossier compiler
│   ├── agents/                     # Multi-Agent Subsystem
│   │   ├── base_agent.py           # Abstract BaseAgent with timing & error isolation
│   │   ├── state.py                # Thread-safe SharedInvestigationState with checkpoints
│   │   ├── registry.py             # AgentRegistry singleton
│   │   ├── schemas.py              # TaskAssignment, AgentResult, ExecutionPlan
│   │   ├── orchestrator.py         # Agent 1 (Master Orchestrator)
│   │   ├── fir_agent.py            # Agent 2
│   │   ├── cdr_agent.py            # Agent 3
│   │   ├── financial_agent.py      # Agent 4
│   │   ├── digital_footprint_agent.py # Agent 5
│   │   ├── entity_resolution_agent.py # Agent 6
│   │   ├── identity_agent.py       # Agent 7
│   │   ├── relationship_agent.py   # Agent 8
│   │   ├── anomaly_agent.py        # Agent 9
│   │   ├── graph_intelligence_agent.py # Agent 10
│   │   ├── evidence_report_agent.py # Agent 11
│   │   ├── tools/                  # Deterministic tool wrapper layer
│   │   └── prompts/                # Dedicated markdown system prompts for all 11 agents
│   └── api/                        # FastAPI REST API
│       ├── main.py                 # Application entrypoint & static mounting
│       └── routes/
│           ├── health.py           # System status & audit integrity check
│           ├── investigation.py    # Investigation trigger, status polling, report retrieval
│           └── graph.py            # N-hop ego subgraph query
├── static/                         # Investigator Dashboard Frontend
│   ├── index.html                  # Dashboard HTML
│   ├── dashboard.js                # State machine tracker & API polling
│   └── styles.css                  # Modern cyber-intelligence UI styling
└── tests/                          # Pytest Test Suite (Synthetic Datasets)
    ├── conftest.py                 # Synthetic test fixtures
    ├── test_schemas.py             # Schema validation tests
    ├── test_security.py            # RBAC, AES-256, PII masking, hash-chained audit tests
    ├── test_source_agents.py       # Agents 2-5 tests
    ├── test_resolution_identity.py # Agents 6-7 tests
    ├── test_graph_anomaly.py       # Agents 8-10 tests
    ├── test_report_agent.py        # Agent 11 tests
    ├── test_orchestrator.py        # Agent 1 state machine & recovery tests
    └── test_end_to_end.py          # FastAPI end-to-end integration tests
```

---

## 4. Quickstart Guide

### Prerequisites
- Python 3.11+ (Python 3.14 compatible)
- (Optional) Local Ollama instance running `llama3.2` for confidential offline summarization
- (Optional) Neo4j instance for live graph database persistence (the system automatically falls back to an ultra-fast in-memory NetworkX graph when Neo4j is offline)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Multi-Agent System Backend & Dashboard
```bash
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```
Access the Investigator Dashboard at: **`http://localhost:8000`**  
Access the OpenAPI documentation at: **`http://localhost:8000/docs`**

### 3. Run the Test Suite
```bash
python -m pytest tests/ -v
```

---

## 5. Security & Privacy Safeguards

1. **Investigation-Seeded Access:** No autonomous crawling outside an explicitly authorized `case_id`.
2. **Confidential Local LLM:** Local Ollama inference only. Zero transmission of tokens to external cloud APIs.
3. **Automated PII Masking:** Direct personal identifiers (phone numbers, Aadhaar, PAN) are masked before prompt template population.
4. **Tamper-Evident Audit Trail:** Every agent invocation and tool execution is cryptographically hash-chained (`SHA-256`).
5. **No Autonomous Criminal Accusations:** Anomaly scores and graph rankings are strictly defined as *investigative leads*, never legal proof of guilt. All conclusions maintain human-in-the-loop accountability.

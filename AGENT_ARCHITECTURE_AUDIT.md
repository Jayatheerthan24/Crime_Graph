# CRIMEGRAPH AI — AGENT ARCHITECTURE AUDIT & MULTI-AGENT SPECIFICATION

**Project:** CrimeGraph AI  
**Problem Statement ID:** SIH26189  
**Organization:** NCRB – Women Safety Division, Ministry of Home Affairs  
**Team:** NEXORA (Team ID: 151)  
**Theme:** Blockchain & Cybersecurity  
**Date of Audit:** November 23, 2026  
**Auditor / Architect:** Senior AI Architect, Multi-Agent Systems Engineer

---

## 1. REPOSITORY AUDIT & ENVIRONMENT ASSESSMENT

### 1.1 Workspace State
- **Workspace Location:** `D:\crimegraph`
- **Initial Workspace Inspection:** The directory `D:\crimegraph` was initialized as a fresh workspace. No pre-existing source files, Git commit history, or legacy codebase files were present in `D:\crimegraph`.
- **System-Wide Discovery:**
  - Located project pitch/specification presentation at `C:\Users\hp\Downloads\CrimeGraph-AI.pptx` (Team: NEXORA / POWER PULSE; Problem Statement: SIH26189; NCRB – Women Safety Division).
  - Located unrelated legacy dataset/demo projects (`sentinel-ka` / `new senti` in `D:\new senti` which focuses on Karnataka crime tabular risk-scoring with SQLite/vanilla JS).
- **Runtime Environment:**
  - **OS:** Windows (x64)
  - **Python:** 3.14.3 (64-bit) available via `py -0` / `python`
  - **Package Manager:** `pip` (Python 3.14)
  - **Hardware & Local AI Services:** Dedicated local Ollama support capability, Git 2.4x.

### 1.2 System Architecture Baseline
Based on the master specification and the foundational blueprint from `CrimeGraph-AI.pptx`, CrimeGraph AI is structured around an investigation-seeded architecture that ingests multi-source forensic evidence, builds a dynamic Neo4j knowledge graph, computes behavioral anomalies against deterministic baselines, runs graph centrality and community detection algorithms, and produces an explainable, auditable investigation intelligence report.

Below is the formal architecture mapping designed to govern the modular foundation and the 11 specialized agents.

---

## 2. MODULAR FOUNDATION TO AGENT MAPPING

To fulfill the mandate that **"agents call Python processing functions as tools and do not independently modify the database without going through approved service interfaces"**, the platform is organized into clean service interfaces and corresponding agent tool wrappers.

```
                  ┌─────────────────────────────────────────────────────────┐
                  │              FastAPI Backend & API Gateway              │
                  └───────────────────────────┬─────────────────────────────┘
                                              │ Investigation Request
                                              ▼
                  ┌─────────────────────────────────────────────────────────┐
                  │          AGENT 1: MASTER ORCHESTRATOR AGENT             │
                  │   (State Machine: PENDING -> RUNNING -> VALIDATING ->   │
                  │    GRAPH_PROCESSING -> ANALYSIS -> COMPLETED)           │
                  └──────┬────────────────────┬────────────────────┬────────┘
                         │                    │                    │
          ┌──────────────┴──────────────┐     │     ┌──────────────┴──────────────┐
          │  Parallel Source Extraction │     │     │  Consolidation & Resolution │
          ▼                             ▼     │     ▼                             ▼
   ┌──────────────┐             ┌──────────┐  │  ┌──────────────┐          ┌─────────────┐
   │   AGENT 2    │             │ AGENT 3  │  │  │   AGENT 6    │          │   AGENT 7   │
   │FIR Intel     │             │CDR Intel │  │  │Entity Valid. │─────────▶│Identity     │
   │Agent         │             │Agent     │  │  │& Resolution  │          │Intel Agent  │
   └──────┬───────┘             └────┬─────┘  │  └──────┬───────┘          └──────┬──────┘
          │                          │        │         │                         │
          │  ┌───────────────────────┤        │         │                         │
          ▼  ▼                       ▼        │         ▼                         │
   ┌──────────────┐             ┌──────────┐  │  ┌────────────────────────────────┘
   │   AGENT 4    │             │ AGENT 5  │  │  │
   │Financial     │             │Digital   │  │  │ Validated Entities, Candidates & Signals
   │Intel Agent   │             │Footprint │  │  │
   └──────┬───────┘             └────┬─────┘  │  │
          └──────────────┬───────────┘        │  │
                         ▼                    │  │
                Extracted Evidences           │  ▼
                         └────────────────────┼──▶┌───────────────────────────────┐
                                              │   │           AGENT 8             │
                                              │   │  Relationship Mapping Agent   │
                                              │   │    (Neo4j Idempotent Graph)   │
                                              │   └───────────────┬───────────────┘
                                              │                   │ Graph Built
                                              │                   ▼
                                              ├──▶┌───────────────────────────────┐
                                              │   │           AGENT 9             │
                                              │   │ Anomaly Investigation Agent   │
                                              │   │  (Deterministic Rule Engine)  │
                                              │   └───────────────┬───────────────┘
                                              │                   │ Anomalies
                                              │                   ▼
                                              ├──▶┌───────────────────────────────┐
                                              │   │           AGENT 10            │
                                              │   │   Graph Intelligence Agent    │
                                              │   │ (Louvain, Centrality, Brokers)│
                                              │   └───────────────┬───────────────┘
                                              │                   │ Graph Metrics
                                              │                   ▼
                                              └──▶┌───────────────────────────────┐
                                                  │           AGENT 11            │
                                                  │ Evidence Validation & Report  │
                                                  └───────────────┬───────────────┘
                                                                  │
                                                                  ▼
                                                      Final Investigation Dossier
                                                        & Investigator Dashboard
```

---

## 3. DETAILED AGENT-TO-MODULE SPECIFICATION

### AGENT 1: Master Orchestrator Agent
- **Role:** High-level coordinator, execution plan generator, parallel task dispatcher, workflow state machine manager.
- **State Machine States:**
  - `PENDING` → Request received and authenticated.
  - `RUNNING` → Parallel source extraction dispatched (FIR, CDR, Financial, Digital Footprint).
  - `VALIDATING` → Entity normalization, deduplication, and identity resolution.
  - `GRAPH_PROCESSING` → Incremental Neo4j graph construction.
  - `ANALYSIS` → Deterministic anomaly scoring and GDS graph intelligence analytics.
  - `COMPLETED` → Evidence validation passed and final report delivered.
  - *Exception states:* `PARTIALLY_COMPLETED` (if non-critical sources fail), `REQUIRES_REVIEW` (if ambiguous entity links exist), `FAILED` (if fatal error or mandatory step fails).
- **Core Modules & Service Tools Reused:**
  - `src.core.state`: Manages persistent investigation state and step checkpoints.
  - `src.services.orchestration_service`: Dispatches async tasks, enforces timeout/retries, logs execution tracking metadata.
- **Safety Boundary:** Never allows duplicate ingestion; checks idempotency tokens before task dispatch.

---

### AGENT 2: FIR Intelligence Agent
- **Role:** Ingests FIR documents (PDF, image, text), performs OCR when necessary, detects language (English, Hindi, regional), extracts named entities with character offsets, identifies crime events and supported roles (Complainant, Accused, Witness, Suspect).
- **Core Modules & Service Tools Reused:**
  - `src.nlp.ocr_engine`: EasyOCR wrapper with pre-processing (grayscale, thresholding) for scanned police documents.
  - `src.nlp.ner_extractor`: Hybrid extraction using spaCy, regex patterns (Indian phone numbers, PAN, Aadhaar, vehicle registration [e.g. `DL01AB1234`], Indian IFSC codes, bank account numbers), and Transformer/IndicNER for regional script handling.
  - `src.nlp.language_detector`: Fast, deterministic language identifier.
  - `src.tools.fir_tools`: Clean interface converting raw document payload into `ExtractionResult` containing `ExtractedEntity` and `ExtractedEdge`.
- **Safety Boundary:** Strict guardrail against LLM hallucinations. Entities must be grounded in verbatim text offsets or verified OCR spans.

---

### AGENT 3: CDR Intelligence Agent
- **Role:** Ingests Call Detail Records (CSV/XLSX/JSON), resolves calling/receiving parties, extracts timestamps, duration, tower cell IDs, IMEI, and IMSI. Calculates calling velocity, day/night distributions, communication bursts, and contact overlap.
- **Core Modules & Service Tools Reused:**
  - `src.ingestion.cdr_parser`: Streaming/batch parser for telecom provider records.
  - `src.analytics.cdr_metrics`: Calculates call frequency, mutual contact Jaccard index, burst duration, call-timing cosine similarity.
  - `src.tools.cdr_tools`: Generates `COMMUNICATED_WITH` relationship candidates, SIM-churn indicator events, and sends telemetry to the Identity and Anomaly engines.
- **Safety Boundary:** A telecom interaction candidate is an evidentiary link, never proof of criminality.

---

### AGENT 4: Financial Intelligence Agent
- **Role:** Processes bank statements, UPI transaction dumps, and wire transfer logs. Extracts source/destination accounts, IFSC, amounts, dates, reference IDs. Detects high-velocity transfers and circular layering patterns.
- **Core Modules & Service Tools Reused:**
  - `src.ingestion.financial_parser`: Transaction normalizer across IMPS, NEFT, RTGS, UPI, and cash deposits.
  - `src.analytics.financial_cycles`: Graph/cycle detection identifying triangular transfers (A → B → C → A) and layering within configurable time windows.
  - `src.tools.transaction_tools`: Emits `TRANSACTED_WITH` edge candidates with aggregated volume, count, and transaction ID provenance.
- **Safety Boundary:** Does not infer beneficial ownership without explicit corporate or account registration evidence.

---

### AGENT 5: Digital Footprint Intelligence Agent
- **Role:** Extracts authorized social profiles, messaging identifiers, email addresses, usernames, and IP login timestamps from cybercrime exhibits.
- **Core Modules & Service Tools Reused:**
  - `src.ingestion.digital_parser`: Normalizes digital handles, email domains, IP subnets, and platform IDs.
  - `src.tools.social_tools`: Identifies repeated identifiers across exhibits and emits `ASSOCIATED_WITH` digital candidate edges.
- **Safety Boundary:** Never merges accounts solely on matching display names; requires unique handle, email, or verified device binding.

---

### AGENT 6: Entity Validation and Resolution Agent
- **Role:** Consolidates extractions across all sources (FIR, CDR, Financial, Digital Footprint). Normalizes phone numbers (+91 E.164 standard), bank accounts, and names. Performs fuzzy string matching with RapidFuzz.
- **Match Tiers:**
  - **Tier 1 (Exact Identifier Match):** Same normalized phone, PAN, Aadhaar, account, or IMEI → deterministic merge.
  - **Tier 2 (Strongly Supported Match):** Exact alias + co-occurrence in same case context with high token sort ratio (>95%).
  - **Tier 3 (Probabilistic Match):** Name similarity 80–94% or shared non-unique attributes → preserved as separate nodes linked by `POTENTIAL_DUPLICATE` edge for investigator review.
  - **Tier 4 (Unresolved / Distinct):** Similarity <80% → distinct entities.
- **Core Modules & Service Tools Reused:**
  - `src.resolution.normalizer`: Cleans phonetics, honorifics, titles, and whitespace.
  - `src.resolution.fuzzy_matcher`: RapidFuzz token sorting and weighted Levenshtein distance.
  - `src.tools.entity_tools`: Emits resolved `ExtractedEntity` master list and flags ambiguous pairs.

---

### AGENT 7: Identity Intelligence Agent
- **Role:** Implements evasion-resistant identity linkage across distinct phone numbers and digital personae using multi-signal correlation.
- **Signals Evaluated:**
  1. **IMEI / Hardware Sharing:** High weight ($w = 0.40$).
  2. **Common Contact Overlap (Jaccard Index):** Contact list overlap ($w = 0.25$).
  3. **Temporal Calling Pattern Cosine Similarity:** Hourly calling profile ($w = 0.15$).
  4. **Geographic / Cell Tower Co-location:** Shared cell towers during incident windows ($w = 0.10$).
  5. **SIM Churn Detection:** Rapid succession of SIM activations on single IMEI ($w = 0.10$).
- **Core Modules & Service Tools Reused:**
  - `src.identity.scoring_engine`: Mathematical formulation producing confidence score $S \in [0.0, 1.0]$.
  - `src.identity.blocking`: Candidate pairing via blocking indices to prevent $O(N^2)$ cross-comparison.
  - `src.tools.identity_tools`: Emits structured `IdentityResolutionResult` detailing supporting, missing, and contradictory evidence.
- **Safety Boundary:** Never makes binary identity claims ("Person A IS Person B"). Emits probabilistic `ASSOCIATED_WITH` relations with transparent signal breakdowns.

---

### AGENT 8: Relationship Mapping Agent
- **Role:** Translates validated entities and edges into parameterized Cypher transactions in Neo4j. Maintains incremental graph updates, relationship property aggregations (weight, count, amount), `first_seen`, `last_seen`, and investigation scopes.
- **Core Modules & Service Tools Reused:**
  - `src.database.neo4j_client`: Connection pooling, transaction management, and session safety.
  - `src.database.cypher_repository`: Parameterized upsert queries avoiding Cypher injection.
  - `src.tools.graph_tools`: Upserts nodes (`Person`, `PhoneNumber`, `BankAccount`, `Vehicle`, `Location`, `Case`) and edges (`COMMUNICATED_WITH`, `TRANSACTED_WITH`, `ASSOCIATED_WITH`, `MENTIONED_IN`).
- **Safety Boundary:** Cypher strings are strictly parameterized; zero string interpolation of untrusted input.

---

### AGENT 9: Anomaly Investigation Agent
- **Role:** Coordinates the deterministic anomaly and expectedness scoring engine. Identifies suspicious deviations from behavioral baselines.
- **Deterministic Rules Evaluated:**
  1. `CallBurstRule`: Detects sudden 5x+ communication frequency spikes within 24h of an incident date.
  2. `SharedIdentityCrossCaseRule`: Identifies same IMEI, phone, or account appearing across distinct active cases without prior declared association.
  3. `CircularTransactionRule`: Identifies closed funds flow paths ($A \to B \to C \to A$) within a 72-hour window.
  4. `SuddenUncontextualizedConnectionRule`: High-frequency communication between suspects who have zero shared community history prior to the crime window.
  5. `SIMChurnAnomalyRule`: 3+ phone numbers activated on the same hardware within 30 days.
- **Core Modules & Service Tools Reused:**
  - `src.anomaly.rule_engine`: Deterministic rule orchestrator.
  - `src.anomaly.rules.*`: Concrete, isolated rule implementations.
  - `src.tools.anomaly_tools`: Produces explainable anomaly dossiers with mathematical evidence, contributing weights, and human-readable investigator summaries.
- **Safety Boundary:** LLM is used ONLY to summarize the explanation for investigators. The numerical score is strictly deterministic and unalterable by the LLM.

---

### AGENT 10: Graph Intelligence Agent
- **Role:** Executes graph data science algorithms to uncover network architecture, structural brokers, and hidden hubs.
- **Algorithms:**
  - **Degree Centrality:** Direct connection volume.
  - **Betweenness Centrality:** Information flow bottlenecks / structural brokers bridging separate sub-gangs.
  - **Eigenvector Centrality:** Connections to high-value network players.
  - **Louvain Community Detection:** Partitions network into criminal cells or operational clusters.
- **Core Modules & Service Tools Reused:**
  - `src.analytics.gds_service`: Interfaces with Neo4j GDS library or local NetworkX fallback when GDS is unavailable.
  - `src.tools.analytics_tools`: Computes composite key-player scores combining graph centrality with anomaly weights.
- **Safety Boundary:** Centrality is explicitly labeled as structural importance within the collected graph, NOT guilt.

---

### AGENT 11: Evidence Validation & Report Agent
- **Role:** Quality assurance gatekeeper and final intelligence report generator. Verifies provenance for every node and edge, isolates inferred links from direct evidence, highlights contradictory evidence, and formats the executive intelligence dossier for the dashboard.
- **Core Modules & Service Tools Reused:**
  - `src.reporting.provenance_validator`: Verifies cryptographic hashes, document references, and source offsets.
  - `src.reporting.report_generator`: Synthesizes final JSON and Markdown intelligence summaries.
  - `src.tools.evidence_report_tools`: Emits structured investigation report consumed by the frontend dashboard.
- **Safety Boundary:** Strictly prevents ungrounded investigative conclusions. Omits any claim lacking documented evidentiary backing.

---

## 4. SHARED DATA CONTRACTS (PYDANTIC V2)

All agents communicate exclusively through immutable, validated schemas:

```python
class SourceProvenance(BaseModel):
    source_id: str
    source_type: Literal["FIR", "CDR", "BANK_STATEMENT", "DIGITAL_FOOTPRINT"]
    document_hash: str
    page_number: Optional[int] = None
    character_offsets: Optional[Tuple[int, int]] = None
    timestamp: datetime

class ExtractedEntity(BaseModel):
    entity_id: str
    entity_type: Literal["PERSON", "PHONE", "BANK_ACCOUNT", "VEHICLE", "LOCATION", "ORGANIZATION"]
    primary_value: str
    normalized_value: str
    aliases: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    provenance: List[SourceProvenance] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ExtractedEdge(BaseModel):
    source_entity_id: str
    target_entity_id: str
    relationship_type: Literal["COMMUNICATED_WITH", "TRANSACTED_WITH", "ASSOCIATED_WITH", "MENTIONED_IN", "LOCATED_AT"]
    confidence: float = Field(ge=0.0, le=1.0)
    weight: float = 1.0
    first_seen: datetime
    last_seen: datetime
    provenance: List[SourceProvenance] = Field(default_factory=list)
    properties: Dict[str, Any] = Field(default_factory=dict)

class AgentResult(BaseModel):
    agent_name: str
    execution_id: str
    case_id: str
    status: Literal["SUCCESS", "PARTIAL", "FAILED"]
    input_reference: str
    output: Dict[str, Any]
    evidence_references: List[str]
    confidence: float
    errors: List[str] = Field(default_factory=list)
    processing_time_ms: float
```

---

## 5. SECURITY, PRIVACY & COMPLIANCE BOUNDARIES

1. **Investigation-Seeded Access Control:** No system component can query or crawl outside the scope of an explicitly authorized, active `case_id`.
2. **Local LLM Isolation:** Ollama local inference running strictly offline. Zero transmission of tokens to external cloud APIs.
3. **PII Masking Filter:** Direct identifiers (names, Aadhaar digits, phone numbers) are masked using pseudo-tokens before any context is passed to local LLM prompt templates.
4. **Tamper-Evident Audit Trail:** Every agent invocation, tool execution, and state change is cryptographically hash-chained (`SHA-256`) and recorded in the audit log.
5. **Human-in-the-Loop:** High-impact identity merges (probabilistic tier) and criminal role assignments require explicit investigator confirmation in the dashboard.

---

## 6. PHASE-BY-PHASE IMPLEMENTATION PLAN

- **Phase 1: Repository Audit & Architecture Blueprint** (Current Stage)
  - Perform system discovery, document modular architecture, author `AGENT_ARCHITECTURE_AUDIT.md`.
- **Phase 2: Agent Foundation & Shared Data Contracts**
  - Implement Pydantic schemas, `BaseAgent`, `AgentRegistry`, `AgentState`, execution tracking, and `MasterOrchestratorAgent`.
- **Phase 3: Source Intelligence Agents (Agents 2–5)**
  - Implement FIR, CDR, Financial, and Digital Footprint agents with deterministic tool integrations.
- **Phase 4: Entity Validation & Identity Agents (Agents 6–7)**
  - Implement RapidFuzz fuzzy deduplication, canonical entity resolution, multi-signal identity scoring, and SIM churn tracking.
- **Phase 5: Graph, Anomaly & Intelligence Agents (Agents 8–10)**
  - Implement Neo4j relationship mapper, deterministic rule engine (`CallBurstRule`, `CircularTransactionRule`, etc.), and GDS graph analytics.
- **Phase 6: Evidence Validation & Report Agent (Agent 11)**
  - Implement provenance checker, fact grounding verification, and executive dossier generator.
- **Phase 7: FastAPI Backend & Dashboard Integration**
  - Wire investigation endpoints, background worker execution, state streaming, and dashboard API models.
- **Phase 8: Comprehensive Testing & Verification**
  - Unit tests for all 11 agents, schema tests, mock Neo4j & Ollama tests, end-to-end multi-agent integration test suite.

---
*Signed and Approved for Architecture Baseline.*  
**Lead AI Architect & Systems Engineer — Team NEXORA**

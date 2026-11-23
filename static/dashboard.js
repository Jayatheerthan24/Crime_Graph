const AGENT_LIST = [
    "MASTER_ORCHESTRATOR_AGENT",
    "FIR_INTELLIGENCE_AGENT",
    "CDR_INTELLIGENCE_AGENT",
    "FINANCIAL_INTELLIGENCE_AGENT",
    "DIGITAL_FOOTPRINT_AGENT",
    "ENTITY_RESOLUTION_AGENT",
    "IDENTITY_INTELLIGENCE_AGENT",
    "RELATIONSHIP_MAPPING_AGENT",
    "ANOMALY_INVESTIGATION_AGENT",
    "GRAPH_INTELLIGENCE_AGENT",
    "EVIDENCE_REPORT_AGENT"
];

let activeInvestigationId = null;
let pollTimer = null;

// Initialize Dashboard UI
document.addEventListener("DOMContentLoaded", () => {
    renderAgentsGrid({});
    document.getElementById("trigger-btn").addEventListener("click", triggerSampleInvestigation);
});

function renderAgentsGrid(agentSummary) {
    const grid = document.getElementById("agents-grid");
    grid.innerHTML = "";

    AGENT_LIST.forEach(agentName => {
        const info = agentSummary[agentName] || { status: "PENDING", time_ms: 0 };
        const card = document.createElement("div");
        card.className = "agent-card";
        card.innerHTML = `
            <div>
                <div class="agent-name">${agentName.replace(/_/g, " ")}</div>
                <span class="agent-status ${info.status.toLowerCase()}">${info.status}</span>
            </div>
            <div class="agent-time">${info.time_ms > 0 ? info.time_ms + " ms" : "—"}</div>
        `;
        grid.appendChild(card);
    });
}

function updateStateMachine(currentStatus) {
    const steps = document.querySelectorAll("#state-steps .step");
    const statusMap = {
        "PENDING": 0,
        "RUNNING": 1,
        "VALIDATING": 2,
        "GRAPH_PROCESSING": 3,
        "ANALYSIS": 4,
        "COMPLETED": 5,
        "PARTIALLY_COMPLETED": 5,
        "REQUIRES_REVIEW": 5,
        "FAILED": -1
    };

    const activeIdx = statusMap[currentStatus] ?? 0;

    steps.forEach((step, idx) => {
        step.classList.remove("active", "completed");
        if (idx < activeIdx) {
            step.classList.add("completed");
        } else if (idx === activeIdx) {
            step.classList.add("active");
        }
    });

    const statusTag = document.getElementById("lbl-state-status");
    statusTag.textContent = currentStatus;
    if (currentStatus === "COMPLETED") {
        statusTag.style.background = "#065f46";
    } else if (currentStatus === "REQUIRES_REVIEW") {
        statusTag.style.background = "#92400e";
    } else if (currentStatus === "FAILED") {
        statusTag.style.background = "#7f1d1d";
    }
}

async function triggerSampleInvestigation() {
    const btn = document.getElementById("trigger-btn");
    btn.disabled = true;
    btn.textContent = "Orchestrating Agents...";

    const samplePayload = {
        case_id: "CASE-2026-DEL-0418",
        investigator_id: "INV-OFFICER-74",
        investigator_role: "INVESTIGATOR",
        priority: "HIGH",
        source_documents: [
            {
                source_type: "FIR",
                source_id: "FIR-DEL-418-2026",
                content: "FIR No 418/2026 PS Connaught Place. Complainant: Sunita Verma. Accused: Vikram Malhotra alias Vicky operating black SUV plate DL01AB1234, contacting victim via mobile +919811122233. Accused received funds into Bank A/C No 1002345678 IFSC HDFC0001234."
            },
            {
                source_type: "CDR",
                source_id: "CDR-TELCO-418",
                records: [
                    {"caller": "+919811122233", "receiver": "+919876543210", "duration_seconds": 180, "timestamp": "2026-11-20T23:15:00", "imei": "358921098471201"},
                    {"caller": "+919811122233", "receiver": "+919876543210", "duration_seconds": 210, "timestamp": "2026-11-20T23:25:00", "imei": "358921098471201"},
                    {"caller": "+919811122233", "receiver": "+919876543210", "duration_seconds": 150, "timestamp": "2026-11-20T23:45:00", "imei": "358921098471201"},
                    {"caller": "+919811122233", "receiver": "+919876543210", "duration_seconds": 320, "timestamp": "2026-11-21T00:10:00", "imei": "358921098471201"},
                    {"caller": "+919811122233", "receiver": "+919876543210", "duration_seconds": 190, "timestamp": "2026-11-21T00:30:00", "imei": "358921098471201"},
                    {"caller": "+919899988877", "receiver": "+919876543210", "duration_seconds": 90, "timestamp": "2026-11-21T02:00:00", "imei": "358921098471201"}
                ]
            },
            {
                source_type: "FINANCIAL",
                source_id: "BANK-LEDGER-418",
                transactions: [
                    {"source_account": "1002345678", "target_account": "2003456789", "amount": 150000.0, "channel": "IMPS", "transaction_id": "TXN90123"},
                    {"source_account": "2003456789", "target_account": "3004567890", "amount": 145000.0, "channel": "RTGS", "transaction_id": "TXN90124"},
                    {"source_account": "3004567890", "target_account": "1002345678", "amount": 140000.0, "channel": "NEFT", "transaction_id": "TXN90125"}
                ]
            },
            {
                source_type: "DIGITAL",
                source_id: "CYBER-EXHIBIT-418",
                records: [
                    {"platform": "TELEGRAM", "handle": "vicky_syndicate", "phone": "+919811122233", "email": "vicky.ops@proton.me"}
                ]
            }
        ]
    };

    try {
        const response = await fetch("/api/v1/investigations/trigger", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(samplePayload)
        });

        const data = await response.json();
        activeInvestigationId = data.investigation_id;
        document.getElementById("lbl-inv-id").textContent = activeInvestigationId;

        if (pollTimer) clearInterval(pollTimer);
        pollTimer = setInterval(pollInvestigationStatus, 1000);
    } catch (e) {
        console.error("Trigger error:", e);
        btn.disabled = false;
        btn.textContent = "Run Sample Investigation";
    }
}

async function pollInvestigationStatus() {
    if (!activeInvestigationId) return;

    try {
        const res = await fetch(`/api/v1/investigations/${activeInvestigationId}/status`);
        if (!res.ok) return;

        const state = await res.json();
        updateStateMachine(state.status);
        renderAgentsGrid(state.agent_execution_summary || {});

        // Fetch and display anomalies
        fetchAnomalies(state.case_id);
        // Fetch and display identities
        fetchIdentities(state.case_id);

        if (["COMPLETED", "PARTIALLY_COMPLETED", "REQUIRES_REVIEW", "FAILED"].includes(state.status)) {
            clearInterval(pollTimer);
            document.getElementById("trigger-btn").disabled = false;
            document.getElementById("trigger-btn").textContent = "Run Sample Investigation";
            fetchDossier(activeInvestigationId);
        }
    } catch (e) {
        console.error("Poll error:", e);
    }
}

async function fetchAnomalies(caseId) {
    try {
        const res = await fetch(`/api/v1/investigations/${caseId}/anomalies`);
        if (!res.ok) return;
        const data = await res.json();
        const container = document.getElementById("anomalies-feed");
        document.getElementById("badge-anomalies-count").textContent = data.anomalies_count;

        if (data.anomalies.length === 0) {
            container.innerHTML = `<p class="empty-state">No anomalies flagged.</p>`;
            return;
        }

        container.innerHTML = data.anomalies.map(a => `
            <div class="feed-item ${a.severity === 'CRITICAL' ? 'critical' : 'high'}">
                <div class="feed-item-title">${a.rule_name} (Score: ${a.anomaly_score})</div>
                <div>${a.rationale}</div>
                <div class="feed-item-meta">Severity: ${a.severity} · Source: ${a.source_entity_id || a.imei}</div>
            </div>
        `).join("");
    } catch (e) {}
}

async function fetchIdentities(caseId) {
    try {
        const res = await fetch(`/api/v1/investigations/${caseId}/identities`);
        if (!res.ok) return;
        const data = await res.json();
        const container = document.getElementById("identities-feed");
        document.getElementById("badge-identities-count").textContent = data.identity_links_count;

        if (data.identity_links.length === 0) {
            container.innerHTML = `<p class="empty-state">No identity links identified.</p>`;
            return;
        }

        container.innerHTML = data.identity_links.map(l => `
            <div class="feed-item">
                <div class="feed-item-title">${l.entity_a_phone} ⇄ ${l.entity_b_phone}</div>
                <div>Confidence: <strong>${Math.round(l.overall_confidence * 100)}%</strong> (${l.resolution_status})</div>
                <div class="feed-item-meta">Supporting: ${l.supporting_evidence.join("; ")}</div>
            </div>
        `).join("");
    } catch (e) {}
}

async function fetchDossier(invId) {
    try {
        const res = await fetch(`/api/v1/investigations/${invId}/report`);
        if (!res.ok) return;
        const dossier = await res.json();
        document.getElementById("dossier-viewer").textContent = JSON.stringify(dossier, null, 2);

        // Populate Key Players from report
        const kp = dossier.graph_intelligence_highlights?.top_ranked_players || [];
        const container = document.getElementById("key-players-feed");
        document.getElementById("badge-players-count").textContent = kp.length;
        if (kp.length > 0) {
            container.innerHTML = kp.map(p => `
                <div class="feed-item">
                    <div class="feed-item-title">${p.name} (${p.entity_type})</div>
                    <div>Composite Rank Score: <strong>${p.composite_rank_score}</strong> (${p.investigative_priority})</div>
                    <div class="feed-item-meta">${p.structural_rationale}</div>
                </div>
            `).join("");
        }
    } catch (e) {}
}

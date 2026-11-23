"""
Synthetic Test Fixtures for CrimeGraph AI
Strictly synthetic data generated for testing. No real PII or live cases.
"""
import pytest
from datetime import datetime
from src.core.schemas import InvestigationRequest
from src.agents.state import SharedInvestigationState


@pytest.fixture
def sample_case_id():
    return "TEST-CASE-2026-SYNTHETIC-001"


@pytest.fixture
def sample_investigation_state(sample_case_id):
    return SharedInvestigationState(case_id=sample_case_id)


@pytest.fixture
def synthetic_fir_text():
    return (
        "FIR No 99/2026 PS Cyber Crime. "
        "Complainant: Priya Sharma. "
        "Accused: Rajesh Kumar alias Raju operating vehicle DL04XY9999, "
        "contacting victim via mobile phone +919810011222. "
        "Transferred sum of INR 50,000 into Bank Account No 9988776655 IFSC SBIN0004321."
    )


@pytest.fixture
def synthetic_cdr_records():
    return [
        {
            "caller": "+919810011222",
            "receiver": "+919820033444",
            "duration_seconds": 150,
            "timestamp": "2026-11-21T23:10:00",
            "imei": "864209048123456"
        },
        {
            "caller": "+919810011222",
            "receiver": "+919820033444",
            "duration_seconds": 240,
            "timestamp": "2026-11-21T23:25:00",
            "imei": "864209048123456"
        },
        {
            "caller": "+919810011222",
            "receiver": "+919820033444",
            "duration_seconds": 180,
            "timestamp": "2026-11-21T23:45:00",
            "imei": "864209048123456"
        },
        {
            "caller": "+919810011222",
            "receiver": "+919820033444",
            "duration_seconds": 300,
            "timestamp": "2026-11-22T00:10:00",
            "imei": "864209048123456"
        },
        {
            "caller": "+919810011222",
            "receiver": "+919820033444",
            "duration_seconds": 210,
            "timestamp": "2026-11-22T00:30:00",
            "imei": "864209048123456"
        },
        # SIM churn signal: Same IMEI used by another number
        {
            "caller": "+919830055666",
            "receiver": "+919820033444",
            "duration_seconds": 60,
            "timestamp": "2026-11-22T01:00:00",
            "imei": "864209048123456"
        }
    ]


@pytest.fixture
def synthetic_financial_transactions():
    return [
        {
            "transaction_id": "TXN-SYNTH-01",
            "source_account": "ACC111",
            "target_account": "ACC222",
            "amount": 100000.0,
            "channel": "IMPS",
            "timestamp": "2026-11-21T10:00:00"
        },
        {
            "transaction_id": "TXN-SYNTH-02",
            "source_account": "ACC222",
            "target_account": "ACC333",
            "amount": 95000.0,
            "channel": "RTGS",
            "timestamp": "2026-11-21T11:00:00"
        },
        {
            "transaction_id": "TXN-SYNTH-03",
            "source_account": "ACC333",
            "target_account": "ACC111",
            "amount": 90000.0,
            "channel": "NEFT",
            "timestamp": "2026-11-21T12:00:00"
        }
    ]


@pytest.fixture
def synthetic_digital_records():
    return [
        {
            "platform": "TELEGRAM",
            "handle": "raju_ops",
            "phone": "+919810011222",
            "email": "raju.ops@testmail.com"
        }
    ]


@pytest.fixture
def full_synthetic_investigation_request(
    sample_case_id,
    synthetic_fir_text,
    synthetic_cdr_records,
    synthetic_financial_transactions,
    synthetic_digital_records
):
    return InvestigationRequest(
        case_id=sample_case_id,
        investigator_id="INV-TEST-OFFICER-01",
        investigator_role="INVESTIGATOR",
        priority="NORMAL",
        source_documents=[
            {
                "source_type": "FIR",
                "source_id": "SRC-FIR-01",
                "content": synthetic_fir_text
            },
            {
                "source_type": "CDR",
                "source_id": "SRC-CDR-01",
                "records": synthetic_cdr_records
            },
            {
                "source_type": "FINANCIAL",
                "source_id": "SRC-FIN-01",
                "transactions": synthetic_financial_transactions
            },
            {
                "source_type": "DIGITAL",
                "source_id": "SRC-DIG-01",
                "records": synthetic_digital_records
            }
        ]
    )

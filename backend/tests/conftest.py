"""
Pytest Fixtures and Mock Environment Configuration for AI Controller Tests.
"""
import pytest
import os
import sys

# Ensure ai-controller is in Python sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Configure test environment variables
os.environ["ENVIRONMENT"] = "test"
os.environ["FIREBASE_PROJECT_ID"] = "yourmemo-9dec5"
os.environ["CHROMA_PERSIST_DIRECTORY"] = "/tmp/test_chroma_db"
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY"] = "False"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from config import settings
from firebase.firebase_service import firebase_service
from schemas.state import AgentState


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Setups clean environment for each test."""
    monkeypatch.setattr(settings, "ENVIRONMENT", "test")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", None)


@pytest.fixture
def mock_user_a():
    return {
        "uid": "user_alpha_123",
        "email": "user_alpha_123@example.com",
        "name": "Alpha User"
    }


@pytest.fixture
def mock_user_b():
    return {
        "uid": "user_beta_456",
        "email": "user_beta_456@example.com",
        "name": "Beta User"
    }


@pytest.fixture
def seeded_firebase_mock(monkeypatch):
    """Mocks Firestore data to test user isolation and financial tools."""
    storage = {
        "user_alpha_123": {
            "profile": {
                "uid": "user_alpha_123",
                "email": "alpha@example.com",
                "displayName": "Alpha User",
                "employer": "Tech Corp Global",
                "salaries": {
                    "2026-9": {"amount": 75000, "employer": "Tech Corp Global", "payDay": 1},
                    "2026-10": {"amount": 80000, "employer": "Tech Corp Global", "payDay": 1}
                },
                "budgets": {
                    "2026-9": 45000,
                    "2026-10": 50000
                }
            },
            "transactions": [
                {
                    "id": "tx_alpha_1",
                    "amount": 75000,
                    "category": "Salary",
                    "description": "Monthly In-Hand Salary Credit",
                    "date": "2026-10-01",
                    "type": "income",
                    "splitWith": []
                },
                {
                    "id": "tx_alpha_2",
                    "amount": 18000,
                    "category": "Bills",
                    "description": "Apartment Rent & Society Maintenance",
                    "date": "2026-10-02",
                    "type": "expense",
                    "splitWith": []
                },
                {
                    "id": "tx_alpha_3",
                    "amount": 5200,
                    "category": "Food",
                    "description": "Supermarket Grocery Haul",
                    "date": "2026-10-05",
                    "type": "expense",
                    "splitWith": []
                },
                {
                    "id": "tx_alpha_4",
                    "amount": 3500,
                    "category": "Shopping",
                    "description": "Noise Cancelling Work Headphones",
                    "date": "2026-10-10",
                    "type": "expense",
                    "splitWith": []
                },
                {
                    "id": "tx_alpha_5",
                    "amount": 1500,
                    "category": "Entertainment",
                    "description": "Weekend Cinema & Popcorn",
                    "date": "2026-10-12",
                    "type": "expense",
                    "splitWith": []
                }
            ]
        },
        "user_beta_456": {
            "profile": {
                "uid": "user_beta_456",
                "email": "user_beta_456@example.com",
                "displayName": "Beta User",
                "employer": "Fintech Innovations",
                "salaries": {
                    "2026-9": {"amount": 120000, "employer": "Fintech Innovations", "payDay": 5},
                    "2026-10": {"amount": 120000, "employer": "Fintech Innovations", "payDay": 5}
                },
                "budgets": {
                    "2026-9": 70000,
                    "2026-10": 70000
                }
            },
            "transactions": [
                {
                    "id": "tx_beta_1",
                    "amount": 120000,
                    "category": "Salary",
                    "description": "October Salary Credited",
                    "date": "2026-10-05",
                    "type": "income",
                    "splitWith": []
                },
                {
                    "id": "tx_beta_2",
                    "amount": 42000,
                    "category": "Shopping",
                    "description": "Designer Clothes & Luxury Watch",
                    "date": "2026-10-08",
                    "type": "expense",
                    "splitWith": []
                }
            ]
        }
    }

    def mock_get_user_profile(uid: str):
        return storage.get(uid, {}).get("profile", {"uid": uid, "budgets": {}, "salaries": {}})

    def mock_get_user_transactions(uid: str, month=None, year=None, transaction_type=None, limit=500):
        txs = storage.get(uid, {}).get("transactions", [])
        filtered = []
        for t in txs:
            if transaction_type and t.get("type") != transaction_type:
                continue
            if month is not None or year is not None:
                d = t.get("date", "")
                parts = d.split("-")
                if len(parts) >= 2:
                    tx_y = int(parts[0])
                    tx_m = int(parts[1]) - 1
                    if month is not None and tx_m != month:
                        continue
                    if year is not None and tx_y != year:
                        continue
            filtered.append(t)
        return filtered

    def mock_get_salary(uid: str, month: int, year: int):
        prof = mock_get_user_profile(uid)
        key = f"{year}-{month}"
        s = prof.get("salaries", {}).get(key, {})
        if isinstance(s, dict):
            return float(s.get("amount", 0)), s.get("employer", prof.get("employer", "")), int(s.get("payDay", 1))
        return float(s or 0), prof.get("employer", ""), 1

    def mock_get_budget(uid: str, month: int, year: int):
        prof = mock_get_user_profile(uid)
        key = f"{year}-{month}"
        return float(prof.get("budgets", {}).get(key, 0))

    monkeypatch.setattr(firebase_service, "get_user_profile", mock_get_user_profile)
    monkeypatch.setattr(firebase_service, "get_user_transactions", mock_get_user_transactions)
    monkeypatch.setattr(firebase_service, "get_salary_for_month", mock_get_salary)
    monkeypatch.setattr(firebase_service, "get_budget_for_month", mock_get_budget)
    monkeypatch.setattr(firebase_service, "get_all_user_transactions_for_indexing", lambda uid: mock_get_user_transactions(uid))

    return storage

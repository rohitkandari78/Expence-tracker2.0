"""
Tests for Firebase Token Authentication and Strict User-Specific Data Isolation.
"""
import pytest
from firebase.firebase_service import firebase_service
from tools import FinancialTools


def test_token_verification_success(mock_user_a):
    """Test valid token verification returns correct authenticated UID."""
    token = f"test-token-{mock_user_a['uid']}"
    decoded = firebase_service.verify_token(token)
    assert decoded["uid"] == mock_user_a["uid"]
    assert decoded["email"] == mock_user_a["email"]


def test_token_verification_missing():
    """Test that missing or empty token raises ValueError."""
    with pytest.raises(ValueError):
        firebase_service.verify_token("")


def test_user_data_isolation_proof(seeded_firebase_mock, mock_user_a, mock_user_b):
    """
    CRITICAL SECURITY TEST:
    Proves that User A cannot see or access User B's financial data,
    and User B cannot see or access User A's financial data.
    """
    uid_a = mock_user_a["uid"]
    uid_b = mock_user_b["uid"]

    # 1. User A's expenses in October 2026 (month index 9)
    # Rent (18000) + Food (5200) + Shopping (3500) + Entertainment (1500) = 28200
    res_a = FinancialTools.expense_retrieval_tool(uid=uid_a, month=9, year=2026)
    assert res_a["total_expenses"] == 28200
    assert res_a["transaction_count"] == 4

    # 2. User B's expenses in October 2026
    # Shopping (42000) = 42000
    res_b = FinancialTools.expense_retrieval_tool(uid=uid_b, month=9, year=2026)
    assert res_b["total_expenses"] == 42000
    assert res_b["transaction_count"] == 1

    # 3. Verify User A does NOT have User B's 42000 shopping expense
    a_descriptions = [t["description"] for t in res_a["transactions"]]
    assert "Designer Clothes & Luxury Watch" not in a_descriptions
    assert "Supermarket Grocery Haul" in a_descriptions

    # 4. Verify User B does NOT have User A's bills, groceries or cinema expenses
    b_descriptions = [t["description"] for t in res_b["transactions"]]
    assert "Apartment Rent & Society Maintenance" not in b_descriptions
    assert "Designer Clothes & Luxury Watch" in b_descriptions

    # 5. Verify User A and User B have separate salary and budget allocations
    salary_a, emp_a, _ = firebase_service.get_salary_for_month(uid_a, 9, 2026)
    salary_b, emp_b, _ = firebase_service.get_salary_for_month(uid_b, 9, 2026)
    assert salary_a == 75000
    assert emp_a == "Tech Corp Global"
    assert salary_b == 120000
    assert emp_b == "Fintech Innovations"

    budget_a = firebase_service.get_budget_for_month(uid_a, 9, 2026)
    budget_b = firebase_service.get_budget_for_month(uid_b, 9, 2026)
    assert budget_a == 45000
    assert budget_b == 70000

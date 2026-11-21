"""
Tests for Financial Tools and Numerical Calculations.
"""
import pytest
from tools import FinancialTools


def test_expense_calculations(seeded_firebase_mock, mock_user_a):
    uid = mock_user_a["uid"]
    # User A October expenses: 18000 + 5200 + 3500 + 1500 = 28200
    res = FinancialTools.expense_retrieval_tool(uid=uid, month=9, year=2026)
    assert res["total_expenses"] == 28200
    assert res["transaction_count"] == 4
    assert res["total_expenses_formatted"] == "₹28,200"


def test_income_calculations(seeded_firebase_mock, mock_user_a):
    uid = mock_user_a["uid"]
    # Base salary is 75000, logged also as income transaction 75000 (no double count)
    res = FinancialTools.income_retrieval_tool(uid=uid, month=9, year=2026)
    assert res["total_income"] == 75000
    assert res["employer"] == "Tech Corp Global"


def test_budget_calculations(seeded_firebase_mock, mock_user_a):
    uid = mock_user_a["uid"]
    # Budget = 45000, Spent = 28200 -> Remaining = 16800, Utilization = 28200/45000 = 62.7%
    res = FinancialTools.budget_calculator_tool(uid=uid, month=9, year=2026)
    assert res["budget"] == 45000
    assert res["total_spent"] == 28200
    assert res["remaining_budget"] == 16800
    assert res["is_over_budget"] is False
    assert res["utilization_percentage"] == 62.7


def test_category_breakdown_calculations(seeded_firebase_mock, mock_user_a):
    uid = mock_user_a["uid"]
    res = FinancialTools.category_analysis_tool(uid=uid, month=9, year=2026)
    assert res["top_category"] == "Bills"
    assert res["raw_totals"]["Bills"] == 18000
    assert res["raw_totals"]["Food"] == 5200
    assert res["raw_totals"]["Shopping"] == 3500
    assert res["raw_totals"]["Entertainment"] == 1500


def test_fifty_thirty_twenty_rule(seeded_firebase_mock, mock_user_a):
    uid = mock_user_a["uid"]
    # Income = 75000
    # Needs: Bills (18000) + Food (5200) = 23200 (30.9%)
    # Wants: Shopping (3500) + Entertainment (1500) = 5000 (6.7%)
    # Savings: 75000 - 28200 = 46800 (62.4%)
    res = FinancialTools.spending_pattern_analyzer(uid=uid, month=9, year=2026)
    assert res["needs"]["spent"] == 23200
    assert res["needs"]["percentage"] == 30.9
    assert res["wants"]["spent"] == 5000
    assert res["wants"]["percentage"] == 6.7
    assert res["savings"]["amount"] == 46800
    assert res["savings"]["percentage"] == 62.4


def test_missing_data_handling(seeded_firebase_mock):
    """Test behavior when user has zero transactions and no budget/salary set."""
    empty_uid = "empty_user_999"
    
    exp = FinancialTools.expense_retrieval_tool(uid=empty_uid, month=9, year=2026)
    assert exp["total_expenses"] == 0
    assert exp["transaction_count"] == 0

    inc = FinancialTools.income_retrieval_tool(uid=empty_uid, month=9, year=2026)
    assert inc["total_income"] == 0

    bud = FinancialTools.budget_calculator_tool(uid=empty_uid, month=9, year=2026)
    assert bud["budget"] == 0
    assert bud["remaining_budget"] == 0
    assert bud["is_over_budget"] is False

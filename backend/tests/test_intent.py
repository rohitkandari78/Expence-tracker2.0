"""
Tests for Intent Detection and Natural Language Parsing across English, Hindi, and Hinglish.
"""
import pytest
from intent import intent_detector
from schemas.state import IntentEnum


@pytest.mark.parametrize("query,expected_intent", [
    # 1. expense_query
    ("How much did I spend this month?", IntentEnum.EXPENSE_QUERY),
    ("Maine is month kitne paise kharch kiye?", IntentEnum.EXPENSE_QUERY),
    ("Mera total kharcha kitna hua?", IntentEnum.EXPENSE_QUERY),
    ("Show my total spending for October", IntentEnum.EXPENSE_QUERY),

    # 2. income_query
    ("What was my total income this month?", IntentEnum.INCOME_QUERY),
    ("Kitni income aayi is mahine?", IntentEnum.INCOME_QUERY),
    ("Show my bonus and earnings credits", IntentEnum.INCOME_QUERY),

    # 3. salary_query
    ("How much salary is left?", IntentEnum.SALARY_QUERY),
    ("Meri tankhwah kitni bachi hai?", IntentEnum.SALARY_QUERY),
    ("What is my in-hand salary and payday?", IntentEnum.SALARY_QUERY),

    # 4. budget_query
    ("Mera kitna budget remaining hai?", IntentEnum.BUDGET_QUERY),
    ("What is my remaining budget for this month?", IntentEnum.BUDGET_QUERY),
    ("Am I over budget?", IntentEnum.BUDGET_QUERY),

    # 5. savings_query
    ("What is my net savings this month?", IntentEnum.SAVINGS_QUERY),
    ("Maine kitne paise bachaye?", IntentEnum.SAVINGS_QUERY),
    ("Show my current savings rate percentage", IntentEnum.SAVINGS_QUERY),

    # 6. category_analysis
    ("Where am I spending the most?", IntentEnum.CATEGORY_ANALYSIS),
    ("Sabse jyada kharcha kaha ho raha hai?", IntentEnum.CATEGORY_ANALYSIS),
    ("Show my category breakdown for expenses", IntentEnum.CATEGORY_ANALYSIS),

    # 7. monthly_comparison
    ("Compare my last two months' expenses.", IntentEnum.MONTHLY_COMPARISON),
    ("Pichle mahine se compare karo", IntentEnum.MONTHLY_COMPARISON),
    ("Difference between September and October expenses", IntentEnum.MONTHLY_COMPARISON),

    # 8. historical_expense_search
    ("Find my travel-related expenses.", IntentEnum.HISTORICAL_EXPENSE_SEARCH),
    ("Search for Uber and Swiggy transactions", IntentEnum.HISTORICAL_EXPENSE_SEARCH),
    ("Dhundho headphones ka transaction", IntentEnum.HISTORICAL_EXPENSE_SEARCH),

    # 9. spending_pattern_analysis
    ("Analyze my 50/30/20 salary rule allocation", IntentEnum.SPENDING_PATTERN_ANALYSIS),
    ("Show my needs vs wants spending breakdown", IntentEnum.SPENDING_PATTERN_ANALYSIS),
    ("Fifty thirty twenty rule ka status kya hai?", IntentEnum.SPENDING_PATTERN_ANALYSIS),

    # 10. saving_recommendation
    ("Mujhe paise save karne ke suggestions do.", IntentEnum.SAVING_RECOMMENDATION),
    ("How can I save more money this month?", IntentEnum.SAVING_RECOMMENDATION),
    ("Give me tips to reduce my expenses", IntentEnum.SAVING_RECOMMENDATION),

    # 11. financial_summary
    ("Give me a complete financial summary", IntentEnum.FINANCIAL_SUMMARY),
    ("Overall financial report dikhao", IntentEnum.FINANCIAL_SUMMARY),
    ("Show monthly dashboard overview", IntentEnum.FINANCIAL_SUMMARY)
])
def test_intent_detection(query, expected_intent):
    intent, confidence = intent_detector.detect_intent(query)
    assert intent == expected_intent
    assert confidence >= 0.60


def test_month_extraction():
    # Explicit month
    m, y = intent_detector.extract_month_and_year("What was my budget in October 2026?")
    assert m == 9  # October is index 9 (0-indexed)
    assert y == 2026

    # Relative last month
    m, _ = intent_detector.extract_month_and_year("Compare with pichle mahine")
    assert m is not None

"""
Financial Calculation and Retrieval Tools.
Provides deterministic calculations and structured financial data for the AI Financial Assistant.
"""
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date
import calendar

from firebase.firebase_service import firebase_service


# 50/30/20 Category mappings
NEEDS_CATEGORIES = {"Bills", "Food", "Transport", "Health"}
WANTS_CATEGORIES = {"Shopping", "Entertainment", "Other"}


def get_current_month_year() -> Tuple[int, int]:
    """Returns current (month_index 0-11, year)."""
    now = datetime.now()
    return now.month - 1, now.year


def format_inr(val: float) -> str:
    """Formats float value as Indian Rupee string."""
    return f"₹{val:,.2f}".rstrip('0').rstrip('.') if val != int(val) else f"₹{int(val):,}"


class FinancialTools:
    """Collection of deterministic financial retrieval and calculation tools."""

    @staticmethod
    def expense_retrieval_tool(
        uid: str, 
        month: Optional[int] = None, 
        year: Optional[int] = None,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Tool 1: Expense Retrieval Tool
        Calculates total expenses and returns itemized list for a specific month or overall.
        """
        curr_m, curr_y = get_current_month_year()
        target_m = month if month is not None else curr_m
        target_y = year if year is not None else curr_y

        transactions = firebase_service.get_user_transactions(
            uid=uid, month=target_m, year=target_y, transaction_type="expense"
        )

        if category:
            transactions = [t for t in transactions if t.get("category", "").lower() == category.lower()]

        total_spent = sum(float(t.get("amount", 0)) for t in transactions)
        month_name = calendar.month_name[target_m + 1]

        return {
            "tool": "expense_retrieval_tool",
            "month": target_m,
            "year": target_y,
            "month_name": month_name,
            "total_expenses": total_spent,
            "total_expenses_formatted": format_inr(total_spent),
            "transaction_count": len(transactions),
            "category_filter": category,
            "transactions": transactions[:50]  # Cap for context
        }

    @staticmethod
    def income_retrieval_tool(
        uid: str, 
        month: Optional[int] = None, 
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Tool 2: Income Retrieval Tool
        Calculates base salary + extra income credits, avoiding double-counting with salary transactions.
        """
        curr_m, curr_y = get_current_month_year()
        target_m = month if month is not None else curr_m
        target_y = year if year is not None else curr_y

        base_salary, employer, payday = firebase_service.get_salary_for_month(uid, target_m, target_y)
        income_txs = firebase_service.get_user_transactions(
            uid=uid, month=target_m, year=target_y, transaction_type="income"
        )

        # Sum additional income credits
        income_credits = sum(float(t.get("amount", 0)) for t in income_txs)
        
        # Check if salary was logged as an income transaction
        has_salary_tx = any(
            t.get("category") in ["Salary", "Monthly Salary"]
            for t in income_txs
        )

        # If already logged as transaction, use transaction sum to avoid double counting
        total_income = income_credits if has_salary_tx else (base_salary + income_credits)
        month_name = calendar.month_name[target_m + 1]

        return {
            "tool": "income_retrieval_tool",
            "month": target_m,
            "year": target_y,
            "month_name": month_name,
            "base_salary": base_salary,
            "employer": employer,
            "payday": payday,
            "income_credits": income_credits,
            "total_income": total_income,
            "total_income_formatted": format_inr(total_income),
            "income_transactions": income_txs
        }

    @staticmethod
    def salary_analysis_tool(
        uid: str, 
        month: Optional[int] = None, 
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Tool 3: Salary Analysis Tool
        Analyzes in-hand salary, expenses debited against salary, remaining in-hand balance, daily burn rate.
        """
        curr_m, curr_y = get_current_month_year()
        target_m = month if month is not None else curr_m
        target_y = year if year is not None else curr_y

        income_data = FinancialTools.income_retrieval_tool(uid, target_m, target_y)
        expense_data = FinancialTools.expense_retrieval_tool(uid, target_m, target_y)

        total_income = income_data["total_income"]
        total_spent = expense_data["total_expenses"]
        net_savings = total_income - total_spent
        savings_rate = (net_savings / total_income * 100) if total_income > 0 else 0.0

        # Daily burn calculation
        now = datetime.now()
        days_in_month = calendar.monthrange(target_y, target_m + 1)[1]
        is_curr = (target_m == curr_m and target_y == curr_y)
        elapsed_days = max(1, now.day) if is_curr else days_in_month
        daily_burn = total_spent / elapsed_days if elapsed_days > 0 else 0.0

        days_left_in_month = max(0, days_in_month - now.day) if is_curr else 0

        return {
            "tool": "salary_analysis_tool",
            "month": target_m,
            "year": target_y,
            "month_name": income_data["month_name"],
            "base_salary": income_data["base_salary"],
            "employer": income_data["employer"],
            "total_income": total_income,
            "total_spent": total_spent,
            "net_savings": net_savings,
            "net_savings_formatted": format_inr(net_savings),
            "savings_rate_percent": round(savings_rate, 1),
            "daily_burn_rate": round(daily_burn, 2),
            "daily_burn_formatted": format_inr(daily_burn),
            "is_deficit": net_savings < 0,
            "status": "Salary Deficit ⚠️" if net_savings < 0 else "Positive Savings ✨",
            "days_left_in_month": days_left_in_month
        }

    @staticmethod
    def budget_calculator_tool(
        uid: str, 
        month: Optional[int] = None, 
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Tool 4: Budget Calculator Tool
        Calculates monthly budget, spent amount, remaining budget, over-budget status.
        """
        curr_m, curr_y = get_current_month_year()
        target_m = month if month is not None else curr_m
        target_y = year if year is not None else curr_y

        budget = firebase_service.get_budget_for_month(uid, target_m, target_y)
        expense_data = FinancialTools.expense_retrieval_tool(uid, target_m, target_y)
        total_spent = expense_data["total_expenses"]

        remaining = budget - total_spent
        utilization_pct = (total_spent / budget * 100) if budget > 0 else 0.0
        is_over = budget > 0 and total_spent > budget

        return {
            "tool": "budget_calculator_tool",
            "month": target_m,
            "year": target_y,
            "month_name": expense_data["month_name"],
            "budget": budget,
            "budget_formatted": format_inr(budget),
            "total_spent": total_spent,
            "total_spent_formatted": format_inr(total_spent),
            "remaining_budget": remaining,
            "remaining_budget_formatted": format_inr(remaining),
            "utilization_percentage": round(utilization_pct, 1),
            "is_over_budget": is_over,
            "overspend_amount": max(0.0, total_spent - budget) if is_over else 0.0
        }

    @staticmethod
    def category_analysis_tool(
        uid: str, 
        month: Optional[int] = None, 
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Tool 5: Category Analysis Tool
        Computes spendings by category, percentage of total spend for each category, highest spending category.
        """
        curr_m, curr_y = get_current_month_year()
        target_m = month if month is not None else curr_m
        target_y = year if year is not None else curr_y

        transactions = firebase_service.get_user_transactions(
            uid=uid, month=target_m, year=target_y, transaction_type="expense"
        )

        category_totals: Dict[str, float] = {}
        category_counts: Dict[str, int] = {}
        total_spent = 0.0

        for t in transactions:
            cat = t.get("category") or "Other"
            amt = float(t.get("amount", 0))
            category_totals[cat] = category_totals.get(cat, 0.0) + amt
            category_counts[cat] = category_counts.get(cat, 0) + 1
            total_spent += amt

        # Compute percentages & rank
        breakdown = []
        for cat, amt in category_totals.items():
            pct = (amt / total_spent * 100) if total_spent > 0 else 0.0
            breakdown.append({
                "category": cat,
                "amount": amt,
                "amount_formatted": format_inr(amt),
                "percentage": round(pct, 1),
                "count": category_counts[cat]
            })

        breakdown.sort(key=lambda x: x["amount"], reverse=True)
        top_category = breakdown[0]["category"] if breakdown else "None"

        return {
            "tool": "category_analysis_tool",
            "month": target_m,
            "year": target_y,
            "month_name": calendar.month_name[target_m + 1],
            "total_spent": total_spent,
            "total_spent_formatted": format_inr(total_spent),
            "top_category": top_category,
            "category_breakdown": breakdown,
            "raw_totals": category_totals
        }

    @staticmethod
    def monthly_comparison_tool(
        uid: str, 
        month1: Optional[int] = None, 
        year1: Optional[int] = None,
        month2: Optional[int] = None, 
        year2: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Tool 6: Monthly Comparison Tool
        Compares two months (defaults to current month vs previous month).
        """
        curr_m, curr_y = get_current_month_year()
        
        # Current or requested month 1
        m1 = month1 if month1 is not None else curr_m
        y1 = year1 if year1 is not None else curr_y

        # Month 2 defaults to the month immediately preceding Month 1
        if month2 is None or year2 is None:
            if m1 == 0:
                m2 = 11
                y2 = y1 - 1
            else:
                m2 = m1 - 1
                y2 = y1
        else:
            m2 = month2
            y2 = year2

        m1_expenses = FinancialTools.expense_retrieval_tool(uid, m1, y1)
        m2_expenses = FinancialTools.expense_retrieval_tool(uid, m2, y2)
        m1_income = FinancialTools.income_retrieval_tool(uid, m1, y1)
        m2_income = FinancialTools.income_retrieval_tool(uid, m2, y2)

        spent1 = m1_expenses["total_expenses"]
        spent2 = m2_expenses["total_expenses"]
        diff_spent = spent1 - spent2
        pct_change_spent = ((diff_spent / spent2) * 100) if spent2 > 0 else 0.0

        savings1 = m1_income["total_income"] - spent1
        savings2 = m2_income["total_income"] - spent2

        return {
            "tool": "monthly_comparison_tool",
            "period_1": {
                "month": m1,
                "year": y1,
                "name": f"{m1_expenses['month_name']} {y1}",
                "total_spent": spent1,
                "total_income": m1_income["total_income"],
                "net_savings": savings1
            },
            "period_2": {
                "month": m2,
                "year": y2,
                "name": f"{m2_expenses['month_name']} {y2}",
                "total_spent": spent2,
                "total_income": m2_income["total_income"],
                "net_savings": savings2
            },
            "expense_difference": diff_spent,
            "expense_difference_formatted": format_inr(abs(diff_spent)),
            "percentage_change": round(pct_change_spent, 1),
            "trend": "increased" if diff_spent > 0 else "decreased" if diff_spent < 0 else "unchanged"
        }

    @staticmethod
    def historical_transaction_search_tool(
        uid: str, 
        query: str,
        category: Optional[str] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Tool 7: Historical Transaction Search Tool
        Searches transaction descriptions, notes, and categories across all time for the authenticated user.
        """
        all_txs = firebase_service.get_user_transactions(uid=uid, limit=1000)
        q = query.lower().strip()

        matched = []
        for t in all_txs:
            desc = str(t.get("description", "")).lower()
            cat = str(t.get("category", "")).lower()
            
            if category and cat != category.lower():
                continue

            if q in desc or q in cat:
                matched.append(t)

        total_matched_amt = sum(float(t.get("amount", 0)) for t in matched)

        return {
            "tool": "historical_transaction_search_tool",
            "query": query,
            "total_matches": len(matched),
            "total_amount": total_matched_amt,
            "total_amount_formatted": format_inr(total_matched_amt),
            "results": matched[:limit]
        }

    @staticmethod
    def spending_pattern_analyzer(
        uid: str, 
        month: Optional[int] = None, 
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Tool 8: Spending Pattern Analyzer
        Analyzes spending according to 50/30/20 Rule: Needs (<=50%), Wants (<=30%), Savings (>=20%).
        """
        curr_m, curr_y = get_current_month_year()
        target_m = month if month is not None else curr_m
        target_y = year if year is not None else curr_y

        income_data = FinancialTools.income_retrieval_tool(uid, target_m, target_y)
        txs = firebase_service.get_user_transactions(
            uid=uid, month=target_m, year=target_y, transaction_type="expense"
        )

        total_income = income_data["total_income"]
        needs_total = 0.0
        wants_total = 0.0

        for t in txs:
            cat = t.get("category", "Other")
            amt = float(t.get("amount", 0))
            if cat in NEEDS_CATEGORIES:
                needs_total += amt
            else:
                wants_total += amt

        total_spent = needs_total + wants_total
        net_savings = total_income - total_spent

        needs_pct = (needs_total / total_income * 100) if total_income > 0 else 0.0
        wants_pct = (wants_total / total_income * 100) if total_income > 0 else 0.0
        savings_pct = (max(0.0, net_savings) / total_income * 100) if total_income > 0 else 0.0

        # Health evaluation
        observations = []
        if needs_pct > 50:
            observations.append(f"Needs spending is {needs_pct:.1f}% (exceeds recommended 50% cap by {needs_pct-50:.1f}%).")
        else:
            observations.append(f"Needs spending is healthy at {needs_pct:.1f}% (within 50% target).")

        if wants_pct > 30:
            observations.append(f"Wants spending is high at {wants_pct:.1f}% (exceeds recommended 30% cap by {wants_pct-30:.1f}%).")
        else:
            observations.append(f"Wants spending is well-controlled at {wants_pct:.1f}% (within 30% limit).")

        if savings_pct < 20:
            observations.append(f"Savings rate is {savings_pct:.1f}%, which is below the benchmark of 20%.")
        else:
            observations.append(f"Savings rate is strong at {savings_pct:.1f}% (meets/exceeds 20% target).")

        return {
            "tool": "spending_pattern_analyzer",
            "month": target_m,
            "year": target_y,
            "month_name": income_data["month_name"],
            "total_income": total_income,
            "total_spent": total_spent,
            "net_savings": net_savings,
            "needs": {
                "spent": needs_total,
                "spent_formatted": format_inr(needs_total),
                "percentage": round(needs_pct, 1),
                "target_percentage": 50.0,
                "categories": list(NEEDS_CATEGORIES)
            },
            "wants": {
                "spent": wants_total,
                "spent_formatted": format_inr(wants_total),
                "percentage": round(wants_pct, 1),
                "target_percentage": 30.0,
                "categories": list(WANTS_CATEGORIES)
            },
            "savings": {
                "amount": net_savings,
                "amount_formatted": format_inr(net_savings),
                "percentage": round(savings_pct, 1),
                "target_percentage": 20.0
            },
            "observations": observations
        }

    @staticmethod
    def savings_recommendation_tool(
        uid: str, 
        month: Optional[int] = None, 
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Tool 9: Savings Recommendation Tool
        Generates actionable, personalized recommendations based on actual spending and category patterns.
        """
        pattern = FinancialTools.spending_pattern_analyzer(uid, month, year)
        cat_data = FinancialTools.category_analysis_tool(uid, month, year)
        budget_data = FinancialTools.budget_calculator_tool(uid, month, year)

        wants_total = pattern["wants"]["spent"]
        wants_pct = pattern["wants"]["percentage"]
        net_savings = pattern["net_savings"]
        recommendations = []

        # 1. Wants reduction recommendation
        if wants_pct > 30:
            target_reduction = wants_total - (pattern["total_income"] * 0.30)
            recommendations.append(
                f"Reduce discretionary expenditure (Shopping, Entertainment, Outings) by approximately "
                f"{format_inr(target_reduction)} to bring wants within the healthy 30% threshold."
            )

        # 2. Top category optimization
        top_cat = cat_data["top_category"]
        if top_cat != "None" and top_cat in WANTS_CATEGORIES:
            top_amt = cat_data["raw_totals"].get(top_cat, 0.0)
            recommendations.append(
                f"Your highest expenditure in discretionary spending is in '{top_cat}' ({format_inr(top_amt)}). "
                f"Setting a specific sub-budget cap on {top_cat} could immediately boost monthly savings."
            )

        # 3. Budget overrun
        if budget_data["is_over_budget"]:
            recommendations.append(
                f"You have currently overspent your budget by {format_inr(budget_data['overspend_amount'])}. "
                f"Pause non-essential transactions for the remainder of the month."
            )

        # 4. In-pocket retention
        if net_savings > 0 and pattern["savings"]["percentage"] >= 20:
            recommendations.append(
                f"You have retained {format_inr(net_savings)} ({pattern['savings']['percentage']}% of income) this month. "
                f"Consider transferring surplus funds to an emergency fund or short-term high-yield account."
            )
        elif net_savings < 0:
            recommendations.append(
                f"You are currently running a deficit of {format_inr(abs(net_savings))}. "
                f"Prioritize essential expenses only until your next salary credit."
            )

        if not recommendations:
            recommendations.append(
                "Maintain your disciplined spending pace. Keep logging daily expenses to preserve your current savings rate."
            )

        return {
            "tool": "savings_recommendation_tool",
            "month": pattern["month"],
            "year": pattern["year"],
            "month_name": pattern["month_name"],
            "recommendations": recommendations,
            "current_savings_rate": pattern["savings"]["percentage"],
            "wants_percentage": wants_pct
        }

    @staticmethod
    def financial_summary(
        uid: str, 
        month: Optional[int] = None, 
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        """Comprehensive combined monthly financial summary."""
        curr_m, curr_y = get_current_month_year()
        target_m = month if month is not None else curr_m
        target_y = year if year is not None else curr_y

        user_profile = firebase_service.get_user_profile(uid)
        salary_analysis = FinancialTools.salary_analysis_tool(uid, target_m, target_y)
        budget_data = FinancialTools.budget_calculator_tool(uid, target_m, target_y)
        category_data = FinancialTools.category_analysis_tool(uid, target_m, target_y)
        pattern = FinancialTools.spending_pattern_analyzer(uid, target_m, target_y)

        return {
            "user_id": uid,
            "user_name": user_profile.get("displayName", "User"),
            "month": target_m,
            "year": target_y,
            "month_name": salary_analysis["month_name"],
            "base_salary": salary_analysis["base_salary"],
            "employer": salary_analysis["employer"],
            "total_income": salary_analysis["total_income"],
            "total_spent": salary_analysis["total_spent"],
            "net_savings": salary_analysis["net_savings"],
            "savings_rate": salary_analysis["savings_rate_percent"],
            "budget": budget_data["budget"],
            "remaining_budget": budget_data["remaining_budget"],
            "budget_utilization_percent": budget_data["utilization_percentage"],
            "category_breakdown": category_data["raw_totals"],
            "fifty_thirty_twenty": {
                "needs_spent": pattern["needs"]["spent"],
                "needs_percentage": pattern["needs"]["percentage"],
                "wants_spent": pattern["wants"]["spent"],
                "wants_percentage": pattern["wants"]["percentage"],
                "savings_amount": pattern["savings"]["amount"],
                "savings_percentage": pattern["savings"]["percentage"],
                "status": salary_analysis["status"]
            },
            "transaction_count": len(category_data["category_breakdown"])
        }

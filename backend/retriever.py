"""
Hybrid Financial Retriever Module.
Combines deterministic structured Firestore retrieval with semantic ChromaDB vector search.
"""
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import calendar

from firebase.firebase_service import firebase_service
from vectorstore.vector_store import vector_store
from tools import FinancialTools, format_inr

logger = logging.getLogger("ai_controller.retriever")


class HybridRetriever:
    """Orchestrates structured financial queries and semantic vector retrieval."""

    def __init__(self):
        self.firebase = firebase_service
        self.vector_store = vector_store

    def retrieve(
        self,
        uid: str,
        query: str,
        intent: str,
        month: Optional[int] = None,
        year: Optional[int] = None,
        semantic_limit: int = 5
    ) -> Dict[str, Any]:
        """
        Executes hybrid retrieval:
        1. Structured deterministic retrieval tailored to the detected intent.
        2. Semantic similarity retrieval over user's historical transactions.
        3. Fuses both into a comprehensive grounded context dictionary.
        """
        curr_dt = datetime.now()
        target_m = month if month is not None else (curr_dt.month - 1)
        target_y = year if year is not None else curr_dt.year
        month_name = calendar.month_name[target_m + 1]

        # 1. Deterministic Structured Retrieval based on intent
        structured_data: Dict[str, Any] = {
            "period": {
                "month_index": target_m,
                "month_name": month_name,
                "year": target_y
            }
        }

        # Retrieve core baseline for all queries to ensure full grounding
        salary_analysis = FinancialTools.salary_analysis_tool(uid, target_m, target_y)
        budget_data = FinancialTools.budget_calculator_tool(uid, target_m, target_y)
        category_data = FinancialTools.category_analysis_tool(uid, target_m, target_y)

        structured_data["financial_snapshot"] = {
            "base_salary": salary_analysis["base_salary"],
            "employer": salary_analysis["employer"],
            "total_income": salary_analysis["total_income"],
            "total_spent": salary_analysis["total_spent"],
            "net_savings": salary_analysis["net_savings"],
            "savings_rate_percent": salary_analysis["savings_rate_percent"],
            "budget": budget_data["budget"],
            "remaining_budget": budget_data["remaining_budget"],
            "is_over_budget": budget_data["is_over_budget"],
            "top_spending_category": category_data["top_category"]
        }

        # Intent-specific structured data enrichment
        if intent in ["expense_query", "category_analysis"]:
            structured_data["expenses"] = FinancialTools.expense_retrieval_tool(uid, target_m, target_y)
            structured_data["categories"] = category_data

        elif intent in ["income_query", "salary_query"]:
            structured_data["income"] = FinancialTools.income_retrieval_tool(uid, target_m, target_y)
            structured_data["salary_analysis"] = salary_analysis

        elif intent == "budget_query":
            structured_data["budget_analysis"] = budget_data
            structured_data["categories"] = category_data

        elif intent in ["savings_query", "spending_pattern_analysis"]:
            structured_data["spending_pattern"] = FinancialTools.spending_pattern_analyzer(uid, target_m, target_y)
            structured_data["salary_analysis"] = salary_analysis

        elif intent == "monthly_comparison":
            structured_data["monthly_comparison"] = FinancialTools.monthly_comparison_tool(uid, target_m, target_y)

        elif intent == "saving_recommendation":
            structured_data["spending_pattern"] = FinancialTools.spending_pattern_analyzer(uid, target_m, target_y)
            structured_data["recommendations"] = FinancialTools.savings_recommendation_tool(uid, target_m, target_y)

        elif intent == "financial_summary":
            structured_data["summary"] = FinancialTools.financial_summary(uid, target_m, target_y)

        elif intent == "historical_expense_search":
            structured_data["keyword_search"] = FinancialTools.historical_transaction_search_tool(uid, query)

        # 2. Semantic Vector Retrieval
        semantic_matches = self.vector_store.search_similar(
            uid=uid,
            query=query,
            limit=semantic_limit
        )

        # 3. Context Construction
        formatted_context = self._build_context_prompt(
            structured_data=structured_data,
            semantic_matches=semantic_matches,
            query=query,
            intent=intent
        )

        return {
            "structured_data": structured_data,
            "semantic_matches": semantic_matches,
            "formatted_context": formatted_context
        }

    def _build_context_prompt(
        self,
        structured_data: Dict[str, Any],
        semantic_matches: List[Dict[str, Any]],
        query: str,
        intent: str
    ) -> str:
        """Formats retrieved financial facts and semantic snippets into an explicit LLM context."""
        period = structured_data.get("period", {})
        month_name = period.get("month_name", "Current Month")
        year = period.get("year", datetime.now().year)

        lines = [
            f"=== VERIFIED FINANCIAL CONTEXT FOR {month_name.upper()} {year} ===",
            "NOTE: All figures below are strictly verified from Cloud Firestore for the authenticated user."
        ]

        snapshot = structured_data.get("financial_snapshot", {})
        if snapshot:
            lines.extend([
                f"- Employer: {snapshot.get('employer', 'Not specified')}",
                f"- Base Monthly Salary: {format_inr(snapshot.get('base_salary', 0))}",
                f"- Total Verified Income/Credits: {format_inr(snapshot.get('total_income', 0))}",
                f"- Total Debited Expenses: {format_inr(snapshot.get('total_spent', 0))}",
                f"- Net In-Pocket Savings: {format_inr(snapshot.get('net_savings', 0))} (Savings Rate: {snapshot.get('savings_rate_percent', 0)}%)",
                f"- Monthly Budget: {format_inr(snapshot.get('budget', 0))} (Remaining: {format_inr(snapshot.get('remaining_budget', 0))})",
                f"- Over Budget Status: {'YES ⚠️' if snapshot.get('is_over_budget') else 'NO (Within Budget) ✨'}",
                f"- Highest Expense Category: {snapshot.get('top_spending_category', 'None')}"
            ])

        # Add category breakdown if available
        if "categories" in structured_data:
            cat_info = structured_data["categories"]
            lines.append("\n=== EXPENSE CATEGORY BREAKDOWN ===")
            for item in cat_info.get("category_breakdown", []):
                lines.append(
                    f"• {item['category']}: {item['amount_formatted']} ({item['percentage']}% of expenses, {item['count']} transactions)"
                )

        # Add 50/30/20 spending pattern if available
        if "spending_pattern" in structured_data:
            p = structured_data["spending_pattern"]
            lines.extend([
                "\n=== 50/30/20 SALARY ALLOCATION ANALYSIS ===",
                f"• Needs (Target <=50%): {p['needs']['spent_formatted']} ({p['needs']['percentage']}%)",
                f"• Wants (Target <=30%): {p['wants']['spent_formatted']} ({p['wants']['percentage']}%)",
                f"• Savings (Target >=20%): {p['savings']['amount_formatted']} ({p['savings']['percentage']}%)",
                f"• Observations: {'; '.join(p.get('observations', []))}"
            ])

        # Add monthly comparison if available
        if "monthly_comparison" in structured_data:
            c = structured_data["monthly_comparison"]
            lines.extend([
                "\n=== MONTHLY COMPARISON ===",
                f"• {c['period_1']['name']}: Spent {format_inr(c['period_1']['total_spent'])}, Income {format_inr(c['period_1']['total_income'])}, Savings {format_inr(c['period_1']['net_savings'])}",
                f"• {c['period_2']['name']}: Spent {format_inr(c['period_2']['total_spent'])}, Income {format_inr(c['period_2']['total_income'])}, Savings {format_inr(c['period_2']['net_savings'])}",
                f"• Difference in spending: {c['expense_difference_formatted']} ({c['trend']} by {c['percentage_change']}%)"
            ])

        # Add keyword search matches if available
        if "keyword_search" in structured_data:
            ks = structured_data["keyword_search"]
            lines.extend([
                f"\n=== KEYWORD TRANSACTION MATCHES (Query: '{ks['query']}') ===",
                f"Total Matched: {ks['total_matches']}, Total Amount: {ks['total_amount_formatted']}"
            ])
            for t in ks.get("results", [])[:10]:
                lines.append(f"• [{t.get('date')}] {t.get('description')} ({t.get('category')}): {format_inr(t.get('amount', 0))}")

        # Add semantic vector retrieval results
        if semantic_matches:
            lines.append("\n=== RELEVANT HISTORICAL TRANSACTIONS (SEMANTIC VECTOR RETRIEVAL) ===")
            for sm in semantic_matches:
                meta = sm.get("metadata", {})
                lines.append(
                    f"• {sm.get('text')} [Date: {meta.get('date')}, Category: {meta.get('category')}, Relevance: {sm.get('similarity')}]"
                )

        return "\n".join(lines)


# Singleton
hybrid_retriever = HybridRetriever()

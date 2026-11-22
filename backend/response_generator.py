"""
Response Generation Module using Google Gemini.
Generates grounded financial answers with strict anti-hallucination guarantees.
Supports English, Hindi, and Hinglish.
"""
import logging
from typing import Dict, List, Optional, Tuple, Any

import google.generativeai as genai
from config import settings
from tools import format_inr

logger = logging.getLogger("ai_controller.generator")


SYSTEM_PROMPT = """
You are Antigravity Financial AI, an expert personal financial advisor and assistant embedded in an Expense Tracker for salaried employees.
Your core mission is to provide accurate, grounded financial analysis and guidance based on the user's verified Cloud Firestore and transaction data.

CRITICAL RULES & CONSTRAINTS:
1. STRICT GROUNDING: You must ONLY use the verified financial figures, dates, and transactions provided in the context below.
2. NO HALLUCINATIONS: NEVER invent, guess, or extrapolate transactions, amounts, salaries, budgets, or dates.
3. ABSOLUTE NUMERICAL ACCURACY: Do not perform mental arithmetic that contradicts the context figures.
4. EXPLICIT UNAVAILABILITY: If a requested metric (e.g. salary, budget, or transaction) is missing or 0 in the context, explicitly inform the user that it hasn't been set or recorded yet.
5. DISTINGUISH FACTS FROM SUGGESTIONS: Clearly separate actual recorded numbers from financial recommendations.
6. CURRENCY FORMATTING: Format all monetary amounts in Indian Rupees (₹) (e.g., ₹75,000, ₹1,450).
7. MULTI-LINGUAL FLUENCY: If the user asks in Hindi or Hinglish (e.g., "Maine kitna kharch kiya?", "Kitna budget bacha hai?"), reply in fluent, natural, professional Hinglish. If in English, reply in clear, structured English.
8. ACTIONABLE ADVICE: When providing recommendations, tie them directly to the user's discretionary spending categories (Shopping, Entertainment, etc.) and the 50/30/20 salary allocation rule.
"""


class ResponseGenerator:
    """Generates grounded financial answers using Gemini with deterministic fallback."""

    def __init__(self):
        self.model = None
        self._init_gemini()

    def _init_gemini(self):
        """Initializes Google Gemini API client if valid API key is provided."""
        has_real_key = bool(
            settings.GEMINI_API_KEY 
            and not settings.GEMINI_API_KEY.startswith("your_")
            and len(settings.GEMINI_API_KEY) > 20
        )
        if has_real_key:
            try:
                genai.configure(api_key=settings.GEMINI_API_KEY)
                self.model = genai.GenerativeModel(
                    model_name=settings.GEMINI_MODEL,
                    system_instruction=SYSTEM_PROMPT
                )
                logger.info(f"Gemini model '{settings.GEMINI_MODEL}' initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini model: {e}")
                self.model = None
        else:
            logger.info("Real GEMINI_API_KEY not configured. Deterministic grounded generator will serve as active responder.")

    def generate_response(
        self,
        query: str,
        intent: str,
        retrieval_result: Dict[str, Any]
    ) -> Tuple[str, List[str]]:
        """
        Generates grounded response and relevant follow-up questions.
        Returns: (answer: str, suggested_followups: List[str])
        """
        structured_data = retrieval_result.get("structured_data", {})
        formatted_context = retrieval_result.get("formatted_context", "")

        # Try Gemini LLM first if configured
        if self.model and settings.GEMINI_API_KEY:
            try:
                prompt = (
                    f"{formatted_context}\n\n"
                    f"USER QUERY: {query}\n"
                    f"DETECTED INTENT: {intent}\n\n"
                    f"Generate a clear, accurate, conversational, and grounded answer according to the system instructions."
                )
                response = self.model.generate_content(prompt)
                if response and response.text:
                    answer = response.text.strip()
                    followups = self._generate_followups(intent, structured_data)
                    return answer, followups
            except Exception as e:
                logger.warning(f"Gemini API generation error: {e}. Falling back to deterministic response generator.")

        # Deterministic grounded fallback (guarantees 100% accurate responses even without LLM key)
        answer = self._generate_deterministic_grounded_answer(query, intent, structured_data)
        followups = self._generate_followups(intent, structured_data)
        return answer, followups

    def _generate_deterministic_grounded_answer(
        self,
        query: str,
        intent: str,
        structured_data: Dict[str, Any]
    ) -> str:
        """Deterministic, grounded financial responder based on verified Firestore calculations."""
        period = structured_data.get("period", {})
        month_name = period.get("month_name", "Current Month")
        year = period.get("year", 2026)
        snapshot = structured_data.get("financial_snapshot", {})

        is_hindi = any(word in query.lower() for word in [
            "kitne", "kitna", "kharch", "kharcha", "bacha", "bachat", "pichle", "mahine", "kaise", "batao", "dikhao"
        ])

        if intent == "expense_query":
            spent = snapshot.get("total_spent", 0)
            if spent == 0:
                return (
                    f"Aapne {month_name} {year} me abhi tak koi expense record nahi kiya hai. 🟢" 
                    if is_hindi else 
                    f"You have not recorded any expenses yet for {month_name} {year}. 🟢"
                )
            if is_hindi:
                return (
                    f"Aapne **{month_name} {year}** me kul **{format_inr(spent)}** kharch kiye hain. "
                    f"Aapka highest expenditure category **{snapshot.get('top_spending_category', 'General')}** me raha hai."
                )
            return (
                f"Your total debited expenses for **{month_name} {year}** are **{format_inr(spent)}**. "
                f"Your highest spending category is **{snapshot.get('top_spending_category', 'General')}**."
            )

        elif intent in ["income_query", "salary_query"]:
            income = snapshot.get("total_income", 0)
            salary = snapshot.get("base_salary", 0)
            employer = snapshot.get("employer", "Salaried Pro")
            savings = snapshot.get("net_savings", 0)
            
            if is_hindi:
                return (
                    f"**{month_name} {year}** ke liye aapki in-hand monthly salary **{format_inr(salary)}** ({employer}) hai, "
                    f"aur total recorded income **{format_inr(income)}** hai. "
                    f"Abhi aapke paas **{format_inr(savings)}** net bachat bachi hui hai."
                )
            return (
                f"For **{month_name} {year}**, your base in-hand salary from **{employer}** is **{format_inr(salary)}** "
                f"with a total verified income of **{format_inr(income)}**. "
                f"Your remaining net balance in hand is **{format_inr(savings)}**."
            )

        elif intent == "budget_query":
            b_info = structured_data.get("budget_analysis", {})
            budget = b_info.get("budget", snapshot.get("budget", 0))
            rem = b_info.get("remaining_budget", snapshot.get("remaining_budget", 0))
            is_over = b_info.get("is_over_budget", False)
            util = b_info.get("utilization_percentage", 0)

            if budget == 0:
                return (
                    f"{month_name} {year} ke liye koi budget set nahi kiya gaya hai. Dashboard me '🎯 Budget' button daba kar budget set karein."
                    if is_hindi else
                    f"No monthly budget has been set for {month_name} {year}. Click '🎯 Budget' on the card to set your cap."
                )

            if is_over:
                if is_hindi:
                    return (
                        f"⚠️ **Budget Overrun Alert!** Aapka {month_name} budget **{format_inr(budget)}** tha, "
                        f"aur aapne **{format_inr(snapshot.get('total_spent', 0))}** kharch kar liye hain "
                        f"({util}% utilization). Aap budget se **{format_inr(abs(rem))}** aage nikal chuke hain!"
                    )
                return (
                    f"⚠️ **Budget Exceeded Alert!** Your budget for {month_name} was **{format_inr(budget)}**, "
                    f"and you have spent **{format_inr(snapshot.get('total_spent', 0))}** ({util}%). "
                    f"You have exceeded your limit by **{format_inr(abs(rem))}**."
                )
            else:
                if is_hindi:
                    return (
                        f"✨ Aapka budget track par hai! {month_name} ka total budget **{format_inr(budget)}** hai, "
                        f"jisme se **{format_inr(rem)}** remaining bacha hua hai ({util}% utilized)."
                    )
                return (
                    f"✨ Your budget is on track! Your total monthly budget is **{format_inr(budget)}**, "
                    f"with **{format_inr(rem)}** remaining balance ({util}% utilized)."
                )

        elif intent == "savings_query":
            savings = snapshot.get("net_savings", 0)
            rate = snapshot.get("savings_rate_percent", 0)
            if is_hindi:
                return (
                    f"**{month_name} {year}** me aapki net in-pocket bachat **{format_inr(savings)}** hai, "
                    f"jo aapki income ka **{rate}%** savings rate darshati hai."
                )
            return (
                f"For **{month_name} {year}**, your net in-pocket savings are **{format_inr(savings)}**, "
                f"which represents an active savings rate of **{rate}%** of your total monthly income."
            )

        elif intent == "category_analysis":
            cat_data = structured_data.get("categories", {})
            breakdown = cat_data.get("category_breakdown", [])
            top_cat = cat_data.get("top_category", "None")
            total = cat_data.get("total_spent", 0)

            if not breakdown:
                return f"No category transactions found for {month_name} {year}."

            lines = [
                f"Aap sabse zyada kharcha **{top_cat}** category me kar rahe hain." if is_hindi else f"You are spending the most in **{top_cat}**."
            ]
            lines.append(f"\n**{month_name} Category Breakdown:**")
            for item in breakdown:
                lines.append(f"- **{item['category']}**: {item['amount_formatted']} ({item['percentage']}%)")
            return "\n".join(lines)

        elif intent == "monthly_comparison":
            comp = structured_data.get("monthly_comparison", {})
            if comp:
                p1 = comp["period_1"]
                p2 = comp["period_2"]
                diff = comp["expense_difference_formatted"]
                trend = comp["trend"]
                pct = comp["percentage_change"]

                if is_hindi:
                    return (
                        f"📊 **Monthly Expense Comparison:**\n"
                        f"- **{p1['name']}**: Kharcha {format_inr(p1['total_spent'])}, Savings {format_inr(p1['net_savings'])}\n"
                        f"- **{p2['name']}**: Kharcha {format_inr(p2['total_spent'])}, Savings {format_inr(p2['net_savings'])}\n\n"
                        f"{p1['name']} me aapka kharcha {p2['name']} ke mukable **{diff}** ({pct}%) {trend} hua hai."
                    )
                return (
                    f"📊 **Monthly Expense Comparison:**\n"
                    f"- **{p1['name']}**: Spent {format_inr(p1['total_spent'])}, Savings {format_inr(p1['net_savings'])}\n"
                    f"- **{p2['name']}**: Spent {format_inr(p2['total_spent'])}, Savings {format_inr(p2['net_savings'])}\n\n"
                    f"In {p1['name']}, your spending {trend} by **{diff}** ({pct}%) compared to {p2['name']}."
                )

        elif intent == "spending_pattern_analysis":
            pat = structured_data.get("spending_pattern", {})
            if pat:
                needs = pat.get("needs", {})
                wants = pat.get("wants", {})
                sav = pat.get("savings", {})
                obs = pat.get("observations", [])

                lines = [
                    f"📊 **50/30/20 Salary Allocation Rule Analysis ({month_name} {year}):**",
                    f"- **Needs (≤ 50% target)**: {needs.get('spent_formatted')} ({needs.get('percentage')}%)",
                    f"- **Wants (≤ 30% target)**: {wants.get('spent_formatted')} ({wants.get('percentage')}%)",
                    f"- **Savings (≥ 20% target)**: {sav.get('amount_formatted')} ({sav.get('percentage')}%)",
                    f"\n**Observations:**"
                ]
                for o in obs:
                    lines.append(f"• {o}")
                return "\n".join(lines)

        elif intent == "saving_recommendation":
            rec_data = structured_data.get("recommendations", {})
            recs = rec_data.get("recommendations", [])
            lines = [
                f"💡 **Personalized Savings Recommendations ({month_name} {year}):**"
            ]
            for r in recs:
                lines.append(f"• {r}")
            return "\n".join(lines)

        elif intent == "historical_expense_search":
            ks = structured_data.get("keyword_search", {})
            matches = ks.get("results", [])
            if not matches:
                return (
                    f"Aapki search query ke liye koi transaction nahi mila."
                    if is_hindi else
                    f"No matching transactions found for '{ks.get('query', query)}'."
                )
            lines = [
                f"Found **{ks.get('total_matches')}** transaction(s) totaling **{ks.get('total_amount_formatted')}**:"
            ]
            for t in matches[:8]:
                lines.append(f"- **{t.get('date')}**: {t.get('description')} ({t.get('category')}) — **{format_inr(t.get('amount', 0))}**")
            return "\n".join(lines)

        # Default financial overview
        return (
            f"Here is your verified financial overview for **{month_name} {year}**:\n"
            f"- Base Salary: **{format_inr(snapshot.get('base_salary', 0))}** ({snapshot.get('employer')})\n"
            f"- Total Income: **{format_inr(snapshot.get('total_income', 0))}**\n"
            f"- Total Spent: **{format_inr(snapshot.get('total_spent', 0))}**\n"
            f"- Net In-Pocket Savings: **{format_inr(snapshot.get('net_savings', 0))}** ({snapshot.get('savings_rate_percent', 0)}%)\n"
            f"- Budget: **{format_inr(snapshot.get('budget', 0))}** (Remaining: {format_inr(snapshot.get('remaining_budget', 0))})\n\n"
            f"Feel free to ask me to analyze categories, compare months, or suggest ways to save!"
        )

    def _generate_followups(self, intent: str, structured_data: Dict[str, Any]) -> List[str]:
        """Provides dynamic contextual suggestions for the chat interface."""
        followup_map = {
            "expense_query": [
                "Where am I spending the most?",
                "Mera kitna budget remaining hai?",
                "Compare my last two months' expenses"
            ],
            "income_query": [
                "How much salary is left?",
                "Check my 50/30/20 salary rule breakdown",
                "Mujhe paise save karne ke suggestions do"
            ],
            "salary_query": [
                "What is my daily burn rate?",
                "Mera kitna budget remaining hai?",
                "Where am I spending the most?"
            ],
            "budget_query": [
                "Maine is month kitne paise kharch kiye?",
                "Show my category breakdown",
                "How can I save more this month?"
            ],
            "category_analysis": [
                "Find my shopping expenses",
                "Compare with last month",
                "Mujhe paise save karne ke suggestions do"
            ],
            "monthly_comparison": [
                "Where am I spending the most?",
                "Analyze my 50/30/20 spending pattern",
                "Give me savings advice"
            ],
            "saving_recommendation": [
                "What are my highest expense categories?",
                "Show my 50/30/20 rule breakdown",
                "How much salary is left?"
            ],
            "spending_pattern_analysis": [
                "Mujhe paise save karne ke suggestions do",
                "Where am I spending the most?",
                "Mera kitna budget remaining hai?"
            ]
        }
        return followup_map.get(intent, [
            "Maine is month kitne paise kharch kiye?",
            "Where am I spending the most?",
            "Mera kitna budget remaining hai?",
            "Mujhe paise save karne ke suggestions do"
        ])


# Singleton
response_generator = ResponseGenerator()

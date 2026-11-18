"""
Intent Detection Module.
Classifies natural language user queries (in English, Hindi, and Hinglish)
into one of the 12 supported financial intents.
"""
import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

from schemas.state import IntentEnum

logger = logging.getLogger("ai_controller.intent")


class IntentDetector:
    """Detects user financial intents with comprehensive multi-lingual and Hinglish support."""

    # Hinglish & English Pattern Rule sets
    PATTERNS: Dict[IntentEnum, List[str]] = {
        IntentEnum.EXPENSE_QUERY: [
            r"kharch", r"kharcha", r"kitne.*paise.*kharch", r"spend", r"spent", r"spending",
            r"expenses?", r"total.*kharcha", r"how much did i spend", r"how much have i spent",
            r"what did i spend", r"kitna kharcha hua", r"total expense", r"kitna kharch kiya"
        ],
        IntentEnum.INCOME_QUERY: [
            r"income", r"kamai", r"credits?", r"aamdani", r"inflow", r"bonus", r"freelance",
            r"kitni income", r"paise aaye", r"total income", r"earnings?"
        ],
        IntentEnum.SALARY_QUERY: [
            r"salary", r"tankhwah", r"tanha", r"paycheck", r"in-?hand", r"employer",
            r"salary left", r"salary bachi", r"kitni salary", r"salary remaining",
            r"take[- ]home", r"payday"
        ],
        IntentEnum.BUDGET_QUERY: [
            r"budget", r"remaining.*budget", r"budget.*remaining", r"budget.*left",
            r"budget bacha", r"kitna budget", r"over[- ]budget", r"budget limit",
            r"budget cap", r"budget khatam"
        ],
        IntentEnum.SAVINGS_QUERY: [
            r"savings?", r"bachat", r"kitne.*bachaye", r"how much.*saved",
            r"net savings", r"savings rate", r"paise bache", r"kitna bacha",
            r"retained", r"savings percentage"
        ],
        IntentEnum.CATEGORY_ANALYSIS: [
            r"where am i spending the most", r"sabse jyada kharcha", r"sabse zyada",
            r"highest expense", r"top category", r"breakdown", r"categories",
            r"food.*kharch", r"travel.*kharch", r"shopping.*kharch", r"category-wise",
            r"kis cheez me", r"kis category"
        ],
        IntentEnum.MONTHLY_COMPARISON: [
            r"compare", r"comparison", r"pichle mahine se", r"last month vs",
            r"previous month", r"two months", r"month over month", r"tula",
            r"difference between", r"pichle do mahine", r"last 2 months"
        ],
        IntentEnum.HISTORICAL_EXPENSE_SEARCH: [
            r"find", r"search", r"dhundho", r"khojo", r"uber", r"swiggy", r"zomato",
            r"rent", r"travel[- ]related", r"transactions? for", r"show me all",
            r"cinema", r"grocery", r"headphones?", r"artisan"
        ],
        IntentEnum.SPENDING_PATTERN_ANALYSIS: [
            r"pattern", r"50[\s/-]?30[\s/-]?20", r"fifty thirty twenty", r"needs vs wants",
            r"needs", r"wants", r"lifestyle", r"burn rate", r"daily average",
            r"spending habits?", r"kaha ud rahe paise"
        ],
        IntentEnum.SAVING_RECOMMENDATION: [
            r"suggest", r"recommend", r"tips?", r"advice", r"salah", r"kaise bacha",
            r"how can i save", r"paise save karne", r"save more", r"reduce expenses",
            r"kharcha kam kaise kare", r"guidance"
        ],
        IntentEnum.FINANCIAL_SUMMARY: [
            r"summary", r"overview", r"report", r"dashboard", r"paisa kaisa raha",
            r"financial health", r"complete overview", r"sab kuch dikhao",
            r"overall summary", r"monthly status"
        ],
        IntentEnum.GENERAL_FINANCIAL_QUESTION: [
            r"what is", r"how does", r"explain", r"kya hota hai", r"investment advice",
            r"mutual fund", r"tax", r"emergency fund"
        ]
    }

    MONTH_PATTERNS = {
        0: [r"january", r"jan", r"janwary"],
        1: [r"february", r"feb", r"farvari"],
        2: [r"march", r"mar"],
        3: [r"april", r"apr"],
        4: [r"may", r"mai"],
        5: [r"june", r"jun"],
        6: [r"july", r"jul"],
        7: [r"august", r"aug", r"agast"],
        8: [r"september", r"sep", r"sept"],
        9: [r"october", r"oct", r"sitambar", r"aktubar"],
        10: [r"november", r"nov"],
        11: [r"december", r"dec", r"disambar"]
    }

    @classmethod
    def detect_intent(cls, query: str) -> Tuple[IntentEnum, float]:
        """
        Detects primary intent from query string.
        Returns: (IntentEnum, confidence: float 0.0 - 1.0)
        """
        clean_q = query.lower().strip()
        scores: Dict[IntentEnum, int] = {intent: 0 for intent in IntentEnum}

        # Priority checks for high specificity
        if any(re.search(p, clean_q) for p in [r"50[\s/-]?30[\s/-]?20", r"fifty thirty twenty", r"needs.*wants", r"pattern"]):
            return IntentEnum.SPENDING_PATTERN_ANALYSIS, 0.95

        if any(re.search(p, clean_q) for p in [r"compare", r"comparison", r"difference between", r"pichle mahine se", r"last.*months?"]):
            return IntentEnum.MONTHLY_COMPARISON, 0.95

        if any(re.search(p, clean_q) for p in [r"category", r"breakdown", r"where am i spending", r"sabse j[y|z]ada", r"highest expense", r"top category"]):
            return IntentEnum.CATEGORY_ANALYSIS, 0.95

        if any(re.search(p, clean_q) for p in [r"suggest", r"recommend", r"tips?", r"kaise bacha", r"save karne ke"]):
            return IntentEnum.SAVING_RECOMMENDATION, 0.95

        if any(re.search(p, clean_q) for p in [r"find", r"search", r"dhundho", r"travel-related", r"expenses? on"]):
            return IntentEnum.HISTORICAL_EXPENSE_SEARCH, 0.90

        if any(re.search(p, clean_q) for p in [r"budget.*remaining", r"remaining.*budget", r"kitna budget"]):
            return IntentEnum.BUDGET_QUERY, 0.95

        if any(re.search(p, clean_q) for p in [r"salary.*left", r"kitni salary", r"tankhwah"]):
            return IntentEnum.SALARY_QUERY, 0.95

        if any(re.search(p, clean_q) for p in [r"summary", r"overview", r"report", r"sab kuch dikhao"]):
            return IntentEnum.FINANCIAL_SUMMARY, 0.90

        # Pattern scoring
        for intent, patterns in cls.PATTERNS.items():
            for pat in patterns:
                if re.search(pat, clean_q):
                    scores[intent] += 1

        best_intent = max(scores, key=scores.get)
        max_score = scores[best_intent]

        if max_score > 0:
            confidence = min(0.9, 0.6 + (max_score * 0.1))
            return best_intent, confidence

        # Default fallback
        if any(word in clean_q for word in ["rupee", "rs", "inr", "paisa", "paise", "cost", "bill"]):
            return IntentEnum.EXPENSE_QUERY, 0.60

        return IntentEnum.GENERAL_FINANCIAL_QUESTION, 0.50

    @classmethod
    def extract_month_and_year(cls, query: str) -> Tuple[Optional[int], Optional[int]]:
        """
        Extracts mentioned month (0-11 index) and 4-digit year from query string.
        Also parses 'this month' (is mahine), 'last month' (pichle mahine).
        """
        clean_q = query.lower()
        now = datetime.now()
        detected_month = None
        detected_year = None

        # Year check
        year_match = re.search(r"\b(202[0-9])\b", clean_q)
        if year_match:
            detected_year = int(year_match.group(1))

        # Relative month check
        if any(re.search(p, clean_q) for p in [r"last month", r"pichle mahine", r"previous month"]):
            curr_m = now.month - 1
            if curr_m == 0:
                detected_month = 11
                detected_year = (detected_year or now.year) - 1
            else:
                detected_month = curr_m - 1
                detected_year = detected_year or now.year
            return detected_month, detected_year

        if any(re.search(p, clean_q) for p in [r"this month", r"is mahine", r"current month"]):
            return now.month - 1, (detected_year or now.year)

        # Explicit month check
        for m_idx, pats in cls.MONTH_PATTERNS.items():
            for p in pats:
                if re.search(rf"\b{p}\b", clean_q):
                    detected_month = m_idx
                    break
            if detected_month is not None:
                break

        return detected_month, detected_year


# Singleton
intent_detector = IntentDetector()

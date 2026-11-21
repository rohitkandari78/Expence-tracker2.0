"""
Pydantic Schemas for Request/Response validation and Agent State.
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum


class IntentEnum(str, Enum):
    EXPENSE_QUERY = "expense_query"
    INCOME_QUERY = "income_query"
    SALARY_QUERY = "salary_query"
    BUDGET_QUERY = "budget_query"
    SAVINGS_QUERY = "savings_query"
    CATEGORY_ANALYSIS = "category_analysis"
    MONTHLY_COMPARISON = "monthly_comparison"
    HISTORICAL_EXPENSE_SEARCH = "historical_expense_search"
    SPENDING_PATTERN_ANALYSIS = "spending_pattern_analysis"
    SAVING_RECOMMENDATION = "saving_recommendation"
    FINANCIAL_SUMMARY = "financial_summary"
    GENERAL_FINANCIAL_QUESTION = "general_financial_question"


class ChatRequest(BaseModel):
    """
    Incoming chat message request.
    Notice: NO user_id field is allowed in the body to enforce strict token-derived UID.
    """
    message: str = Field(..., min_length=1, max_length=2000, description="Natural language question from user")
    month: Optional[int] = Field(None, ge=0, le=11, description="Optional target month index (0=Jan ... 11=Dec)")
    year: Optional[int] = Field(None, ge=2000, le=2100, description="Optional target year")


class ChatResponse(BaseModel):
    """Standardized response schema returned by POST /chat."""
    success: bool = True
    intent: str
    answer: str
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    data: Dict[str, Any] = Field(default_factory=dict)
    suggested_followups: Optional[List[str]] = Field(default_factory=list)


class ReindexResponse(BaseModel):
    """Response returned by POST /rag/reindex or /rag/index."""
    success: bool
    indexed_count: int
    user_id: str
    message: str


class FiftyThirtyTwentyBreakdown(BaseModel):
    needs_spent: float
    needs_percentage: float
    wants_spent: float
    wants_percentage: float
    savings_amount: float
    savings_percentage: float
    status: str


class FinancialSummaryResponse(BaseModel):
    """Response schema for GET /user/financial-summary."""
    user_id: str
    user_name: Optional[str] = None
    month: int
    year: int
    month_name: str
    base_salary: float
    total_income: float
    total_spent: float
    net_savings: float
    savings_rate: float
    budget: float
    remaining_budget: float
    budget_utilization_percent: float
    category_breakdown: Dict[str, float]
    fifty_thirty_twenty: FiftyThirtyTwentyBreakdown
    transaction_count: int


class AgentState(BaseModel):
    """Internal state tracked across agent orchestration steps."""
    user_id: str
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    query: str
    month: Optional[int] = None
    year: Optional[int] = None
    detected_intent: Optional[str] = None
    intent_confidence: float = 1.0
    selected_tools: List[str] = Field(default_factory=list)
    structured_data: Dict[str, Any] = Field(default_factory=dict)
    semantic_context: List[Dict[str, Any]] = Field(default_factory=list)
    combined_context: str = ""
    final_answer: Optional[str] = None
    error: Optional[str] = None

"""
Agent Workflow and Orchestration Graph.
Coordinates intent detection, tool selection, hybrid retrieval, and grounded response generation.
"""
import logging
from typing import Dict, List, Optional, Any

from schemas.state import AgentState, IntentEnum
from intent import intent_detector
from retriever import hybrid_retriever
from response_generator import response_generator

logger = logging.getLogger("ai_controller.graph")


# Tool mapping based on intent
INTENT_TOOL_MAPPING: Dict[str, List[str]] = {
    IntentEnum.EXPENSE_QUERY.value: ["expense_retrieval_tool", "category_analysis_tool"],
    IntentEnum.INCOME_QUERY.value: ["income_retrieval_tool", "salary_analysis_tool"],
    IntentEnum.SALARY_QUERY.value: ["salary_analysis_tool", "income_retrieval_tool"],
    IntentEnum.BUDGET_QUERY.value: ["budget_calculator_tool", "expense_retrieval_tool"],
    IntentEnum.SAVINGS_QUERY.value: ["spending_pattern_analyzer", "salary_analysis_tool"],
    IntentEnum.CATEGORY_ANALYSIS.value: ["category_analysis_tool", "expense_retrieval_tool"],
    IntentEnum.MONTHLY_COMPARISON.value: ["monthly_comparison_tool"],
    IntentEnum.HISTORICAL_EXPENSE_SEARCH.value: ["historical_transaction_search_tool"],
    IntentEnum.SPENDING_PATTERN_ANALYSIS.value: ["spending_pattern_analyzer", "salary_analysis_tool"],
    IntentEnum.SAVING_RECOMMENDATION.value: ["savings_recommendation_tool", "spending_pattern_analyzer", "category_analysis_tool"],
    IntentEnum.FINANCIAL_SUMMARY.value: ["financial_summary"],
    IntentEnum.GENERAL_FINANCIAL_QUESTION.value: ["spending_pattern_analyzer"]
}


class AgentWorkflow:
    """Orchestrates the multi-stage RAG financial agent pipeline."""

    def __init__(self):
        self.intent_detector = intent_detector
        self.retriever = hybrid_retriever
        self.generator = response_generator

    def execute(self, state: AgentState) -> AgentState:
        """
        Executes sequential state graph transitions:
        Intent Detection -> Tool Selection -> Hybrid Retrieval -> Grounded Response Generation.
        """
        try:
            # 1. Intent Detection Node
            state = self._detect_intent(state)

            # 2. Tool Selection Node
            state = self._select_tools(state)

            # 3. Context Retrieval Node
            state = self._retrieve_context(state)

            # 4. Response Generation Node
            state = self._generate_response(state)

            return state
        except Exception as e:
            logger.error(f"Error during agent workflow execution for user {state.user_id}: {e}", exc_info=True)
            state.error = str(e)
            state.final_answer = (
                "Sorry, an error occurred while processing your financial query. "
                "Please verify your query or try again shortly."
            )
            return state

    def _detect_intent(self, state: AgentState) -> AgentState:
        """Step 1: Detect Intent and Month/Year."""
        intent, confidence = self.intent_detector.detect_intent(state.query)
        detected_m, detected_y = self.intent_detector.extract_month_and_year(state.query)

        state.detected_intent = intent.value
        state.intent_confidence = confidence
        
        # Override month/year if explicitly passed or detected in natural language
        if state.month is None and detected_m is not None:
            state.month = detected_m
        if state.year is None and detected_y is not None:
            state.year = detected_y

        logger.info(f"Detected intent '{state.detected_intent}' (confidence: {state.intent_confidence}) for query: '{state.query}'")
        return state

    def _select_tools(self, state: AgentState) -> AgentState:
        """Step 2: Tool Selection."""
        tools = INTENT_TOOL_MAPPING.get(
            state.detected_intent, 
            ["expense_retrieval_tool", "salary_analysis_tool"]
        )
        state.selected_tools = tools
        logger.info(f"Selected tools: {tools}")
        return state

    def _retrieve_context(self, state: AgentState) -> AgentState:
        """Step 3: Execute Hybrid Retrieval."""
        retrieval_res = self.retriever.retrieve(
            uid=state.user_id,
            query=state.query,
            intent=state.detected_intent or "expense_query",
            month=state.month,
            year=state.year
        )
        state.structured_data = retrieval_res.get("structured_data", {})
        state.semantic_context = retrieval_res.get("semantic_matches", [])
        state.combined_context = retrieval_res.get("formatted_context", "")
        return state

    def _generate_response(self, state: AgentState) -> AgentState:
        """Step 4: Generate Grounded Answer."""
        retrieval_dict = {
            "structured_data": state.structured_data,
            "semantic_matches": state.semantic_context,
            "formatted_context": state.combined_context
        }
        answer, _ = self.generator.generate_response(
            query=state.query,
            intent=state.detected_intent or "general_financial_question",
            retrieval_result=retrieval_dict
        )
        state.final_answer = answer
        return state


# Singleton
agent_workflow = AgentWorkflow()

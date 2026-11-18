"""
FastAPI Router and Endpoint Controllers for AI Financial Assistant.
Enforces strict Firebase authentication on all financial operations.
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Header, Query, status

from config import settings
from schemas.state import (
    ChatRequest, 
    ChatResponse, 
    FinancialSummaryResponse, 
    ReindexResponse,
    AgentState
)
from firebase.firebase_service import firebase_service
from intent import intent_detector
from graph import agent_workflow
from rag import rag_pipeline
from tools import FinancialTools

logger = logging.getLogger("ai_controller.controller")

router = APIRouter()


async def get_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """
    FastAPI dependency that enforces Firebase token authentication.
    Extracts authenticated UID strictly from verified token.
    Never trusts client-supplied user IDs.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header. Firebase ID token required."
        )

    try:
        decoded_token = firebase_service.verify_token(authorization)
        uid = decoded_token.get("uid")
        if not uid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token does not contain a valid user ID."
            )
        return decoded_token
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected token verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed: Invalid credentials."
        )


@router.get("/health", summary="Service Health Check")
async def health_check():
    """Health check endpoint reporting API and component statuses."""
    return {
        "status": "healthy",
        "service": "AI Expense Tracker Controller",
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.utcnow().isoformat(),
        "gemini_configured": bool(settings.GEMINI_API_KEY),
        "firebase_project": settings.FIREBASE_PROJECT_ID
    }


@router.post("/chat", response_model=ChatResponse, summary="Natural Language Financial Chatbot")
async def chat_endpoint(
    request: ChatRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Core AI Chatbot endpoint:
    1. Authenticates via Firebase ID token.
    2. Extracts authenticated UID.
    3. Detects user intent (English, Hindi, Hinglish).
    4. Orchestrates financial calculation tools and hybrid RAG context.
    5. Generates grounded answer and contextual follow-ups.
    """
    uid = current_user["uid"]
    logger.info(f"Incoming chat from verified user {uid}: '{request.message}'")

    # Initial Agent State
    state = AgentState(
        user_id=uid,
        user_email=current_user.get("email"),
        user_name=current_user.get("name"),
        query=request.message,
        month=request.month,
        year=request.year
    )

    # Execute State Graph Workflow
    final_state = agent_workflow.execute(state)

    # Format sources for transparency
    sources = []
    for s in final_state.semantic_context:
        meta = s.get("metadata", {})
        sources.append({
            "type": meta.get("document_type", "transaction"),
            "transaction_id": meta.get("transaction_id"),
            "description": s.get("text"),
            "category": meta.get("category"),
            "date": meta.get("date"),
            "amount": meta.get("amount"),
            "relevance": s.get("similarity")
        })

    # Get follow-up suggestions
    _, followups = rag_pipeline.generator.generate_response(
        query=request.message,
        intent=final_state.detected_intent or "general_financial_question",
        retrieval_result={
            "structured_data": final_state.structured_data,
            "semantic_matches": final_state.semantic_context,
            "formatted_context": final_state.combined_context
        }
    )

    return ChatResponse(
        success=final_state.error is None,
        intent=final_state.detected_intent or "general_financial_question",
        answer=final_state.final_answer or "Unable to generate answer.",
        sources=sources,
        data=final_state.structured_data,
        suggested_followups=followups
    )


@router.post("/rag/index", response_model=ReindexResponse, summary="Index User Transactions")
@router.post("/rag/reindex", response_model=ReindexResponse, summary="Reindex User Transactions")
async def reindex_endpoint(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Indexes or reindexes all transactions for the authenticated user from Cloud Firestore into ChromaDB.
    Enforces user isolation and clears stale entries.
    """
    uid = current_user["uid"]
    logger.info(f"Re-indexing vectorstore for user {uid}")
    
    count = rag_pipeline.index_user_data(uid)
    return ReindexResponse(
        success=True,
        indexed_count=count,
        user_id=uid,
        message=f"Successfully indexed {count} transaction records into ChromaDB vectorstore."
    )


@router.get("/user/financial-summary", response_model=FinancialSummaryResponse, summary="Get Monthly Financial Summary")
async def get_financial_summary(
    month: Optional[int] = Query(None, ge=0, le=11, description="Month index (0=Jan, 11=Dec)"),
    year: Optional[int] = Query(None, ge=2000, le=2100, description="4-digit year"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Returns verified monthly financial metrics, 50/30/20 breakdown, and budget utilization
    strictly for the authenticated user.
    """
    uid = current_user["uid"]
    summary_dict = FinancialTools.financial_summary(uid=uid, month=month, year=year)
    return FinancialSummaryResponse(**summary_dict)

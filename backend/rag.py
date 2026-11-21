"""
RAG Pipeline Interface.
Provides unified indexing, querying, and retrieval augmentation methods.
"""
import logging
from typing import Dict, List, Optional, Any, Tuple

from firebase.firebase_service import firebase_service
from vectorstore.vector_store import vector_store
from retriever import hybrid_retriever
from response_generator import response_generator

logger = logging.getLogger("ai_controller.rag")


class RAGPipeline:
    """High-level facade for RAG indexing and hybrid generation."""

    def __init__(self):
        self.firebase = firebase_service
        self.vector_store = vector_store
        self.retriever = hybrid_retriever
        self.generator = response_generator

    def index_user_data(self, uid: str) -> int:
        """
        Indexes all current transactions for the authenticated user from Cloud Firestore into ChromaDB.
        Strictly scopes data to users/{uid}/expenses.
        """
        if not uid:
            raise ValueError("UID required for indexing")

        transactions = self.firebase.get_all_user_transactions_for_indexing(uid)
        count = self.vector_store.reindex_user_data(uid, transactions)
        logger.info(f"Indexed {count} transactions for user {uid}")
        return count

    def generate_rag_response(
        self,
        uid: str,
        query: str,
        intent: str,
        month: Optional[int] = None,
        year: Optional[int] = None
    ) -> Tuple[str, Dict[str, Any], List[Dict[str, Any]], List[str]]:
        """
        Executes hybrid retrieval and generates a grounded response.
        Returns: (answer, structured_data, sources, suggested_followups)
        """
        retrieval_res = self.retriever.retrieve(
            uid=uid,
            query=query,
            intent=intent,
            month=month,
            year=year
        )

        answer, followups = self.generator.generate_response(
            query=query,
            intent=intent,
            retrieval_result=retrieval_res
        )

        sources = retrieval_res.get("semantic_matches", [])
        structured_data = retrieval_res.get("structured_data", {})

        return answer, structured_data, sources, followups


# Singleton
rag_pipeline = RAGPipeline()

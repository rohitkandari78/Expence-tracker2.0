"""
ChromaDB Vector Store Management.
Handles document creation, embedding, indexing, metadata filtering, and semantic search.
Strictly isolates records per user_id.
"""
import os
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.utils import embedding_functions

from config import settings

logger = logging.getLogger("ai_controller.vectorstore")


class DummyEmbeddingFunction(embedding_functions.EmbeddingFunction):
    """Fast deterministic offline embedding function for testing and fallback."""
    def __call__(self, input: chromadb.Documents) -> chromadb.Embeddings:
        embeddings = []
        for text in input:
            # Deterministic pseudo-embedding based on hash
            h = hash(text)
            vec = [((h >> (i % 30)) & 0xFF) / 255.0 for i in range(384)]
            embeddings.append(vec)
        return embeddings


class VectorStoreService:
    """Service encapsulating ChromaDB operations for semantic transaction retrieval."""

    def __init__(self):
        persist_path = Path(settings.CHROMA_PERSIST_DIRECTORY)
        if not persist_path.is_absolute():
            persist_path = Path(__file__).resolve().parent.parent / persist_path
        self.persist_dir = str(persist_path.resolve())
        self.client = None
        self.collection = None
        self.embedding_fn = None

    def _ensure_initialized(self):
        """Initializes ChromaDB PersistentClient and Embedding Function lazily."""
        if self.client is not None and self.collection is not None:
            return

        try:
            os.makedirs(self.persist_dir, exist_ok=True)
            os.environ["ANONYMIZED_TELEMETRY"] = "False"
            os.environ["CHROMA_TELEMETRY"] = "False"

            self.client = chromadb.PersistentClient(
                path=self.persist_dir,
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    is_persistent=True
                )
            )

            # Fast, memory-efficient embedding configuration (optimized for cloud & 512MB RAM)
            if settings.ENVIRONMENT == "test":
                self.embedding_fn = DummyEmbeddingFunction()
            elif settings.GEMINI_API_KEY:
                try:
                    self.embedding_fn = embedding_functions.GoogleGenerativeAiEmbeddingFunction(
                        api_key=settings.GEMINI_API_KEY
                    )
                    logger.info("Using Google Gemini Generative AI Embedding Function")
                except Exception as g_err:
                    logger.warning(f"Could not load Gemini Embedding ({g_err}), falling back to default")
                    self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()
            else:
                try:
                    self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()
                    logger.info("Using ChromaDB DefaultEmbeddingFunction (ONNX runtime, low memory)")
                except Exception as onnx_err:
                    logger.warning(f"Could not load ONNX embedding ({onnx_err}), using DummyEmbeddingFunction fallback")
                    self.embedding_fn = DummyEmbeddingFunction()

            self.collection = self.client.get_or_create_collection(
                name="user_financial_context",
                embedding_function=self.embedding_fn,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info("ChromaDB initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing ChromaDB: {e}")
            raise

    @staticmethod
    def _format_document_text(tx: Dict[str, Any]) -> str:
        """Creates rich semantic textual representation of a transaction."""
        desc = tx.get("description", "Unnamed Transaction")
        cat = tx.get("category", "General")
        amt = tx.get("amount", 0)
        dt = tx.get("date", "Unknown date")
        tx_type = tx.get("type", "expense")
        split_with = tx.get("splitWith", [])
        
        split_info = f" Split with: {', '.join(split_with)}." if split_with else ""
        return (
            f"Transaction: {desc}. "
            f"Category: {cat}. "
            f"Amount: ₹{amt}. "
            f"Date: {dt}. "
            f"Type: {tx_type}.{split_info}"
        )

    def index_transaction(self, uid: str, tx: Dict[str, Any]) -> None:
        """
        Indexes a single transaction into ChromaDB with user_id metadata filtering.
        """
        if not uid or not tx:
            return

        self._ensure_initialized()
        tx_id = tx.get("id")
        if not tx_id:
            return

        doc_id = f"{uid}_{tx_id}"
        document_text = self._format_document_text(tx)
        
        metadata = {
            "user_id": str(uid),
            "transaction_id": str(tx_id),
            "category": str(tx.get("category", "")),
            "date": str(tx.get("date", "")),
            "type": str(tx.get("type", "expense")),
            "amount": float(tx.get("amount", 0)),
            "document_type": "transaction"
        }

        self.collection.upsert(
            ids=[doc_id],
            documents=[document_text],
            metadatas=[metadata]
        )
        logger.debug(f"Indexed transaction {doc_id} for user {uid}")

    def delete_transaction(self, uid: str, tx_id: str) -> None:
        """Deletes a transaction document from ChromaDB."""
        self._ensure_initialized()
        doc_id = f"{uid}_{tx_id}"
        try:
            self.collection.delete(ids=[doc_id])
            logger.debug(f"Deleted vector doc {doc_id}")
        except Exception as e:
            logger.warning(f"Failed deleting vector doc {doc_id}: {e}")

    def reindex_user_data(self, uid: str, transactions: List[Dict[str, Any]]) -> int:
        """
        Clears existing records for the authenticated user and re-indexes all transactions.
        Ensures zero stale or duplicate entries.
        """
        if not uid:
            raise ValueError("UID required")

        self._ensure_initialized()
        # 1. Delete all existing records for this user
        try:
            self.collection.delete(where={"user_id": uid})
        except Exception as e:
            logger.warning(f"Note on clearing existing index for {uid}: {e}")

        if not transactions:
            return 0

        # 2. Batch prepare documents
        ids = []
        documents = []
        metadatas = []

        for tx in transactions:
            tx_id = tx.get("id")
            if not tx_id:
                continue

            doc_id = f"{uid}_{tx_id}"
            ids.append(doc_id)
            documents.append(self._format_document_text(tx))
            metadatas.append({
                "user_id": str(uid),
                "transaction_id": str(tx_id),
                "category": str(tx.get("category", "")),
                "date": str(tx.get("date", "")),
                "type": str(tx.get("type", "expense")),
                "amount": float(tx.get("amount", 0)),
                "document_type": "transaction"
            })

        # Chroma upsert in batches of 100
        batch_size = 100
        for i in range(0, len(ids), batch_size):
            self.collection.upsert(
                ids=ids[i:i + batch_size],
                documents=documents[i:i + batch_size],
                metadatas=metadatas[i:i + batch_size]
            )

        logger.info(f"Successfully reindexed {len(ids)} transactions for user {uid}")
        return len(ids)

    def search_similar(
        self, 
        uid: str, 
        query: str, 
        limit: int = 5,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Performs semantic similarity search restricted strictly to user_id.
        Returns list of matched documents with metadata and relevance scores.
        """
        if not uid or not query.strip():
            return []

        self._ensure_initialized()

        where_filter: Dict[str, Any] = {"user_id": uid}
        if category:
            where_filter = {
                "$and": [
                    {"user_id": uid},
                    {"category": category}
                ]
            }

        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=limit,
                where=where_filter
            )

            matched_docs = []
            if results and results.get("documents") and results["documents"][0]:
                docs = results["documents"][0]
                metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)
                dists = results["distances"][0] if results.get("distances") else [0.0] * len(docs)
                ids = results["ids"][0] if results.get("ids") else [""] * len(docs)

                for doc, meta, dist, doc_id in zip(docs, metas, dists, ids):
                    # cosine distance to similarity score
                    sim_score = max(0.0, 1.0 - dist) if dist is not None else 1.0
                    matched_docs.append({
                        "id": doc_id,
                        "text": doc,
                        "metadata": meta,
                        "similarity": round(sim_score, 3)
                    })

            return matched_docs
        except Exception as e:
            logger.error(f"Semantic search error for user {uid}: {e}")
            return []


# Singleton
vector_store = VectorStoreService()

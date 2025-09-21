"""Hybrid retrieval system combining dense and sparse search"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union
from rank_bm25 import BM25Okapi
import logging
from rich.console import Console

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from rag.embeddings.local_embedder import LocalEmbedder
from rag.vectorstore.faiss_store import FAISSVectorStore

console = Console()
logger = logging.getLogger(__name__)

class HybridRetriever:
    """Hybrid retrieval combining dense embeddings and BM25 sparse search"""

    def __init__(
        self,
        embedder: LocalEmbedder,
        vector_store: FAISSVectorStore,
        alpha: float = 0.6,  # Weight for dense retrieval (1-alpha for sparse)
        bm25_k1: float = 1.5,
        bm25_b: float = 0.75
    ):
        self.embedder = embedder
        self.vector_store = vector_store
        self.alpha = alpha
        self.bm25_k1 = bm25_k1
        self.bm25_b = bm25_b

        # BM25 index
        self.bm25 = None
        self.documents = []
        self.metadata = []

        console.print(f"[green]Hybrid retriever initialized (α={alpha})[/green]")

    def index_documents(
        self,
        documents: List[str],
        embeddings: Optional[np.ndarray] = None,
        metadata: Optional[List[Dict[str, Any]]] = None
    ):
        """Index documents for both dense and sparse retrieval"""

        self.documents = documents
        self.metadata = metadata or [{} for _ in documents]

        # Index in vector store
        if embeddings is None:
            console.print("[yellow]Computing embeddings for documents...[/yellow]")
            embeddings = self.embedder.encode_batch(documents)

        self.vector_store.add_documents(embeddings, documents, metadata)

        # Build BM25 index
        console.print("[yellow]Building BM25 index...[/yellow]")
        tokenized_docs = [doc.lower().split() for doc in documents]
        self.bm25 = BM25Okapi(
            tokenized_docs,
            k1=self.bm25_k1,
            b=self.bm25_b
        )

        console.print(f"[green]Indexed {len(documents)} documents for hybrid retrieval[/green]")

    def search(
        self,
        query: str,
        top_k: int = 10,
        dense_weight: Optional[float] = None,
        return_scores: bool = True,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Perform hybrid search combining dense and sparse retrieval"""

        if not self.documents:
            return []

        alpha = dense_weight if dense_weight is not None else self.alpha

        # Dense retrieval
        query_embedding = self.embedder.encode_query(query)
        dense_results = self.vector_store.search(
            query_embedding,
            top_k=min(top_k * 2, len(self.documents))  # Get more candidates
        )

        # Sparse retrieval (BM25)
        tokenized_query = query.lower().split()
        bm25_scores = self.bm25.get_scores(tokenized_query)

        # Normalize scores
        dense_scores = self._normalize_scores([r["score"] for r in dense_results])
        bm25_scores = self._normalize_scores(bm25_scores)

        # Combine scores
        combined_scores = {}

        # Add dense scores
        for i, result in enumerate(dense_results):
            doc_idx = result["index"]
            combined_scores[doc_idx] = alpha * dense_scores[i]

        # Add sparse scores
        for doc_idx, bm25_score in enumerate(bm25_scores):
            if doc_idx in combined_scores:
                combined_scores[doc_idx] += (1 - alpha) * bm25_score
            else:
                combined_scores[doc_idx] = (1 - alpha) * bm25_score

        # Sort by combined score
        sorted_results = sorted(
            combined_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_k]

        # Build final results
        final_results = []
        for doc_idx, combined_score in sorted_results:
            # Apply metadata filtering if specified
            if filter_metadata:
                doc_metadata = self.metadata[doc_idx]
                if not self._matches_filter(doc_metadata, filter_metadata):
                    continue

            result = {
                "document": self.documents[doc_idx],
                "metadata": self.metadata[doc_idx],
                "index": doc_idx,
                "combined_score": float(combined_score)
            }

            if return_scores:
                # Include individual scores
                dense_score = 0.0
                for dense_result in dense_results:
                    if dense_result["index"] == doc_idx:
                        dense_score = dense_result["score"]
                        break

                result.update({
                    "dense_score": float(dense_score),
                    "bm25_score": float(bm25_scores[doc_idx]),
                    "alpha": alpha
                })

            final_results.append(result)

        return final_results

    def search_batch(
        self,
        queries: List[str],
        top_k: int = 10,
        dense_weight: Optional[float] = None
    ) -> List[List[Dict[str, Any]]]:
        """Perform batch hybrid search"""

        if not self.documents:
            return [[] for _ in queries]

        alpha = dense_weight if dense_weight is not None else self.alpha

        # Batch dense retrieval
        query_embeddings = self.embedder.encode_batch(queries)
        dense_batch_results = self.vector_store.search_batch(
            query_embeddings,
            top_k=min(top_k * 2, len(self.documents))
        )

        # Batch sparse retrieval
        bm25_batch_scores = []
        for query in queries:
            tokenized_query = query.lower().split()
            scores = self.bm25.get_scores(tokenized_query)
            bm25_batch_scores.append(scores)

        # Combine results for each query
        batch_results = []
        for i, (query, dense_results, bm25_scores) in enumerate(
            zip(queries, dense_batch_results, bm25_batch_scores)
        ):
            # Normalize scores
            dense_scores = self._normalize_scores([r["score"] for r in dense_results])
            bm25_scores = self._normalize_scores(bm25_scores)

            # Combine scores
            combined_scores = {}

            # Add dense scores
            for j, result in enumerate(dense_results):
                doc_idx = result["index"]
                combined_scores[doc_idx] = alpha * dense_scores[j]

            # Add sparse scores
            for doc_idx, bm25_score in enumerate(bm25_scores):
                if doc_idx in combined_scores:
                    combined_scores[doc_idx] += (1 - alpha) * bm25_score
                else:
                    combined_scores[doc_idx] = (1 - alpha) * bm25_score

            # Sort and format results
            sorted_results = sorted(
                combined_scores.items(),
                key=lambda x: x[1],
                reverse=True
            )[:top_k]

            query_results = []
            for doc_idx, combined_score in sorted_results:
                result = {
                    "document": self.documents[doc_idx],
                    "metadata": self.metadata[doc_idx],
                    "index": doc_idx,
                    "combined_score": float(combined_score),
                    "query_index": i
                }
                query_results.append(result)

            batch_results.append(query_results)

        return batch_results

    def update_weights(self, alpha: float):
        """Update the weighting between dense and sparse retrieval"""
        if not 0 <= alpha <= 1:
            raise ValueError("Alpha must be between 0 and 1")

        self.alpha = alpha
        console.print(f"[cyan]Updated hybrid weights: dense={alpha:.2f}, sparse={1-alpha:.2f}[/cyan]")

    def get_similar_documents(
        self,
        doc_index: int,
        top_k: int = 5,
        method: str = "dense"  # "dense", "sparse", or "hybrid"
    ) -> List[Dict[str, Any]]:
        """Find documents similar to a given document"""

        if doc_index >= len(self.documents):
            raise ValueError(f"Document index {doc_index} out of range")

        reference_doc = self.documents[doc_index]

        if method == "dense":
            # Use embedding similarity
            ref_embedding = self.embedder.encode_single(reference_doc)
            return self.vector_store.search(ref_embedding, top_k + 1)[1:]  # Exclude self

        elif method == "sparse":
            # Use BM25 similarity
            tokenized_doc = reference_doc.lower().split()
            scores = self.bm25.get_scores(tokenized_doc)

            # Get top-k excluding self
            sorted_indices = np.argsort(scores)[::-1]
            similar_indices = [idx for idx in sorted_indices if idx != doc_index][:top_k]

            results = []
            for idx in similar_indices:
                results.append({
                    "document": self.documents[idx],
                    "metadata": self.metadata[idx],
                    "index": idx,
                    "score": float(scores[idx])
                })

            return results

        elif method == "hybrid":
            # Use hybrid similarity
            return self.search(reference_doc, top_k + 1)[1:]  # Exclude self

        else:
            raise ValueError(f"Unknown method: {method}")

    def _normalize_scores(self, scores: List[float]) -> List[float]:
        """Normalize scores to 0-1 range using min-max normalization"""
        if len(scores) == 0:
            return []

        scores = np.array(scores)
        min_score = np.min(scores)
        max_score = np.max(scores)

        if max_score == min_score:
            return [0.5] * len(scores)

        normalized = (scores - min_score) / (max_score - min_score)
        return normalized.tolist()

    def _matches_filter(
        self,
        metadata: Dict[str, Any],
        filter_criteria: Dict[str, Any]
    ) -> bool:
        """Check if metadata matches filter criteria"""

        for key, value in filter_criteria.items():
            if key not in metadata:
                return False

            if isinstance(value, list):
                if metadata[key] not in value:
                    return False
            elif metadata[key] != value:
                return False

        return True

    def explain_ranking(
        self,
        query: str,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """Explain how ranking scores were computed"""

        results = self.search(query, top_k, return_scores=True)

        explanation = {
            "query": query,
            "alpha": self.alpha,
            "dense_weight": self.alpha,
            "sparse_weight": 1 - self.alpha,
            "results": []
        }

        for result in results:
            explanation["results"].append({
                "document_snippet": result["document"][:200] + "..." if len(result["document"]) > 200 else result["document"],
                "combined_score": result["combined_score"],
                "dense_score": result.get("dense_score", 0),
                "bm25_score": result.get("bm25_score", 0),
                "dense_contribution": result.get("dense_score", 0) * self.alpha,
                "sparse_contribution": result.get("bm25_score", 0) * (1 - self.alpha)
            })

        return explanation

    def get_stats(self) -> Dict[str, Any]:
        """Get retrieval system statistics"""
        return {
            "document_count": len(self.documents),
            "alpha": self.alpha,
            "bm25_k1": self.bm25_k1,
            "bm25_b": self.bm25_b,
            "has_bm25_index": self.bm25 is not None,
            "vector_store_stats": self.vector_store.get_stats()
        }
"""FAISS-based vector store implementation"""

import os
import json
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union
import numpy as np
import faiss
from rich.console import Console
import logging

console = Console()
logger = logging.getLogger(__name__)

class FAISSVectorStore:
    """FAISS-based vector store for efficient similarity search"""

    def __init__(
        self,
        embedding_dim: int,
        index_type: str = "IVF",
        metric: str = "L2",
        nlist: int = 4096,
        store_path: str = "data/index/faiss"
    ):
        self.embedding_dim = embedding_dim
        self.index_type = index_type
        self.metric = metric
        self.nlist = nlist
        self.store_path = Path(store_path)
        self.store_path.mkdir(parents=True, exist_ok=True)

        # Initialize FAISS index
        self.index = self._create_index()
        self.is_trained = False

        # Document storage
        self.documents = []
        self.metadata = []

        console.print(f"[green]FAISS vector store initialized (dim={embedding_dim}, type={index_type})[/green]")

    def _create_index(self) -> faiss.Index:
        """Create FAISS index based on configuration"""
        if self.index_type == "IVF":
            # Index with Inverted File structure for large datasets
            quantizer = faiss.IndexFlatL2(self.embedding_dim)
            if self.metric == "IP":  # Inner Product (cosine similarity)
                quantizer = faiss.IndexFlatIP(self.embedding_dim)

            index = faiss.IndexIVFFlat(quantizer, self.embedding_dim, self.nlist)
            index.nprobe = 16  # Number of clusters to search

        elif self.index_type == "HNSW":
            # Hierarchical Navigable Small World for fast approximate search
            index = faiss.IndexHNSWFlat(self.embedding_dim, 32)
            index.hnsw.efConstruction = 40
            index.hnsw.efSearch = 16

        elif self.index_type == "Flat":
            # Exact search (slower but perfect recall)
            if self.metric == "IP":
                index = faiss.IndexFlatIP(self.embedding_dim)
            else:
                index = faiss.IndexFlatL2(self.embedding_dim)

        else:
            raise ValueError(f"Unsupported index type: {self.index_type}")

        return index

    def add_documents(
        self,
        embeddings: np.ndarray,
        documents: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None
    ):
        """Add documents with their embeddings to the vector store"""
        if len(embeddings.shape) != 2:
            raise ValueError("Embeddings must be 2D array")

        if embeddings.shape[1] != self.embedding_dim:
            raise ValueError(f"Embedding dimension mismatch: expected {self.embedding_dim}, got {embeddings.shape[1]}")

        if len(embeddings) != len(documents):
            raise ValueError("Number of embeddings must match number of documents")

        # Normalize embeddings for cosine similarity if using IP metric
        if self.metric == "IP":
            embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)

        # Train index if needed
        if not self.is_trained and self.index_type == "IVF":
            # Need enough training points for clustering
            if len(embeddings) >= self.nlist:
                console.print("[yellow]Training FAISS index...[/yellow]")
                self.index.train(embeddings.astype(np.float32))
                self.is_trained = True
                console.print("[green]Index training completed[/green]")
            else:
                # Switch to flat index for small datasets
                console.print(f"[yellow]Dataset too small for IVF ({len(embeddings)} < {self.nlist}), switching to Flat index[/yellow]")
                if self.metric == "IP":
                    self.index = faiss.IndexFlatIP(self.embedding_dim)
                else:
                    self.index = faiss.IndexFlatL2(self.embedding_dim)
                self.index_type = "Flat"
                self.is_trained = True

        # Add embeddings to index
        start_id = len(self.documents)
        self.index.add(embeddings.astype(np.float32))

        # Store documents and metadata
        self.documents.extend(documents)
        if metadata:
            self.metadata.extend(metadata)
        else:
            self.metadata.extend([{} for _ in documents])

        console.print(f"[green]Added {len(documents)} documents to vector store (total: {len(self.documents)})[/green]")

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 10,
        score_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar documents"""
        if len(self.documents) == 0:
            return []

        if len(query_embedding.shape) == 1:
            query_embedding = query_embedding.reshape(1, -1)

        # Normalize query embedding for cosine similarity
        if self.metric == "IP":
            query_embedding = query_embedding / np.linalg.norm(query_embedding, axis=1, keepdims=True)

        # Perform search
        scores, indices = self.index.search(query_embedding.astype(np.float32), top_k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:  # FAISS returns -1 for invalid indices
                continue

            if score_threshold and score < score_threshold:
                continue

            result = {
                "document": self.documents[idx],
                "metadata": self.metadata[idx],
                "score": float(score),
                "index": int(idx)
            }
            results.append(result)

        return results

    def search_batch(
        self,
        query_embeddings: np.ndarray,
        top_k: int = 10,
        score_threshold: Optional[float] = None
    ) -> List[List[Dict[str, Any]]]:
        """Search for multiple queries at once"""
        if len(self.documents) == 0:
            return [[] for _ in range(len(query_embeddings))]

        # Normalize query embeddings for cosine similarity
        if self.metric == "IP":
            query_embeddings = query_embeddings / np.linalg.norm(query_embeddings, axis=1, keepdims=True)

        # Perform batch search
        scores, indices = self.index.search(query_embeddings.astype(np.float32), top_k)

        batch_results = []
        for query_scores, query_indices in zip(scores, indices):
            results = []
            for score, idx in zip(query_scores, query_indices):
                if idx == -1:
                    continue

                if score_threshold and score < score_threshold:
                    continue

                result = {
                    "document": self.documents[idx],
                    "metadata": self.metadata[idx],
                    "score": float(score),
                    "index": int(idx)
                }
                results.append(result)
            batch_results.append(results)

        return batch_results

    def get_document_by_id(self, doc_id: int) -> Optional[Dict[str, Any]]:
        """Get document by its ID"""
        if 0 <= doc_id < len(self.documents):
            return {
                "document": self.documents[doc_id],
                "metadata": self.metadata[doc_id],
                "index": doc_id
            }
        return None

    def update_metadata(self, doc_id: int, metadata: Dict[str, Any]):
        """Update metadata for a document"""
        if 0 <= doc_id < len(self.metadata):
            self.metadata[doc_id].update(metadata)

    def delete_documents(self, doc_ids: List[int]):
        """Remove documents (creates new index)"""
        # FAISS doesn't support deletion, so we rebuild the index
        console.print("[yellow]Rebuilding index after deletion...[/yellow]")

        # Get remaining documents
        remaining_docs = []
        remaining_metadata = []
        remaining_embeddings = []

        for i in range(len(self.documents)):
            if i not in doc_ids:
                remaining_docs.append(self.documents[i])
                remaining_metadata.append(self.metadata[i])

        if remaining_docs:
            # We need to re-extract embeddings (this is a limitation)
            console.print("[red]Warning: Document deletion requires re-embedding remaining documents[/red]")

        # Reset and rebuild
        self.index = self._create_index()
        self.is_trained = False
        self.documents = remaining_docs
        self.metadata = remaining_metadata

    def save(self, name: str = "default"):
        """Save the vector store to disk"""
        save_dir = self.store_path / name
        save_dir.mkdir(parents=True, exist_ok=True)

        # Save FAISS index
        index_path = save_dir / "index.faiss"
        faiss.write_index(self.index, str(index_path))

        # Save documents and metadata
        data = {
            "documents": self.documents,
            "metadata": self.metadata,
            "embedding_dim": self.embedding_dim,
            "index_type": self.index_type,
            "metric": self.metric,
            "nlist": self.nlist,
            "is_trained": self.is_trained
        }

        with open(save_dir / "store_data.pkl", "wb") as f:
            pickle.dump(data, f)

        # Save config
        config = {
            "embedding_dim": self.embedding_dim,
            "index_type": self.index_type,
            "metric": self.metric,
            "nlist": self.nlist,
            "document_count": len(self.documents)
        }

        with open(save_dir / "config.json", "w") as f:
            json.dump(config, f, indent=2)

        console.print(f"[green]Vector store saved to {save_dir}[/green]")

    def load(self, name: str = "default"):
        """Load vector store from disk"""
        load_dir = self.store_path / name

        if not load_dir.exists():
            raise FileNotFoundError(f"Vector store not found: {load_dir}")

        # Load FAISS index
        index_path = load_dir / "index.faiss"
        self.index = faiss.read_index(str(index_path))

        # Load documents and metadata
        with open(load_dir / "store_data.pkl", "rb") as f:
            data = pickle.load(f)

        self.documents = data["documents"]
        self.metadata = data["metadata"]
        self.embedding_dim = data["embedding_dim"]
        self.index_type = data["index_type"]
        self.metric = data["metric"]
        self.nlist = data["nlist"]
        self.is_trained = data["is_trained"]

        console.print(f"[green]Vector store loaded from {load_dir} ({len(self.documents)} documents)[/green]")

    def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics"""
        return {
            "document_count": len(self.documents),
            "embedding_dim": self.embedding_dim,
            "index_type": self.index_type,
            "metric": self.metric,
            "is_trained": self.is_trained,
            "index_size": self.index.ntotal if hasattr(self.index, "ntotal") else 0
        }

    def clear(self):
        """Clear all documents from the vector store"""
        self.index = self._create_index()
        self.is_trained = False
        self.documents = []
        self.metadata = []
        console.print("[yellow]Vector store cleared[/yellow]")
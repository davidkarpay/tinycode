"""Local embedding system using sentence-transformers"""

import os
import hashlib
import pickle
from pathlib import Path
from typing import List, Optional, Union, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer
from diskcache import Cache
import logging
from rich.console import Console

console = Console()
logger = logging.getLogger(__name__)

class LocalEmbedder:
    """Local embedding system for RAG with caching"""

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        cache_dir: str = "data/embeddings_cache",
        device: str = "cpu"
    ):
        self.model_name = model_name
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Initialize cache
        self.cache = Cache(str(self.cache_dir / "embeddings.cache"))

        # Load model
        console.print(f"[cyan]Loading embedding model: {model_name}[/cyan]")
        self.model = SentenceTransformer(model_name, device=device)
        self.embed_dim = self.model.get_sentence_embedding_dimension()

        console.print(f"[green]Embedding model loaded. Dimension: {self.embed_dim}[/green]")

    def _get_cache_key(self, text: str, prefix: str = "") -> str:
        """Generate cache key for text"""
        key = f"{self.model_name}:{prefix}:{hashlib.md5(text.encode()).hexdigest()}"
        return key

    def encode_single(self, text: str, normalize: bool = True) -> np.ndarray:
        """Encode a single text into embedding with caching"""
        cache_key = self._get_cache_key(text)

        # Check cache first
        if cache_key in self.cache:
            return self.cache[cache_key]

        # Generate embedding
        embedding = self.model.encode(text, normalize_embeddings=normalize)

        # Cache result
        self.cache[cache_key] = embedding

        return embedding

    def encode_batch(
        self,
        texts: List[str],
        batch_size: int = 32,
        normalize: bool = True,
        show_progress: bool = True
    ) -> np.ndarray:
        """Encode multiple texts with batching and caching"""
        embeddings = []
        cached_count = 0

        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i+batch_size]
            batch_embeddings = []
            texts_to_encode = []
            indices_to_encode = []

            # Check cache for each text in batch
            for j, text in enumerate(batch_texts):
                cache_key = self._get_cache_key(text)
                if cache_key in self.cache:
                    batch_embeddings.append(self.cache[cache_key])
                    cached_count += 1
                else:
                    batch_embeddings.append(None)
                    texts_to_encode.append(text)
                    indices_to_encode.append(j)

            # Encode uncached texts
            if texts_to_encode:
                new_embeddings = self.model.encode(
                    texts_to_encode,
                    batch_size=len(texts_to_encode),
                    normalize_embeddings=normalize,
                    show_progress_bar=False
                )

                # Insert new embeddings and cache them
                for idx, emb, text in zip(indices_to_encode, new_embeddings, texts_to_encode):
                    batch_embeddings[idx] = emb
                    cache_key = self._get_cache_key(text)
                    self.cache[cache_key] = emb

            embeddings.extend(batch_embeddings)

            if show_progress:
                console.print(f"[yellow]Processed batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}[/yellow]")

        if cached_count > 0:
            console.print(f"[green]Used {cached_count} cached embeddings[/green]")

        return np.array(embeddings)

    def encode_documents(
        self,
        documents: List[Dict[str, Any]],
        text_field: str = "content",
        batch_size: int = 32
    ) -> Dict[str, np.ndarray]:
        """Encode documents with metadata"""
        texts = [doc.get(text_field, "") for doc in documents]
        embeddings = self.encode_batch(texts, batch_size=batch_size)

        result = {
            "embeddings": embeddings,
            "texts": texts,
            "metadata": [
                {k: v for k, v in doc.items() if k != text_field}
                for doc in documents
            ]
        }

        return result

    def encode_query(self, query: str) -> np.ndarray:
        """Encode a search query"""
        return self.encode_single(query)

    def similarity_search(
        self,
        query_embedding: np.ndarray,
        doc_embeddings: np.ndarray,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """Find most similar documents using cosine similarity"""
        # Normalize embeddings
        query_norm = query_embedding / np.linalg.norm(query_embedding)
        doc_norms = doc_embeddings / np.linalg.norm(doc_embeddings, axis=1, keepdims=True)

        # Calculate cosine similarities
        similarities = np.dot(doc_norms, query_norm)

        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for idx in top_indices:
            results.append({
                "index": int(idx),
                "score": float(similarities[idx])
            })

        return results

    def clear_cache(self):
        """Clear embedding cache"""
        self.cache.clear()
        console.print("[yellow]Embedding cache cleared[/yellow]")

    def cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "size": len(self.cache),
            "cache_dir": str(self.cache_dir),
            "model": self.model_name,
            "embed_dim": self.embed_dim
        }

    def save_embeddings(self, embeddings: np.ndarray, filepath: str):
        """Save embeddings to file"""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'wb') as f:
            pickle.dump({
                "embeddings": embeddings,
                "model": self.model_name,
                "embed_dim": self.embed_dim
            }, f)
        console.print(f"[green]Embeddings saved to {filepath}[/green]")

    def load_embeddings(self, filepath: str) -> np.ndarray:
        """Load embeddings from file"""
        with open(filepath, 'rb') as f:
            data = pickle.load(f)

        if data["model"] != self.model_name:
            console.print(f"[yellow]Warning: Model mismatch. Saved: {data['model']}, Current: {self.model_name}[/yellow]")

        console.print(f"[green]Embeddings loaded from {filepath}[/green]")
        return data["embeddings"]
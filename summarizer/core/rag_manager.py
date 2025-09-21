"""Central RAG system manager coordinating all components"""

import asyncio
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import logging
from rich.console import Console

# Import RAG components
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from rag.embeddings.local_embedder import LocalEmbedder
from rag.vectorstore.faiss_store import FAISSVectorStore
from rag.ingestion.document_loader import DocumentLoader
from rag.ingestion.chunker import TextChunker
from rag.retrieval.hybrid_retriever import HybridRetriever
from genetics.corpus_crawler import GeneticsCorpusCrawler
from tiny_code.ollama_client import OllamaClient

console = Console()
logger = logging.getLogger(__name__)

class RAGManager:
    """Central manager for the RAG system"""

    def __init__(
        self,
        embedding_model: str = "all-MiniLM-L6-v2",
        data_dir: str = "data",
        cache_dir: str = "data/cache"
    ):
        self.data_dir = Path(data_dir)
        self.cache_dir = Path(cache_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        console.print("[cyan]Initializing RAG system...[/cyan]")

        # Embedder
        self.embedder = LocalEmbedder(
            model_name=embedding_model,
            cache_dir=str(self.cache_dir / "embeddings")
        )

        # Vector store
        self.vector_store = FAISSVectorStore(
            embedding_dim=self.embedder.embed_dim,
            store_path=str(self.data_dir / "index" / "faiss")
        )

        # Document processing
        self.document_loader = DocumentLoader()
        self.chunker = TextChunker(chunk_size=800, chunk_overlap=100)

        # Retrieval
        self.retriever = HybridRetriever(
            embedder=self.embedder,
            vector_store=self.vector_store,
            alpha=0.7  # Favor dense retrieval slightly
        )

        # Genetics crawler
        self.genetics_crawler = GeneticsCorpusCrawler(
            output_dir=str(self.data_dir / "genetics_corpus")
        )

        # TinyLlama clients
        self.primary_llm = None  # For coding tasks
        self.summarization_llm = None  # For summarization

        # Knowledge bases
        self.knowledge_bases = {
            "general": {"loaded": False, "doc_count": 0},
            "genetics": {"loaded": False, "doc_count": 0},
            "code": {"loaded": False, "doc_count": 0}
        }

        # Auto-load existing knowledge bases
        self._auto_load_existing_knowledge_bases()

        console.print("[green]RAG system initialized successfully[/green]")

    def initialize_llms(
        self,
        primary_model: str = "tinyllama:latest",
        summarization_model: str = "tinyllama:latest"
    ):
        """Initialize TinyLlama models"""
        console.print("[yellow]Initializing TinyLlama models...[/yellow]")

        self.primary_llm = OllamaClient(model=primary_model, temperature=0.3)
        self.summarization_llm = OllamaClient(model=summarization_model, temperature=0.7)

        console.print("[green]TinyLlama models initialized[/green]")

    async def ingest_documents(
        self,
        documents_path: Union[str, Path, List[str]],
        knowledge_base: str = "general",
        chunking_strategy: str = "adaptive",
        batch_size: int = 50
    ) -> Dict[str, Any]:
        """Ingest documents into the RAG system"""

        console.print(f"[cyan]Ingesting documents into '{knowledge_base}' knowledge base...[/cyan]")

        # Load documents
        if isinstance(documents_path, (str, Path)):
            documents_path = Path(documents_path)
            if documents_path.is_file():
                documents = [self.document_loader.load_document(documents_path)]
            else:
                documents = self.document_loader.load_directory(documents_path, recursive=True)
        else:
            # List of file paths
            documents = []
            for path in documents_path:
                documents.append(self.document_loader.load_document(path))

        if not documents:
            console.print("[red]No documents found to ingest[/red]")
            return {"success": False, "error": "No documents found"}

        # Filter out failed documents
        valid_documents = [doc for doc in documents if doc["content"].strip()]
        failed_count = len(documents) - len(valid_documents)

        if failed_count > 0:
            console.print(f"[yellow]Warning: {failed_count} documents failed to load[/yellow]")

        # Chunk documents
        console.print("[yellow]Chunking documents...[/yellow]")
        chunks = self.chunker.chunk_documents(valid_documents, strategy=chunking_strategy)

        # Generate embeddings
        console.print("[yellow]Generating embeddings...[/yellow]")
        chunk_texts = [chunk["content"] for chunk in chunks]
        embeddings = self.embedder.encode_batch(chunk_texts, batch_size=batch_size)

        # Add to vector store
        console.print("[yellow]Adding to vector store...[/yellow]")
        chunk_metadata = []
        for chunk in chunks:
            metadata = chunk["metadata"].copy()
            metadata["knowledge_base"] = knowledge_base
            chunk_metadata.append(metadata)

        self.vector_store.add_documents(embeddings, chunk_texts, chunk_metadata)

        # Update retriever
        self.retriever.index_documents(chunk_texts, embeddings, chunk_metadata)

        # Update knowledge base stats
        self.knowledge_bases[knowledge_base] = {
            "loaded": True,
            "doc_count": len(valid_documents),
            "chunk_count": len(chunks)
        }

        # Save vector store
        self.vector_store.save(f"{knowledge_base}_index")

        result = {
            "success": True,
            "documents_processed": len(valid_documents),
            "documents_failed": failed_count,
            "chunks_created": len(chunks),
            "knowledge_base": knowledge_base
        }

        console.print(f"[green]Successfully ingested {len(valid_documents)} documents ({len(chunks)} chunks)[/green]")
        return result

    async def ingest_genetics_corpus(self, max_pages_per_source: int = 50) -> Dict[str, Any]:
        """Crawl and ingest genetics corpus"""

        console.print("[cyan]Crawling genetics corpus...[/cyan]")

        # Crawl genetics documentation
        crawl_stats = await self.genetics_crawler.crawl_genetics_corpus(
            max_pages_per_source=max_pages_per_source
        )

        # Get crawled documents
        genetics_docs = self.genetics_crawler.get_crawled_documents()

        if genetics_docs:
            # Process documents for ingestion
            processed_docs = []
            for doc in genetics_docs:
                processed_docs.append({
                    "content": doc["content"],
                    "metadata": {
                        "source_url": doc["url"],
                        "title": doc.get("title", ""),
                        "source_type": doc.get("source_type", "genetics"),
                        "domain": doc.get("source_domain", ""),
                        "crawled_at": doc.get("crawled_at", 0)
                    }
                })

            # Ingest into genetics knowledge base
            ingest_result = await self.ingest_documents(
                processed_docs,
                knowledge_base="genetics",
                chunking_strategy="heading"  # Good for documentation
            )

            result = {
                "crawl_stats": crawl_stats,
                "ingest_result": ingest_result
            }
        else:
            result = {
                "crawl_stats": crawl_stats,
                "ingest_result": {"success": False, "error": "No documents crawled"}
            }

        return result

    def search(
        self,
        query: str,
        knowledge_base: Optional[str] = None,
        top_k: int = 5,
        include_scores: bool = True
    ) -> List[Dict[str, Any]]:
        """Search the knowledge base"""

        # Load knowledge base on demand if needed
        if knowledge_base and not self.knowledge_bases.get(knowledge_base, {}).get("loaded", False):
            self._load_knowledge_base_on_demand(knowledge_base)

        # Filter by knowledge base if specified
        filter_metadata = {"knowledge_base": knowledge_base} if knowledge_base else None

        results = self.retriever.search(
            query,
            top_k=top_k,
            return_scores=include_scores
        )

        # Apply knowledge base filtering if needed
        if filter_metadata:
            filtered_results = []
            for result in results:
                if result["metadata"].get("knowledge_base") == knowledge_base:
                    filtered_results.append(result)
            results = filtered_results[:top_k]

        return results

    def summarize_document(
        self,
        document: str,
        summary_type: str = "extractive",
        max_length: int = 500
    ) -> str:
        """Summarize a document using TinyLlama"""

        if not self.summarization_llm:
            raise ValueError("Summarization LLM not initialized. Call initialize_llms() first.")

        if summary_type == "extractive":
            # Use RAG to find key passages
            chunks = self.chunker.chunk_text(document, strategy="semantic")
            key_passages = []

            for chunk in chunks[:5]:  # Limit to top 5 chunks
                # Use the chunk content as a query to find related content
                related = self.search(chunk["content"][:200], top_k=2)
                if related:
                    key_passages.append(chunk["content"])

            content_to_summarize = "\n\n".join(key_passages)
        else:
            content_to_summarize = document

        # Truncate if too long
        if len(content_to_summarize) > 4000:  # Leave room for prompt
            content_to_summarize = content_to_summarize[:4000] + "..."

        prompt = f"""Please provide a concise summary of the following document. Focus on the main points and key information. Limit the summary to approximately {max_length} words.

Document:
{content_to_summarize}

Summary:"""

        try:
            summary = self.summarization_llm.generate(prompt)
            return summary.strip()
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return "Error: Could not generate summary"

    def ask_question(
        self,
        question: str,
        knowledge_base: Optional[str] = None,
        context_length: int = 3
    ) -> str:
        """Ask a question using RAG"""

        if not self.primary_llm:
            raise ValueError("Primary LLM not initialized. Call initialize_llms() first.")

        # Search for relevant context
        search_results = self.search(
            question,
            knowledge_base=knowledge_base,
            top_k=context_length
        )

        if not search_results:
            return "I don't have enough information to answer that question."

        # Build context
        context_parts = []
        for i, result in enumerate(search_results):
            context_parts.append(f"Context {i+1}:")
            context_parts.append(result["document"])
            context_parts.append("")

        context = "\n".join(context_parts)

        # Generate response
        prompt = f"""Based on the following context, please answer the question. If the context doesn't contain enough information to answer the question, say so.

Context:
{context}

Question: {question}

Answer:"""

        try:
            response = self.primary_llm.generate(prompt)
            return response.strip()
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "Error: Could not generate response"

    def get_system_stats(self) -> Dict[str, Any]:
        """Get RAG system statistics"""

        embedder_stats = self.embedder.cache_stats()
        vector_stats = self.vector_store.get_stats()
        retriever_stats = self.retriever.get_stats()

        return {
            "knowledge_bases": self.knowledge_bases,
            "embedder": embedder_stats,
            "vector_store": vector_stats,
            "retriever": retriever_stats,
            "llms_initialized": {
                "primary": self.primary_llm is not None,
                "summarization": self.summarization_llm is not None
            }
        }

    def save_system_state(self, name: str = "default"):
        """Save the current system state"""

        # Save vector store
        self.vector_store.save(f"{name}_vectors")

        # Save system metadata
        metadata = {
            "knowledge_bases": self.knowledge_bases,
            "system_stats": self.get_system_stats()
        }

        metadata_file = self.data_dir / f"{name}_metadata.json"
        with open(metadata_file, 'w') as f:
            import json
            json.dump(metadata, f, indent=2)

        console.print(f"[green]System state saved as '{name}'[/green]")

    def load_system_state(self, name: str = "default"):
        """Load a saved system state"""

        try:
            # Load vector store
            self.vector_store.load(f"{name}_vectors")

            # Load metadata
            metadata_file = self.data_dir / f"{name}_metadata.json"
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    import json
                    metadata = json.load(f)
                    self.knowledge_bases = metadata.get("knowledge_bases", {})

            console.print(f"[green]System state '{name}' loaded successfully[/green]")

        except Exception as e:
            console.print(f"[red]Error loading system state '{name}': {e}[/red]")
            raise

    def _auto_load_existing_knowledge_bases(self):
        """Auto-load existing knowledge base indexes if they exist"""
        try:
            # Check for existing knowledge base indexes
            faiss_dir = self.data_dir / "index" / "faiss"
            if not faiss_dir.exists():
                return

            # Check what knowledge bases exist
            existing_kbs = []
            for kb_name in ["general", "genetics", "code"]:
                kb_path = faiss_dir / f"{kb_name}_index"
                if kb_path.exists() and (kb_path / "index.faiss").exists():
                    existing_kbs.append(kb_name)
                    # Update status without loading (will load on first use)
                    try:
                        with open(kb_path / "config.json", 'r') as f:
                            config = json.load(f)
                            self.knowledge_bases[kb_name] = {
                                "loaded": False,  # Will be loaded on demand
                                "doc_count": config.get("document_count", 0)
                            }
                    except:
                        self.knowledge_bases[kb_name] = {
                            "loaded": False,
                            "doc_count": 0
                        }

            if existing_kbs:
                console.print(f"[cyan]Found existing knowledge bases: {', '.join(existing_kbs)}[/cyan]")
                console.print("[dim]Knowledge bases will be loaded on first use[/dim]")

        except Exception as e:
            console.print(f"[yellow]Error checking existing knowledge bases: {e}[/yellow]")

    def _load_knowledge_base_on_demand(self, knowledge_base: str):
        """Load a specific knowledge base when needed"""
        try:
            faiss_dir = self.data_dir / "index" / "faiss"
            kb_path = faiss_dir / f"{knowledge_base}_index"

            if kb_path.exists() and (kb_path / "index.faiss").exists():
                console.print(f"[cyan]Loading {knowledge_base} knowledge base...[/cyan]")

                # Load vector store
                self.vector_store.load(f"{knowledge_base}_index")

                # Load into retriever
                if self.vector_store.documents:
                    self.retriever.index_documents(
                        self.vector_store.documents,
                        embeddings=None,  # Will be recomputed if needed
                        metadata=self.vector_store.metadata
                    )

                    # Update knowledge base status
                    self.knowledge_bases[knowledge_base]["loaded"] = True
                    self.knowledge_bases[knowledge_base]["doc_count"] = len(self.vector_store.documents)

                    console.print(f"[green]Loaded {knowledge_base} knowledge base with {len(self.vector_store.documents)} documents[/green]")
                else:
                    console.print(f"[yellow]Knowledge base {knowledge_base} appears to be empty[/yellow]")
            else:
                console.print(f"[yellow]Knowledge base {knowledge_base} not found[/yellow]")

        except Exception as e:
            console.print(f"[red]Error loading {knowledge_base} knowledge base: {e}[/red]")
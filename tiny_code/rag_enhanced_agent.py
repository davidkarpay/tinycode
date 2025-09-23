"""RAG-enhanced Tiny Code agent with document summarization capabilities"""

import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from .agent import TinyCodeAgent
from summarizer.core.rag_manager import RAGManager

console = Console()

class RAGEnhancedTinyCodeAgent(TinyCodeAgent):
    """Tiny Code agent enhanced with RAG capabilities"""

    def __init__(self, model: str = "tinyllama:latest", temperature: float = 0.7):
        super().__init__(model, temperature)

        # Initialize RAG system
        console.print("[cyan]Initializing RAG-enhanced agent...[/cyan]")
        self.rag = RAGManager()
        self.rag.initialize_llms(
            primary_model=model,
            summarization_model=model
        )

        # Track conversation context for RAG
        self.conversation_history = []
        self.current_knowledge_base = "general"

        console.print("[green]RAG-enhanced agent ready[/green]")

    async def ingest_documents(
        self,
        documents_path: str,
        knowledge_base: str = "general"
    ) -> Dict[str, Any]:
        """Ingest documents into RAG system"""
        console.print(f"[yellow]Ingesting documents from {documents_path}...[/yellow]")

        result = await self.rag.ingest_documents(
            documents_path,
            knowledge_base=knowledge_base
        )

        if result["success"]:
            console.print(Panel(
                f"Successfully ingested {result['documents_processed']} documents\n"
                f"Created {result['chunks_created']} chunks\n"
                f"Knowledge base: {knowledge_base}",
                title="Document Ingestion Complete",
                style="green"
            ))
        else:
            console.print(Panel(
                f"Ingestion failed: {result.get('error', 'Unknown error')}",
                title="Ingestion Error",
                style="red"
            ))

        return result

    async def setup_genetics_knowledge(self, max_pages: int = 30) -> Dict[str, Any]:
        """Set up genetics knowledge base"""
        console.print("[cyan]Setting up genetics knowledge base...[/cyan]")

        result = await self.rag.ingest_genetics_corpus(max_pages_per_source=max_pages)

        if result["ingest_result"]["success"]:
            console.print(Panel(
                f"Genetics corpus setup complete!\n"
                f"Crawled: {result['crawl_stats']['pages_downloaded']} pages\n"
                f"Processed: {result['ingest_result']['documents_processed']} documents",
                title="Genetics Knowledge Base Ready",
                style="green"
            ))
        else:
            console.print(Panel(
                "Genetics corpus setup failed",
                title="Setup Error",
                style="red"
            ))

        return result

    def rag_search(
        self,
        query: str,
        knowledge_base: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Search RAG knowledge base"""
        kb = knowledge_base or self.current_knowledge_base
        results = self.rag.search(query, knowledge_base=kb, top_k=top_k)

        if results:
            console.print(f"[green]Found {len(results)} relevant documents[/green]")
            for i, result in enumerate(results):
                score = result.get("combined_score", 0)
                snippet = result["document"][:200] + "..." if len(result["document"]) > 200 else result["document"]
                console.print(f"[cyan]{i+1}. Score: {score:.3f}[/cyan]")
                console.print(f"[dim]{snippet}[/dim]")
                console.print()
        else:
            console.print("[yellow]No relevant documents found[/yellow]")

        return results

    def rag_enhanced_coding(
        self,
        coding_request: str,
        include_context: bool = True,
        context_top_k: int = 3
    ) -> str:
        """Generate code with RAG context"""

        response_parts = [f"Request: {coding_request}\n"]

        if include_context:
            # Search for relevant coding patterns
            search_results = self.rag.search(
                f"code programming {coding_request}",
                knowledge_base="code",
                top_k=context_top_k
            )

            if search_results:
                response_parts.append("Relevant patterns found:")
                for result in search_results:
                    response_parts.append(f"- {result['document'][:150]}...")
                response_parts.append("")

        # Generate code using standard agent with context
        enhanced_prompt = "\n".join(response_parts) + f"\n\nGenerate code for: {coding_request}"
        return self.client.generate(enhanced_prompt, system=self.get_enhanced_system_prompt())

    def summarize_document(
        self,
        document_path: str,
        summary_type: str = "extractive",
        max_length: int = 500
    ) -> str:
        """Summarize a document"""
        document_content = self.tools.read_file(document_path)

        if not document_content:
            return "Error: Could not read document"

        console.print("[yellow]Generating summary...[/yellow]")
        summary = self.rag.summarize_document(
            document_content,
            summary_type=summary_type,
            max_length=max_length
        )

        console.print(Panel(
            Markdown(summary),
            title=f"Summary of {Path(document_path).name}",
            style="blue"
        ))

        return summary

    def chat_with_documents(
        self,
        question: str,
        knowledge_base: Optional[str] = None
    ) -> str:
        """Chat interface for document exploration"""

        # Add to conversation history
        self.conversation_history.append({"role": "user", "content": question})

        # Get RAG-enhanced response
        response = self.rag.ask_question(
            question,
            knowledge_base=knowledge_base or self.current_knowledge_base
        )

        # Add to conversation history
        self.conversation_history.append({"role": "assistant", "content": response})

        console.print(Panel(
            Markdown(response),
            title="RAG Response",
            style="cyan"
        ))

        return response

    def explain_genetics_concept(self, concept: str) -> str:
        """Explain genetics concepts using knowledge base"""
        return self.chat_with_documents(
            f"Explain the genetics concept: {concept}",
            knowledge_base="genetics"
        )

    def get_coding_help(self, coding_question: str) -> str:
        """Get coding help with RAG context"""
        # Search for relevant coding information
        context_results = self.rag.search(
            coding_question,
            knowledge_base="code",
            top_k=3
        )

        # Build enhanced prompt
        context = ""
        if context_results:
            context = "Relevant information:\n"
            for result in context_results:
                context += f"- {result['document'][:300]}...\n"
            context += "\n"

        enhanced_prompt = f"{context}Question: {coding_question}"

        response = self.client.generate(
            enhanced_prompt,
            system=self.get_enhanced_system_prompt()
        )

        console.print(Panel(
            Markdown(response),
            title="Coding Help",
            style="green"
        ))

        return response

    def set_knowledge_base(self, kb_name: str):
        """Switch active knowledge base"""
        if kb_name in self.rag.knowledge_bases:
            self.current_knowledge_base = kb_name
            console.print(f"[green]Switched to knowledge base: {kb_name}[/green]")
        else:
            console.print(f"[red]Knowledge base '{kb_name}' not found[/red]")

    def get_enhanced_system_prompt(self) -> str:
        """Get enhanced system prompt with RAG context"""
        base_prompt = """You are Tiny Code, an AI coding assistant enhanced with RAG (Retrieval Augmented Generation) capabilities.

RAG SYSTEM OVERVIEW:
RAG enhances your responses by retrieving relevant documents before generating answers. This means you can:
- Access up-to-date documentation and specifications
- Reference specific code patterns and examples
- Provide more accurate technical information
- Give context-aware recommendations

AVAILABLE KNOWLEDGE BASES:
1. 'general' - General programming and technical documentation
2. 'genetics' - Bioinformatics and genetics-specific resources including:
   • SAM/BAM/VCF file format specifications
   • GATK, samtools, bcftools documentation
   • Genomics workflow best practices
   • Coordinate system explanations
3. 'code' - Code examples, patterns, and programming documentation

HOW RAG WORKS:
When you receive a query, relevant documents are automatically retrieved from the knowledge bases and provided as context. Use this context to:
- Enhance your answers with specific examples
- Reference exact specifications and documentation
- Provide more accurate technical details
- Give implementation guidance based on proven patterns

RESPONSE GUIDELINES:
- Use retrieved context when relevant and cite sources
- Be precise about technical concepts, especially genetics coordinate systems
- Provide working code examples when possible
- Explain your reasoning and how the retrieved information supports your answer
- If no relevant context is found, clearly state you're relying on base knowledge

CURRENT KNOWLEDGE BASE: {current_kb}
""".format(current_kb=self.current_knowledge_base)
        return base_prompt

    def get_rag_stats(self) -> Dict[str, Any]:
        """Get RAG system statistics"""
        stats = self.rag.get_system_stats()

        console.print(Panel(
            f"Knowledge Bases: {len(stats['knowledge_bases'])}\n"
            f"Documents: {sum(kb.get('doc_count', 0) for kb in stats['knowledge_bases'].values())}\n"
            f"Vector Store: {stats['vector_store']['document_count']} chunks\n"
            f"Cache Size: {stats['embedder']['size']} embeddings",
            title="RAG System Stats",
            style="blue"
        ))

        return stats

    def save_rag_state(self, name: str = "default"):
        """Save RAG system state"""
        self.rag.save_system_state(name)

    def load_rag_state(self, name: str = "default"):
        """Load RAG system state"""
        self.rag.load_system_state(name)

    # Enhanced processing methods
    def process_file_with_rag(self, filepath: str, operation: str, **kwargs) -> str:
        """Process file with RAG enhancement"""

        # First do standard processing
        base_result = super().process_file(filepath, operation, **kwargs)

        # For certain operations, enhance with RAG
        if operation in ['explain', 'review']:
            # Get additional context from knowledge base
            code = self.tools.read_file(filepath)
            if code:
                rag_context = self.rag.search(f"code explanation {Path(filepath).suffix}", top_k=2)

                if rag_context:
                    enhanced_prompt = f"""
Based on the following context and the code analysis below, provide additional insights:

Context:
{rag_context[0]['document'][:500]}

Original Analysis:
{base_result}

Provide enhanced analysis with additional context:
"""
                    enhanced_result = self.client.generate(enhanced_prompt)
                    return f"{base_result}\n\n--- Enhanced Analysis ---\n{enhanced_result}"

        return base_result

    async def run_async_operation(self, operation: str, *args, **kwargs):
        """Run async operations (like document ingestion)"""
        if operation == "ingest":
            return await self.ingest_documents(*args, **kwargs)
        elif operation == "setup_genetics":
            return await self.setup_genetics_knowledge(*args, **kwargs)
        else:
            raise ValueError(f"Unknown async operation: {operation}")
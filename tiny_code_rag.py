#!/usr/bin/env python3
"""Enhanced Tiny Code with RAG capabilities launcher"""

import asyncio
import sys
from pathlib import Path

# Add package to path
sys.path.insert(0, str(Path(__file__).parent))

from tiny_code.rag_enhanced_agent import RAGEnhancedTinyCodeAgent
from tiny_code.cli import TinyCodeCLI
from tiny_code.mode_manager import ModeManager, OperationMode
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
import click

console = Console()

class RAGEnhancedCLI(TinyCodeCLI):
    """Enhanced CLI with RAG capabilities"""

    def __init__(self, model: str = "tinyllama:latest"):
        # Initialize parent class first
        super().__init__(model=model)

        # Then override with RAG-enhanced agent
        self.agent = RAGEnhancedTinyCodeAgent(model=model)
        self.tools = self.agent.tools
        self.history_file = Path.home() / '.tiny_code_rag_history'

    def show_help(self):
        """Show enhanced help with RAG commands"""
        help_text = """
        [bold cyan]Tiny Code with RAG (Retrieval Augmented Generation):[/bold cyan]

        [bold green]What is RAG?[/bold green]
        RAG enhances AI responses by retrieving relevant documents before generating answers.
        This provides more accurate, contextual, and up-to-date information.

        [yellow]Knowledge Bases Available:[/yellow]
        • general - Programming and technical documentation
        • genetics - Bioinformatics, genomics, SAM/BAM/VCF formats
        • code - Code examples, patterns, and best practices

        [yellow]Chat & RAG:[/yellow]
        Just type your question (automatically uses RAG context when available)
        Example: "How do I parse a VCF file?" (uses genetics knowledge base)

        [yellow]RAG Commands (prefix with /):[/yellow]
        /explain_rag          - Learn how RAG works and how to use it effectively
        /rag <query>          - Search RAG knowledge base directly
        /chat <question>      - Chat with documents using current knowledge base
        /knowledge <base>     - Switch active knowledge base (general/genetics/code)
        /rag_stats           - Show RAG system statistics and knowledge base info

        [yellow]Document Management:[/yellow]
        /ingest <path>        - Add documents to RAG system
        /summarize <path>     - Summarize a document using RAG
        /setup_genetics       - Download and ingest genetics documentation
        /genetics <concept>   - Explain genetics concept using knowledge base

        [yellow]RAG-Enhanced File Commands:[/yellow]
        /explain <path>       - Explain code with retrieved context and examples
        /review <path>        - Review code with best practices from knowledge base
        /analyze <path>       - Analyze file with relevant documentation context

        [yellow]Standard Commands:[/yellow]
        /complete <path>      - Complete code in file
        /fix <path>           - Fix bugs in code
        /refactor <path>      - Refactor code
        /test <path>          - Generate tests for code
        /run <path>           - Execute a Python file
        /workspace <path>     - Set working directory
        /list [pattern]       - List files in workspace

        [yellow]Other:[/yellow]
        help    - Show this help
        clear   - Clear screen
        exit    - Quit the program
        """
        console.print(Panel(help_text, title="RAG-Enhanced TinyCode Help", border_style="blue"))

    def handle_command(self, command: str):
        """Handle enhanced commands including RAG with mode awareness"""
        parts = command.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        # Handle mode commands first
        if cmd == 'mode':
            self.handle_mode_command(args)
            return

        # Check if command is allowed in current mode
        if not self.mode_manager.is_command_allowed(cmd):
            console.print(f"[red]Command '{cmd}' not allowed in {self.mode_manager.current_mode.value} mode[/red]")
            console.print(f"[yellow]Use '/mode help' to see available modes[/yellow]")
            return

        # RAG-specific commands (mostly safe, some require execution mode)
        rag_commands = {
            # Safe RAG commands
            'explain_rag': self._explain_rag_system,
            'rag': self._rag_search,
            'summarize': self._summarize_document,
            'chat': self._chat_with_documents,
            'genetics': self._explain_genetics,
            'knowledge': self._switch_knowledge_base,
            'rag_stats': self._show_rag_stats,

            # Execution RAG commands
            'ingest': self._ingest_documents,
            'setup_genetics': self._setup_genetics,
        }

        if cmd in rag_commands:
            rag_commands[cmd](args)
        # Enhanced standard commands
        elif cmd in ['analyze', 'explain', 'review']:
            self._enhanced_file_command(cmd, args)
        else:
            # Fall back to standard commands
            super().handle_command(command)

    def _ingest_documents(self, path: str):
        """Ingest documents command"""
        if not path:
            path = Prompt.ask("Enter document path")

        kb = Prompt.ask("Knowledge base", choices=["general", "genetics", "code"], default="general")

        console.print(f"[yellow]Ingesting documents from {path} into '{kb}' knowledge base...[/yellow]")

        # Run async ingestion
        try:
            result = asyncio.run(self.agent.ingest_documents(path, kb))
            if result["success"]:
                console.print("[green]Documents ingested successfully![/green]")
            else:
                console.print(f"[red]Ingestion failed: {result.get('error', 'Unknown error')}[/red]")
        except Exception as e:
            console.print(f"[red]Error during ingestion: {e}[/red]")

    def _rag_search(self, query: str):
        """RAG search command"""
        if not query:
            query = Prompt.ask("Enter search query")

        kb = Prompt.ask("Knowledge base", choices=["general", "genetics", "code", "all"], default="all")
        if kb == "all":
            kb = None

        results = self.agent.rag_search(query, knowledge_base=kb)

        if not results:
            console.print("[yellow]No results found[/yellow]")

    def _summarize_document(self, filepath: str):
        """Summarize document command"""
        if not filepath:
            filepath = Prompt.ask("Enter document path")

        summary_type = Prompt.ask("Summary type", choices=["extractive", "abstractive"], default="extractive")
        max_length = int(Prompt.ask("Max length (words)", default="500"))

        try:
            summary = self.agent.summarize_document(filepath, summary_type, max_length)
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

    def _chat_with_documents(self, question: str):
        """Chat with documents command"""
        if not question:
            question = Prompt.ask("Ask a question")

        kb = Prompt.ask("Knowledge base", choices=["general", "genetics", "code"], default=self.agent.current_knowledge_base)

        try:
            response = self.agent.chat_with_documents(question, kb)
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

    def _explain_genetics(self, concept: str):
        """Explain genetics concept"""
        if not concept:
            concept = Prompt.ask("Enter genetics concept")

        try:
            explanation = self.agent.explain_genetics_concept(concept)
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

    def _switch_knowledge_base(self, kb_name: str):
        """Switch knowledge base"""
        if not kb_name:
            kb_name = Prompt.ask("Knowledge base", choices=["general", "genetics", "code"])

        self.agent.set_knowledge_base(kb_name)

    def _setup_genetics(self):
        """Set up genetics knowledge base"""
        confirm = Confirm.ask("This will crawl genetics documentation. Continue?")
        if confirm:
            max_pages = int(Prompt.ask("Max pages per source", default="30"))

            console.print("[cyan]Setting up genetics knowledge base (this may take a while)...[/cyan]")
            try:
                result = asyncio.run(self.agent.setup_genetics_knowledge(max_pages))
                console.print("[green]Genetics knowledge base setup complete![/green]")
            except Exception as e:
                console.print(f"[red]Setup failed: {e}[/red]")

    def _explain_rag_system(self, args):
        """Explain how RAG (Retrieval Augmented Generation) works"""
        explanation = """
        [bold cyan]RAG (Retrieval Augmented Generation) Explained[/bold cyan]

        [bold green]What is RAG?[/bold green]
        RAG is an AI technique that enhances language model responses by retrieving relevant
        documents before generating answers. Instead of relying only on training data,
        RAG systems can access current, specific information.

        [bold green]How TinyCode's RAG Works:[/bold green]
        1. [yellow]Document Ingestion[/yellow]: Documents are processed and stored in vector databases
        2. [yellow]Query Processing[/yellow]: When you ask a question, it's converted to a search vector
        3. [yellow]Retrieval[/yellow]: Similar documents are found using vector similarity search
        4. [yellow]Context Addition[/yellow]: Retrieved documents are added to your query as context
        5. [yellow]Enhanced Generation[/yellow]: The AI generates responses using both its training and retrieved context

        [bold green]Available Knowledge Bases:[/bold green]
        • [cyan]general[/cyan] - Programming docs, technical specifications, general knowledge
        • [cyan]genetics[/cyan] - Bioinformatics tools (GATK, samtools), file formats (SAM/BAM/VCF), genomics workflows
        • [cyan]code[/cyan] - Code examples, programming patterns, best practices

        [bold green]Benefits of RAG:[/bold green]
        ✓ More accurate technical information
        ✓ Access to up-to-date documentation
        ✓ Context-aware recommendations
        ✓ Specific examples and code patterns
        ✓ Reduced hallucination for technical details

        [bold green]Example Usage:[/bold green]
        [dim]# Switch to genetics knowledge base[/dim]
        /knowledge genetics

        [dim]# Ask a genetics question (RAG automatically retrieves relevant docs)[/dim]
        "How do I filter variants in a VCF file with bcftools?"

        [dim]# Search knowledge base directly[/dim]
        /rag "VCF filtering bcftools"

        [dim]# Ingest your own documents[/dim]
        /ingest /path/to/your/docs

        [bold green]Best Practices:[/bold green]
        • Use specific, technical language in queries for better retrieval
        • Switch knowledge bases based on your domain (/knowledge <base>)
        • Ingest project-specific documentation for better context
        • Use /rag_stats to see what's available in each knowledge base

        [bold yellow]Current Knowledge Base:[/bold yellow] {current_kb}
        """.format(current_kb=self.agent.current_knowledge_base)

        console.print(Panel(explanation, title="RAG System Guide", border_style="cyan"))

    def _show_rag_stats(self):
        """Show RAG statistics"""
        self.agent.get_rag_stats()

    def _enhanced_file_command(self, cmd: str, filepath: str):
        """Enhanced file commands with RAG"""
        if not filepath:
            filepath = self.agent.current_file or Prompt.ask("Enter file path")

        try:
            result = self.agent.process_file_with_rag(filepath, cmd)
            console.print(Panel(result, title=f"Enhanced {cmd.title()}", border_style="green"))
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

@click.group(invoke_without_command=True)
@click.option('--model', default='tinyllama:latest', help='Ollama model to use')
@click.pass_context
def cli(ctx, model):
    """Tiny Code RAG - AI Coding Assistant with RAG"""
    if ctx.invoked_subcommand is None:
        console.print(Panel.fit(
            "[bold cyan]Tiny Code RAG[/bold cyan]\n"
            "AI Coding Assistant with Retrieval-Augmented Generation\n"
            "Enhanced with genetics knowledge and document summarization\n"
            "Type 'help' for commands, 'exit' to quit",
            border_style="cyan"
        ))

        cli_instance = RAGEnhancedCLI(model=model)
        cli_instance.interactive_mode()

@cli.command()
@click.argument('path')
@click.option('--kb', default='general', help='Knowledge base: general/genetics/code')
@click.option('--model', default='tinyllama:latest', help='Ollama model to use')
def ingest(path, kb, model):
    """Ingest documents into RAG system"""
    agent = RAGEnhancedTinyCodeAgent(model=model)
    result = asyncio.run(agent.ingest_documents(path, kb))
    if result["success"]:
        console.print(f"[green]Ingested {result['documents_processed']} documents[/green]")
    else:
        console.print(f"[red]Failed: {result.get('error')}[/red]")

@cli.command()
@click.argument('query')
@click.option('--kb', help='Knowledge base to search')
@click.option('--model', default='tinyllama:latest', help='Ollama model to use')
def search(query, kb, model):
    """Search RAG knowledge base"""
    agent = RAGEnhancedTinyCodeAgent(model=model)
    results = agent.rag_search(query, knowledge_base=kb)
    console.print(f"Found {len(results)} results")

@cli.command()
@click.argument('filepath')
@click.option('--type', 'summary_type', default='extractive', help='Summary type')
@click.option('--length', default=500, help='Max summary length')
@click.option('--model', default='tinyllama:latest', help='Ollama model to use')
def summarize(filepath, summary_type, length, model):
    """Summarize a document"""
    agent = RAGEnhancedTinyCodeAgent(model=model)
    summary = agent.summarize_document(filepath, summary_type, length)
    console.print(summary)

@cli.command()
@click.option('--max-pages', default=30, help='Max pages per source')
@click.option('--model', default='tinyllama:latest', help='Ollama model to use')
def setup_genetics(max_pages, model):
    """Set up genetics knowledge base"""
    agent = RAGEnhancedTinyCodeAgent(model=model)
    result = asyncio.run(agent.setup_genetics_knowledge(max_pages))
    console.print("Genetics knowledge base setup complete")

@cli.command()
@click.argument('question')
@click.option('--kb', default='general', help='Knowledge base')
@click.option('--model', default='tinyllama:latest', help='Ollama model to use')
def ask(question, kb, model):
    """Ask a question using RAG"""
    agent = RAGEnhancedTinyCodeAgent(model=model)
    response = agent.chat_with_documents(question, kb)
    console.print(response)

if __name__ == "__main__":
    cli()
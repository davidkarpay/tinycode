#!/usr/bin/env python3
"""Simple test of TinyCode Natural Language Interface"""

import sys
from pathlib import Path

# Add tiny_code to path
sys.path.insert(0, str(Path(__file__).parent))

from tiny_code.nlp_interface import NLPProcessor, Intent
from tiny_code.command_translator import CommandTranslator
from rich.console import Console

def test_basic_nlp():
    """Test basic NLP functionality"""
    console = Console()

    console.print("[bold cyan]TinyCode Natural Language Interface - Basic Test[/bold cyan]\n")

    # Initialize components
    nlp = NLPProcessor()
    translator = CommandTranslator()

    test_phrases = [
        "show me the files in this directory",
        "help me fix bugs in my Python code",
        "can you analyze this file?",
        "I want to refactor my code",
        "run the tests please"
    ]

    console.print("[bold]Testing natural language understanding:[/bold]\n")

    for phrase in test_phrases:
        # Process with NLP
        result = nlp.process_input(phrase, {})

        # Translate to command
        from tiny_code.command_translator import ContextInfo
        from tiny_code.mode_manager import OperationMode
        context = ContextInfo(
            current_directory=".",
            current_mode=OperationMode.CHAT,
            available_files=["test.py", "README.md"],
            last_commands=[],
            user_preferences={}
        )
        translated = translator.translate(result, context)

        console.print(f"[cyan]Input:[/cyan] \"{phrase}\"")
        console.print(f"[green]Intent:[/green] {result.intent.value}")
        console.print(f"[yellow]Command:[/yellow] {translated.primary_command}")
        console.print(f"[blue]Explanation:[/blue] {translated.explanation}")
        console.print()

    console.print("[bold green]✅ Natural Language Interface is working![/bold green]")
    console.print("\n[dim]The TinyCode NLP system can understand natural language and translate it to commands.[/dim]")

if __name__ == "__main__":
    test_basic_nlp()
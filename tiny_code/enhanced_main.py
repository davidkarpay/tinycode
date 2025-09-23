#!/usr/bin/env python3
"""Enhanced main entry point for TinyCode with Natural Language Interface"""

import sys
import logging
import click
from pathlib import Path
from rich.console import Console
from rich.logging import RichHandler

# Add package to path if running as script
sys.path.insert(0, str(Path(__file__).parent.parent))

from tiny_code.enhanced_cli import create_enhanced_cli
from tiny_code.cli import cli as traditional_cli  # Keep traditional CLI available

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True)]
)

console = Console()


@click.group(invoke_without_command=True)
@click.option('--model', default='tinyllama:latest', help='Ollama model to use')
@click.option('--traditional', is_flag=True, help='Use traditional command-only interface')
@click.option('--debug', is_flag=True, help='Enable debug logging')
@click.pass_context
def enhanced_cli(ctx, model, traditional, debug):
    """TinyCode - AI Coding Assistant with Natural Language Interface"""

    if debug:
        logging.getLogger().setLevel(logging.DEBUG)

    if ctx.invoked_subcommand is None:
        # No subcommand - launch interactive mode
        if traditional:
            console.print("[yellow]Launching TinyCode in traditional command mode...[/yellow]")
            traditional_cli(standalone_mode=False)
        else:
            console.print("[green]Launching TinyCode with Natural Language Interface...[/green]")
            launch_enhanced_interactive(model)


def launch_enhanced_interactive(model: str = "tinyllama:latest"):
    """Launch enhanced interactive mode with natural language processing"""
    try:
        # Create enhanced CLI instance
        enhanced_cli_instance = create_enhanced_cli(model)

        # Start interactive mode
        enhanced_cli_instance.interactive_mode()

    except KeyboardInterrupt:
        console.print("\n[yellow]Session ended by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]Error starting enhanced CLI: {e}[/red]")
        logging.exception("Failed to start enhanced CLI")
        console.print("\n[yellow]Falling back to traditional CLI...[/yellow]")

        # Fallback to traditional CLI
        try:
            traditional_cli(standalone_mode=False)
        except Exception as fallback_error:
            console.print(f"[red]Fallback also failed: {fallback_error}[/red]")
            sys.exit(1)


@enhanced_cli.command()
@click.argument('message')
@click.option('--model', default='tinyllama:latest', help='Ollama model to use')
def ask(message, model):
    """Ask TinyCode a question using natural language"""
    try:
        cli_instance = create_enhanced_cli(model)

        # Process the message directly
        system_context = cli_instance._build_system_context()
        response = cli_instance.conversation_manager.process_user_input(message, system_context)

        # Display response
        cli_instance.response_formatter.format_response(
            response.get('response', ''), response
        )

        # Execute any actions
        actions = response.get('actions', [])
        for action in actions:
            cli_instance._execute_action(action, message)

    except Exception as e:
        console.print(f"[red]Error processing question: {e}[/red]")
        sys.exit(1)


@enhanced_cli.command()
@click.option('--model', default='tinyllama:latest', help='Ollama model to use')
def suggestions():
    """Get smart suggestions for current project"""
    try:
        cli_instance = create_enhanced_cli(model)
        cli_instance._show_smart_suggestions()
    except Exception as e:
        console.print(f"[red]Error getting suggestions: {e}[/red]")


@enhanced_cli.command()
@click.option('--model', default='tinyllama:latest', help='Ollama model to use')
def status():
    """Show TinyCode status and capabilities"""
    try:
        cli_instance = create_enhanced_cli(model)

        # Show enhanced status
        console.print("[bold cyan]TinyCode Enhanced Status[/bold cyan]")
        console.print("✅ Natural Language Processing: Enabled")
        console.print("✅ Smart Assistant: Active")
        console.print("✅ Conversation Manager: Ready")
        console.print("✅ Command Translation: Available")

        # Show current context
        system_context = cli_instance._build_system_context()
        console.print(f"\n[bold]Current Context:[/bold]")
        console.print(f"Directory: {system_context['current_directory']}")
        console.print(f"Mode: {system_context['current_mode']}")
        console.print(f"Files: {len(system_context.get('available_files', []))}")

        # Show conversation status
        cli_instance._show_conversation_status()

    except Exception as e:
        console.print(f"[red]Error getting status: {e}[/red]")


@enhanced_cli.command()
def test_nlp():
    """Test natural language processing with sample inputs"""
    console.print("[bold cyan]Testing Natural Language Processing...[/bold cyan]")

    from tiny_code.enhanced_cli import test_enhanced_cli
    test_enhanced_cli()


@enhanced_cli.command()
@click.option('--model', default='tinyllama:latest', help='Ollama model to use')
def demo(model):
    """Run a demonstration of natural language capabilities"""
    try:
        cli_instance = create_enhanced_cli(model)

        console.print("[bold cyan]TinyCode Natural Language Demo[/bold cyan]")
        console.print("\n[bold]Try these natural language commands:[/bold]")

        demo_commands = [
            "Show me what files are in this directory",
            "I need help analyzing my code",
            "Can you fix bugs in my Python files?",
            "Write some tests for my main function",
            "What's the git status of this project?"
        ]

        for i, cmd in enumerate(demo_commands, 1):
            console.print(f"\n[bold green]{i}.[/bold green] [cyan]\"{cmd}\"[/cyan]")

            # Process the demo command
            system_context = cli_instance._build_system_context()
            response = cli_instance.conversation_manager.process_user_input(cmd, system_context)

            # Show what would happen
            console.print(f"   [dim]→ {response.get('response', 'No response')}[/dim]")

            if response.get('actions'):
                for action in response['actions']:
                    if action.get('command'):
                        console.print(f"   [dim]→ Would execute: {action['command']}[/dim]")

        console.print(f"\n[bold yellow]💡 Try running TinyCode interactively to use these features![/bold yellow]")
        console.print(f"[dim]Run: python tiny_code.py (or use --traditional for classic mode)[/dim]")

    except Exception as e:
        console.print(f"[red]Error running demo: {e}[/red]")


@enhanced_cli.command()
@click.option('--model', default='tinyllama:latest', help='Ollama model to use')
def traditional(model):
    """Launch traditional command-only interface"""
    console.print("[yellow]Launching TinyCode in traditional mode...[/yellow]")
    traditional_cli(standalone_mode=False)


def main():
    """Enhanced main entry point"""
    try:
        enhanced_cli()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        logging.exception("Unexpected error in main")
        sys.exit(1)


if __name__ == "__main__":
    main()
"""
Enhanced CLI Interface with Natural Language Support

This module enhances the existing TinyCode CLI to support natural language input
while maintaining full backward compatibility with command-based interface.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.markdown import Markdown

from .nlp_interface import NLPProcessor
from .command_translator import CommandTranslator, ContextInfo
from .conversation_manager import ConversationManager
from .smart_assistant import SmartAssistant
from .mode_manager import OperationMode
from .cli import TinyCodeCLI  # Import existing CLI

console = Console()


class EnhancedCLI(TinyCodeCLI):
    """Enhanced CLI with natural language processing capabilities"""

    def __init__(self, model: str = "tinyllama:latest"):
        # Initialize parent CLI
        super().__init__(model)

        # Initialize natural language components
        self.nlp_processor = NLPProcessor()
        self.command_translator = CommandTranslator()
        self.conversation_manager = ConversationManager()
        self.smart_assistant = SmartAssistant()

        # Natural language mode flag
        self.natural_language_mode = True  # Default to natural language
        self.show_command_translations = True  # Show what commands would be executed

        # Enhanced response formatting
        self.response_formatter = ResponseFormatter()

        # Welcome message customization
        self.welcome_shown = False

    def interactive_mode(self):
        """Enhanced interactive mode with natural language support"""
        self._show_enhanced_welcome()

        while True:
            try:
                # Create enhanced prompt
                mode_indicator = f"[{self.mode_manager.current_mode.value}]"
                user_input = self._get_enhanced_user_input(mode_indicator).strip()

                if not user_input:
                    continue

                if user_input.lower() in ['exit', 'quit', 'q']:
                    console.print("[yellow]Goodbye![/yellow]")
                    break

                # Handle special commands
                if self._handle_special_commands(user_input):
                    continue

                # Process input through natural language pipeline
                self._process_enhanced_input(user_input)

            except KeyboardInterrupt:
                console.print("\n[yellow]Use 'exit' to quit[/yellow]")
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                # Still show helpful suggestions on error
                self._show_error_recovery_suggestions()

    def _show_enhanced_welcome(self):
        """Show enhanced welcome message with natural language introduction"""
        if self.welcome_shown:
            return

        welcome_text = """
[bold cyan]Welcome to TinyCode with Natural Language Interface![/bold cyan]

🗣️  **Talk to me naturally** - No need to memorize commands
🤖 **I'll understand your intent** - Just describe what you want to do
🛡️  **Safety first** - I'll always ask before making changes
💡 **I'll learn your patterns** - And suggest improvements over time

[dim]Examples of what you can say:[/dim]
• "Fix the bugs in my main.py file"
• "Can you analyze my code quality?"
• "I need help writing tests"
• "Show me what files are in this project"

[dim]You can also use traditional commands like /analyze, /fix, etc.[/dim]
        """

        console.print(Panel(
            welcome_text,
            border_style="cyan",
            padding=(1, 2)
        ))

        # Show context-aware suggestions
        self._show_initial_suggestions()
        self.welcome_shown = True

    def _get_enhanced_user_input(self, mode_indicator: str) -> str:
        """Get user input with enhanced prompting"""
        # Show current context hint
        context_hint = self._get_context_hint()

        # Create prompt with context
        prompt_text = f"TinyCode {mode_indicator}"
        if context_hint:
            prompt_text += f" {context_hint}"
        prompt_text += "> "

        # Use the CLI enhancements for autocomplete and history
        return self.cli_enhancements.enhanced_prompt(prompt_text)

    def _get_context_hint(self) -> str:
        """Get contextual hint for the prompt"""
        # Show file count if in a project directory
        if hasattr(self, 'tools') and self.tools:
            try:
                files = self.tools.list_files(".")
                if files and len(files) > 0:
                    return f"[dim]({len(files)} files)[/dim]"
            except:
                pass

        return ""

    def _handle_special_commands(self, user_input: str) -> bool:
        """Handle special enhanced commands"""
        if user_input.lower() in ['help', '?']:
            self._show_enhanced_help()
            return True

        if user_input.lower() == 'clear':
            console.clear()
            return True

        if user_input.lower().startswith('nlp '):
            # Toggle natural language mode
            if 'off' in user_input.lower():
                self.natural_language_mode = False
                console.print("[yellow]Natural language mode disabled. Using traditional commands only.[/yellow]")
            elif 'on' in user_input.lower():
                self.natural_language_mode = True
                console.print("[green]Natural language mode enabled.[/green]")
            return True

        if user_input.lower() == 'suggestions':
            self._show_smart_suggestions()
            return True

        if user_input.lower() == 'conversation':
            self._show_conversation_status()
            return True

        # Handle traditional commands (starting with /)
        if user_input.startswith('/'):
            # Use parent class method for traditional command handling
            self.handle_command(user_input[1:])
            return True

        return False

    def _process_enhanced_input(self, user_input: str):
        """Process user input through the enhanced natural language pipeline"""
        # Get current system context
        system_context = self._build_system_context()

        if self.natural_language_mode:
            # Process through conversation manager
            conversation_response = self.conversation_manager.process_user_input(
                user_input, system_context
            )

            # Handle the conversation response
            self._handle_conversation_response(conversation_response, user_input)
        else:
            # Fallback to traditional processing
            console.print("[dim]Processing as natural language...[/dim]")
            self._process_as_natural_language(user_input, system_context)

    def _build_system_context(self) -> Dict[str, Any]:
        """Build current system context for processing"""
        context = {
            'current_directory': str(Path.cwd()),
            'current_mode': self.mode_manager.current_mode.value,
            'available_files': [],
        }

        # Get available files
        try:
            if hasattr(self, 'tools') and self.tools:
                files = self.tools.list_files(".")
                context['available_files'] = files if files else []
        except:
            pass

        # Get git status if available
        try:
            if self.git_ops:
                git_status = self.git_ops.get_status()
                context['git_status'] = git_status
        except:
            pass

        return context

    def _handle_conversation_response(self, response: Dict[str, Any], original_input: str):
        """Handle response from conversation manager"""
        # Display the response
        response_text = response.get('response', '')
        if response_text:
            self.response_formatter.format_response(response_text, response)

        # Handle actions
        actions = response.get('actions', [])
        for action in actions:
            self._execute_action(action, original_input)

        # Show suggestions if available
        suggestions = response.get('suggestions', [])
        if suggestions:
            self._show_suggestions(suggestions, "What would you like to do next?")

        # Handle required input
        if response.get('requires_input'):
            self._handle_required_input(response)

    def _execute_action(self, action: Dict[str, Any], original_input: str):
        """Execute an action from the conversation manager"""
        action_type = action.get('type')

        if action_type == 'execute_command':
            command = action.get('command', '')
            if command:
                self._execute_translated_command(command, original_input)

        elif action_type == 'await_confirmation':
            # Confirmation already handled by conversation manager
            pass

        elif action_type == 'switch_mode':
            target_mode = action.get('mode')
            if target_mode:
                try:
                    mode_enum = OperationMode(target_mode)
                    self.mode_manager.switch_mode(mode_enum)
                    console.print(f"[green]Switched to {target_mode} mode[/green]")
                except ValueError:
                    console.print(f"[red]Invalid mode: {target_mode}[/red]")

    def _execute_translated_command(self, command: str, original_input: str):
        """Execute a translated command with enhanced feedback"""
        if self.show_command_translations:
            console.print(f"[dim]Executing: {command}[/dim]")

        try:
            # Parse and execute the command
            if command.startswith('/'):
                command = command[1:]  # Remove leading slash

            # Split command and arguments
            parts = command.split(maxsplit=1)
            cmd = parts[0]
            args = parts[1] if len(parts) > 1 else ""

            # Execute through parent CLI
            self.handle_command(f"{cmd} {args}".strip())

            # Show follow-up suggestions
            self._show_post_execution_suggestions(cmd, original_input)

        except Exception as e:
            console.print(f"[red]Error executing command: {e}[/red]")
            self._show_error_recovery_suggestions()

    def _process_as_natural_language(self, user_input: str, system_context: Dict[str, Any]):
        """Process input as natural language without conversation manager"""
        # Direct NLP processing for fallback mode
        intent_result = self.nlp_processor.process_input(user_input)

        # Build context info for translator
        context_info = ContextInfo(
            current_directory=system_context['current_directory'],
            available_files=system_context.get('available_files', []),
            current_mode=OperationMode(system_context['current_mode'])
        )

        # Translate to command
        translated_command = self.command_translator.translate(intent_result, context_info)

        if translated_command.primary_command:
            console.print(f"[cyan]I understand you want to: {translated_command.explanation}[/cyan]")

            if translated_command.requires_confirmation:
                if Confirm.ask(translated_command.confirmation_message):
                    self._execute_translated_command(translated_command.primary_command, user_input)
                else:
                    console.print("[yellow]Operation cancelled.[/yellow]")
            else:
                self._execute_translated_command(translated_command.primary_command, user_input)
        else:
            console.print("[yellow]I'm not sure how to help with that. Could you try rephrasing?[/yellow]")
            self._show_help_suggestions()

    def _show_enhanced_help(self):
        """Show enhanced help with natural language examples"""
        help_content = """
[bold]TinyCode Enhanced Help[/bold]

[bold cyan]Natural Language Commands:[/bold cyan]
You can talk to TinyCode naturally! Here are some examples:

[bold]Code Analysis & Review:[/bold]
• "Analyze my main.py file"
• "Check the code quality in this project"
• "Review my Python code for issues"
• "What does this function do?" (after loading a file)

[bold]Bug Fixing & Improvements:[/bold]
• "Fix the bugs in app.py"
• "Help me debug this error"
• "Make my code more readable"
• "Optimize the performance"

[bold]Testing & Validation:[/bold]
• "Write tests for my functions"
• "Generate unit tests for main.py"
• "Run the test suite"
• "Check if my tests pass"

[bold]File Operations:[/bold]
• "Show me what files are here"
• "Find all Python files"
• "Compare these two files"
• "What's in the config.json file?"

[bold]Project Management:[/bold]
• "What's the git status?"
• "Commit my changes"
• "Switch to propose mode"
• "Help me plan this feature"

[bold cyan]Traditional Commands:[/bold cyan]
You can still use traditional commands like:
/analyze, /fix, /test, /help, /mode, etc.

[bold cyan]Special Commands:[/bold cyan]
• [bold]help[/bold] or [bold]?[/bold] - Show this help
• [bold]suggestions[/bold] - Get smart suggestions
• [bold]conversation[/bold] - Show conversation status
• [bold]nlp off/on[/bold] - Toggle natural language mode
• [bold]clear[/bold] - Clear screen
        """

        console.print(Panel(help_content, border_style="blue"))

    def _show_initial_suggestions(self):
        """Show initial context-aware suggestions"""
        system_context = self._build_system_context()

        # Get suggestions from smart assistant
        suggestions = self.smart_assistant.analyze_context_and_suggest(
            system_context, [], None
        )

        if suggestions:
            self._show_suggestions(
                [s.title for s in suggestions[:4]],
                "Here's what I can help you with:"
            )

    def _show_smart_suggestions(self):
        """Show current smart suggestions"""
        system_context = self._build_system_context()

        # Get conversation history
        conversation_history = []
        if hasattr(self.conversation_manager, 'conversation_history'):
            recent_history = self.conversation_manager.conversation_history[-5:]
            conversation_history = [
                {
                    'command': turn.translated_command.primary_command if turn.translated_command else '',
                    'success': turn.success,
                    'timestamp': turn.timestamp
                }
                for turn in recent_history
            ]

        suggestions = self.smart_assistant.analyze_context_and_suggest(
            system_context, conversation_history, None
        )

        if suggestions:
            console.print("[bold cyan]Smart Suggestions:[/bold cyan]")
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Priority", width=8)
            table.add_column("Suggestion", width=40)
            table.add_column("Impact", width=10)

            for suggestion in suggestions[:5]:
                priority_icon = "🔥" if suggestion.priority == 1 else "⚡" if suggestion.priority == 2 else "💡"
                impact_color = "green" if suggestion.estimated_impact == "high" else "yellow" if suggestion.estimated_impact == "medium" else "blue"

                table.add_row(
                    f"{priority_icon} {suggestion.priority}",
                    suggestion.title,
                    f"[{impact_color}]{suggestion.estimated_impact}[/{impact_color}]"
                )

            console.print(table)

            # Show how to execute suggestions
            console.print("[dim]💡 You can ask me to implement any of these suggestions using natural language![/dim]")
        else:
            console.print("[yellow]No specific suggestions right now. Ask me what you'd like to work on![/yellow]")

    def _show_conversation_status(self):
        """Show current conversation status"""
        summary = self.conversation_manager.get_conversation_summary()

        status_content = f"""
[bold]Conversation Status[/bold]

Session ID: [cyan]{summary['session_id'][:8]}...[/cyan]
Total Interactions: [green]{summary['total_turns']}[/green]
Current State: [yellow]{summary['current_state']}[/yellow]
Success Rate: [{'green' if summary['success_rate'] > 0.8 else 'yellow' if summary['success_rate'] > 0.6 else 'red'}]{summary['success_rate']:.1%}[/]

Recent Commands:
{chr(10).join(f"• {cmd}" for cmd in summary['recent_commands'][-3:]) if summary['recent_commands'] else "None"}

Files Mentioned:
{chr(10).join(f"• {file}" for file in summary['mentioned_files'][:3]) if summary['mentioned_files'] else "None"}
        """

        console.print(Panel(status_content.strip(), border_style="blue"))

    def _show_suggestions(self, suggestions: List[str], title: str = "Suggestions:"):
        """Show a list of suggestions"""
        if not suggestions:
            return

        console.print(f"\n[bold cyan]{title}[/bold cyan]")
        for i, suggestion in enumerate(suggestions[:5], 1):
            console.print(f"  {i}. {suggestion}")
        console.print()

    def _show_help_suggestions(self):
        """Show helpful suggestions when user seems stuck"""
        suggestions = [
            "Try asking: 'What can you help me with?'",
            "Describe what you want to do in plain English",
            "Use '/help' to see all available commands",
            "Ask me to analyze or fix a specific file"
        ]
        self._show_suggestions(suggestions, "Not sure what to ask? Try:")

    def _show_error_recovery_suggestions(self):
        """Show suggestions to recover from errors"""
        suggestions = [
            "Try rephrasing your request",
            "Check if the file exists with 'list files'",
            "Switch modes if needed (chat/propose/execute)",
            "Ask for help with: 'How do I...?'"
        ]
        self._show_suggestions(suggestions, "Let's try a different approach:")

    def _show_post_execution_suggestions(self, executed_command: str, original_input: str):
        """Show suggestions after executing a command"""
        # Get context-aware follow-up suggestions
        system_context = self._build_system_context()

        suggestion_map = {
            'analyze': ["Fix any issues found", "Review code quality", "Write tests"],
            'fix': ["Run tests to verify fixes", "Review the changes", "Commit changes"],
            'test': ["Run the tests", "Check test coverage", "Fix failing tests"],
            'complete': ["Review completed code", "Add documentation", "Write tests"]
        }

        base_cmd = executed_command.split()[0] if executed_command else ''
        suggestions = suggestion_map.get(base_cmd, [])

        if suggestions:
            self._show_suggestions(suggestions, "What's next?")

    def _handle_required_input(self, response: Dict[str, Any]):
        """Handle when the conversation requires additional input"""
        # The conversation manager handles this through its state management
        # This method could be extended for special UI behaviors
        pass


class ResponseFormatter:
    """Formats responses with enhanced styling and structure"""

    def format_response(self, response_text: str, response_data: Dict[str, Any]):
        """Format and display response with appropriate styling"""
        conversation_state = response_data.get('conversation_state', 'listening')

        if conversation_state == 'clarifying':
            self._format_clarification_response(response_text, response_data)
        elif conversation_state == 'confirming':
            self._format_confirmation_response(response_text, response_data)
        elif conversation_state == 'executing':
            self._format_execution_response(response_text, response_data)
        else:
            # Standard response
            console.print(f"[bold green]TinyCode:[/bold green] {response_text}")

    def _format_clarification_response(self, response_text: str, response_data: Dict[str, Any]):
        """Format clarification questions"""
        console.print(f"[bold yellow]❓ TinyCode:[/bold yellow] {response_text}")

        # Show clarification options if available
        questions = response_data.get('clarification_questions', [])
        if len(questions) > 1:
            console.print("[dim]Additional questions:[/dim]")
            for q in questions[1:3]:  # Show up to 2 additional questions
                console.print(f"[dim]  • {q}[/dim]")

    def _format_confirmation_response(self, response_text: str, response_data: Dict[str, Any]):
        """Format confirmation requests"""
        console.print(f"[bold orange3]⚠️  TinyCode:[/bold orange3] {response_text}")

        # Show command preview if available
        command_preview = response_data.get('command_preview')
        if command_preview:
            console.print(f"[dim]Command: `{command_preview}`[/dim]")

    def _format_execution_response(self, response_text: str, response_data: Dict[str, Any]):
        """Format execution responses"""
        console.print(f"[bold blue]🔧 TinyCode:[/bold blue] {response_text}")


# Integration function to replace the standard CLI
def create_enhanced_cli(model: str = "tinyllama:latest") -> EnhancedCLI:
    """Create an enhanced CLI instance"""
    return EnhancedCLI(model)


# Test function
def test_enhanced_cli():
    """Test the enhanced CLI with sample interactions"""
    print("Enhanced CLI Test - Natural Language Processing")
    print("=" * 50)

    # Create enhanced CLI instance
    cli = EnhancedCLI()

    # Test natural language processing without full interactive mode
    test_inputs = [
        "Hello there!",
        "I need to fix bugs in my main.py file",
        "Can you help me write some tests?",
        "What files are in this directory?",
        "How do I analyze my code quality?"
    ]

    for test_input in test_inputs:
        print(f"\nUser: {test_input}")
        print("TinyCode: [Processing through enhanced natural language interface...]")

        # Simulate processing
        system_context = cli._build_system_context()
        response = cli.conversation_manager.process_user_input(test_input, system_context)

        print(f"Response: {response.get('response', 'No response')}")
        if response.get('suggestions'):
            print(f"Suggestions: {response['suggestions'][:2]}")


if __name__ == "__main__":
    test_enhanced_cli()
"""
CLI Enhancements for TinyCode
Provides advanced command completion, history management, and improved user experience
"""

import os
import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from prompt_toolkit import prompt
from prompt_toolkit.completion import Completer, Completion, PathCompleter
from prompt_toolkit.history import FileHistory, History
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.shortcuts import CompleteStyle
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.filters import Condition
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

@dataclass
class CommandUsage:
    """Statistics about command usage"""
    command: str
    count: int
    last_used: datetime
    avg_success_rate: float
    parameters: List[str]

@dataclass
class CommandSuggestion:
    """A command suggestion with context"""
    command: str
    description: str
    example: str
    confidence: float
    category: str

class CompletionType(Enum):
    """Types of completions available"""
    COMMAND = "command"
    FILE_PATH = "file_path"
    GIT_BRANCH = "git_branch"
    PROCESS_NAME = "process_name"
    ENV_VAR = "env_var"
    DEPENDENCY = "dependency"

class TinyCodeCompleter(Completer):
    """Advanced completer for TinyCode commands"""

    def __init__(self, command_registry, git_ops=None, system_integration=None):
        self.command_registry = command_registry
        self.git_ops = git_ops
        self.system_integration = system_integration
        self.path_completer = PathCompleter()

        # Common dependencies for completion
        self.common_dependencies = [
            'python', 'python3', 'pip', 'pip3', 'node', 'npm', 'yarn',
            'git', 'docker', 'docker-compose', 'java', 'javac', 'go',
            'rust', 'cargo', 'ruby', 'gem', 'php', 'composer', 'make',
            'cmake', 'gcc', 'clang', 'vim', 'emacs', 'code', 'curl', 'wget'
        ]

    def get_completions(self, document, complete_event):
        """Get completions for the current input"""
        text = document.text

        # Handle command completion (starts with /)
        if text.startswith('/'):
            yield from self._complete_commands(document)

        # Handle parameter completion for known commands
        elif text and ' ' in text:
            yield from self._complete_command_parameters(document)

        # Default to path completion
        else:
            yield from self.path_completer.get_completions(document, complete_event)

    def _complete_commands(self, document):
        """Complete command names"""
        text = document.text[1:]  # Remove the '/'
        word_before_cursor = document.get_word_before_cursor()

        if word_before_cursor.startswith('/'):
            word_before_cursor = word_before_cursor[1:]

        # Get available commands from registry
        commands = list(self.command_registry.commands.keys())

        # Filter commands that match
        matching_commands = [
            cmd for cmd in commands
            if cmd.startswith(word_before_cursor.lower())
        ]

        for cmd in matching_commands:
            cmd_info = self.command_registry.commands[cmd]
            yield Completion(
                cmd,
                start_position=-len(word_before_cursor),
                display=f"/{cmd}",
                display_meta=cmd_info.description
            )

    def _complete_command_parameters(self, document):
        """Complete parameters for specific commands"""
        text = document.text
        parts = text.split()

        if not parts:
            return

        command = parts[0]
        if command.startswith('/'):
            command = command[1:]

        # Get the current parameter being typed
        current_param = document.get_word_before_cursor()

        # Command-specific completions
        if command in ['find', 'grep']:
            # File pattern completions
            yield from self._complete_file_patterns(current_param)

        elif command in ['git-checkout', 'git-branch']:
            # Git branch completions
            yield from self._complete_git_branches(current_param)

        elif command in ['processes', 'kill', 'monitor']:
            # Process name completions
            yield from self._complete_process_names(current_param)

        elif command in ['env', 'setenv']:
            # Environment variable completions
            yield from self._complete_env_vars(current_param)

        elif command == 'deps':
            # Dependency completions
            yield from self._complete_dependencies(current_param)

        elif command in ['file', 'analyze', 'explain', 'review', 'complete', 'fix', 'refactor', 'test', 'run']:
            # File path completions
            yield from self.path_completer.get_completions(document, None)

    def _complete_file_patterns(self, current_param):
        """Complete file patterns for find/grep commands"""
        patterns = [
            '*.py', '*.js', '*.ts', '*.tsx', '*.jsx', '*.java', '*.cpp', '*.c', '*.h',
            '*.go', '*.rs', '*.rb', '*.php', '*.html', '*.css', '*.scss', '*.md',
            '*.json', '*.xml', '*.yaml', '*.yml', '*.toml', '*.ini', '*.cfg',
            '**/*.py', '**/*.js', 'src/**/*', 'tests/**/*', 'docs/**/*'
        ]

        for pattern in patterns:
            if pattern.startswith(current_param):
                yield Completion(
                    pattern,
                    start_position=-len(current_param),
                    display_meta="File pattern"
                )

    def _complete_git_branches(self, current_param):
        """Complete git branch names"""
        if not self.git_ops:
            return

        try:
            branches = self.git_ops.get_branches(include_remote=False)
            for branch in branches:
                if branch.name.startswith(current_param):
                    yield Completion(
                        branch.name,
                        start_position=-len(current_param),
                        display_meta="Git branch"
                    )
        except:
            pass

    def _complete_process_names(self, current_param):
        """Complete process names"""
        if not self.system_integration:
            return

        try:
            processes = self.system_integration.get_processes(limit=50)
            process_names = set()

            for proc in processes:
                if proc.name.startswith(current_param.lower()):
                    process_names.add(proc.name)

            for name in sorted(process_names):
                yield Completion(
                    name,
                    start_position=-len(current_param),
                    display_meta="Process name"
                )
        except:
            pass

    def _complete_env_vars(self, current_param):
        """Complete environment variable names"""
        if not self.system_integration:
            return

        try:
            env_vars = self.system_integration.get_environment_variables()
            for var in env_vars:
                if var.name.startswith(current_param.upper()):
                    yield Completion(
                        var.name,
                        start_position=-len(current_param),
                        display_meta="Environment variable"
                    )
        except:
            pass

    def _complete_dependencies(self, current_param):
        """Complete dependency names"""
        for dep in self.common_dependencies:
            if dep.startswith(current_param.lower()):
                yield Completion(
                    dep,
                    start_position=-len(current_param),
                    display_meta="Development tool"
                )

class CommandHistoryManager:
    """Advanced command history management with analytics"""

    def __init__(self, history_dir: str = None):
        self.history_dir = Path(history_dir or Path.home() / '.tiny_code')
        self.history_dir.mkdir(exist_ok=True)

        self.history_file = self.history_dir / 'command_history.txt'
        self.analytics_db = self.history_dir / 'command_analytics.db'

        self._init_analytics_db()

    def _init_analytics_db(self):
        """Initialize the analytics database"""
        with sqlite3.connect(str(self.analytics_db)) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS command_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    command TEXT NOT NULL,
                    parameters TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    success BOOLEAN DEFAULT TRUE,
                    execution_time REAL,
                    mode TEXT
                )
            ''')

            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_command_timestamp
                ON command_usage(command, timestamp)
            ''')

    def record_command(self, command: str, parameters: str = "",
                      success: bool = True, execution_time: float = 0,
                      mode: str = "CHAT"):
        """Record a command execution"""
        with sqlite3.connect(str(self.analytics_db)) as conn:
            conn.execute('''
                INSERT INTO command_usage
                (command, parameters, success, execution_time, mode)
                VALUES (?, ?, ?, ?, ?)
            ''', (command, parameters, success, execution_time, mode))

    def get_command_statistics(self, limit: int = 20) -> List[CommandUsage]:
        """Get command usage statistics"""
        with sqlite3.connect(str(self.analytics_db)) as conn:
            cursor = conn.execute('''
                SELECT
                    command,
                    COUNT(*) as count,
                    MAX(timestamp) as last_used,
                    AVG(CASE WHEN success THEN 1.0 ELSE 0.0 END) as success_rate,
                    GROUP_CONCAT(DISTINCT parameters) as params
                FROM command_usage
                WHERE timestamp > datetime('now', '-30 days')
                GROUP BY command
                ORDER BY count DESC
                LIMIT ?
            ''', (limit,))

            results = []
            for row in cursor.fetchall():
                command, count, last_used, success_rate, params = row

                # Parse parameters
                param_list = []
                if params:
                    param_list = list(set(p.strip() for p in params.split(',') if p.strip()))

                results.append(CommandUsage(
                    command=command,
                    count=count,
                    last_used=datetime.fromisoformat(last_used.replace(' ', 'T')),
                    avg_success_rate=success_rate or 0.0,
                    parameters=param_list[:10]  # Limit to 10 unique parameters
                ))

            return results

    def get_command_suggestions(self, context: str = "") -> List[CommandSuggestion]:
        """Get intelligent command suggestions based on usage patterns"""
        suggestions = []

        # Get recent command patterns
        with sqlite3.connect(str(self.analytics_db)) as conn:
            # Most used commands
            cursor = conn.execute('''
                SELECT command, COUNT(*) as count
                FROM command_usage
                WHERE timestamp > datetime('now', '-7 days')
                GROUP BY command
                ORDER BY count DESC
                LIMIT 5
            ''')

            for command, count in cursor.fetchall():
                suggestions.append(CommandSuggestion(
                    command=f"/{command}",
                    description=f"Frequently used command ({count} times this week)",
                    example=f"/{command}",
                    confidence=min(count / 10.0, 1.0),
                    category="frequent"
                ))

        # Context-based suggestions
        context_lower = context.lower()

        if any(word in context_lower for word in ['file', 'code', 'python']):
            suggestions.extend([
                CommandSuggestion("/find", "Find files by pattern", "/find *.py", 0.8, "file"),
                CommandSuggestion("/analyze", "Analyze code structure", "/analyze main.py", 0.7, "code"),
                CommandSuggestion("/review", "Review code quality", "/review src/", 0.6, "code")
            ])

        if any(word in context_lower for word in ['git', 'commit', 'branch']):
            suggestions.extend([
                CommandSuggestion("/git-status", "Show git status", "/git-status", 0.9, "git"),
                CommandSuggestion("/git-log", "Show commit history", "/git-log 10", 0.8, "git"),
                CommandSuggestion("/git-branches", "Show branches", "/git-branches", 0.7, "git")
            ])

        if any(word in context_lower for word in ['system', 'process', 'memory']):
            suggestions.extend([
                CommandSuggestion("/processes", "Show running processes", "/processes python", 0.8, "system"),
                CommandSuggestion("/resources", "Show resource usage", "/resources", 0.7, "system"),
                CommandSuggestion("/sysinfo", "Show system info", "/sysinfo", 0.6, "system")
            ])

        return sorted(suggestions, key=lambda x: x.confidence, reverse=True)

    def search_history(self, query: str, limit: int = 20) -> List[str]:
        """Search command history"""
        with sqlite3.connect(str(self.analytics_db)) as conn:
            cursor = conn.execute('''
                SELECT DISTINCT command || ' ' || parameters as full_command
                FROM command_usage
                WHERE full_command LIKE ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (f'%{query}%', limit))

            return [row[0].strip() for row in cursor.fetchall()]

class CLIEnhancements:
    """Enhanced CLI features for TinyCode"""

    def __init__(self, command_registry, git_ops=None, system_integration=None):
        self.command_registry = command_registry
        self.git_ops = git_ops
        self.system_integration = system_integration

        self.history_manager = CommandHistoryManager()
        self.completer = TinyCodeCompleter(command_registry, git_ops, system_integration)

        # Create enhanced history
        self.history = FileHistory(str(self.history_manager.history_file))

        # Create key bindings
        self.key_bindings = self._create_key_bindings()

        # Create style
        self.style = Style.from_dict({
            'completion-menu.completion': 'bg:#008888 #ffffff',
            'completion-menu.completion.current': 'bg:#00aaaa #000000',
            'completion-menu.scrollbar': 'bg:#88aaaa',
            'completion-menu.meta.completion': 'bg:#999999 #ffffff',
            'completion-menu.meta.completion.current': 'bg:#aaaaaa #000000',
            'prompt': '#0080ff bold',
        })

    def _create_key_bindings(self):
        """Create custom key bindings"""
        bindings = KeyBindings()

        @bindings.add('c-r')  # Ctrl+R for reverse history search
        def _(event):
            """Reverse history search"""
            # This would trigger a history search dialog
            pass

        @bindings.add('c-space')  # Ctrl+Space for command suggestions
        def _(event):
            """Show command suggestions"""
            # This would show intelligent suggestions
            pass

        @bindings.add('f1')  # F1 for help
        def _(event):
            """Show help"""
            event.app.output.write("\n")
            event.app.output.write("TinyCode Quick Help:\n")
            event.app.output.write("  Ctrl+R: Search history\n")
            event.app.output.write("  Ctrl+Space: Show suggestions\n")
            event.app.output.write("  Tab: Complete commands\n")
            event.app.output.write("  F1: This help\n")
            event.app.output.flush()

        return bindings

    def enhanced_prompt(self, message: str = "TinyCode> ", **kwargs):
        """Enhanced prompt with completion and history"""
        return prompt(
            HTML(f'<prompt>{message}</prompt>'),
            history=self.history,
            auto_suggest=AutoSuggestFromHistory(),
            completer=self.completer,
            complete_style=CompleteStyle.MULTI_COLUMN,
            key_bindings=self.key_bindings,
            style=self.style,
            **kwargs
        )

    def show_command_statistics(self, limit: int = 20):
        """Show command usage statistics"""
        stats = self.history_manager.get_command_statistics(limit)

        if not stats:
            console.print("[yellow]No command statistics available[/yellow]")
            return

        table = Table(title="Command Usage Statistics (Last 30 Days)")
        table.add_column("Command", style="cyan")
        table.add_column("Usage Count", justify="right", style="green")
        table.add_column("Success Rate", justify="right", style="yellow")
        table.add_column("Last Used", style="dim")
        table.add_column("Common Parameters", style="blue")

        for stat in stats:
            # Format last used time
            time_diff = datetime.now() - stat.last_used
            if time_diff.days == 0:
                last_used = "Today"
            elif time_diff.days == 1:
                last_used = "Yesterday"
            else:
                last_used = f"{time_diff.days} days ago"

            # Format parameters
            params_display = ", ".join(stat.parameters[:3])
            if len(stat.parameters) > 3:
                params_display += f" (+{len(stat.parameters) - 3} more)"

            table.add_row(
                f"/{stat.command}",
                str(stat.count),
                f"{stat.avg_success_rate * 100:.1f}%",
                last_used,
                params_display or "None"
            )

        console.print(table)

    def show_command_suggestions(self, context: str = ""):
        """Show intelligent command suggestions"""
        suggestions = self.history_manager.get_command_suggestions(context)

        if not suggestions:
            console.print("[yellow]No suggestions available[/yellow]")
            return

        table = Table(title="Command Suggestions")
        table.add_column("Command", style="cyan")
        table.add_column("Description", style="green")
        table.add_column("Example", style="yellow")
        table.add_column("Category", style="blue")
        table.add_column("Confidence", justify="right", style="magenta")

        for suggestion in suggestions[:10]:  # Show top 10
            table.add_row(
                suggestion.command,
                suggestion.description,
                suggestion.example,
                suggestion.category,
                f"{suggestion.confidence * 100:.0f}%"
            )

        console.print(table)

    def search_and_display_history(self, query: str, limit: int = 20):
        """Search and display command history"""
        results = self.history_manager.search_history(query, limit)

        if not results:
            console.print(f"[yellow]No commands found matching '{query}'[/yellow]")
            return

        console.print(f"[bold]Commands matching '{query}':[/bold]")
        for i, command in enumerate(results, 1):
            console.print(f"  {i:2d}. [cyan]{command}[/cyan]")

    def get_completion_help(self, command: str) -> str:
        """Get help text for command completion"""
        if command in self.command_registry.commands:
            cmd_info = self.command_registry.commands[command]
            return f"{cmd_info.description}\nCategory: {cmd_info.category.value}"
        return "Unknown command"

    def record_command_execution(self, command: str, parameters: str = "",
                                success: bool = True, execution_time: float = 0,
                                mode: str = "CHAT"):
        """Record command execution for analytics"""
        self.history_manager.record_command(
            command, parameters, success, execution_time, mode
        )

    def export_history(self, format: str = "json", output_file: str = None) -> str:
        """Export command history in various formats"""
        stats = self.history_manager.get_command_statistics(1000)  # Get all stats

        if format.lower() == "json":
            data = {
                "export_date": datetime.now().isoformat(),
                "total_commands": len(stats),
                "statistics": [
                    {
                        "command": stat.command,
                        "count": stat.count,
                        "last_used": stat.last_used.isoformat(),
                        "success_rate": stat.avg_success_rate,
                        "parameters": stat.parameters
                    }
                    for stat in stats
                ]
            }

            output = json.dumps(data, indent=2)

        elif format.lower() == "csv":
            import csv
            import io

            output_buffer = io.StringIO()
            writer = csv.writer(output_buffer)

            # Write header
            writer.writerow(["Command", "Count", "Last Used", "Success Rate", "Parameters"])

            # Write data
            for stat in stats:
                writer.writerow([
                    stat.command,
                    stat.count,
                    stat.last_used.isoformat(),
                    stat.avg_success_rate,
                    "; ".join(stat.parameters)
                ])

            output = output_buffer.getvalue()

        else:
            # Plain text format
            output = f"TinyCode Command History Export\n"
            output += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            output += f"Total Commands: {len(stats)}\n\n"

            for stat in stats:
                output += f"Command: /{stat.command}\n"
                output += f"  Usage Count: {stat.count}\n"
                output += f"  Success Rate: {stat.avg_success_rate * 100:.1f}%\n"
                output += f"  Last Used: {stat.last_used.strftime('%Y-%m-%d %H:%M:%S')}\n"
                if stat.parameters:
                    output += f"  Parameters: {', '.join(stat.parameters)}\n"
                output += "\n"

        # Save to file if requested
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(output)
            console.print(f"[green]History exported to {output_file}[/green]")

        return output

    def get_usage_analytics(self) -> Dict[str, Any]:
        """Get comprehensive usage analytics"""
        with sqlite3.connect(str(self.history_manager.analytics_db)) as conn:
            # Overall statistics
            cursor = conn.execute('''
                SELECT
                    COUNT(*) as total_commands,
                    COUNT(DISTINCT command) as unique_commands,
                    AVG(CASE WHEN success THEN 1.0 ELSE 0.0 END) as overall_success_rate,
                    AVG(execution_time) as avg_execution_time
                FROM command_usage
            ''')

            overall_stats = cursor.fetchone()

            # Most used commands
            cursor = conn.execute('''
                SELECT command, COUNT(*) as count
                FROM command_usage
                GROUP BY command
                ORDER BY count DESC
                LIMIT 10
            ''')

            top_commands = cursor.fetchall()

            # Usage by mode
            cursor = conn.execute('''
                SELECT mode, COUNT(*) as count
                FROM command_usage
                GROUP BY mode
            ''')

            mode_usage = cursor.fetchall()

            # Daily usage (last 30 days)
            cursor = conn.execute('''
                SELECT
                    DATE(timestamp) as date,
                    COUNT(*) as count
                FROM command_usage
                WHERE timestamp > datetime('now', '-30 days')
                GROUP BY DATE(timestamp)
                ORDER BY date
            ''')

            daily_usage = cursor.fetchall()

        return {
            "overall": {
                "total_commands": overall_stats[0] or 0,
                "unique_commands": overall_stats[1] or 0,
                "success_rate": overall_stats[2] or 0.0,
                "avg_execution_time": overall_stats[3] or 0.0
            },
            "top_commands": [{"command": cmd, "count": count} for cmd, count in top_commands],
            "mode_usage": [{"mode": mode, "count": count} for mode, count in mode_usage],
            "daily_usage": [{"date": date, "count": count} for date, count in daily_usage]
        }
"""Mode management system for TinyCode operation modes"""

from enum import Enum
from typing import Optional, Dict, Any, List
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from .command_registry import CommandRegistry, DangerLevel

console = Console()

class OperationMode(Enum):
    """Available operation modes for TinyCode"""
    CHAT = "chat"          # Safe exploration, Q&A only
    PROPOSE = "propose"    # Plan generation and review
    EXECUTE = "execute"    # Execute approved plans

class ModeManager:
    """Manages operation modes and command permissions"""

    def __init__(self, initial_mode: OperationMode = OperationMode.CHAT):
        self.current_mode = initial_mode
        self.mode_history = [initial_mode]

        # Initialize command registry
        self.command_registry = CommandRegistry()

    def get_current_mode(self) -> OperationMode:
        """Get the current operation mode"""
        return self.current_mode

    def set_mode(self, mode: OperationMode) -> bool:
        """Switch to a different operation mode"""
        if mode == self.current_mode:
            console.print(f"[yellow]Already in {mode.value} mode[/yellow]")
            return False

        self.current_mode = mode
        self.mode_history.append(mode)

        self._show_mode_change(mode)
        return True

    def is_command_allowed(self, command: str) -> bool:
        """Check if a command is allowed in the current mode"""
        return self.command_registry.is_command_allowed_in_mode(command, self.current_mode.value)

    def get_allowed_commands(self) -> List[str]:
        """Get list of commands allowed in current mode"""
        return sorted(self.command_registry.get_commands_by_mode(self.current_mode.value))

    def get_mode_description(self, mode: Optional[OperationMode] = None) -> str:
        """Get description of a mode"""
        if mode is None:
            mode = self.current_mode

        descriptions = {
            OperationMode.CHAT: "Safe exploration and Q&A mode. No file modifications allowed.",
            OperationMode.PROPOSE: "Plan generation mode. Review and approve changes before execution.",
            OperationMode.EXECUTE: "Execution mode. Run approved plans or make immediate changes."
        }

        return descriptions.get(mode, "Unknown mode")

    def get_mode_status(self) -> Dict[str, Any]:
        """Get current mode status information"""
        return {
            "current_mode": self.current_mode.value,
            "description": self.get_mode_description(),
            "allowed_commands": self.get_allowed_commands(),
            "mode_history": [mode.value for mode in self.mode_history[-5:]]  # Last 5 modes
        }

    def _show_mode_change(self, new_mode: OperationMode):
        """Display mode change notification"""
        mode_colors = {
            OperationMode.CHAT: "green",
            OperationMode.PROPOSE: "yellow",
            OperationMode.EXECUTE: "red"
        }

        color = mode_colors.get(new_mode, "white")
        description = self.get_mode_description(new_mode)

        console.print(Panel(
            f"[bold]Mode: {new_mode.value.upper()}[/bold]\n{description}",
            title="Mode Changed",
            border_style=color
        ))

    def show_mode_help(self):
        """Show help for mode system"""
        help_text = """
[bold cyan]TinyCode Operation Modes:[/bold cyan]

[green]• CHAT MODE[/green] (Default)
  - Safe exploration and Q&A about the codebase
  - Code analysis and explanation (read-only)
  - RAG-enhanced responses from knowledge bases
  - No file modifications allowed

[yellow]• PROPOSE MODE[/yellow]
  - Generate execution plans for requested changes
  - Review plans before execution
  - Preview file modifications and impacts
  - Approve or reject proposed changes

[red]• EXECUTE MODE[/red]
  - Execute approved plans from Propose mode
  - Make immediate file modifications (use with caution)
  - Full access to all system capabilities
  - Automatic backups and safety features

[bold cyan]Mode Commands:[/bold cyan]
  /mode chat     - Switch to Chat mode
  /mode propose  - Switch to Propose mode
  /mode execute  - Switch to Execute mode
  /mode status   - Show current mode and available commands
  /mode help     - Show this help
        """

        console.print(Panel(help_text, title="Mode System Help", border_style="blue"))

    def get_command_info(self, command: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a command"""
        cmd_info = self.command_registry.get_command_info(command)
        if not cmd_info:
            return None

        return {
            "name": cmd_info.name,
            "category": cmd_info.category.value,
            "danger_level": cmd_info.danger_level.name,
            "description": cmd_info.description,
            "requires_confirmation": cmd_info.requires_confirmation,
            "requires_backup": cmd_info.requires_backup,
            "allowed_in_current_mode": self.is_command_allowed(command)
        }

    def requires_confirmation(self, command: str) -> bool:
        """Check if a command requires user confirmation"""
        return self.command_registry.requires_confirmation(command)

    def requires_backup(self, command: str) -> bool:
        """Check if a command requires backup before execution"""
        return self.command_registry.requires_backup(command)

    def get_command_danger_level(self, command: str) -> Optional[DangerLevel]:
        """Get the danger level of a command"""
        cmd_info = self.command_registry.get_command_info(command)
        return cmd_info.danger_level if cmd_info else None

    def show_command_registry_stats(self):
        """Show detailed statistics about the command registry"""
        stats = self.command_registry.get_command_stats()

        table = Table(title="Command Registry Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Count", style="yellow")

        table.add_row("Total Commands", str(stats["total_commands"]))
        table.add_row("", "")  # Separator

        # Category breakdown
        table.add_row("[bold]By Category", "")
        for category, count in stats["by_category"].items():
            table.add_row(f"  {category.title()}", str(count))

        table.add_row("", "")  # Separator

        # Danger level breakdown
        table.add_row("[bold]By Danger Level", "")
        for level, count in stats["by_danger_level"].items():
            table.add_row(f"  {level.title()}", str(count))

        table.add_row("", "")  # Separator

        # Safety requirements
        table.add_row("[bold]Safety Requirements", "")
        table.add_row("  Requiring Confirmation", str(stats["requiring_confirmation"]))
        table.add_row("  Requiring Backup", str(stats["requiring_backup"]))

        console.print(table)

    def show_commands_by_danger_level(self, max_level: DangerLevel = DangerLevel.CRITICAL):
        """Show commands grouped by danger level"""
        table = Table(title=f"Commands by Danger Level (up to {max_level.name})")
        table.add_column("Command", style="cyan")
        table.add_column("Category", style="yellow")
        table.add_column("Danger", style="red")
        table.add_column("Description", style="white")

        commands = self.command_registry.get_commands_by_danger_level(max_level)
        commands.sort(key=lambda x: (x.danger_level.value, x.name))

        for cmd in commands:
            danger_color = {
                DangerLevel.NONE: "[green]",
                DangerLevel.LOW: "[yellow]",
                DangerLevel.MEDIUM: "[orange]",
                DangerLevel.HIGH: "[red]",
                DangerLevel.CRITICAL: "[bold red]"
            }.get(cmd.danger_level, "[white]")

            table.add_row(
                cmd.name,
                cmd.category.value,
                f"{danger_color}{cmd.danger_level.name}[/]",
                cmd.description[:50] + "..." if len(cmd.description) > 50 else cmd.description
            )

        console.print(table)
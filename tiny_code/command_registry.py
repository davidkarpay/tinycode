"""Command registry and categorization system for TinyCode"""

from enum import Enum
from typing import Dict, List, Optional, Set
from dataclasses import dataclass

class CommandCategory(Enum):
    """Categories of commands based on their safety and functionality"""
    SAFE = "safe"                    # Read-only, no system changes
    PLANNING = "planning"            # Plan generation and review
    MODIFICATION = "modification"    # File modifications
    EXECUTION = "execution"         # Code execution and system operations
    SYSTEM = "system"               # System-level operations

class DangerLevel(Enum):
    """Danger levels for command operations"""
    NONE = 0      # Completely safe
    LOW = 1       # Minor changes, easily reversible
    MEDIUM = 2    # Significant changes, may affect multiple files
    HIGH = 3      # Major changes, difficult to reverse
    CRITICAL = 4  # System-level changes, potential for damage

@dataclass
class CommandInfo:
    """Information about a command"""
    name: str
    category: CommandCategory
    danger_level: DangerLevel
    description: str
    requires_confirmation: bool = False
    requires_backup: bool = False
    allowed_in_chat: bool = False
    allowed_in_propose: bool = False
    allowed_in_execute: bool = False

class CommandRegistry:
    """Registry for all TinyCode commands with detailed categorization"""

    def __init__(self):
        self.commands: Dict[str, CommandInfo] = {}
        self._register_all_commands()

    def _register_all_commands(self):
        """Register all available commands with their properties"""

        # Safe commands (available in all modes)
        safe_commands = [
            CommandInfo("help", CommandCategory.SAFE, DangerLevel.NONE,
                       "Show help information",
                       allowed_in_chat=True, allowed_in_propose=True, allowed_in_execute=True),

            CommandInfo("analyze", CommandCategory.SAFE, DangerLevel.NONE,
                       "Analyze code files for structure and complexity",
                       allowed_in_chat=True, allowed_in_propose=True, allowed_in_execute=True),

            CommandInfo("explain", CommandCategory.SAFE, DangerLevel.NONE,
                       "Explain code functionality and structure",
                       allowed_in_chat=True, allowed_in_propose=True, allowed_in_execute=True),

            CommandInfo("review", CommandCategory.SAFE, DangerLevel.NONE,
                       "Review code quality and suggest improvements",
                       allowed_in_chat=True, allowed_in_propose=True, allowed_in_execute=True),

            CommandInfo("list", CommandCategory.SAFE, DangerLevel.NONE,
                       "List files in workspace",
                       allowed_in_chat=True, allowed_in_propose=True, allowed_in_execute=True),

            CommandInfo("workspace", CommandCategory.SAFE, DangerLevel.LOW,
                       "Change workspace directory",
                       allowed_in_chat=True, allowed_in_propose=True, allowed_in_execute=True),

            # RAG safe commands
            CommandInfo("rag", CommandCategory.SAFE, DangerLevel.NONE,
                       "Search RAG knowledge base",
                       allowed_in_chat=True, allowed_in_propose=True, allowed_in_execute=True),

            CommandInfo("summarize", CommandCategory.SAFE, DangerLevel.NONE,
                       "Summarize documents using RAG",
                       allowed_in_chat=True, allowed_in_propose=True, allowed_in_execute=True),

            CommandInfo("chat", CommandCategory.SAFE, DangerLevel.NONE,
                       "Chat with documents using RAG",
                       allowed_in_chat=True, allowed_in_propose=True, allowed_in_execute=True),

            CommandInfo("genetics", CommandCategory.SAFE, DangerLevel.NONE,
                       "Explain genetics concepts using knowledge base",
                       allowed_in_chat=True, allowed_in_propose=True, allowed_in_execute=True),

            CommandInfo("knowledge", CommandCategory.SAFE, DangerLevel.NONE,
                       "Switch knowledge base context",
                       allowed_in_chat=True, allowed_in_propose=True, allowed_in_execute=True),

            CommandInfo("rag_stats", CommandCategory.SAFE, DangerLevel.NONE,
                       "Show RAG system statistics",
                       allowed_in_chat=True, allowed_in_propose=True, allowed_in_execute=True),
        ]

        # Planning commands (propose mode and above)
        planning_commands = [
            CommandInfo("plan", CommandCategory.PLANNING, DangerLevel.NONE,
                       "Create execution plan for code changes",
                       allowed_in_propose=True, allowed_in_execute=True),

            CommandInfo("preview", CommandCategory.PLANNING, DangerLevel.NONE,
                       "Preview planned changes",
                       allowed_in_propose=True, allowed_in_execute=True),

            CommandInfo("approve", CommandCategory.PLANNING, DangerLevel.LOW,
                       "Approve a plan for execution",
                       allowed_in_propose=True, allowed_in_execute=True),

            CommandInfo("reject", CommandCategory.PLANNING, DangerLevel.NONE,
                       "Reject a proposed plan",
                       allowed_in_propose=True, allowed_in_execute=True),

            CommandInfo("show_plan", CommandCategory.PLANNING, DangerLevel.NONE,
                       "Show details of a specific plan",
                       allowed_in_propose=True, allowed_in_execute=True),

            CommandInfo("list_plans", CommandCategory.PLANNING, DangerLevel.NONE,
                       "List all available plans",
                       allowed_in_propose=True, allowed_in_execute=True),
        ]

        # Modification commands (execute mode only)
        modification_commands = [
            CommandInfo("complete", CommandCategory.MODIFICATION, DangerLevel.MEDIUM,
                       "Complete code in files", requires_backup=True,
                       allowed_in_execute=True),

            CommandInfo("fix", CommandCategory.MODIFICATION, DangerLevel.MEDIUM,
                       "Fix bugs in code", requires_backup=True,
                       allowed_in_execute=True),

            CommandInfo("refactor", CommandCategory.MODIFICATION, DangerLevel.HIGH,
                       "Refactor code structure", requires_confirmation=True, requires_backup=True,
                       allowed_in_execute=True),

            CommandInfo("file", CommandCategory.MODIFICATION, DangerLevel.LOW,
                       "Load and potentially modify files",
                       allowed_in_execute=True),

            CommandInfo("save", CommandCategory.MODIFICATION, DangerLevel.MEDIUM,
                       "Save generated content to files", requires_backup=True,
                       allowed_in_execute=True),
        ]

        # Execution commands (execute mode only)
        execution_commands = [
            CommandInfo("run", CommandCategory.EXECUTION, DangerLevel.HIGH,
                       "Execute code files", requires_confirmation=True,
                       allowed_in_execute=True),

            CommandInfo("test", CommandCategory.EXECUTION, DangerLevel.MEDIUM,
                       "Generate and run tests",
                       allowed_in_execute=True),

            CommandInfo("execute_plan", CommandCategory.EXECUTION, DangerLevel.HIGH,
                       "Execute approved plans", requires_confirmation=True, requires_backup=True,
                       allowed_in_execute=True),

            # RAG execution commands
            CommandInfo("ingest", CommandCategory.EXECUTION, DangerLevel.MEDIUM,
                       "Ingest documents into RAG system",
                       allowed_in_execute=True),

            CommandInfo("setup_genetics", CommandCategory.EXECUTION, DangerLevel.MEDIUM,
                       "Set up genetics knowledge base",
                       allowed_in_execute=True),
        ]

        # System commands (available in all modes but may have restrictions)
        system_commands = [
            CommandInfo("mode", CommandCategory.SYSTEM, DangerLevel.NONE,
                       "Switch operation modes",
                       allowed_in_chat=True, allowed_in_propose=True, allowed_in_execute=True),

            CommandInfo("clear", CommandCategory.SYSTEM, DangerLevel.NONE,
                       "Clear screen",
                       allowed_in_chat=True, allowed_in_propose=True, allowed_in_execute=True),

            CommandInfo("exit", CommandCategory.SYSTEM, DangerLevel.NONE,
                       "Exit the application",
                       allowed_in_chat=True, allowed_in_propose=True, allowed_in_execute=True),
        ]

        # Register all commands
        all_commands = safe_commands + planning_commands + modification_commands + execution_commands + system_commands

        for cmd in all_commands:
            self.commands[cmd.name] = cmd

    def get_command_info(self, command_name: str) -> Optional[CommandInfo]:
        """Get information about a specific command"""
        return self.commands.get(command_name)

    def is_command_allowed_in_mode(self, command_name: str, mode: str) -> bool:
        """Check if a command is allowed in a specific mode"""
        cmd_info = self.get_command_info(command_name)
        if not cmd_info:
            return False

        mode_attr = f"allowed_in_{mode.lower()}"
        return getattr(cmd_info, mode_attr, False)

    def get_commands_by_category(self, category: CommandCategory) -> List[CommandInfo]:
        """Get all commands in a specific category"""
        return [cmd for cmd in self.commands.values() if cmd.category == category]

    def get_commands_by_mode(self, mode: str) -> List[str]:
        """Get all commands allowed in a specific mode"""
        mode_attr = f"allowed_in_{mode.lower()}"
        return [name for name, cmd in self.commands.items()
                if getattr(cmd, mode_attr, False)]

    def get_commands_by_danger_level(self, max_level: DangerLevel) -> List[CommandInfo]:
        """Get commands up to a certain danger level"""
        return [cmd for cmd in self.commands.values() if cmd.danger_level.value <= max_level.value]

    def requires_confirmation(self, command_name: str) -> bool:
        """Check if a command requires user confirmation"""
        cmd_info = self.get_command_info(command_name)
        return cmd_info.requires_confirmation if cmd_info else False

    def requires_backup(self, command_name: str) -> bool:
        """Check if a command requires backup before execution"""
        cmd_info = self.get_command_info(command_name)
        return cmd_info.requires_backup if cmd_info else False

    def get_command_stats(self) -> Dict[str, int]:
        """Get statistics about command distribution"""
        stats = {
            "total_commands": len(self.commands),
            "by_category": {},
            "by_danger_level": {},
            "requiring_confirmation": 0,
            "requiring_backup": 0
        }

        for cmd in self.commands.values():
            # Category stats
            cat_name = cmd.category.value
            stats["by_category"][cat_name] = stats["by_category"].get(cat_name, 0) + 1

            # Danger level stats
            danger_name = cmd.danger_level.name
            stats["by_danger_level"][danger_name] = stats["by_danger_level"].get(danger_name, 0) + 1

            # Safety requirement stats
            if cmd.requires_confirmation:
                stats["requiring_confirmation"] += 1
            if cmd.requires_backup:
                stats["requiring_backup"] += 1

        return stats
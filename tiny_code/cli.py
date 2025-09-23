"""CLI interface for Tiny Code"""

import click
import sys
import os
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.markdown import Markdown
from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory

from .agent import TinyCodeAgent
from .tools import CodeTools, AdvancedFileOperations
from .mode_manager import ModeManager, OperationMode
from .legal.ooda_processor import LegalOODAProcessor
from .legal.legal_reasoning import LegalReasoningEngine, ReasoningMode
from .legal.tools.citation_validator import CitationValidator
from .legal.privilege_system import PrivilegeProtectionSystem
from .legal.authority_hierarchy import LegalAuthorityHierarchy
from .git_operations import GitOperations
from .system_integration import SystemIntegration
from .cli_enhancements import CLIEnhancements
from .command_registry import CommandRegistry
from .error_handling import ErrorRecoveryManager, ErrorCategory, handle_errors, error_context
from .plan_generator import PlanGenerator, PlanStatus
from .plan_executor import PlanExecutor
from .self_awareness import SelfAwareness
from .plugin_system import PluginManager

console = Console()

class TinyCodeCLI:
    """Command-line interface for Tiny Code"""

    def __init__(self, model: str = "tinyllama:latest"):
        self.agent = TinyCodeAgent(model=model)
        self.tools = CodeTools()
        self.mode_manager = ModeManager(initial_mode=OperationMode.CHAT)
        self.plan_generator = PlanGenerator()
        self.plan_executor = PlanExecutor()
        self.history_file = Path.home() / '.tiny_code_history'
        self.last_response = None  # Track last response for save functionality
        self.self_awareness = SelfAwareness()
        self.command_registry = CommandRegistry()

        # Initialize error handling
        self.error_manager = ErrorRecoveryManager()

        # Initialize git operations (gracefully handle non-git directories)
        try:
            self.git_ops = GitOperations()
        except ValueError:
            self.git_ops = None

        # Initialize system integration
        self.system_integration = SystemIntegration()

        # Initialize CLI enhancements
        self.cli_enhancements = CLIEnhancements(
            self.command_registry,
            self.git_ops,
            self.system_integration
        )

        # Initialize plugin system
        self.plugin_manager = PluginManager(agent=self.agent)
        self.plugin_manager.auto_load_plugins()

        # Initialize legal systems (lazy loaded for performance)
        self._legal_ooda = None
        self._legal_reasoning = None
        self._citation_validator = None
        self._privilege_system = None
        self._authority_hierarchy = None

    @property
    def legal_ooda(self) -> LegalOODAProcessor:
        """Lazy load OODA processor"""
        if self._legal_ooda is None:
            self._legal_ooda = LegalOODAProcessor()
        return self._legal_ooda

    @property
    def legal_reasoning(self) -> LegalReasoningEngine:
        """Lazy load legal reasoning engine"""
        if self._legal_reasoning is None:
            self._legal_reasoning = LegalReasoningEngine()
        return self._legal_reasoning

    @property
    def citation_validator(self) -> CitationValidator:
        """Lazy load citation validator"""
        if self._citation_validator is None:
            self._citation_validator = CitationValidator()
        return self._citation_validator

    @property
    def privilege_system(self) -> PrivilegeProtectionSystem:
        """Lazy load privilege system"""
        if self._privilege_system is None:
            self._privilege_system = PrivilegeProtectionSystem()
        return self._privilege_system

    @property
    def authority_hierarchy(self) -> LegalAuthorityHierarchy:
        """Lazy load authority hierarchy"""
        if self._authority_hierarchy is None:
            self._authority_hierarchy = LegalAuthorityHierarchy()
        return self._authority_hierarchy

    def interactive_mode(self):
        """Run interactive chat mode"""
        console.print(Panel.fit(
            "[bold cyan]Welcome to Tiny Code![/bold cyan]\n"
            "Your AI coding assistant powered by TinyLlama\n"
            "Type 'help' for commands, '/mode help' for mode info, 'exit' to quit",
            border_style="cyan"
        ))

        # Show initial mode
        self.mode_manager._show_mode_change(self.mode_manager.current_mode)

        while True:
            try:
                # Create mode-aware prompt with enhancements
                mode_indicator = f"[{self.mode_manager.current_mode.value}]"
                user_input = self.cli_enhancements.enhanced_prompt(
                    f"Tiny Code {mode_indicator}> "
                ).strip()

                if not user_input:
                    continue

                if user_input.lower() in ['exit', 'quit', 'q']:
                    console.print("[yellow]Goodbye![/yellow]")
                    break

                if user_input.lower() == 'help':
                    self.show_help()
                    continue

                if user_input.lower() == 'clear':
                    console.clear()
                    continue

                if user_input.startswith('/'):
                    with error_context(self.error_manager, f"command: {user_input}", ErrorCategory.USER_INPUT):
                        self.handle_command(user_input[1:])
                else:
                    # Chat mode - safe Q&A only
                    if self.mode_manager.current_mode == OperationMode.CHAT:
                        console.print("[dim]Thinking...[/dim]")
                        response = self.agent.chat(user_input, stream=True)
                        self.last_response = response
                        console.print()
                    else:
                        # In propose or execute mode, treat as potential action request
                        self.handle_user_request(user_input)

            except KeyboardInterrupt:
                console.print("\n[yellow]Use 'exit' to quit[/yellow]")
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")

    def handle_command(self, command: str):
        """Handle special commands with mode awareness"""
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

        commands = {
            # Safe commands (available in all modes)
            'help': self.show_help,
            'analyze': self.analyze_file_cmd,
            'explain': self.explain_code_cmd,
            'review': self.review_code_cmd,
            'principles': self.show_principles_cmd,
            'evaluate': self.evaluate_code_cmd,
            'workspace': self.set_workspace_cmd,
            'list': self.list_files_cmd,
            'capabilities': self.show_capabilities_cmd,
            'commands': self.show_commands_cmd,
            'status': self.show_status_cmd,
            'version': self.show_version_cmd,

            # Advanced file operations (available in all modes)
            'find': self.find_files_cmd,
            'grep': self.grep_files_cmd,
            'tree': self.show_tree_cmd,
            'compare': self.compare_files_cmd,
            'dirstat': self.analyze_directory_cmd,

            # Git operations (safe commands in all modes)
            'git-status': self.git_status_cmd,
            'git-log': self.git_log_cmd,
            'git-branches': self.git_branches_cmd,
            'git-remotes': self.git_remotes_cmd,
            'git-stashes': self.git_stashes_cmd,
            'git-diff': self.git_diff_cmd,
            'git-info': self.git_info_cmd,

            # System integration (safe commands in all modes)
            'env': self.env_cmd,
            'processes': self.processes_cmd,
            'sysinfo': self.sysinfo_cmd,
            'netstat': self.netstat_cmd,
            'deps': self.dependencies_cmd,
            'devenv': self.devenv_cmd,
            'resources': self.resources_cmd,

            # CLI enhancement commands (safe commands in all modes)
            'history': self.history_cmd,
            'stats': self.command_stats_cmd,
            'suggestions': self.suggestions_cmd,
            'export-history': self.export_history_cmd,

            # Error handling commands (safe commands in all modes)
            'errors': self.show_errors_cmd,
            'error-stats': self.error_stats_cmd,
            'recover': self.manual_recovery_cmd,

            # Execution commands (execute mode only)
            'file': self.load_file,
            'complete': self.complete_code_cmd,
            'fix': self.fix_code_cmd,
            'refactor': self.refactor_code_cmd,
            'test': self.generate_tests_cmd,
            'run': self.run_code_cmd,
            'save': self.save_output_cmd,
            'replace': self.replace_in_files_cmd,

            # Git execution commands (execute mode only)
            'git-add': self.git_add_cmd,
            'git-commit': self.git_commit_cmd,
            'git-push': self.git_push_cmd,
            'git-pull': self.git_pull_cmd,
            'git-branch': self.git_branch_cmd,
            'git-checkout': self.git_checkout_cmd,
            'git-stash': self.git_stash_cmd,

            # System execution commands (execute mode only)
            'setenv': self.setenv_cmd,
            'kill': self.kill_process_cmd,
            'exec': self.execute_command_cmd,
            'monitor': self.monitor_process_cmd,

            # Planning commands (propose mode)
            'plan': self.create_plan_cmd,
            'preview': self.preview_plan_cmd,
            'approve': self.approve_plan_cmd,
            'reject': self.reject_plan_cmd,
            'show_plan': self.show_plan_cmd,
            'list_plans': self.list_plans_cmd,
            'execute_plan': self.execute_plan_cmd,

            # Plugin management commands (available in all modes)
            'plugins': self.list_plugins_cmd,
            'plugin-enable': self.enable_plugin_cmd,
            'plugin-disable': self.disable_plugin_cmd,
            'plugin-reload': self.reload_plugin_cmd,
            'plugin-info': self.plugin_info_cmd,

            # Legal commands (paralegal mode and execute mode)
            'validate_citation': self.validate_citation_cmd,
            'authority_hierarchy': self.authority_hierarchy_cmd,
            'legal_search': self.legal_search_cmd,
            # Legal Writing Knowledge System Commands
            'writing_principles': self.writing_principles_cmd,
            'writing_evaluate': self.writing_evaluate_cmd,
            'document_templates': self.document_templates_cmd,
            'generate_template': self.generate_template_cmd,
            'citation_check': self.citation_check_cmd,
            'irac_analysis': self.irac_analysis_cmd,
            'writing_score': self.writing_score_cmd,
            # TODO: Implement these legal command handlers
            # 'legal_reasoning': self.legal_reasoning_cmd,
            # 'constitutional_analysis': self.constitutional_analysis_cmd,
            # 'jurisdiction_compare': self.jurisdiction_compare_cmd,
            # 'precedent_analysis': self.precedent_analysis_cmd,
            # 'statute_interpretation': self.statute_interpretation_cmd,
            'start_case_analysis': self.start_case_analysis_cmd,
            # TODO: Implement these OODA loop command handlers
            # 'observe_facts': self.observe_facts_cmd,
            # 'orient_issues': self.orient_issues_cmd,
            # 'decide_strategy': self.decide_strategy_cmd,
            # 'act_execute': self.act_execute_cmd,
            # 'generate_legal_report': self.generate_legal_report_cmd,
            # 'calculate_deadlines': self.calculate_deadlines_cmd,
            # TODO: Implement these legal document command handlers
            # 'conflict_check': self.conflict_check_cmd,
            # 'motion_template': self.motion_template_cmd,
            # 'legal_memo': self.legal_memo_cmd,
            # 'brief_outline': self.brief_outline_cmd,
            # 'privilege_scan': self.privilege_scan_cmd,
            # 'redact_document': self.redact_document_cmd,
            'privilege_log': self.privilege_log_cmd,
            # TODO: Implement these advanced legal command handlers
            # 'case_tracker': self.case_tracker_cmd,
            # 'billing_tracker': self.billing_tracker_cmd,
            # 'matter_summary': self.matter_summary_cmd,
            # 'florida_statute_lookup': self.florida_statute_lookup_cmd,
            # 'florida_dca_analysis': self.florida_dca_analysis_cmd,
            # 'florida_rules_check': self.florida_rules_check_cmd,
            # 'mega_brief_analysis': self.mega_brief_analysis_cmd,
            # 'hallucination_check': self.hallucination_check_cmd,
            # 'legal_audit': self.legal_audit_cmd
        }

        if cmd in commands:
            import time
            start_time = time.time()
            try:
                commands[cmd](args)
                execution_time = time.time() - start_time
                self.record_command_usage(cmd, args, True, execution_time)
            except Exception as e:
                execution_time = time.time() - start_time
                self.record_command_usage(cmd, args, False, execution_time)
                raise
        else:
            # Check for plugin commands (format: plugin_name:command)
            found_plugin_command = False
            for plugin_cmd_name in self.plugin_manager.command_registry.keys():
                plugin_name, plugin_cmd = plugin_cmd_name.split(':', 1)
                if cmd == plugin_name and args:
                    # Execute plugin command
                    cmd_args = args.split()
                    if cmd_args[0] == plugin_cmd:
                        try:
                            remaining_args = cmd_args[1:] if len(cmd_args) > 1 else []
                            result = self.plugin_manager.execute_command(plugin_cmd_name, *remaining_args)
                            if result:
                                console.print(result)
                            found_plugin_command = True
                            break
                        except Exception as e:
                            console.print(f"[red]Plugin command error: {e}[/red]")
                            found_plugin_command = True
                            break

            if not found_plugin_command:
                console.print(f"[red]Unknown command: {cmd}[/red]")
                console.print("[yellow]Use '/help' to see available commands or '/plugins' to see plugin commands[/yellow]")

    def show_help(self, args=None):
        """Show help information"""
        help_text = """
        [bold cyan]Tiny Code Commands:[/bold cyan]

        [yellow]Chat:[/yellow]
        Just type your question or request

        [yellow]Information Commands:[/yellow]
        /help              - Show this help
        /capabilities      - Show all TinyCode capabilities
        /commands          - Show all available commands
        /status            - Show system status
        /version           - Show version information
        /mode              - Show/change operation mode

        [yellow]File Operations:[/yellow]
        /file <path>       - Load a file for processing
        /analyze <path>    - Analyze a code file
        /explain <path>    - Explain code in file
        /review <path>     - Review code quality
        /workspace <path>  - Set working directory
        /list [pattern]    - List files in workspace

        [yellow]Advanced File Operations:[/yellow]
        /find <pattern>    - Find files using glob patterns
        /grep <pattern>    - Search for text in files
        /tree [path]       - Show directory tree structure
        /compare <f1> <f2> - Compare two files
        /dirstat [path]    - Analyze directory statistics

        [yellow]Git Operations:[/yellow]
        /git-status        - Show git repository status
        /git-log [limit]   - Show commit history
        /git-branches      - Show all branches
        /git-diff [file]   - Show file differences
        /git-info          - Show repository information

        [yellow]Git Commands (Execute Mode):[/yellow]
        /git-add <files>   - Stage files for commit
        /git-commit <msg>  - Create a commit
        /git-push [remote] - Push changes to remote
        /git-pull [remote] - Pull changes from remote
        /git-branch <name> - Create/manage branches
        /git-stash [msg]   - Stash changes

        [yellow]System Integration:[/yellow]
        /env [pattern]     - Show environment variables
        /processes [name]  - Show running processes
        /sysinfo           - Show system information
        /netstat [process] - Show network connections
        /deps <tools>      - Check dependencies
        /devenv            - Show development environment
        /resources         - Show resource usage

        [yellow]CLI Features:[/yellow]
        /history [query]   - Search command history
        /stats             - Show command usage statistics
        /suggestions       - Show intelligent command suggestions
        /export-history    - Export command history

        [yellow]Error Management:[/yellow]
        /errors [limit]    - Show recent errors
        /error-stats       - Show error statistics and recovery rates
        /recover [error-id] - Manually attempt error recovery

        [yellow]System Commands (Execute Mode):[/yellow]
        /setenv <var> <val> - Set environment variable
        /kill <pid>        - Kill process by PID
        /exec <command>    - Execute system command
        /monitor <pid>     - Monitor process performance

        [yellow]Code Operations (Execute Mode):[/yellow]
        /complete <path>   - Complete code in file
        /fix <path>        - Fix bugs in code
        /refactor <path>   - Refactor code
        /test <path>       - Generate tests for code
        /run <path>        - Execute a Python file
        /save <path>       - Save last response to file
        /replace <pattern> - Replace text in multiple files

        [yellow]Planning Commands (Propose/Execute Modes):[/yellow]
        /plan <desc>       - Create execution plan
        /list_plans        - List all plans
        /show_plan <id>    - Show plan details
        /approve <id>      - Approve a plan
        /execute_plan <id> - Execute approved plan

        [yellow]Other:[/yellow]
        clear              - Clear screen
        exit               - Quit the program
        """
        console.print(Panel(help_text, title="Help", border_style="blue"))

    def load_file(self, filepath: str):
        """Load a file for processing"""
        if not filepath:
            filepath = Prompt.ask("Enter file path")

        code = self.tools.read_file(filepath)
        if code:
            self.agent.current_file = filepath
            lines = len(code.splitlines())
            console.print(f"[green]Loaded {filepath} ({lines} lines)[/green]")
            self.tools.display_code(code[:500] + ("..." if len(code) > 500 else ""))
        else:
            console.print(f"[red]Could not load {filepath}[/red]")

    def analyze_file_cmd(self, filepath: str):
        """Analyze a file"""
        if not filepath:
            filepath = self.agent.current_file or Prompt.ask("Enter file path")

        analysis = self.agent.analyze_file(filepath)

        if "error" in analysis:
            console.print(f"[red]{analysis['error']}[/red]")
            return

        table = Table(title=f"Analysis of {filepath}")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="yellow")

        for key, value in analysis['metrics'].items():
            table.add_row(key.capitalize(), str(value))

        console.print(table)

        if analysis['functions']:
            console.print("\n[bold cyan]Functions:[/bold cyan]")
            for func in analysis['functions']:
                console.print(f"  • {func['name']}({', '.join(func['args'])})")

        if analysis['classes']:
            console.print("\n[bold cyan]Classes:[/bold cyan]")
            for cls in analysis['classes']:
                console.print(f"  • {cls['name']}")
                for method in cls['methods']:
                    console.print(f"    - {method}")

    def complete_code_cmd(self, filepath: str):
        """Complete code in a file"""
        if not filepath:
            filepath = self.agent.current_file or Prompt.ask("Enter file path")

        requirements = Prompt.ask("Requirements (optional)", default="")
        result = self.agent.process_file(filepath, 'complete', requirements=requirements)
        console.print(Panel(result, title="Code Completion", border_style="green"))

    def fix_code_cmd(self, filepath: str):
        """Fix bugs in code"""
        if not filepath:
            filepath = self.agent.current_file or Prompt.ask("Enter file path")

        error = Prompt.ask("Describe the error/issue")
        result = self.agent.process_file(filepath, 'fix', error=error)
        console.print(Panel(result, title="Bug Fix", border_style="green"))

    def explain_code_cmd(self, filepath: str):
        """Explain code"""
        if not filepath:
            filepath = self.agent.current_file or Prompt.ask("Enter file path")

        result = self.agent.process_file(filepath, 'explain')
        console.print(Panel(Markdown(result), title="Code Explanation", border_style="blue"))

    def refactor_code_cmd(self, filepath: str):
        """Refactor code"""
        if not filepath:
            filepath = self.agent.current_file or Prompt.ask("Enter file path")

        requirements = Prompt.ask("Refactoring goals (optional)", default="")
        result = self.agent.process_file(filepath, 'refactor', requirements=requirements)
        console.print(Panel(result, title="Refactored Code", border_style="green"))

    def generate_tests_cmd(self, filepath: str):
        """Generate tests for code"""
        if not filepath:
            filepath = self.agent.current_file or Prompt.ask("Enter file path")

        result = self.agent.process_file(filepath, 'test')
        console.print(Panel(result, title="Generated Tests", border_style="green"))

    def review_code_cmd(self, filepath: str):
        """Review code quality"""
        if not filepath:
            filepath = self.agent.current_file or Prompt.ask("Enter file path")

        result = self.agent.process_file(filepath, 'review')
        console.print(Panel(Markdown(result), title="Code Review", border_style="yellow"))

    def run_code_cmd(self, filepath: str):
        """Execute a Python file"""
        if not filepath:
            filepath = self.agent.current_file or Prompt.ask("Enter file path")

        code = self.tools.read_file(filepath)
        if code:
            self.agent.execute_code(code)

    def save_output_cmd(self, filepath: str):
        """Save last output to file"""
        if not filepath:
            filepath = Prompt.ask("Enter output file path")

        # This would need to track last response
        console.print("[yellow]Save functionality requires response tracking[/yellow]")

    def set_workspace_cmd(self, path: str):
        """Set workspace directory"""
        if not path:
            path = Prompt.ask("Enter workspace path")

        self.agent.set_workspace(path)

    def list_files_cmd(self, pattern: str):
        """List files in workspace"""
        if not pattern:
            pattern = "*.py"

        files = self.agent.list_files(pattern)
        if files:
            console.print(f"[cyan]Files matching '{pattern}':[/cyan]")
            for f in files:
                console.print(f"  • {f}")
        else:
            console.print(f"[yellow]No files found matching '{pattern}'[/yellow]")

    def handle_mode_command(self, args: str):
        """Handle mode-related commands"""
        if not args:
            # Show current mode status
            status = self.mode_manager.get_mode_status()
            console.print(Panel(
                f"[bold]Current Mode: {status['current_mode'].upper()}[/bold]\n"
                f"{status['description']}\n\n"
                f"[cyan]Available Commands:[/cyan]\n" +
                ", ".join(status['allowed_commands'][:10]) +
                (f" ... and {len(status['allowed_commands']) - 10} more" if len(status['allowed_commands']) > 10 else ""),
                title="Mode Status",
                border_style="blue"
            ))
            return

        parts = args.split()
        cmd = parts[0].lower()

        if cmd in ['chat', 'propose', 'execute', 'paralegal']:
            mode_map = {
                'chat': OperationMode.CHAT,
                'propose': OperationMode.PROPOSE,
                'execute': OperationMode.EXECUTE,
                'paralegal': OperationMode.PARALEGAL
            }
            self.mode_manager.set_mode(mode_map[cmd])

        elif cmd == 'status':
            status = self.mode_manager.get_mode_status()
            console.print(Panel(
                f"[bold]Current Mode: {status['current_mode'].upper()}[/bold]\n"
                f"{status['description']}\n\n"
                f"[cyan]Available Commands:[/cyan]\n" +
                "\n".join(f"  • {cmd}" for cmd in status['allowed_commands']),
                title="Detailed Mode Status",
                border_style="blue"
            ))

        elif cmd == 'help':
            self.mode_manager.show_mode_help()

        else:
            console.print(f"[red]Unknown mode command: {cmd}[/red]")
            console.print("[yellow]Available: chat, propose, execute, paralegal, status, help[/yellow]")

    def handle_user_request(self, user_input: str):
        """Handle user requests in propose/execute modes"""
        if self.mode_manager.current_mode == OperationMode.PROPOSE:
            # Generate a plan for the request
            console.print(f"[yellow]Generating execution plan...[/yellow]")
            try:
                plan = self.plan_generator.generate_plan(user_input)
                self.plan_generator.show_plan_details(plan)

                console.print(f"\n[cyan]Plan '{plan.id}' created successfully![/cyan]")
                console.print(f"[dim]Use '/approve {plan.id}' to approve or '/reject {plan.id}' to reject[/dim]")

            except Exception as e:
                console.print(f"[red]Error generating plan: {e}[/red]")

        elif self.mode_manager.current_mode == OperationMode.EXECUTE:
            # Execute immediately with confirmation
            console.print(f"[red]Execute mode - immediate execution[/red]")
            console.print(f"[dim]Request: {user_input}[/dim]")

            if Confirm.ask(f"Execute this request immediately?"):
                console.print(f"[dim]Thinking...[/dim]")
                response = self.agent.chat(user_input, stream=True)
                self.last_response = response
                console.print()
            else:
                console.print(f"[yellow]Execution cancelled[/yellow]")

    # Planning command implementations
    def create_plan_cmd(self, args: str):
        """Create a new execution plan"""
        if not args:
            args = Prompt.ask("Enter request to plan")

        try:
            plan = self.plan_generator.generate_plan(args)
            self.plan_generator.show_plan_details(plan)
            console.print(f"\n[green]Plan '{plan.id}' created successfully![/green]")
        except Exception as e:
            console.print(f"[red]Error creating plan: {e}[/red]")

    def preview_plan_cmd(self, args: str):
        """Preview a plan"""
        if not args:
            args = Prompt.ask("Enter plan ID to preview")

        plan = self.plan_generator.get_plan(args)
        if plan:
            self.plan_generator.show_plan_details(plan)
        else:
            console.print(f"[red]Plan '{args}' not found[/red]")

    def approve_plan_cmd(self, args: str):
        """Approve a plan for execution"""
        if not args:
            args = Prompt.ask("Enter plan ID to approve")

        plan = self.plan_generator.get_plan(args)
        if not plan:
            console.print(f"[red]Plan '{args}' not found[/red]")
            return

        if plan.status != PlanStatus.DRAFT and plan.status != PlanStatus.PENDING:
            console.print(f"[red]Plan '{args}' cannot be approved (status: {plan.status.value})[/red]")
            return

        # Show plan details before approval
        self.plan_generator.show_plan_details(plan)

        if Confirm.ask(f"Approve plan '{plan.title}'?"):
            if self.plan_generator.update_plan_status(args, PlanStatus.APPROVED):
                console.print(f"[green]Plan '{args}' approved for execution[/green]")
                console.print(f"[dim]Use '/execute_plan {args}' to execute[/dim]")
            else:
                console.print(f"[red]Error approving plan '{args}'[/red]")
        else:
            console.print(f"[yellow]Plan approval cancelled[/yellow]")

    def reject_plan_cmd(self, args: str):
        """Reject a plan"""
        if not args:
            args = Prompt.ask("Enter plan ID to reject")

        plan = self.plan_generator.get_plan(args)
        if not plan:
            console.print(f"[red]Plan '{args}' not found[/red]")
            return

        if plan.status not in [PlanStatus.DRAFT, PlanStatus.PENDING]:
            console.print(f"[red]Plan '{args}' cannot be rejected (status: {plan.status.value})[/red]")
            return

        reason = Prompt.ask("Reason for rejection (optional)", default="")

        if self.plan_generator.update_plan_status(args, PlanStatus.REJECTED):
            console.print(f"[yellow]Plan '{args}' rejected[/yellow]")
            if reason:
                console.print(f"[dim]Reason: {reason}[/dim]")
        else:
            console.print(f"[red]Error rejecting plan '{args}'[/red]")

    def show_plan_cmd(self, args: str):
        """Show details of a plan"""
        if not args:
            # List all plans first to help user choose
            self.list_plans_cmd("")
            args = Prompt.ask("Enter plan ID to show details")

        plan = self.plan_generator.get_plan(args)
        if plan:
            self.plan_generator.show_plan_details(plan)
        else:
            console.print(f"[red]Plan '{args}' not found[/red]")

    def list_plans_cmd(self, args: str):
        """List all available plans"""
        # Parse optional status filter
        status_filter = None
        if args:
            try:
                status_filter = PlanStatus(args.lower())
            except ValueError:
                console.print(f"[yellow]Invalid status '{args}'. Available: draft, pending, approved, rejected, executed, failed[/yellow]")

        plans = self.plan_generator.list_plans(status_filter)

        if not plans:
            status_text = f" with status '{status_filter.value}'" if status_filter else ""
            console.print(f"[yellow]No plans found{status_text}[/yellow]")
            return

        # Create plans table
        table = Table(title=f"Plans{' - ' + status_filter.value.title() if status_filter else ''}")
        table.add_column("ID", style="cyan")
        table.add_column("Title", style="white")
        table.add_column("Status", style="yellow")
        table.add_column("Risk", style="red")
        table.add_column("Actions", style="green")
        table.add_column("Created", style="dim")

        for plan in plans:
            status_color = {
                PlanStatus.DRAFT: "[yellow]",
                PlanStatus.PENDING: "[blue]",
                PlanStatus.APPROVED: "[green]",
                PlanStatus.REJECTED: "[red]",
                PlanStatus.EXECUTED: "[bright_green]",
                PlanStatus.FAILED: "[bright_red]"
            }.get(plan.status, "[white]")

            table.add_row(
                plan.id,
                plan.title[:40] + "..." if len(plan.title) > 40 else plan.title,
                f"{status_color}{plan.status.value}[/]",
                plan.risk_assessment,
                str(len(plan.actions)),
                plan.created_at.strftime("%m/%d %H:%M")
            )

        console.print(table)

        # Show summary
        total_plans = len(plans)
        if total_plans > 0:
            console.print(f"\n[dim]Showing {total_plans} plan{'s' if total_plans != 1 else ''}[/dim]")
            console.print("[dim]Use '/show_plan <id>' to see details[/dim]")

    def execute_plan_cmd(self, args: str):
        """Execute an approved plan"""
        if not args:
            # Show approved plans
            approved_plans = self.plan_generator.list_plans(PlanStatus.APPROVED)
            if not approved_plans:
                console.print("[yellow]No approved plans available for execution[/yellow]")
                return

            console.print("[cyan]Approved plans available for execution:[/cyan]")
            for plan in approved_plans:
                console.print(f"  {plan.id}: {plan.title}")

            args = Prompt.ask("Enter plan ID to execute")

        plan = self.plan_generator.get_plan(args)
        if not plan:
            console.print(f"[red]Plan '{args}' not found[/red]")
            return

        if plan.status != PlanStatus.APPROVED:
            console.print(f"[red]Plan '{args}' is not approved for execution (status: {plan.status.value})[/red]")
            return

        # Show final confirmation
        self.plan_generator.show_plan_details(plan)

        if not Confirm.ask(f"Execute plan '{plan.title}' with {len(plan.actions)} actions?"):
            console.print("[yellow]Plan execution cancelled[/yellow]")
            return

        # Execute the plan using PlanExecutor
        try:
            console.print(f"[yellow]Executing plan '{plan.title}'...[/yellow]")

            # Update plan status to executing
            self.plan_generator.update_plan_status(args, PlanStatus.PENDING)

            # Execute using PlanExecutor
            execution_log = self.plan_executor.execute_plan(plan)

            # Update plan status based on execution result
            from .plan_executor import ExecutionStatus, ActionResult
            if execution_log.status == ExecutionStatus.COMPLETED:
                self.plan_generator.update_plan_status(args, PlanStatus.EXECUTED)
                console.print(f"[green]✓ Plan '{args}' executed successfully![/green]")

                # Show execution summary
                console.print(Panel(
                    f"[bold]Execution Summary[/bold]\n"
                    f"Duration: {execution_log.total_duration:.2f}s\n"
                    f"Actions completed: {len([a for a in execution_log.action_results if a.result == ActionResult.SUCCESS])}\n"
                    f"Actions failed: {len([a for a in execution_log.action_results if a.result == ActionResult.FAILED])}\n"
                    f"Backup created: {execution_log.backup_directory}",
                    title="Execution Complete",
                    border_style="green"
                ))

            else:
                self.plan_generator.update_plan_status(args, PlanStatus.FAILED)
                console.print(f"[red]✗ Plan '{args}' execution failed[/red]")
                console.print(f"[dim]Error: {execution_log.error_message}[/dim]")

                # Offer rollback option
                if execution_log.backup_directory and Confirm.ask("Rollback changes?"):
                    try:
                        self.plan_executor.rollback_execution(execution_log)
                        console.print("[green]Changes rolled back successfully[/green]")
                    except Exception as rollback_error:
                        console.print(f"[red]Rollback failed: {rollback_error}[/red]")

        except Exception as e:
            self.plan_generator.update_plan_status(args, PlanStatus.FAILED)
            console.print(f"[red]Error executing plan: {e}[/red]")
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")

    def show_capabilities_cmd(self, args: str):
        """Show TinyCode capabilities"""
        capabilities = self.self_awareness.get_capability_summary()
        console.print(Panel(
            Markdown(capabilities),
            title="TinyCode Capabilities",
            border_style="cyan"
        ))

    def show_commands_cmd(self, args: str):
        """Show available commands"""
        commands = self.self_awareness.get_commands_list(dynamic=True)
        console.print(Panel(
            Markdown(commands),
            title="Available Commands",
            border_style="blue"
        ))

    def show_status_cmd(self, args: str):
        """Show system status"""
        mode_status = self.mode_manager.get_mode_status()
        plans = self.plan_generator.list_plans()

        status_info = f"""
**Current Mode**: {mode_status['current_mode'].upper()}
**Mode Description**: {mode_status['description']}

**Plans Summary**:
- Total plans: {len(plans)}
- Draft: {len([p for p in plans if p.status.value == 'draft'])}
- Approved: {len([p for p in plans if p.status.value == 'approved'])}
- Executed: {len([p for p in plans if p.status.value == 'executed'])}

**Workspace**: {self.agent.workspace}
**History File**: {self.history_file}

**Available Commands**: {len(mode_status['allowed_commands'])} commands in current mode
"""
        console.print(Panel(
            Markdown(status_info),
            title="System Status",
            border_style="green"
        ))

    def show_version_cmd(self, args: str):
        """Show version information"""
        version_info = f"""
**TinyCode** - AI Coding Assistant

**Version**: 1.0.0-dev
**Model**: TinyLlama (via Ollama)
**Python**: {sys.version.split()[0]}

**Features**:
- Three-mode operation (Chat/Propose/Execute)
- Plan-based execution with safety checks
- RAG-enhanced responses
- Comprehensive audit logging
- {len(self.self_awareness.command_registry.commands)} registered commands

**Components**:
- Agent: Enhanced with self-awareness
- Tools: File operations, code analysis
- Safety: 4-tier safety system
- Planning: Risk-assessed execution plans
"""
        console.print(Panel(
            Markdown(version_info),
            title="Version Information",
            border_style="magenta"
        ))

    # Advanced File Operations Commands

    def find_files_cmd(self, args: str):
        """Find files using glob patterns"""
        if not args.strip():
            console.print("[red]Please provide a search pattern[/red]")
            console.print("[yellow]Usage: /find *.py[/yellow]")
            console.print("[yellow]       /find src/**/*.js[/yellow]")
            return

        parts = args.split()
        pattern = parts[0]
        base_path = parts[1] if len(parts) > 1 else "."

        console.print(f"[dim]Searching for files matching: {pattern}[/dim]")

        files = AdvancedFileOperations.find_files(pattern, base_path)

        if not files:
            console.print("[yellow]No files found matching the pattern[/yellow]")
            return

        # Display results in a table
        table = Table(title=f"Files matching: {pattern}")
        table.add_column("File", style="cyan")
        table.add_column("Size", justify="right")
        table.add_column("Modified", style="dim")

        for file_match in files[:20]:  # Limit to first 20 results
            size_str = AdvancedFileOperations._format_file_size(file_match.size)
            from datetime import datetime
            modified_str = datetime.fromtimestamp(file_match.modified_time).strftime("%Y-%m-%d %H:%M")
            table.add_row(file_match.path, size_str, modified_str)

        console.print(table)

        if len(files) > 20:
            console.print(f"[dim]... and {len(files) - 20} more files[/dim]")

    def grep_files_cmd(self, args: str):
        """Search for patterns in files"""
        if not args.strip():
            console.print("[red]Please provide a search pattern[/red]")
            console.print("[yellow]Usage: /grep \"search term\"[/yellow]")
            console.print("[yellow]       /grep \"regex\" --regex --files *.py[/yellow]")
            return

        # Parse arguments
        parts = args.split()
        if not parts:
            return

        pattern = parts[0].strip('"\'')
        file_pattern = "**/*"
        case_sensitive = False
        regex = False

        # Parse additional options
        i = 1
        while i < len(parts):
            if parts[i] == "--files" and i + 1 < len(parts):
                file_pattern = parts[i + 1]
                i += 2
            elif parts[i] == "--regex":
                regex = True
                i += 1
            elif parts[i] == "--case":
                case_sensitive = True
                i += 1
            else:
                i += 1

        console.print(f"[dim]Searching for: {pattern} in {file_pattern}[/dim]")

        results = AdvancedFileOperations.grep_files(
            pattern, file_pattern, case_sensitive=case_sensitive, regex=regex
        )

        if not results:
            console.print("[yellow]No matches found[/yellow]")
            return

        # Group results by file
        from collections import defaultdict
        by_file = defaultdict(list)
        for result in results:
            by_file[result.file_path].append(result)

        for file_path, file_results in by_file.items():
            console.print(f"\n[bold cyan]{file_path}[/bold cyan]")
            for result in file_results:
                line_text = result.line_content.strip()
                # Highlight the match
                highlighted = line_text[:result.match_start] + \
                             f"[bold red]{line_text[result.match_start:result.match_end]}[/bold red]" + \
                             line_text[result.match_end:]
                console.print(f"  [dim]{result.line_number:4d}:[/dim] {highlighted}")

    def show_tree_cmd(self, args: str):
        """Show directory tree structure"""
        parts = args.split() if args.strip() else ["."]
        base_path = parts[0]
        max_depth = 3
        show_hidden = False
        file_filter = None

        # Parse options
        i = 1
        while i < len(parts):
            if parts[i] == "--depth" and i + 1 < len(parts):
                max_depth = int(parts[i + 1])
                i += 2
            elif parts[i] == "--hidden":
                show_hidden = True
                i += 1
            elif parts[i] == "--filter" and i + 1 < len(parts):
                file_filter = parts[i + 1]
                i += 2
            else:
                i += 1

        tree = AdvancedFileOperations.show_file_tree(
            base_path, max_depth, show_hidden, file_filter
        )
        console.print(tree)

    def compare_files_cmd(self, args: str):
        """Compare two files"""
        parts = args.split()
        if len(parts) < 2:
            console.print("[red]Please provide two file paths[/red]")
            console.print("[yellow]Usage: /compare file1.py file2.py[/yellow]")
            return

        file1, file2 = parts[0], parts[1]
        context_lines = 3

        if len(parts) > 2 and parts[2].startswith("--context="):
            context_lines = int(parts[2].split("=")[1])

        diff_result = AdvancedFileOperations.compare_files(file1, file2, context_lines)

        if not diff_result.strip():
            console.print("[green]Files are identical[/green]")
        else:
            console.print(f"[bold]Differences between {file1} and {file2}:[/bold]")
            console.print(diff_result)

    def analyze_directory_cmd(self, args: str):
        """Analyze directory structure and statistics"""
        path = args.strip() or "."

        console.print(f"[dim]Analyzing directory: {path}[/dim]")
        stats = AdvancedFileOperations.analyze_directory(path)

        if 'error' in stats:
            console.print(f"[red]Error: {stats['error']}[/red]")
            return

        # Create summary table
        table = Table(title=f"Directory Analysis: {path}")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right")

        table.add_row("Total Files", str(stats['total_files']))
        table.add_row("Total Directories", str(stats['total_directories']))
        table.add_row("Total Size", AdvancedFileOperations._format_file_size(stats['total_size']))

        console.print(table)

        # Show file types
        if stats['file_types']:
            console.print("\n[bold]File Types:[/bold]")
            type_table = Table()
            type_table.add_column("Extension", style="yellow")
            type_table.add_column("Count", justify="right")

            sorted_types = sorted(stats['file_types'].items(), key=lambda x: x[1], reverse=True)
            for ext, count in sorted_types[:10]:  # Top 10
                type_table.add_row(ext or "no extension", str(count))

            console.print(type_table)

        # Show largest files
        if stats['largest_files']:
            console.print("\n[bold]Largest Files:[/bold]")
            for i, file_info in enumerate(stats['largest_files'][:5], 1):
                size_str = AdvancedFileOperations._format_file_size(file_info['size'])
                console.print(f"  {i}. {file_info['path']} ({size_str})")

    def replace_in_files_cmd(self, args: str):
        """Replace text in multiple files (execute mode only)"""
        if not args.strip():
            console.print("[red]Please provide search and replacement patterns[/red]")
            console.print("[yellow]Usage: /replace \"old_text\" \"new_text\" --files *.py[/yellow]")
            console.print("[yellow]       /replace \"regex\" \"replacement\" --regex --files src/**/*.js[/yellow]")
            return

        # Parse arguments - this is a simple parser, could be enhanced
        parts = args.split('"')
        if len(parts) < 4:
            console.print("[red]Please provide both search and replacement patterns in quotes[/red]")
            return

        pattern = parts[1]
        replacement = parts[3]

        # Parse remaining arguments
        remaining = ' '.join(parts[4:]).strip()
        file_pattern = "**/*.py"  # default
        regex = False
        case_sensitive = False

        if "--files" in remaining:
            file_part = remaining.split("--files")[1].strip().split()[0]
            file_pattern = file_part
        if "--regex" in remaining:
            regex = True
        if "--case" in remaining:
            case_sensitive = True

        # First, do a dry run to show what would be changed
        console.print(f"[dim]Performing dry run for pattern: {pattern}[/dim]")
        operations = AdvancedFileOperations.replace_in_files(
            pattern, replacement, file_pattern,
            case_sensitive=case_sensitive, regex=regex, dry_run=True
        )

        if not operations:
            console.print("[yellow]No files would be modified[/yellow]")
            return

        # Show what would be changed
        console.print(f"\n[bold]Would modify {len(operations)} files:[/bold]")
        for op in operations[:5]:  # Show first 5
            console.print(f"  - {op.file_path}")

        if len(operations) > 5:
            console.print(f"  ... and {len(operations) - 5} more files")

        # Ask for confirmation
        if Confirm.ask("\nProceed with replacement?"):
            # Perform actual replacement
            console.print("[dim]Performing replacement...[/dim]")
            final_operations = AdvancedFileOperations.replace_in_files(
                pattern, replacement, file_pattern,
                case_sensitive=case_sensitive, regex=regex, dry_run=False
            )

            successful = sum(1 for op in final_operations if op.success)
            failed = len(final_operations) - successful

            console.print(f"[green]Successfully modified {successful} files[/green]")
            if failed > 0:
                console.print(f"[red]Failed to modify {failed} files[/red]")
        else:
            console.print("[yellow]Replacement cancelled[/yellow]")

    # Git Operations Commands

    def git_status_cmd(self, args: str):
        """Show git repository status"""
        if not self.git_ops:
            console.print("[red]Not in a git repository[/red]")
            return

        try:
            status_files = self.git_ops.get_status()

            if not status_files:
                console.print("[green]Working tree clean[/green]")
                return

            # Create status table
            table = Table(title="Git Status")
            table.add_column("Status", style="yellow")
            table.add_column("File", style="cyan")
            table.add_column("Staged", justify="center")

            for file_status in status_files:
                staged_icon = "✓" if file_status.staged else ""
                table.add_row(
                    file_status.status.value,
                    file_status.path,
                    staged_icon
                )

            console.print(table)

            # Summary
            staged_count = sum(1 for f in status_files if f.staged)
            unstaged_count = sum(1 for f in status_files if f.unstaged)
            untracked_count = sum(1 for f in status_files if f.status.value == "??")

            summary = f"[dim]Staged: {staged_count}, Unstaged: {unstaged_count}, Untracked: {untracked_count}[/dim]"
            console.print(summary)

        except Exception as e:
            console.print(f"[red]Error getting git status: {e}[/red]")

    def git_log_cmd(self, args: str):
        """Show commit history"""
        if not self.git_ops:
            console.print("[red]Not in a git repository[/red]")
            return

        try:
            limit = 10  # default
            branch = None

            if args.strip():
                parts = args.split()
                try:
                    limit = int(parts[0])
                except ValueError:
                    branch = parts[0]

            commits = self.git_ops.get_commits(limit=limit, branch=branch)

            if not commits:
                console.print("[yellow]No commits found[/yellow]")
                return

            console.print(f"[bold]Recent {len(commits)} commits:[/bold]\n")

            for commit in commits:
                # Format commit info
                short_hash = commit.hash[:8]
                date_str = commit.date.strftime("%Y-%m-%d %H:%M")

                console.print(f"[yellow]{short_hash}[/yellow] - [cyan]{commit.message}[/cyan]")
                console.print(f"[dim]  Author: {commit.author} <{commit.email}>[/dim]")
                console.print(f"[dim]  Date: {date_str}[/dim]")
                console.print(f"[dim]  Files: {commit.files_changed}, +{commit.insertions}/-{commit.deletions}[/dim]")
                console.print()

        except Exception as e:
            console.print(f"[red]Error getting git log: {e}[/red]")

    def git_branches_cmd(self, args: str):
        """Show all branches"""
        if not self.git_ops:
            console.print("[red]Not in a git repository[/red]")
            return

        try:
            include_remote = "--remote" in args or "-r" in args
            branches = self.git_ops.get_branches(include_remote=include_remote)

            if not branches:
                console.print("[yellow]No branches found[/yellow]")
                return

            # Separate local and remote branches
            local_branches = [b for b in branches if not b.is_remote]
            remote_branches = [b for b in branches if b.is_remote]

            # Show local branches
            if local_branches:
                table = Table(title="Local Branches")
                table.add_column("Branch", style="cyan")
                table.add_column("Current", justify="center")
                table.add_column("Last Commit", style="dim")
                table.add_column("Date", style="dim")
                table.add_column("Ahead/Behind", style="yellow")

                for branch in local_branches:
                    current_icon = "★" if branch.is_current else ""
                    date_str = branch.last_commit_date.strftime("%Y-%m-%d")
                    ahead_behind = ""
                    if branch.ahead > 0 or branch.behind > 0:
                        ahead_behind = f"↑{branch.ahead} ↓{branch.behind}"

                    table.add_row(
                        branch.name,
                        current_icon,
                        branch.last_commit[:8],
                        date_str,
                        ahead_behind
                    )

                console.print(table)

            # Show remote branches if requested
            if include_remote and remote_branches:
                console.print()
                remote_table = Table(title="Remote Branches")
                remote_table.add_column("Branch", style="magenta")
                remote_table.add_column("Last Commit", style="dim")
                remote_table.add_column("Date", style="dim")

                for branch in remote_branches[:10]:  # Limit remote branches
                    date_str = branch.last_commit_date.strftime("%Y-%m-%d")
                    remote_table.add_row(
                        branch.name,
                        branch.last_commit[:8],
                        date_str
                    )

                console.print(remote_table)

        except Exception as e:
            console.print(f"[red]Error getting branches: {e}[/red]")

    def git_remotes_cmd(self, args: str):
        """Show git remotes"""
        if not self.git_ops:
            console.print("[red]Not in a git repository[/red]")
            return

        try:
            remotes = self.git_ops.get_remotes()

            if not remotes:
                console.print("[yellow]No remotes configured[/yellow]")
                return

            table = Table(title="Git Remotes")
            table.add_column("Name", style="cyan")
            table.add_column("Fetch URL", style="green")
            table.add_column("Push URL", style="yellow")

            for remote in remotes:
                table.add_row(remote.name, remote.fetch_url, remote.push_url)

            console.print(table)

        except Exception as e:
            console.print(f"[red]Error getting remotes: {e}[/red]")

    def git_stashes_cmd(self, args: str):
        """Show git stashes"""
        if not self.git_ops:
            console.print("[red]Not in a git repository[/red]")
            return

        try:
            stashes = self.git_ops.get_stashes()

            if not stashes:
                console.print("[yellow]No stashes found[/yellow]")
                return

            table = Table(title="Git Stashes")
            table.add_column("Index", justify="right")
            table.add_column("Message", style="cyan")
            table.add_column("Branch", style="yellow")
            table.add_column("Date", style="dim")

            for stash in stashes:
                date_str = stash.date.strftime("%Y-%m-%d %H:%M")
                table.add_row(
                    str(stash.index),
                    stash.message,
                    stash.branch,
                    date_str
                )

            console.print(table)

        except Exception as e:
            console.print(f"[red]Error getting stashes: {e}[/red]")

    def git_diff_cmd(self, args: str):
        """Show git diff"""
        if not self.git_ops:
            console.print("[red]Not in a git repository[/red]")
            return

        try:
            parts = args.split() if args.strip() else []
            staged = "--staged" in parts or "--cached" in parts
            file_path = None

            # Find file path (not a flag)
            for part in parts:
                if not part.startswith("--"):
                    file_path = part
                    break

            diff_output = self.git_ops.get_diff(staged=staged, file_path=file_path)

            if not diff_output.strip():
                console.print("[green]No differences found[/green]")
                return

            # Display diff with syntax highlighting
            syntax = Syntax(diff_output, "diff", theme="monokai", line_numbers=False)
            console.print(syntax)

        except Exception as e:
            console.print(f"[red]Error getting diff: {e}[/red]")

    def git_info_cmd(self, args: str):
        """Show repository information"""
        if not self.git_ops:
            console.print("[red]Not in a git repository[/red]")
            return

        try:
            analysis = self.git_ops.analyze_repository()

            # Repository info
            info = analysis.get('info', {})
            console.print(Panel.fit(
                f"[bold cyan]Repository: {info.get('path', 'Unknown')}[/bold cyan]\n"
                f"Current Branch: [yellow]{info.get('current_branch', 'Unknown')}[/yellow]\n"
                f"Remote URL: [green]{info.get('remote_url', 'None')}[/green]\n"
                f"Total Commits: [blue]{info.get('commit_count', 0)}[/blue]\n"
                f"Branches: [magenta]{info.get('branches', 0)}[/magenta] | "
                f"Remotes: [cyan]{info.get('remotes', 0)}[/cyan] | "
                f"Stashes: [yellow]{info.get('stashes', 0)}[/yellow]",
                title="Git Repository Info",
                border_style="blue"
            ))

            # File status summary
            file_status = analysis.get('file_status', {})
            if file_status.get('total_files', 0) > 0:
                console.print(f"\n[bold]Working Directory:[/bold]")
                console.print(f"  Staged: [green]{file_status.get('staged', 0)}[/green]")
                console.print(f"  Unstaged: [yellow]{file_status.get('unstaged', 0)}[/yellow]")
                console.print(f"  Untracked: [red]{file_status.get('untracked', 0)}[/red]")

            # Recent activity
            commit_stats = analysis.get('commit_stats', {})
            if commit_stats:
                console.print(f"\n[bold]Recent Activity (last 50 commits):[/bold]")
                console.print(f"  Total Insertions: [green]+{commit_stats.get('total_insertions', 0)}[/green]")
                console.print(f"  Total Deletions: [red]-{commit_stats.get('total_deletions', 0)}[/red]")
                console.print(f"  Files Changed: [blue]{commit_stats.get('total_files_changed', 0)}[/blue]")
                console.print(f"  Avg Files/Commit: [cyan]{commit_stats.get('avg_files_per_commit', 0):.1f}[/cyan]")

        except Exception as e:
            console.print(f"[red]Error getting repository info: {e}[/red]")

    # Git Execution Commands (Execute Mode Only)

    def git_add_cmd(self, args: str):
        """Stage files for commit"""
        if not self.git_ops:
            console.print("[red]Not in a git repository[/red]")
            return

        if not args.strip():
            console.print("[red]Please specify files to add[/red]")
            console.print("[yellow]Usage: /git-add file1.py file2.py[/yellow]")
            console.print("[yellow]       /git-add . (to add all)[/yellow]")
            return

        try:
            files = args.split()
            success = self.git_ops.stage_files(files)
            if success:
                console.print(f"[green]Successfully staged {len(files)} files[/green]")
        except Exception as e:
            console.print(f"[red]Error staging files: {e}[/red]")

    def git_commit_cmd(self, args: str):
        """Create a commit"""
        if not self.git_ops:
            console.print("[red]Not in a git repository[/red]")
            return

        if not args.strip():
            console.print("[red]Please provide a commit message[/red]")
            console.print("[yellow]Usage: /git-commit \"Your commit message\"[/yellow]")
            return

        try:
            # Extract message (handle quotes)
            message = args.strip()
            if message.startswith('"') and message.endswith('"'):
                message = message[1:-1]

            success = self.git_ops.commit(message)
            if success:
                console.print(f"[green]Created commit: {message}[/green]")
        except Exception as e:
            console.print(f"[red]Error creating commit: {e}[/red]")

    def git_push_cmd(self, args: str):
        """Push changes to remote"""
        if not self.git_ops:
            console.print("[red]Not in a git repository[/red]")
            return

        try:
            parts = args.split() if args.strip() else []
            remote = parts[0] if parts else "origin"
            branch = parts[1] if len(parts) > 1 else None
            set_upstream = "--set-upstream" in parts or "-u" in parts

            if Confirm.ask(f"Push to {remote}?"):
                success = self.git_ops.push(remote, branch, set_upstream)
                if success:
                    console.print(f"[green]Successfully pushed to {remote}[/green]")
        except Exception as e:
            console.print(f"[red]Error pushing: {e}[/red]")

    def git_pull_cmd(self, args: str):
        """Pull changes from remote"""
        if not self.git_ops:
            console.print("[red]Not in a git repository[/red]")
            return

        try:
            parts = args.split() if args.strip() else []
            remote = parts[0] if parts else "origin"
            branch = parts[1] if len(parts) > 1 else None

            success = self.git_ops.pull(remote, branch)
            if success:
                console.print(f"[green]Successfully pulled from {remote}[/green]")
        except Exception as e:
            console.print(f"[red]Error pulling: {e}[/red]")

    def git_branch_cmd(self, args: str):
        """Create or manage branches"""
        if not self.git_ops:
            console.print("[red]Not in a git repository[/red]")
            return

        if not args.strip():
            # Just show current branch
            try:
                branches = self.git_ops.get_branches(include_remote=False)
                current = next((b.name for b in branches if b.is_current), "unknown")
                console.print(f"[green]Current branch: {current}[/green]")
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
            return

        try:
            parts = args.split()
            action = parts[0] if parts else ""

            if action == "create":
                if len(parts) < 2:
                    console.print("[red]Please specify branch name[/red]")
                    return
                branch_name = parts[1]
                from_branch = parts[2] if len(parts) > 2 else None
                success = self.git_ops.create_branch(branch_name, from_branch)

            elif action == "delete":
                if len(parts) < 2:
                    console.print("[red]Please specify branch name[/red]")
                    return
                branch_name = parts[1]
                force = "--force" in parts or "-f" in parts
                if Confirm.ask(f"Delete branch '{branch_name}'?"):
                    success = self.git_ops.delete_branch(branch_name, force)

            else:
                # Assume it's a branch name to switch to
                branch_name = action
                success = self.git_ops.switch_branch(branch_name)

        except Exception as e:
            console.print(f"[red]Error with branch operation: {e}[/red]")

    def git_checkout_cmd(self, args: str):
        """Checkout/switch to branch"""
        if not self.git_ops:
            console.print("[red]Not in a git repository[/red]")
            return

        if not args.strip():
            console.print("[red]Please specify branch name[/red]")
            console.print("[yellow]Usage: /git-checkout branch-name[/yellow]")
            return

        try:
            branch_name = args.strip()
            success = self.git_ops.switch_branch(branch_name)
            if success:
                console.print(f"[green]Switched to branch '{branch_name}'[/green]")
        except Exception as e:
            console.print(f"[red]Error checking out branch: {e}[/red]")

    def git_stash_cmd(self, args: str):
        """Stash operations"""
        if not self.git_ops:
            console.print("[red]Not in a git repository[/red]")
            return

        try:
            parts = args.split() if args.strip() else ["save"]
            action = parts[0]

            if action == "save" or action == "push":
                message = " ".join(parts[1:]) if len(parts) > 1 else None
                include_untracked = "--include-untracked" in parts or "-u" in parts
                success = self.git_ops.create_stash(message, include_untracked)

            elif action == "apply":
                stash_index = int(parts[1]) if len(parts) > 1 else 0
                success = self.git_ops.apply_stash(stash_index)

            elif action == "drop":
                stash_index = int(parts[1]) if len(parts) > 1 else 0
                if Confirm.ask(f"Drop stash@{{{stash_index}}}?"):
                    success = self.git_ops.drop_stash(stash_index)

            elif action == "list":
                stashes = self.git_ops.get_stashes()
                if stashes:
                    for stash in stashes:
                        console.print(f"stash@{{{stash.index}}}: {stash.message}")
                else:
                    console.print("[yellow]No stashes found[/yellow]")

            else:
                console.print("[red]Unknown stash action[/red]")
                console.print("[yellow]Available actions: save, apply, drop, list[/yellow]")

        except Exception as e:
            console.print(f"[red]Error with stash operation: {e}[/red]")

    # System Integration Commands

    def env_cmd(self, args: str):
        """Show environment variables"""
        try:
            pattern = args.strip() if args.strip() else None
            show_sensitive = "--show-sensitive" in args

            env_vars = self.system_integration.get_environment_variables(
                filter_pattern=pattern,
                show_sensitive=show_sensitive
            )

            if not env_vars:
                console.print("[yellow]No environment variables found[/yellow]")
                return

            # Create table
            table = Table(title=f"Environment Variables{f' (filtered: {pattern})' if pattern else ''}")
            table.add_column("Variable", style="cyan")
            table.add_column("Value", style="green")
            table.add_column("Type", style="yellow")

            for var in env_vars[:50]:  # Limit display
                var_type = []
                if var.is_path:
                    var_type.append("PATH")
                if var.is_sensitive:
                    var_type.append("SENSITIVE")

                # Truncate long values
                display_value = var.value
                if len(display_value) > 100:
                    display_value = display_value[:97] + "..."

                table.add_row(
                    var.name,
                    display_value,
                    " | ".join(var_type) if var_type else "NORMAL"
                )

            console.print(table)

            if len(env_vars) > 50:
                console.print(f"[dim]... and {len(env_vars) - 50} more variables[/dim]")

        except Exception as e:
            console.print(f"[red]Error getting environment variables: {e}[/red]")

    def processes_cmd(self, args: str):
        """Show running processes"""
        try:
            parts = args.split() if args.strip() else []
            filter_name = None
            sort_by = "cpu"
            limit = 20

            # Parse arguments
            i = 0
            while i < len(parts):
                if parts[i] == "--sort" and i + 1 < len(parts):
                    sort_by = parts[i + 1]
                    i += 2
                elif parts[i] == "--limit" and i + 1 < len(parts):
                    limit = int(parts[i + 1])
                    i += 2
                elif not parts[i].startswith("--"):
                    filter_name = parts[i]
                    i += 1
                else:
                    i += 1

            processes = self.system_integration.get_processes(
                filter_name=filter_name,
                sort_by=sort_by,
                limit=limit
            )

            if not processes:
                console.print("[yellow]No processes found[/yellow]")
                return

            # Create table
            table = Table(title=f"Running Processes (sorted by {sort_by})")
            table.add_column("PID", justify="right")
            table.add_column("Name", style="cyan")
            table.add_column("Status", style="yellow")
            table.add_column("CPU%", justify="right", style="green")
            table.add_column("Memory%", justify="right", style="blue")
            table.add_column("Memory MB", justify="right", style="magenta")
            table.add_column("User", style="dim")

            for proc in processes:
                table.add_row(
                    str(proc.pid),
                    proc.name,
                    proc.status,
                    f"{proc.cpu_percent:.1f}",
                    f"{proc.memory_percent:.1f}",
                    f"{proc.memory_mb:.1f}",
                    proc.username or "unknown"
                )

            console.print(table)

        except Exception as e:
            console.print(f"[red]Error getting processes: {e}[/red]")

    def sysinfo_cmd(self, args: str):
        """Show system information"""
        try:
            info = self.system_integration.get_system_info()

            # Platform information
            platform_info = info['platform']
            console.print(Panel.fit(
                f"[bold cyan]System: {platform_info['system']} {platform_info['release']}[/bold cyan]\n"
                f"Machine: [yellow]{platform_info['machine']}[/yellow]\n"
                f"Processor: [green]{platform_info['processor']}[/green]\n"
                f"Architecture: [blue]{platform_info['architecture'][0]}[/blue]",
                title="Platform Information",
                border_style="blue"
            ))

            # Hardware information
            hardware_info = info['hardware']
            console.print(Panel.fit(
                f"[bold cyan]CPU Cores: {hardware_info['cpu_count']} physical, {hardware_info['cpu_count_logical']} logical[/bold cyan]\n"
                f"Total Memory: [yellow]{hardware_info['memory_total_gb']} GB[/yellow]",
                title="Hardware Information",
                border_style="green"
            ))

            # Python information
            python_info = info['python']
            console.print(Panel.fit(
                f"[bold cyan]Version: {python_info['version'].split()[0]}[/bold cyan]\n"
                f"Executable: [yellow]{python_info['executable']}[/yellow]",
                title="Python Information",
                border_style="yellow"
            ))

            # Disk usage
            if info['disk_usage']:
                disk_table = Table(title="Disk Usage")
                disk_table.add_column("Mount Point", style="cyan")
                disk_table.add_column("Total", justify="right")
                disk_table.add_column("Free", justify="right")
                disk_table.add_column("Used %", justify="right", style="yellow")

                for mount, usage in info['disk_usage'].items():
                    disk_table.add_row(
                        mount,
                        f"{usage['total_gb']} GB",
                        f"{usage['free_gb']} GB",
                        f"{usage['percent']}%"
                    )

                console.print(disk_table)

        except Exception as e:
            console.print(f"[red]Error getting system information: {e}[/red]")

    def netstat_cmd(self, args: str):
        """Show network connections"""
        try:
            process_name = args.strip() if args.strip() else None

            connections = self.system_integration.get_network_connections(process_name)

            if not connections:
                console.print("[yellow]No network connections found[/yellow]")
                return

            # Create table
            table = Table(title=f"Network Connections{f' for {process_name}' if process_name else ''}")
            table.add_column("PID", justify="right")
            table.add_column("Process", style="cyan")
            table.add_column("Type", style="yellow")
            table.add_column("Local Address", style="green")
            table.add_column("Remote Address", style="blue")
            table.add_column("Status", style="magenta")

            for conn in connections[:50]:  # Limit display
                table.add_row(
                    str(conn['pid']) if conn['pid'] else "N/A",
                    conn['process'],
                    conn['type'],
                    conn['local_addr'],
                    conn['remote_addr'],
                    conn['status']
                )

            console.print(table)

            if len(connections) > 50:
                console.print(f"[dim]... and {len(connections) - 50} more connections[/dim]")

        except Exception as e:
            console.print(f"[red]Error getting network connections: {e}[/red]")

    def dependencies_cmd(self, args: str):
        """Check dependencies"""
        if not args.strip():
            console.print("[red]Please specify dependencies to check[/red]")
            console.print("[yellow]Usage: /deps python git node docker[/yellow]")
            return

        try:
            dependencies = args.split()
            results = self.system_integration.check_dependencies(dependencies)

            # Create table
            table = Table(title="Dependency Check")
            table.add_column("Tool", style="cyan")
            table.add_column("Available", justify="center")
            table.add_column("Path", style="yellow")
            table.add_column("Version", style="green")

            for dep, result in results.items():
                available_icon = "✓" if result['available'] else "✗"
                available_style = "green" if result['available'] else "red"

                table.add_row(
                    dep,
                    f"[{available_style}]{available_icon}[/{available_style}]",
                    result['path'] or "N/A",
                    result['version'] or result.get('error', 'N/A')
                )

            console.print(table)

        except Exception as e:
            console.print(f"[red]Error checking dependencies: {e}[/red]")

    def devenv_cmd(self, args: str):
        """Show development environment information"""
        try:
            env_info = self.system_integration.get_development_environment_info()

            # Virtual environment info
            venv = env_info['virtual_environment']
            if venv['active']:
                console.print(Panel.fit(
                    f"[bold green]Active Virtual Environment[/bold green]\n"
                    f"Path: [yellow]{venv['path']}[/yellow]\n"
                    f"Prompt: [cyan]{venv.get('prompt', 'N/A')}[/cyan]",
                    title="Virtual Environment",
                    border_style="green"
                ))
            else:
                console.print(Panel.fit(
                    "[bold red]No Virtual Environment Active[/bold red]",
                    title="Virtual Environment",
                    border_style="red"
                ))

            # Development tools
            tools = env_info['tools']
            available_tools = {k: v for k, v in tools.items() if v['available']}
            missing_tools = {k: v for k, v in tools.items() if not v['available']}

            if available_tools:
                tool_table = Table(title="Available Development Tools")
                tool_table.add_column("Tool", style="cyan")
                tool_table.add_column("Version", style="green")
                tool_table.add_column("Path", style="yellow")

                for tool, info in available_tools.items():
                    tool_table.add_row(
                        tool,
                        info['version'] or "Unknown",
                        info['path']
                    )

                console.print(tool_table)

            if missing_tools:
                console.print(f"\n[bold red]Missing Tools:[/bold red]")
                for tool in missing_tools.keys():
                    console.print(f"  - {tool}")

            # Important environment variables
            if env_info['environment_variables']:
                console.print(f"\n[bold]Key Environment Variables:[/bold]")
                for var, value in env_info['environment_variables'].items():
                    display_value = value[:50] + "..." if len(value) > 50 else value
                    console.print(f"  [cyan]{var}[/cyan]: [yellow]{display_value}[/yellow]")

        except Exception as e:
            console.print(f"[red]Error getting development environment info: {e}[/red]")

    def resources_cmd(self, args: str):
        """Show resource usage summary"""
        try:
            summary = self.system_integration.get_resource_usage_summary()
            metrics = summary['system_metrics']

            # System metrics
            console.print(Panel.fit(
                f"[bold cyan]CPU Usage: {metrics.cpu_percent:.1f}%[/bold cyan]\n"
                f"Memory: [yellow]{metrics.memory_percent:.1f}% ({self.system_integration.format_bytes(metrics.memory_total - metrics.memory_available)} / {self.system_integration.format_bytes(metrics.memory_total)})[/yellow]\n"
                f"Disk: [green]{metrics.disk_percent:.1f}% ({self.system_integration.format_bytes(metrics.disk_total - metrics.disk_free)} / {self.system_integration.format_bytes(metrics.disk_total)})[/green]\n"
                f"Network: [blue]↑{self.system_integration.format_bytes(metrics.network_sent)} ↓{self.system_integration.format_bytes(metrics.network_recv)}[/blue]",
                title="System Resource Usage",
                border_style="blue"
            ))

            # Top CPU processes
            if summary['top_cpu_processes']:
                cpu_table = Table(title="Top CPU Processes")
                cpu_table.add_column("Process", style="cyan")
                cpu_table.add_column("PID", justify="right")
                cpu_table.add_column("CPU%", justify="right", style="red")
                cpu_table.add_column("Memory MB", justify="right", style="yellow")

                for proc in summary['top_cpu_processes']:
                    cpu_table.add_row(
                        proc['name'],
                        str(proc['pid']),
                        f"{proc['cpu_percent']:.1f}%",
                        f"{proc['memory_mb']:.1f}"
                    )

                console.print(cpu_table)

            # Top memory processes
            if summary['top_memory_processes']:
                mem_table = Table(title="Top Memory Processes")
                mem_table.add_column("Process", style="cyan")
                mem_table.add_column("PID", justify="right")
                mem_table.add_column("Memory MB", justify="right", style="blue")
                mem_table.add_column("CPU%", justify="right", style="green")

                for proc in summary['top_memory_processes']:
                    mem_table.add_row(
                        proc['name'],
                        str(proc['pid']),
                        f"{proc['memory_mb']:.1f}",
                        f"{proc['cpu_percent']:.1f}%"
                    )

                console.print(mem_table)

        except Exception as e:
            console.print(f"[red]Error getting resource usage: {e}[/red]")

    # System Execution Commands (Execute Mode Only)

    def setenv_cmd(self, args: str):
        """Set environment variable"""
        parts = args.split(None, 1) if args.strip() else []
        if len(parts) < 2:
            console.print("[red]Please provide variable name and value[/red]")
            console.print("[yellow]Usage: /setenv VARIABLE_NAME value[/yellow]")
            return

        try:
            var_name, var_value = parts[0], parts[1]
            persistent = "--persistent" in args

            success = self.system_integration.set_environment_variable(
                var_name, var_value, persistent
            )

            if success:
                console.print(f"[green]Set {var_name}={var_value}[/green]")
                if persistent:
                    console.print("[yellow]Remember to restart your shell for persistent changes[/yellow]")
        except Exception as e:
            console.print(f"[red]Error setting environment variable: {e}[/red]")

    def kill_process_cmd(self, args: str):
        """Kill process by PID"""
        if not args.strip():
            console.print("[red]Please provide process PID[/red]")
            console.print("[yellow]Usage: /kill 1234[/yellow]")
            return

        try:
            parts = args.split()
            pid = int(parts[0])
            force = "--force" in parts or "-9" in parts

            if Confirm.ask(f"Kill process {pid}{'(forced)' if force else ''}?"):
                success = self.system_integration.kill_process(pid, force)
                if success:
                    console.print(f"[green]Process {pid} terminated[/green]")
        except ValueError:
            console.print("[red]Invalid PID[/red]")
        except Exception as e:
            console.print(f"[red]Error killing process: {e}[/red]")

    def execute_command_cmd(self, args: str):
        """Execute system command"""
        if not args.strip():
            console.print("[red]Please provide command to execute[/red]")
            console.print("[yellow]Usage: /exec ls -la[/yellow]")
            return

        try:
            # Parse options
            timeout = 30
            capture = True

            if "--timeout" in args:
                parts = args.split()
                for i, part in enumerate(parts):
                    if part == "--timeout" and i + 1 < len(parts):
                        timeout = int(parts[i + 1])
                        # Remove timeout args from command
                        args = " ".join(parts[:i] + parts[i + 2:])
                        break

            if "--no-capture" in args:
                capture = False
                args = args.replace("--no-capture", "").strip()

            console.print(f"[dim]Executing: {args}[/dim]")

            result = self.system_integration.run_command(
                args, timeout=timeout, capture_output=capture
            )

            # Display results
            console.print(f"\n[bold]Exit Code:[/bold] {result['returncode']}")
            console.print(f"[bold]Execution Time:[/bold] {result['execution_time']}s")

            if result['stdout']:
                console.print(f"\n[bold green]STDOUT:[/bold green]")
                console.print(result['stdout'])

            if result['stderr']:
                console.print(f"\n[bold red]STDERR:[/bold red]")
                console.print(result['stderr'])

            if result['success']:
                console.print("[green]Command completed successfully[/green]")
            else:
                console.print("[red]Command failed[/red]")

        except Exception as e:
            console.print(f"[red]Error executing command: {e}[/red]")

    def monitor_process_cmd(self, args: str):
        """Monitor process performance"""
        if not args.strip():
            console.print("[red]Please provide process PID[/red]")
            console.print("[yellow]Usage: /monitor 1234[/yellow]")
            console.print("[yellow]       /monitor 1234 --duration 60[/yellow]")
            return

        try:
            parts = args.split()
            pid = int(parts[0])
            duration = 30

            # Parse duration
            if "--duration" in parts:
                for i, part in enumerate(parts):
                    if part == "--duration" and i + 1 < len(parts):
                        duration = int(parts[i + 1])
                        break

            console.print(f"[dim]Monitoring process {pid} for {duration} seconds...[/dim]")

            # Check if process exists
            try:
                import psutil
                proc = psutil.Process(pid)
                console.print(f"[green]Monitoring: {proc.name()} (PID: {pid})[/green]")
            except psutil.NoSuchProcess:
                console.print(f"[red]Process {pid} not found[/red]")
                return

            metrics = self.system_integration.monitor_process(pid, duration)

            if not metrics:
                console.print("[red]Process terminated during monitoring[/red]")
                return

            # Display summary
            if metrics['cpu_percent']:
                avg_cpu = sum(metrics['cpu_percent']) / len(metrics['cpu_percent'])
                max_cpu = max(metrics['cpu_percent'])
                console.print(f"[bold]CPU Usage:[/bold] Avg: {avg_cpu:.1f}%, Max: {max_cpu:.1f}%")

            if metrics['memory_mb']:
                avg_memory = sum(metrics['memory_mb']) / len(metrics['memory_mb'])
                max_memory = max(metrics['memory_mb'])
                console.print(f"[bold]Memory Usage:[/bold] Avg: {avg_memory:.1f}MB, Max: {max_memory:.1f}MB")

            console.print(f"[green]Monitoring completed ({len(metrics['timestamps'])} samples)[/green]")

        except ValueError:
            console.print("[red]Invalid PID[/red]")
        except Exception as e:
            console.print(f"[red]Error monitoring process: {e}[/red]")

    # CLI Enhancement Commands

    def history_cmd(self, args: str):
        """Search command history"""
        try:
            query = args.strip()
            if not query:
                console.print("[yellow]Please provide a search query[/yellow]")
                console.print("[yellow]Usage: /history git[/yellow]")
                console.print("[yellow]       /history \"file operations\"[/yellow]")
                return

            self.cli_enhancements.search_and_display_history(query)

        except Exception as e:
            console.print(f"[red]Error searching history: {e}[/red]")

    def command_stats_cmd(self, args: str):
        """Show command usage statistics"""
        try:
            limit = 20
            if args.strip():
                try:
                    limit = int(args.strip())
                except ValueError:
                    console.print("[yellow]Invalid limit, using default (20)[/yellow]")

            self.cli_enhancements.show_command_statistics(limit)

        except Exception as e:
            console.print(f"[red]Error showing statistics: {e}[/red]")

    def suggestions_cmd(self, args: str):
        """Show intelligent command suggestions"""
        try:
            context = args.strip()
            self.cli_enhancements.show_command_suggestions(context)

        except Exception as e:
            console.print(f"[red]Error showing suggestions: {e}[/red]")

    def export_history_cmd(self, args: str):
        """Export command history"""
        try:
            parts = args.split() if args.strip() else []
            format_type = "json"
            output_file = None

            # Parse arguments
            i = 0
            while i < len(parts):
                if parts[i] == "--format" and i + 1 < len(parts):
                    format_type = parts[i + 1]
                    i += 2
                elif parts[i] == "--output" and i + 1 < len(parts):
                    output_file = parts[i + 1]
                    i += 2
                else:
                    i += 1

            if not output_file:
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"tinycoder_history_{timestamp}.{format_type}"

            if format_type not in ["json", "csv", "txt"]:
                console.print("[red]Invalid format. Use: json, csv, or txt[/red]")
                return

            result = self.cli_enhancements.export_history(format_type, output_file)

            if not output_file:
                # Display output
                console.print(f"[bold]Command History Export ({format_type.upper()}):[/bold]")
                console.print(result[:1000])  # Show first 1000 characters
                if len(result) > 1000:
                    console.print("[dim]... (truncated, use --output to save full export)[/dim]")

        except Exception as e:
            console.print(f"[red]Error exporting history: {e}[/red]")

    # Legal System Commands (Paralegal Mode)

    def validate_citation_cmd(self, args: str):
        """Validate legal citations for accuracy and format"""
        if not args.strip():
            console.print("[red]Please provide a citation to validate[/red]")
            console.print("[yellow]Usage: /validate_citation \"Smith v. Jones, 123 So. 3d 456 (Fla. 1st DCA 2019)\"[/yellow]")
            return

        try:
            citation = args.strip().strip('"\'')
            result = self.citation_validator.validate_citation(citation)

            # Display validation results
            if result.is_valid:
                console.print(f"[green]✓ Valid citation format[/green]")
                console.print(f"[bold]Type:[/bold] {result.citation_type}")
                console.print(f"[bold]Jurisdiction:[/bold] {result.jurisdiction}")

                if result.authority_info:
                    console.print(f"[bold]Authority Level:[/bold] {result.authority_info.authority_level.value}")
                    console.print(f"[bold]Binding:[/bold] {'Yes' if result.authority_info.binding_authority else 'No'}")

                if result.validated_components:
                    console.print("[bold]Components:[/bold]")
                    for key, value in result.validated_components.items():
                        console.print(f"  {key}: [cyan]{value}[/cyan]")
            else:
                console.print(f"[red]✗ Invalid citation[/red]")
                console.print(f"[bold]Errors:[/bold]")
                for error in result.errors:
                    console.print(f"  • [red]{error}[/red]")

            if result.suggestions:
                console.print(f"[bold]Suggestions:[/bold]")
                for suggestion in result.suggestions:
                    console.print(f"  • [yellow]{suggestion}[/yellow]")

        except Exception as e:
            console.print(f"[red]Error validating citation: {e}[/red]")

    def authority_hierarchy_cmd(self, args: str):
        """Analyze legal authority hierarchy and relationships"""
        if not args.strip():
            console.print("[red]Please provide citation or authority to analyze[/red]")
            console.print("[yellow]Usage: /authority_hierarchy \"Fla. Sup. Ct.\"[/yellow]")
            return

        try:
            authority = args.strip().strip('"\'')
            hierarchy = self.authority_hierarchy.analyze_authority(authority)

            console.print(f"[bold]Authority Analysis: {authority}[/bold]")
            console.print(f"Level: [cyan]{hierarchy.authority_level.value}[/cyan]")
            console.print(f"Weight: [yellow]{hierarchy.authority_weight:.2f}[/yellow]")
            console.print(f"Binding: {'Yes' if hierarchy.binding_authority else 'No'}")

            if hierarchy.jurisdiction:
                console.print(f"Jurisdiction: [green]{hierarchy.jurisdiction}[/green]")

            if hierarchy.precedent_relationships:
                console.print("\n[bold]Related Authorities:[/bold]")
                for rel in hierarchy.precedent_relationships:
                    console.print(f"  • {rel.target_authority} ({rel.relationship_type.value})")

        except Exception as e:
            console.print(f"[red]Error analyzing authority: {e}[/red]")

    def legal_search_cmd(self, args: str):
        """Search legal knowledge base"""
        if not args.strip():
            console.print("[red]Please provide search query[/red]")
            console.print("[yellow]Usage: /legal_search \"summary judgment standards\"[/yellow]")
            return

        try:
            query = args.strip().strip('"\'')
            # Implement legal-specific search
            console.print(f"[dim]Searching legal knowledge for: {query}[/dim]")
            console.print("[yellow]Legal search functionality coming soon[/yellow]")

        except Exception as e:
            console.print(f"[red]Error searching legal knowledge: {e}[/red]")

    def start_case_analysis_cmd(self, args: str):
        """Start OODA loop case analysis"""
        if not args.strip():
            console.print("[red]Please provide case description[/red]")
            console.print("[yellow]Usage: /start_case_analysis \"Contract dispute over delivery terms\"[/yellow]")
            return

        try:
            case_description = args.strip().strip('"\'')
            console.print(f"[bold]Starting OODA Loop Analysis[/bold]")
            console.print(f"Case: [cyan]{case_description}[/cyan]")

            # Initialize OODA loop
            session_id = self.ooda_processor.start_analysis_session(case_description)
            console.print(f"Session ID: [yellow]{session_id}[/yellow]")
            console.print("\nUse [cyan]/ooda_observe[/cyan], [cyan]/ooda_orient[/cyan], [cyan]/ooda_decide[/cyan], [cyan]/ooda_act[/cyan] to proceed")

        except Exception as e:
            console.print(f"[red]Error starting case analysis: {e}[/red]")

    def ooda_observe_cmd(self, args: str):
        """OODA Loop - Observe phase"""
        try:
            # Get current session or create default
            session_id = getattr(self, '_current_ooda_session', None)
            if not session_id:
                console.print("[yellow]No active OODA session. Use /start_case_analysis first[/yellow]")
                return

            console.print("[bold blue]OODA - Observe Phase[/bold blue]")
            console.print("Gathering case facts and evidence...")

            # For now, show placeholder - full implementation would gather facts
            console.print("[green]✓ Observation phase initiated[/green]")
            console.print("Use [cyan]/ooda_orient[/cyan] to proceed to orientation phase")

        except Exception as e:
            console.print(f"[red]Error in observe phase: {e}[/red]")

    def ooda_orient_cmd(self, args: str):
        """OODA Loop - Orient phase"""
        try:
            console.print("[bold yellow]OODA - Orient Phase[/bold yellow]")
            console.print("Analyzing legal framework and precedents...")
            console.print("[green]✓ Orientation phase initiated[/green]")
            console.print("Use [cyan]/ooda_decide[/cyan] to proceed to decision phase")

        except Exception as e:
            console.print(f"[red]Error in orient phase: {e}[/red]")

    def ooda_decide_cmd(self, args: str):
        """OODA Loop - Decide phase"""
        try:
            console.print("[bold magenta]OODA - Decide Phase[/bold magenta]")
            console.print("Formulating legal strategy and options...")
            console.print("[green]✓ Decision phase initiated[/green]")
            console.print("Use [cyan]/ooda_act[/cyan] to proceed to action phase")

        except Exception as e:
            console.print(f"[red]Error in decide phase: {e}[/red]")

    def ooda_act_cmd(self, args: str):
        """OODA Loop - Act phase"""
        try:
            console.print("[bold red]OODA - Act Phase[/bold red]")
            console.print("Implementing legal action plan...")
            console.print("[green]✓ Action phase initiated[/green]")
            console.print("OODA loop cycle complete. Use [cyan]/start_case_analysis[/cyan] for new analysis")

        except Exception as e:
            console.print(f"[red]Error in act phase: {e}[/red]")

    def extended_reasoning_cmd(self, args: str):
        """Start extended legal reasoning session"""
        parts = args.split() if args.strip() else []
        mode = parts[0] if parts else "extended"

        try:
            from .legal.legal_reasoning import ReasoningMode

            mode_map = {
                "standard": ReasoningMode.STANDARD,
                "extended": ReasoningMode.EXTENDED,
                "constitutional": ReasoningMode.CONSTITUTIONAL,
                "complex": ReasoningMode.COMPLEX_CASE,
                "mega": ReasoningMode.MEGA_BRIEF
            }

            reasoning_mode = mode_map.get(mode, ReasoningMode.EXTENDED)

            console.print(f"[bold]Extended Reasoning Mode: {reasoning_mode.value}[/bold]")
            console.print(f"Token Allocation: [cyan]{self.legal_reasoning.get_token_allocation(reasoning_mode)}[/cyan]")
            console.print("Enhanced reasoning session started...")

        except Exception as e:
            console.print(f"[red]Error starting extended reasoning: {e}[/red]")

    def privilege_check_cmd(self, args: str):
        """Check content for attorney-client privilege"""
        if not args.strip():
            console.print("[red]Please provide content to check[/red]")
            console.print("[yellow]Usage: /privilege_check \"Client confidential communication\"[/yellow]")
            return

        try:
            content = args.strip().strip('"\'')
            privilege_level = self.privilege_system.classify_privilege_level(content, {})

            console.print(f"[bold]Privilege Analysis[/bold]")
            console.print(f"Level: [cyan]{privilege_level.value}[/cyan]")

            if privilege_level.value != "NONE":
                console.print("[yellow]⚠️  Privileged content detected[/yellow]")
                console.print("Consider encryption and access controls")
            else:
                console.print("[green]✓ No privilege concerns detected[/green]")

        except Exception as e:
            console.print(f"[red]Error checking privilege: {e}[/red]")

    def deadline_calculator_cmd(self, args: str):
        """Calculate legal deadlines"""
        console.print("[bold]Deadline Calculator[/bold]")
        console.print("[yellow]Deadline calculation functionality coming soon[/yellow]")
        console.print("Will support Florida court rules, federal rules, and custom calculations")

    def conflict_checker_cmd(self, args: str):
        """Check for conflicts of interest"""
        console.print("[bold]Conflict Checker[/bold]")
        console.print("[yellow]Conflict checking functionality coming soon[/yellow]")
        console.print("Will analyze client relationships and potential conflicts")

    def precedent_analyzer_cmd(self, args: str):
        """Analyze legal precedents"""
        if not args.strip():
            console.print("[red]Please provide case or legal issue[/red]")
            console.print("[yellow]Usage: /precedent_analyzer \"contract interpretation\"[/yellow]")
            return

        console.print(f"[bold]Precedent Analysis[/bold]")
        console.print(f"Issue: [cyan]{args.strip()}[/cyan]")
        console.print("[yellow]Precedent analysis functionality coming soon[/yellow]")

    def motion_templates_cmd(self, args: str):
        """Generate motion templates"""
        console.print("[bold]Motion Templates[/bold]")
        console.print("[yellow]Motion template generation coming soon[/yellow]")
        console.print("Will support Florida and federal motion templates")

    def case_research_cmd(self, args: str):
        """Research case law"""
        if not args.strip():
            console.print("[red]Please provide research query[/red]")
            console.print("[yellow]Usage: /case_research \"personal jurisdiction\"[/yellow]")
            return

        console.print(f"[bold]Case Research[/bold]")
        console.print(f"Query: [cyan]{args.strip()}[/cyan]")
        console.print("[yellow]Case research functionality coming soon[/yellow]")

    def statute_lookup_cmd(self, args: str):
        """Look up statutes and regulations"""
        if not args.strip():
            console.print("[red]Please provide statute citation or topic[/red]")
            console.print("[yellow]Usage: /statute_lookup \"Fla. Stat. § 95.11\"[/yellow]")
            return

        console.print(f"[bold]Statute Lookup[/bold]")
        console.print(f"Citation: [cyan]{args.strip()}[/cyan]")
        console.print("[yellow]Statute lookup functionality coming soon[/yellow]")

    def brief_generator_cmd(self, args: str):
        """Generate legal briefs"""
        console.print("[bold]Brief Generator[/bold]")
        console.print("[yellow]Brief generation functionality coming soon[/yellow]")
        console.print("Will support appellate briefs, motions, and pleadings")

    def discovery_manager_cmd(self, args: str):
        """Manage discovery requests and responses"""
        console.print("[bold]Discovery Manager[/bold]")
        console.print("[yellow]Discovery management functionality coming soon[/yellow]")

    def client_intake_cmd(self, args: str):
        """Client intake and information gathering"""
        console.print("[bold]Client Intake[/bold]")
        console.print("[yellow]Client intake functionality coming soon[/yellow]")
        console.print("Will include privilege protection and secure storage")

    def document_review_cmd(self, args: str):
        """Review documents for privilege and relevance"""
        if not args.strip():
            console.print("[red]Please provide document path or content[/red]")
            console.print("[yellow]Usage: /document_review \"/path/to/document.pdf\"[/yellow]")
            return

        console.print(f"[bold]Document Review[/bold]")
        console.print(f"Document: [cyan]{args.strip()}[/cyan]")
        console.print("[yellow]Document review functionality coming soon[/yellow]")

    def billing_tracker_cmd(self, args: str):
        """Track billable time and activities"""
        console.print("[bold]Billing Tracker[/bold]")
        console.print("[yellow]Billing tracking functionality coming soon[/yellow]")

    def court_calendar_cmd(self, args: str):
        """Manage court calendar and deadlines"""
        console.print("[bold]Court Calendar[/bold]")
        console.print("[yellow]Court calendar functionality coming soon[/yellow]")

    def evidence_organizer_cmd(self, args: str):
        """Organize and catalog evidence"""
        console.print("[bold]Evidence Organizer[/bold]")
        console.print("[yellow]Evidence organization functionality coming soon[/yellow]")

    def witness_tracker_cmd(self, args: str):
        """Track witness information and availability"""
        console.print("[bold]Witness Tracker[/bold]")
        console.print("[yellow]Witness tracking functionality coming soon[/yellow]")

    def legal_forms_cmd(self, args: str):
        """Generate and fill legal forms"""
        console.print("[bold]Legal Forms[/bold]")
        console.print("[yellow]Legal forms functionality coming soon[/yellow]")

    def rule_interpreter_cmd(self, args: str):
        """Interpret court rules and procedures"""
        if not args.strip():
            console.print("[red]Please provide rule citation or topic[/red]")
            console.print("[yellow]Usage: /rule_interpreter \"Rule 1.420\"[/yellow]")
            return

        console.print(f"[bold]Rule Interpreter[/bold]")
        console.print(f"Rule: [cyan]{args.strip()}[/cyan]")
        console.print("[yellow]Rule interpretation functionality coming soon[/yellow]")

    def settlement_calculator_cmd(self, args: str):
        """Calculate settlement values and ranges"""
        console.print("[bold]Settlement Calculator[/bold]")
        console.print("[yellow]Settlement calculation functionality coming soon[/yellow]")

    def expert_witness_cmd(self, args: str):
        """Manage expert witness information"""
        console.print("[bold]Expert Witness Manager[/bold]")
        console.print("[yellow]Expert witness management functionality coming soon[/yellow]")

    def trial_prep_cmd(self, args: str):
        """Trial preparation and organization"""
        console.print("[bold]Trial Preparation[/bold]")
        console.print("[yellow]Trial prep functionality coming soon[/yellow]")

    def appeal_tracker_cmd(self, args: str):
        """Track appellate proceedings"""
        console.print("[bold]Appeal Tracker[/bold]")
        console.print("[yellow]Appeal tracking functionality coming soon[/yellow]")

    def compliance_checker_cmd(self, args: str):
        """Check regulatory compliance"""
        console.print("[bold]Compliance Checker[/bold]")
        console.print("[yellow]Compliance checking functionality coming soon[/yellow]")

    def legal_analytics_cmd(self, args: str):
        """Analyze legal trends and outcomes"""
        console.print("[bold]Legal Analytics[/bold]")
        console.print("[yellow]Legal analytics functionality coming soon[/yellow]")

    def privilege_log_cmd(self, args: str):
        """Generate privilege logs"""
        console.print("[bold]Privilege Log Generator[/bold]")
        console.print("[yellow]Privilege log functionality coming soon[/yellow]")

    def redaction_tool_cmd(self, args: str):
        """Redact sensitive information"""
        if not args.strip():
            console.print("[red]Please provide document path or content[/red]")
            console.print("[yellow]Usage: /redaction_tool \"/path/to/document.pdf\"[/yellow]")
            return

        console.print(f"[bold]Redaction Tool[/bold]")
        console.print(f"Document: [cyan]{args.strip()}[/cyan]")
        console.print("[yellow]Redaction functionality coming soon[/yellow]")

    def legal_notification_cmd(self, args: str):
        """Send legal notifications and notices"""
        console.print("[bold]Legal Notification System[/bold]")
        console.print("[yellow]Legal notification functionality coming soon[/yellow]")

    def contract_analyzer_cmd(self, args: str):
        """Analyze contracts and agreements"""
        if not args.strip():
            console.print("[red]Please provide contract path or content[/red]")
            console.print("[yellow]Usage: /contract_analyzer \"/path/to/contract.pdf\"[/yellow]")
            return

        console.print(f"[bold]Contract Analyzer[/bold]")
        console.print(f"Contract: [cyan]{args.strip()}[/cyan]")
        console.print("[yellow]Contract analysis functionality coming soon[/yellow]")

    def legal_export_cmd(self, args: str):
        """Export legal documents and reports"""
        console.print("[bold]Legal Export System[/bold]")
        console.print("[yellow]Legal export functionality coming soon[/yellow]")
        console.print("Will support various formats: PDF, DOCX, HTML, JSON")

    # Legal Writing Knowledge System Command Handlers

    def writing_principles_cmd(self, args: str):
        """Show legal writing principles and best practices"""
        try:
            from tiny_code.legal.writing_principles import LegalWritingPrinciples

            principles = LegalWritingPrinciples()

            if args.strip():
                # Show specific category
                category = args.strip().lower()
                category_principles = principles.get_principles_by_category(category)

                if category_principles:
                    console.print(f"[bold]Legal Writing Principles - {category.replace('_', ' ').title()}[/bold]")
                    for principle in category_principles:
                        console.print(f"\n[cyan]{principle.name}[/cyan] ({principle.importance} Priority)")
                        console.print(f"  {principle.description}")

                        if principle.best_practices:
                            console.print("  [dim]Best Practices:[/dim]")
                            for practice in principle.best_practices[:3]:  # Show first 3
                                console.print(f"    • {practice}")
                else:
                    console.print(f"[red]Category '{category}' not found[/red]")
                    console.print(f"Available categories: {', '.join(principles.get_principle_categories())}")
            else:
                # Show all categories overview
                console.print("[bold]Legal Writing Principles Overview[/bold]")
                categories = principles.get_principle_categories()

                for category in categories:
                    category_principles = principles.get_principles_by_category(category)
                    console.print(f"\n[cyan]{category.replace('_', ' ').title()}[/cyan] ({len(category_principles)} principles)")
                    for principle in category_principles:
                        console.print(f"  • {principle.name}")

                console.print(f"\n[dim]Use /writing_principles <category> for details[/dim]")

        except ImportError as e:
            console.print(f"[red]Legal writing module not available: {e}[/red]")
        except Exception as e:
            console.print(f"[red]Error showing writing principles: {e}[/red]")

    def writing_evaluate_cmd(self, args: str):
        """Evaluate legal document against writing principles"""
        if not args.strip():
            console.print("[red]Please provide file path or document content[/red]")
            console.print("[yellow]Usage: /writing_evaluate \"/path/to/document.txt\"[/yellow]")
            console.print("[yellow]       /writing_evaluate \"document content here\"[/yellow]")
            return

        try:
            from tiny_code.legal.writing_evaluator import LegalWritingEvaluator
            import os

            evaluator = LegalWritingEvaluator()
            arg = args.strip().strip('"\'')

            # Check if argument is a file path
            if os.path.isfile(arg):
                with open(arg, 'r', encoding='utf-8') as f:
                    content = f.read()
                console.print(f"[dim]Evaluating file: {arg}[/dim]")
            else:
                content = arg
                console.print("[dim]Evaluating provided content[/dim]")

            # Perform evaluation
            analysis = evaluator.evaluate_document(content)

            # Display formatted report
            report = evaluator.format_analysis_report(analysis)
            console.print(report)

        except ImportError as e:
            console.print(f"[red]Legal writing evaluator not available: {e}[/red]")
        except FileNotFoundError:
            console.print(f"[red]File not found: {arg}[/red]")
        except Exception as e:
            console.print(f"[red]Error evaluating document: {e}[/red]")

    def document_templates_cmd(self, args: str):
        """Show available legal document templates"""
        try:
            from tiny_code.legal.document_templates import LegalDocumentTemplates
            from tiny_code.legal.writing_principles import LegalDocumentType

            templates = LegalDocumentTemplates()

            if args.strip():
                # Show specific template details
                try:
                    doc_type = LegalDocumentType(args.strip().lower())
                    template = templates.get_template(doc_type)

                    if template:
                        outline = templates.generate_document_outline(doc_type, include_instructions=True)
                        console.print(outline)
                    else:
                        console.print(f"[red]Template not found for: {args.strip()}[/red]")
                except ValueError:
                    console.print(f"[red]Invalid document type: {args.strip()}[/red]")
                    console.print("Available types: brief, memorandum, motion, client_letter, contract")
            else:
                # Show all available templates
                console.print("[bold]Available Legal Document Templates[/bold]")
                available_templates = templates.get_available_templates()

                for template in available_templates:
                    console.print(f"\n[cyan]{template.document_type.value}[/cyan] - {template.name}")
                    console.print(f"  {template.description}")
                    console.print(f"  Sections: {len(template.sections)}")
                    if template.analysis_framework:
                        console.print(f"  Framework: {template.analysis_framework.value.upper()}")

                console.print(f"\n[dim]Use /document_templates <type> for details[/dim]")

        except ImportError as e:
            console.print(f"[red]Document templates module not available: {e}[/red]")
        except Exception as e:
            console.print(f"[red]Error showing templates: {e}[/red]")

    def generate_template_cmd(self, args: str):
        """Generate legal document from template"""
        if not args.strip():
            console.print("[red]Please provide document type[/red]")
            console.print("[yellow]Usage: /generate_template brief[/yellow]")
            console.print("[yellow]Available types: brief, memorandum, motion, client_letter, contract[/yellow]")
            return

        try:
            from tiny_code.legal.document_templates import LegalDocumentTemplates
            from tiny_code.legal.writing_principles import LegalDocumentType

            templates = LegalDocumentTemplates()

            try:
                doc_type = LegalDocumentType(args.strip().lower())
                complete_template = templates.generate_complete_template(doc_type, include_instructions=True)

                console.print(f"[bold]Generated Template: {doc_type.value.title()}[/bold]")
                console.print(complete_template)

                # Offer to save to file
                console.print(f"\n[dim]Template generated. Use /save to write to file.[/dim]")

            except ValueError:
                console.print(f"[red]Invalid document type: {args.strip()}[/red]")
                console.print("Available types: brief, memorandum, motion, client_letter, contract")

        except ImportError as e:
            console.print(f"[red]Document templates module not available: {e}[/red]")
        except Exception as e:
            console.print(f"[red]Error generating template: {e}[/red]")

    def citation_check_cmd(self, args: str):
        """Validate citation format and accuracy"""
        if not args.strip():
            console.print("[red]Please provide citation to validate[/red]")
            console.print("[yellow]Usage: /citation_check \"Brown v. Board of Education, 347 U.S. 483 (1954)\"[/yellow]")
            return

        try:
            from tiny_code.legal.writing_principles import LegalWritingPrinciples

            principles = LegalWritingPrinciples()
            citation = args.strip().strip('"\'')

            console.print(f"[bold]Citation Validation[/bold]")
            console.print(f"Citation: [cyan]{citation}[/cyan]")

            # Determine citation type and validate
            if 'v.' in citation:
                citation_type = 'case_citation'
            elif 'U.S.C.' in citation:
                citation_type = 'statute_citation'
            elif 'C.F.R.' in citation:
                citation_type = 'regulation_citation'
            else:
                console.print("[yellow]Citation type not recognized. Checking basic format...[/yellow]")
                citation_type = 'case_citation'  # Default to case citation

            is_valid, errors = principles.validate_citation_format(citation, citation_type)

            if is_valid:
                console.print("[green]✓ Citation format is valid[/green]")
            else:
                console.print("[red]✗ Citation format issues found:[/red]")
                for error in errors:
                    console.print(f"  • {error}")

            # Show citation standard for reference
            standard = principles.get_citation_standard(citation_type)
            if standard:
                console.print(f"\n[dim]Expected format: {standard.description}[/dim]")
                if standard.examples:
                    console.print(f"[dim]Example: {standard.examples[0]}[/dim]")

        except ImportError as e:
            console.print(f"[red]Legal writing module not available: {e}[/red]")
        except Exception as e:
            console.print(f"[red]Error validating citation: {e}[/red]")

    def irac_analysis_cmd(self, args: str):
        """Generate IRAC/CRAC/CREAC analysis framework"""
        if not args.strip():
            console.print("[red]Please specify analysis framework[/red]")
            console.print("[yellow]Usage: /irac_analysis irac|crac|creac[/yellow]")
            return

        try:
            from tiny_code.legal.writing_principles import LegalWritingPrinciples, AnalysisStructure

            principles = LegalWritingPrinciples()
            framework_name = args.strip().lower()

            try:
                framework = AnalysisStructure(framework_name)
                framework_details = principles.get_analysis_framework(framework)

                if framework_details:
                    console.print(f"[bold]{framework_details['name']} Analysis Framework[/bold]")
                    console.print(f"{framework_details['description']}")

                    console.print(f"\n[cyan]Components:[/cyan]")
                    for component in framework_details['components']:
                        console.print(f"\n[yellow]{component['name']}[/yellow]")
                        console.print(f"  {component['description']}")
                        console.print(f"  Requirements:")
                        for req in component['requirements']:
                            console.print(f"    • {req}")

                    console.print(f"\n[dim]Best for: {', '.join(framework_details['best_for'])}[/dim]")
                else:
                    console.print(f"[red]Framework details not found[/red]")

            except ValueError:
                console.print(f"[red]Invalid framework: {framework_name}[/red]")
                console.print("Available frameworks: irac, crac, creac")

        except ImportError as e:
            console.print(f"[red]Legal writing module not available: {e}[/red]")
        except Exception as e:
            console.print(f"[red]Error showing analysis framework: {e}[/red]")

    def writing_score_cmd(self, args: str):
        """Get writing quality score and detailed analysis"""
        if not args.strip():
            console.print("[red]Please provide file path or document content[/red]")
            console.print("[yellow]Usage: /writing_score \"/path/to/document.txt\"[/yellow]")
            return

        try:
            from tiny_code.legal.writing_evaluator import LegalWritingEvaluator
            import os

            evaluator = LegalWritingEvaluator()
            arg = args.strip().strip('"\'')

            # Check if argument is a file path
            if os.path.isfile(arg):
                with open(arg, 'r', encoding='utf-8') as f:
                    content = f.read()
                console.print(f"[dim]Analyzing file: {arg}[/dim]")
            else:
                content = arg
                console.print("[dim]Analyzing provided content[/dim]")

            # Perform evaluation
            analysis = evaluator.evaluate_document(content)

            # Display summary scores
            console.print(f"[bold]Writing Quality Analysis[/bold]")
            console.print(f"Overall Score: [cyan]{analysis.overall_score:.1f}/10.0[/cyan]")

            console.print(f"\n[yellow]Quality Dimensions:[/yellow]")
            for quality_dim, score in analysis.quality_scores.items():
                color = "green" if score.score >= 7 else "yellow" if score.score >= 5 else "red"
                console.print(f"  {quality_dim.value.replace('_', ' ').title():20} [{color}]{score.score:4.1f}[/{color}]/10.0")

            # Show top issues
            high_priority_issues = [i for i in analysis.issues if i.severity.value in ['critical', 'high']]
            if high_priority_issues:
                console.print(f"\n[red]Priority Issues ({len(high_priority_issues)}):[/red]")
                for issue in high_priority_issues[:5]:  # Show top 5
                    console.print(f"  • {issue.description}")
                    console.print(f"    [dim]{issue.suggestion}[/dim]")

            # Show strengths
            if analysis.strengths:
                console.print(f"\n[green]Strengths:[/green]")
                for strength in analysis.strengths[:3]:  # Show top 3
                    console.print(f"  • {strength}")

            console.print(f"\n[dim]Use /writing_evaluate for complete analysis[/dim]")

        except ImportError as e:
            console.print(f"[red]Legal writing evaluator not available: {e}[/red]")
        except FileNotFoundError:
            console.print(f"[red]File not found: {arg}[/red]")
        except Exception as e:
            console.print(f"[red]Error analyzing writing: {e}[/red]")

    def record_command_usage(self, command: str, parameters: str = "",
                           success: bool = True, execution_time: float = 0):
        """Record command usage for analytics"""
        try:
            self.cli_enhancements.record_command_execution(
                command, parameters, success, execution_time,
                self.mode_manager.current_mode.value
            )
        except Exception:
            # Silently fail to avoid disrupting user experience
            pass

    # Error Handling Commands

    def show_errors_cmd(self, args: str):
        """Show recent errors"""
        try:
            limit = 20
            if args.strip():
                try:
                    limit = int(args.strip())
                except ValueError:
                    console.print("[yellow]Invalid limit, using default (20)[/yellow]")

            errors = self.error_manager.get_recent_errors(limit)

            if not errors:
                console.print("[green]No recent errors found[/green]")
                return

            # Create error table
            table = Table(title=f"Recent Errors (Last {len(errors)})")
            table.add_column("ID", style="dim")
            table.add_column("Time", style="cyan")
            table.add_column("Severity", style="yellow")
            table.add_column("Category", style="magenta")
            table.add_column("Message", style="red")
            table.add_column("Recovery", justify="center")

            for error in errors:
                # Format time
                time_diff = datetime.now() - error.timestamp
                if time_diff.days == 0:
                    if time_diff.seconds < 3600:
                        time_str = f"{time_diff.seconds // 60}m ago"
                    else:
                        time_str = f"{time_diff.seconds // 3600}h ago"
                else:
                    time_str = f"{time_diff.days}d ago"

                # Recovery status
                if error.recovery_successful:
                    recovery_icon = "✓"
                elif error.recovery_attempted:
                    recovery_icon = "✗"
                else:
                    recovery_icon = "-"

                # Truncate message
                message = error.message[:50] + "..." if len(error.message) > 50 else error.message

                table.add_row(
                    error.error_id[-8:],  # Last 8 chars of ID
                    time_str,
                    error.severity.value,
                    error.category.value,
                    message,
                    recovery_icon
                )

            console.print(table)

        except Exception as e:
            console.print(f"[red]Error displaying errors: {e}[/red]")

    def error_stats_cmd(self, args: str):
        """Show error statistics"""
        try:
            days = 30
            if args.strip():
                try:
                    days = int(args.strip())
                except ValueError:
                    console.print("[yellow]Invalid days, using default (30)[/yellow]")

            stats = self.error_manager.get_error_statistics(days)

            # Overall statistics
            console.print(Panel.fit(
                f"[bold cyan]Total Errors: {stats['total_errors']}[/bold cyan]\n"
                f"[bold green]Successful Recoveries: {stats['total_recoveries']}[/bold green]\n"
                f"[bold yellow]Recovery Rate: {stats['overall_recovery_rate']:.1f}%[/bold yellow]",
                title=f"Error Statistics (Last {days} Days)",
                border_style="blue"
            ))

            # Detailed breakdown
            if stats['by_category_severity']:
                detail_table = Table(title="Error Breakdown by Category and Severity")
                detail_table.add_column("Category", style="cyan")
                detail_table.add_column("Severity", style="yellow")
                detail_table.add_column("Count", justify="right", style="red")
                detail_table.add_column("Recoveries", justify="right", style="green")
                detail_table.add_column("Recovery Rate", justify="right", style="magenta")

                for stat in stats['by_category_severity']:
                    detail_table.add_row(
                        stat['category'],
                        stat['severity'],
                        str(stat['count']),
                        str(stat['successful_recoveries']),
                        f"{stat['recovery_rate']:.1f}%"
                    )

                console.print(detail_table)

        except Exception as e:
            console.print(f"[red]Error showing statistics: {e}[/red]")

    def manual_recovery_cmd(self, args: str):
        """Manually attempt error recovery"""
        try:
            if not args.strip():
                console.print("[yellow]Please provide an error ID[/yellow]")
                console.print("[yellow]Usage: /recover TC_1234567890_1234[/yellow]")
                console.print("[yellow]Use /errors to see recent error IDs[/yellow]")
                return

            error_id = args.strip()

            # Find the error
            recent_errors = self.error_manager.get_recent_errors(100)
            target_error = None

            for error in recent_errors:
                if error.error_id == error_id or error.error_id.endswith(error_id):
                    target_error = error
                    break

            if not target_error:
                console.print(f"[red]Error {error_id} not found[/red]")
                return

            console.print(f"[bold]Attempting recovery for error:[/bold]")
            console.print(f"  ID: {target_error.error_id}")
            console.print(f"  Message: {target_error.message}")
            console.print(f"  Category: {target_error.category.value}")

            if target_error.recovery_successful:
                console.print("[yellow]This error was already successfully recovered[/yellow]")
                return

            # Attempt recovery
            success = self.error_manager._attempt_recovery(target_error)

            if success:
                console.print("[green]✓ Manual recovery successful![/green]")
            else:
                console.print("[red]✗ Manual recovery failed[/red]")
                self.error_manager._suggest_recovery(target_error)

        except Exception as e:
            console.print(f"[red]Error during manual recovery: {e}[/red]")

    # Plugin Management Commands

    def list_plugins_cmd(self, args: str):
        """List all available plugins"""
        try:
            plugins = self.plugin_manager.list_plugins()

            if not plugins:
                console.print("[yellow]No plugins found[/yellow]")
                return

            table = Table(title="TinyCode Plugins")
            table.add_column("Plugin Name", style="cyan")
            table.add_column("Status", style="green")
            table.add_column("Version", style="dim")
            table.add_column("Description", style="")
            table.add_column("Commands", style="yellow")

            for plugin_name, info in plugins.items():
                if info.get('loaded'):
                    status = "🟢 Enabled" if info.get('enabled') else "🟡 Loaded"
                    version = info.get('version', 'Unknown')
                    description = info.get('description', 'No description')
                    commands = ', '.join(info.get('commands', []))
                else:
                    status = "⚪ Available"
                    version = "Unknown"
                    description = "Not loaded"
                    commands = "Unknown"

                table.add_row(plugin_name, status, version, description, commands)

            console.print(table)

        except Exception as e:
            console.print(f"[red]Error listing plugins: {e}[/red]")

    def enable_plugin_cmd(self, args: str):
        """Enable a plugin"""
        try:
            if not args.strip():
                console.print("[yellow]Please provide a plugin name[/yellow]")
                console.print("[yellow]Usage: /plugin-enable <plugin_name>[/yellow]")
                return

            plugin_name = args.strip()

            # Load plugin if not already loaded
            if plugin_name not in self.plugin_manager.loaded_plugins:
                if not self.plugin_manager.load_plugin(plugin_name):
                    console.print(f"[red]Failed to load plugin: {plugin_name}[/red]")
                    return

            # Enable the plugin
            if self.plugin_manager.enable_plugin(plugin_name):
                console.print(f"[green]✓ Plugin '{plugin_name}' enabled successfully[/green]")

                # Show plugin commands
                plugin_info = self.plugin_manager.get_plugin_info(plugin_name)
                if plugin_info and plugin_info.get('commands'):
                    console.print(f"[cyan]Available commands: {', '.join(plugin_info['commands'])}[/cyan]")
            else:
                console.print(f"[red]Failed to enable plugin: {plugin_name}[/red]")

        except Exception as e:
            console.print(f"[red]Error enabling plugin: {e}[/red]")

    def disable_plugin_cmd(self, args: str):
        """Disable a plugin"""
        try:
            if not args.strip():
                console.print("[yellow]Please provide a plugin name[/yellow]")
                console.print("[yellow]Usage: /plugin-disable <plugin_name>[/yellow]")
                return

            plugin_name = args.strip()

            if self.plugin_manager.disable_plugin(plugin_name):
                console.print(f"[green]✓ Plugin '{plugin_name}' disabled successfully[/green]")
            else:
                console.print(f"[red]Failed to disable plugin: {plugin_name}[/red]")

        except Exception as e:
            console.print(f"[red]Error disabling plugin: {e}[/red]")

    def reload_plugin_cmd(self, args: str):
        """Reload a plugin"""
        try:
            if not args.strip():
                console.print("[yellow]Please provide a plugin name[/yellow]")
                console.print("[yellow]Usage: /plugin-reload <plugin_name>[/yellow]")
                return

            plugin_name = args.strip()

            if self.plugin_manager.reload_plugin(plugin_name):
                console.print(f"[green]✓ Plugin '{plugin_name}' reloaded successfully[/green]")
            else:
                console.print(f"[red]Failed to reload plugin: {plugin_name}[/red]")

        except Exception as e:
            console.print(f"[red]Error reloading plugin: {e}[/red]")

    def plugin_info_cmd(self, args: str):
        """Show detailed information about a plugin"""
        try:
            if not args.strip():
                console.print("[yellow]Please provide a plugin name[/yellow]")
                console.print("[yellow]Usage: /plugin-info <plugin_name>[/yellow]")
                return

            plugin_name = args.strip()
            info = self.plugin_manager.get_plugin_info(plugin_name)

            if not info:
                console.print(f"[red]Plugin '{plugin_name}' not found[/red]")
                return

            console.print(f"\n[bold cyan]Plugin Information: {plugin_name}[/bold cyan]")
            console.print(f"[bold]Status:[/bold] {'🟢 Enabled' if info.get('enabled') else '🟡 Loaded' if info.get('loaded') else '⚪ Available'}")
            console.print(f"[bold]Version:[/bold] {info.get('version', 'Unknown')}")
            console.print(f"[bold]Author:[/bold] {info.get('author', 'Unknown')}")
            console.print(f"[bold]Description:[/bold] {info.get('description', 'No description')}")
            console.print(f"[bold]Safety Level:[/bold] {info.get('safety_level', 'Unknown')}")

            if info.get('dependencies'):
                console.print(f"[bold]Dependencies:[/bold] {', '.join(info['dependencies'])}")

            if info.get('commands'):
                console.print(f"[bold]Commands:[/bold]")
                for cmd in info['commands']:
                    console.print(f"  • {cmd}")

            if info.get('hooks'):
                console.print(f"[bold]Hooks:[/bold]")
                for hook in info['hooks']:
                    console.print(f"  • {hook}")

        except Exception as e:
            console.print(f"[red]Error getting plugin info: {e}[/red]")

    def show_principles_cmd(self, args: str):
        """Show available software development principles"""
        try:
            args_list = args.split() if args else []
            category = args_list[0] if args_list else None

            console.print("\n[bold cyan]Software Development Principles[/bold cyan]")

            if category:
                # Show specific category
                summary = self.agent.get_principle_summary(category)
                if "error" in summary:
                    console.print(f"[red]{summary['error']}[/red]")
                    return

                console.print(f"\n[bold yellow]{summary['category'].upper()} Principles:[/bold yellow]")
                for principle in summary["principles"]:
                    console.print(f"\n[bold green]• {principle['name']}[/bold green]")
                    console.print(f"  {principle['description']}")
                    console.print(f"  [dim]Severity: {principle['severity']}[/dim]")
                    if principle.get("examples"):
                        console.print(f"  [dim]Examples: {', '.join(principle['examples'][:2])}[/dim]")
            else:
                # Show all categories
                summary = self.agent.get_principle_summary()
                console.print("\n[bold yellow]Available Categories:[/bold yellow]")

                for category, info in summary.items():
                    console.print(f"\n[bold green]{category.upper()}[/bold green] ({info['count']} principles)")
                    console.print(f"  {', '.join(info['principles'][:3])}{'...' if len(info['principles']) > 3 else ''}")

                console.print(f"\n[dim]Use '/principles <category>' to see details for a specific category[/dim]")
                console.print(f"[dim]Available categories: {', '.join(summary.keys())}[/dim]")

        except Exception as e:
            console.print(f"[red]Error showing principles: {e}[/red]")

    def evaluate_code_cmd(self, args: str):
        """Evaluate code against software development principles"""
        try:
            args_list = args.split() if args else []

            if not args_list:
                console.print("[red]Usage: /evaluate <file_path> [focus_categories...]")
                console.print("[dim]Example: /evaluate src/main.py clean_code security[/dim]")
                return

            file_path = args_list[0]
            focus_areas = args_list[1:] if len(args_list) > 1 else None

            # Check if file exists
            if not os.path.exists(file_path):
                console.print(f"[red]File not found: {file_path}[/red]")
                return

            # Read the file
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    code_content = f.read()
            except Exception as e:
                console.print(f"[red]Error reading file: {e}[/red]")
                return

            console.print(f"\n[bold cyan]Evaluating: {file_path}[/bold cyan]")
            if focus_areas:
                console.print(f"[dim]Focus areas: {', '.join(focus_areas)}[/dim]")

            # Perform evaluation
            with console.status("[bold green]Analyzing code..."):
                evaluation = self.agent.evaluate_code_principles(code_content, file_path, focus_areas)

            # Display results
            console.print(f"\n[bold yellow]📊 Overall Score: {evaluation.overall_score:.1f}/10.0[/bold yellow]")

            # Quality scores
            console.print("\n[bold]🎯 Quality Dimensions:[/bold]")
            for score in evaluation.quality_scores:
                if score.score >= 8.0:
                    icon, color = "✅", "green"
                elif score.score >= 6.0:
                    icon, color = "⚠️", "yellow"
                else:
                    icon, color = "❌", "red"

                console.print(f"{icon} [{color}]{score.dimension.value.title()}: {score.score:.1f}/10.0[/{color}]")
                if score.details and score.score < 8.0:
                    console.print(f"   [dim]{score.details}[/dim]")

            # Recommendations
            if evaluation.recommendations:
                console.print(f"\n[bold]💡 Recommendations ({len(evaluation.recommendations)}):[/bold]")
                for i, rec in enumerate(evaluation.recommendations[:10], 1):  # Show top 10
                    severity_colors = {
                        "critical": "red",
                        "high": "yellow",
                        "medium": "yellow",
                        "low": "blue"
                    }
                    severity_icons = {
                        "critical": "🚨",
                        "high": "⚠️",
                        "medium": "💡",
                        "low": "📝"
                    }

                    color = severity_colors.get(rec.severity.value, "white")
                    icon = severity_icons.get(rec.severity.value, "•")

                    console.print(f"\n{i}. {icon} [{color}]{rec.message}[/{color}]")
                    if rec.suggested_fix:
                        console.print(f"   [bold]Fix:[/bold] {rec.suggested_fix}")
                    if rec.rationale:
                        console.print(f"   [dim]Why: {rec.rationale}[/dim]")

                if len(evaluation.recommendations) > 10:
                    console.print(f"\n[dim]... and {len(evaluation.recommendations) - 10} more recommendations[/dim]")

            # Code metrics
            if evaluation.metrics:
                console.print(f"\n[bold]📈 Code Metrics:[/bold]")
                metrics = evaluation.metrics
                console.print(f"• Lines of Code: {metrics.lines_of_code}")
                console.print(f"• Functions: {metrics.function_count}")
                console.print(f"• Classes: {metrics.class_count}")
                console.print(f"• Cyclomatic Complexity: {metrics.cyclomatic_complexity}")
                if metrics.max_function_length > 0:
                    console.print(f"• Max Function Length: {metrics.max_function_length} lines")

                if metrics.security_issues:
                    console.print(f"• [red]Security Issues: {len(metrics.security_issues)}[/red]")
                if metrics.performance_issues:
                    console.print(f"• [yellow]Performance Issues: {len(metrics.performance_issues)}[/yellow]")
                if metrics.code_smells:
                    console.print(f"• [yellow]Code Smells: {len(metrics.code_smells)}[/yellow]")

            console.print(f"\n[dim]Analysis completed in {evaluation.analysis_duration:.3f}s[/dim]")
            console.print(f"[dim]Use '/review {file_path}' for AI-powered review with these principles[/dim]")

        except Exception as e:
            console.print(f"[red]Error evaluating code: {e}[/red]")
            self.logger.error(f"Code evaluation error: {e}", exc_info=True)

@click.group(invoke_without_command=True)
@click.option('--model', default='tinyllama:latest', help='Ollama model to use')
@click.pass_context
def cli(ctx, model):
    """Tiny Code - AI Coding Assistant"""
    if ctx.invoked_subcommand is None:
        cli_instance = TinyCodeCLI(model=model)
        cli_instance.interactive_mode()

@cli.command()
@click.argument('filepath')
@click.option('--operation', '-o', default='explain',
              type=click.Choice(['complete', 'fix', 'explain', 'refactor', 'test', 'review', 'analyze']))
@click.option('--model', default='tinyllama:latest', help='Ollama model to use')
def process(filepath, operation, model):
    """Process a code file with specified operation"""
    agent = TinyCodeAgent(model=model)
    result = agent.process_file(filepath, operation)
    console.print(result)

@cli.command()
@click.argument('filepath')
@click.option('--model', default='tinyllama:latest', help='Ollama model to use')
def run(filepath, model):
    """Execute a Python file"""
    agent = TinyCodeAgent(model=model)
    tools = CodeTools()
    code = tools.read_file(filepath)
    if code:
        agent.execute_code(code)

@cli.command()
@click.argument('message')
@click.option('--model', default='tinyllama:latest', help='Ollama model to use')
def ask(message, model):
    """Ask Tiny Code a question"""
    agent = TinyCodeAgent(model=model)
    response = agent.chat(message)
    console.print(response)
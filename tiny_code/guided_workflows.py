#!/usr/bin/env python3
"""Guided Workflows and Interactive Tutorials for TinyCode Natural Language Interface"""

import json
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, TaskID
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.text import Text

from .nlp_interface import Intent, NLPProcessor, IntentResult
from .conversation_manager import ConversationManager
from .smart_assistant import SmartAssistant


class TutorialStep(Enum):
    """Types of tutorial steps"""
    EXPLANATION = "explanation"
    DEMONSTRATION = "demonstration"
    PRACTICE = "practice"
    VALIDATION = "validation"
    RECAP = "recap"


class WorkflowCategory(Enum):
    """Categories of workflows"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    SPECIALIZED = "specialized"


@dataclass
class TutorialStepData:
    """Data for a tutorial step"""
    step_type: TutorialStep
    title: str
    content: str
    example_input: Optional[str] = None
    expected_intent: Optional[Intent] = None
    validation_criteria: Optional[str] = None
    hints: List[str] = None
    next_step_condition: Optional[str] = None

    def __post_init__(self):
        if self.hints is None:
            self.hints = []


@dataclass
class Workflow:
    """A guided workflow for learning TinyCode"""
    id: str
    name: str
    description: str
    category: WorkflowCategory
    difficulty_level: int  # 1-5
    estimated_time_minutes: int
    prerequisites: List[str]
    steps: List[TutorialStepData]
    learning_objectives: List[str]
    completion_criteria: str
    tags: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class ProgressTracker:
    """Tracks user progress through tutorials and workflows"""

    def __init__(self, data_dir: str = "data/tutorials"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.progress_file = self.data_dir / "user_progress.json"
        self.console = Console()
        self._load_progress()

    def _load_progress(self):
        """Load user progress from file"""
        if self.progress_file.exists():
            with open(self.progress_file, 'r') as f:
                self.progress = json.load(f)
        else:
            self.progress = {
                "completed_workflows": [],
                "current_workflow": None,
                "current_step": 0,
                "skill_level": "beginner",
                "preferences": {},
                "statistics": {
                    "total_time_spent": 0,
                    "commands_learned": [],
                    "workflows_completed": 0,
                    "success_rate": 0.0
                }
            }

    def save_progress(self):
        """Save progress to file"""
        with open(self.progress_file, 'w') as f:
            json.dump(self.progress, f, indent=2)

    def mark_workflow_completed(self, workflow_id: str, time_spent: int):
        """Mark a workflow as completed"""
        if workflow_id not in self.progress["completed_workflows"]:
            self.progress["completed_workflows"].append(workflow_id)
            self.progress["statistics"]["workflows_completed"] += 1
            self.progress["statistics"]["total_time_spent"] += time_spent
        self.save_progress()

    def update_current_step(self, workflow_id: str, step_number: int):
        """Update current step in workflow"""
        self.progress["current_workflow"] = workflow_id
        self.progress["current_step"] = step_number
        self.save_progress()

    def add_learned_command(self, command: str):
        """Add a newly learned command"""
        if command not in self.progress["statistics"]["commands_learned"]:
            self.progress["statistics"]["commands_learned"].append(command)
            self.save_progress()

    def get_recommended_workflows(self, available_workflows: List[Workflow]) -> List[Workflow]:
        """Get recommended workflows based on progress"""
        skill_level = self.progress["skill_level"]
        completed = set(self.progress["completed_workflows"])

        # Filter based on skill level and completion status
        recommended = []
        for workflow in available_workflows:
            if workflow.id in completed:
                continue

            # Check skill level compatibility
            if skill_level == "beginner" and workflow.category in [WorkflowCategory.BEGINNER]:
                recommended.append(workflow)
            elif skill_level == "intermediate" and workflow.category in [WorkflowCategory.BEGINNER, WorkflowCategory.INTERMEDIATE]:
                recommended.append(workflow)
            elif skill_level == "advanced":
                recommended.append(workflow)

        # Sort by difficulty and prerequisites
        recommended.sort(key=lambda w: (w.difficulty_level, len(w.prerequisites)))
        return recommended[:5]  # Top 5 recommendations


class InteractiveTutorial:
    """Interactive tutorial system for TinyCode"""

    def __init__(self, intent_recognizer: NLPProcessor, conversation_manager: ConversationManager):
        self.intent_recognizer = intent_recognizer
        self.conversation_manager = conversation_manager
        self.console = Console()
        self.progress_tracker = ProgressTracker()
        self.workflows = self._load_workflows()

    def _load_workflows(self) -> List[Workflow]:
        """Load predefined workflows"""
        workflows = []

        # Beginner workflow: Getting started with natural language
        beginner_steps = [
            TutorialStepData(
                step_type=TutorialStep.EXPLANATION,
                title="Welcome to TinyCode Natural Language Interface",
                content="TinyCode now understands natural language! Instead of memorizing commands, you can just describe what you want to do.",
                hints=["Try speaking naturally", "Don't worry about exact syntax", "TinyCode will guide you"]
            ),
            TutorialStepData(
                step_type=TutorialStep.DEMONSTRATION,
                title="See Natural Language in Action",
                content="Here are examples of natural language commands:\n• 'Show me the files in this directory'\n• 'I need help fixing bugs in my Python code'\n• 'Can you explain this function?'",
                example_input="Show me what files are in this directory"
            ),
            TutorialStepData(
                step_type=TutorialStep.PRACTICE,
                title="Try Your First Natural Language Command",
                content="Now it's your turn! Try asking TinyCode to show you the files in the current directory using natural language.",
                expected_intent=Intent.FIND_FILES,
                validation_criteria="Intent must be LIST_FILES",
                hints=["Ask naturally like 'show me the files'", "Or 'what files are here?'", "Or 'list directory contents'"]
            ),
            TutorialStepData(
                step_type=TutorialStep.PRACTICE,
                title="Ask for Code Analysis",
                content="Try asking TinyCode to analyze a code file. Use natural language to express your request.",
                expected_intent=Intent.ANALYZE_CODE,
                validation_criteria="Intent must be ANALYZE_CODE",
                hints=["Try 'analyze my code'", "Or 'check this file for issues'", "Or 'review my Python script'"]
            ),
            TutorialStepData(
                step_type=TutorialStep.RECAP,
                title="Congratulations!",
                content="You've learned the basics of TinyCode's natural language interface! You can now:\n• Ask questions naturally\n• Request code analysis\n• Get file information\n\nNext, try the 'Code Operations' workflow to learn more advanced features."
            )
        ]

        workflows.append(Workflow(
            id="getting-started",
            name="Getting Started with Natural Language",
            description="Learn how to use TinyCode's natural language interface",
            category=WorkflowCategory.BEGINNER,
            difficulty_level=1,
            estimated_time_minutes=10,
            prerequisites=[],
            steps=beginner_steps,
            learning_objectives=[
                "Understand natural language interface",
                "Make first natural language requests",
                "Learn basic interaction patterns"
            ],
            completion_criteria="Successfully complete 2 practice steps",
            tags=["beginner", "nlp", "basics"]
        ))

        # Intermediate workflow: Code operations
        code_ops_steps = [
            TutorialStepData(
                step_type=TutorialStep.EXPLANATION,
                title="Code Operations with Natural Language",
                content="TinyCode can help with many code operations: fixing bugs, adding features, refactoring, and testing. Let's explore these capabilities.",
                hints=["Code operations are powerful", "Always review suggested changes", "Use specific requests for better results"]
            ),
            TutorialStepData(
                step_type=TutorialStep.PRACTICE,
                title="Request Bug Fixes",
                content="Try asking TinyCode to find and fix bugs in your code. Be specific about what kind of issues you're experiencing.",
                expected_intent=Intent.FIX_BUGS,
                validation_criteria="Intent must be FIX_BUGS",
                hints=["Try 'fix bugs in my code'", "Or 'help me debug this issue'", "Or 'find problems in my script'"]
            ),
            TutorialStepData(
                step_type=TutorialStep.PRACTICE,
                title="Request Code Completion",
                content="Ask TinyCode to complete or extend your code functionality.",
                expected_intent=Intent.COMPLETE_CODE,
                validation_criteria="Intent must be COMPLETE_CODE",
                hints=["Try 'complete this function'", "Or 'add more functionality'", "Or 'finish this implementation'"]
            ),
            TutorialStepData(
                step_type=TutorialStep.PRACTICE,
                title="Request Code Refactoring",
                content="Ask TinyCode to improve your code structure and organization.",
                expected_intent=Intent.REFACTOR_CODE,
                validation_criteria="Intent must be REFACTOR_CODE",
                hints=["Try 'refactor this code'", "Or 'improve code organization'", "Or 'make this code cleaner'"]
            )
        ]

        workflows.append(Workflow(
            id="code-operations",
            name="Code Operations Mastery",
            description="Master code operations using natural language",
            category=WorkflowCategory.INTERMEDIATE,
            difficulty_level=2,
            estimated_time_minutes=15,
            prerequisites=["getting-started"],
            steps=code_ops_steps,
            learning_objectives=[
                "Perform bug fixes with natural language",
                "Request code completion effectively",
                "Use refactoring capabilities"
            ],
            completion_criteria="Successfully complete all practice steps",
            tags=["intermediate", "coding", "operations"]
        ))

        # Advanced workflow: Project management
        project_mgmt_steps = [
            TutorialStepData(
                step_type=TutorialStep.EXPLANATION,
                title="Project Management with TinyCode",
                content="TinyCode can help manage entire projects: running tests, checking git status, analyzing project structure, and coordinating complex operations.",
                hints=["Project operations affect multiple files", "Always understand the scope", "Use confirmation before major changes"]
            ),
            TutorialStepData(
                step_type=TutorialStep.PRACTICE,
                title="Check Project Status",
                content="Ask TinyCode to give you an overview of your project's current state.",
                expected_intent=Intent.SHOW_STATUS,
                validation_criteria="Intent must be GET_STATUS",
                hints=["Try 'show project status'", "Or 'what's the current state?'", "Or 'give me an overview'"]
            ),
            TutorialStepData(
                step_type=TutorialStep.PRACTICE,
                title="Run Project Tests",
                content="Request that TinyCode run your project's test suite.",
                expected_intent=Intent.GENERATE_TESTS,
                validation_criteria="Intent must be RUN_TESTS",
                hints=["Try 'run the tests'", "Or 'check if tests pass'", "Or 'validate the code'"]
            )
        ]

        workflows.append(Workflow(
            id="project-management",
            name="Project Management with Natural Language",
            description="Manage projects efficiently using natural language commands",
            category=WorkflowCategory.ADVANCED,
            difficulty_level=3,
            estimated_time_minutes=20,
            prerequisites=["getting-started", "code-operations"],
            steps=project_mgmt_steps,
            learning_objectives=[
                "Manage project-wide operations",
                "Coordinate testing workflows",
                "Monitor project health"
            ],
            completion_criteria="Successfully complete project operations",
            tags=["advanced", "project", "management"]
        ))

        return workflows

    def show_available_workflows(self):
        """Display available workflows to the user"""
        table = Table(title="Available TinyCode Workflows")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="magenta")
        table.add_column("Level", style="green")
        table.add_column("Time", style="yellow")
        table.add_column("Status", style="blue")

        completed = set(self.progress_tracker.progress["completed_workflows"])

        for workflow in self.workflows:
            status = "✅ Completed" if workflow.id in completed else "📝 Available"
            table.add_row(
                workflow.id,
                workflow.name,
                workflow.category.value.title(),
                f"{workflow.estimated_time_minutes} min",
                status
            )

        self.console.print(table)

        # Show recommendations
        recommended = self.progress_tracker.get_recommended_workflows(self.workflows)
        if recommended:
            self.console.print("\n[bold green]Recommended for you:[/bold green]")
            for workflow in recommended:
                self.console.print(f"• {workflow.name} ({workflow.category.value})")

    def start_workflow(self, workflow_id: str) -> bool:
        """Start a specific workflow"""
        workflow = next((w for w in self.workflows if w.id == workflow_id), None)
        if not workflow:
            self.console.print(f"[red]Workflow '{workflow_id}' not found[/red]")
            return False

        # Check prerequisites
        completed = set(self.progress_tracker.progress["completed_workflows"])
        missing_prereqs = [p for p in workflow.prerequisites if p not in completed]
        if missing_prereqs:
            self.console.print(f"[yellow]Missing prerequisites: {', '.join(missing_prereqs)}[/yellow]")
            if not Confirm.ask("Continue anyway?"):
                return False

        self.console.print(Panel(
            f"[bold]{workflow.name}[/bold]\n\n"
            f"{workflow.description}\n\n"
            f"[dim]Difficulty: {workflow.difficulty_level}/5\n"
            f"Estimated time: {workflow.estimated_time_minutes} minutes[/dim]",
            title="Starting Workflow",
            border_style="green"
        ))

        start_time = time.time()
        success = self._run_workflow(workflow)
        end_time = time.time()

        time_spent = int((end_time - start_time) / 60)  # Convert to minutes

        if success:
            self.progress_tracker.mark_workflow_completed(workflow.id, time_spent)
            self.console.print(Panel(
                f"[bold green]Workflow Completed![/bold green]\n\n"
                f"Time spent: {time_spent} minutes\n"
                f"You've learned: {', '.join(workflow.learning_objectives)}",
                title="Congratulations!",
                border_style="green"
            ))

        return success

    def _run_workflow(self, workflow: Workflow) -> bool:
        """Run a workflow step by step"""
        total_steps = len(workflow.steps)

        with Progress() as progress:
            task = progress.add_task(f"[green]{workflow.name}", total=total_steps)

            for i, step in enumerate(workflow.steps):
                self.progress_tracker.update_current_step(workflow.id, i)

                if not self._run_step(step, i + 1, total_steps):
                    return False

                progress.update(task, advance=1)

                if i < total_steps - 1:  # Not the last step
                    if not Confirm.ask("\nReady for the next step?", default=True):
                        self.console.print("[yellow]Workflow paused. You can resume later.[/yellow]")
                        return False

        return True

    def _run_step(self, step: TutorialStepData, step_num: int, total_steps: int) -> bool:
        """Run an individual tutorial step"""
        self.console.print(f"\n[bold cyan]Step {step_num}/{total_steps}: {step.title}[/bold cyan]")
        self.console.print(step.content)

        if step.step_type == TutorialStep.EXPLANATION:
            return self._handle_explanation_step(step)
        elif step.step_type == TutorialStep.DEMONSTRATION:
            return self._handle_demonstration_step(step)
        elif step.step_type == TutorialStep.PRACTICE:
            return self._handle_practice_step(step)
        elif step.step_type == TutorialStep.VALIDATION:
            return self._handle_validation_step(step)
        elif step.step_type == TutorialStep.RECAP:
            return self._handle_recap_step(step)

        return True

    def _handle_explanation_step(self, step: TutorialStepData) -> bool:
        """Handle explanation step"""
        if step.hints:
            self.console.print("\n[dim]💡 Tips:[/dim]")
            for hint in step.hints:
                self.console.print(f"[dim]• {hint}[/dim]")

        input("\nPress Enter to continue...")
        return True

    def _handle_demonstration_step(self, step: TutorialStepData) -> bool:
        """Handle demonstration step"""
        if step.example_input:
            self.console.print(f"\n[bold yellow]Example:[/bold yellow] {step.example_input}")

            # Actually process the example to show results
            intent_result = self.intent_recognizer.process_input(step.example_input, {})
            self.console.print(f"[dim]→ TinyCode understands this as: {intent_result.intent.value}[/dim]")

        input("\nPress Enter to continue...")
        return True

    def _handle_practice_step(self, step: TutorialStepData) -> bool:
        """Handle practice step"""
        max_attempts = 3
        attempts = 0

        while attempts < max_attempts:
            self.console.print(f"\n[bold]Your turn![/bold] (Attempt {attempts + 1}/{max_attempts})")

            if step.hints and attempts > 0:
                self.console.print("\n[dim]💡 Hints:[/dim]")
                for hint in step.hints[:attempts]:  # Show more hints with each attempt
                    self.console.print(f"[dim]• {hint}[/dim]")

            user_input = Prompt.ask("Enter your natural language command")

            if user_input.lower() in ['skip', 'help', 'quit']:
                if user_input.lower() == 'skip':
                    self.console.print("[yellow]Skipping this step...[/yellow]")
                    return True
                elif user_input.lower() == 'help':
                    self._show_step_help(step)
                    continue
                elif user_input.lower() == 'quit':
                    return False

            # Validate the input
            intent_result = self.intent_recognizer.process_input(user_input, {})

            if step.expected_intent and intent_result.intent == step.expected_intent:
                self.console.print("[bold green]✅ Excellent! You got it right![/bold green]")
                self.progress_tracker.add_learned_command(user_input)
                return True
            else:
                attempts += 1
                if attempts < max_attempts:
                    self.console.print(f"[yellow]Not quite right. TinyCode understood this as '{intent_result.intent.value}', but we were looking for '{step.expected_intent.value}'. Try again![/yellow]")
                else:
                    self.console.print(f"[red]Let's move on. The expected intent was '{step.expected_intent.value}'.[/red]")
                    return Confirm.ask("Continue anyway?", default=True)

        return True

    def _handle_validation_step(self, step: TutorialStepData) -> bool:
        """Handle validation step"""
        self.console.print("[bold yellow]Validation step - checking your understanding...[/bold yellow]")
        # Implementation would depend on specific validation needs
        return True

    def _handle_recap_step(self, step: TutorialStepData) -> bool:
        """Handle recap step"""
        self.console.print(Panel(step.content, title="Recap", border_style="blue"))
        return True

    def _show_step_help(self, step: TutorialStepData):
        """Show help for a step"""
        help_text = f"This step is asking you to {step.title.lower()}.\n\n"
        help_text += step.content

        if step.hints:
            help_text += "\n\nHints:\n"
            for hint in step.hints:
                help_text += f"• {hint}\n"

        if step.expected_intent:
            help_text += f"\nTinyCode should understand your input as: {step.expected_intent.value}"

        self.console.print(Panel(help_text, title="Step Help", border_style="yellow"))

    def show_progress(self):
        """Show user's learning progress"""
        stats = self.progress_tracker.progress["statistics"]

        table = Table(title="Your Learning Progress")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Workflows Completed", str(stats["workflows_completed"]))
        table.add_row("Commands Learned", str(len(stats["commands_learned"])))
        table.add_row("Total Time Spent", f"{stats['total_time_spent']} minutes")
        table.add_row("Current Skill Level", self.progress_tracker.progress["skill_level"].title())

        self.console.print(table)

        if stats["commands_learned"]:
            self.console.print("\n[bold]Commands you've learned:[/bold]")
            for cmd in stats["commands_learned"][-5:]:  # Show last 5
                self.console.print(f"• {cmd}")

    def suggest_next_workflow(self) -> Optional[str]:
        """Suggest the next workflow to take"""
        recommended = self.progress_tracker.get_recommended_workflows(self.workflows)
        if recommended:
            return recommended[0].id
        return None


class GuidedWorkflowManager:
    """Main manager for guided workflows and tutorials"""

    def __init__(self, intent_recognizer: NLPProcessor, conversation_manager: ConversationManager):
        self.tutorial = InteractiveTutorial(intent_recognizer, conversation_manager)
        self.console = Console()

    def start_interactive_tutorial_mode(self):
        """Start interactive tutorial mode"""
        self.console.print(Panel(
            "[bold cyan]Welcome to TinyCode Interactive Tutorials![/bold cyan]\n\n"
            "Learn to use TinyCode's natural language interface through guided workflows.\n"
            "You can speak naturally instead of memorizing commands!",
            title="TinyCode Tutorials",
            border_style="cyan"
        ))

        while True:
            self.console.print("\n[bold]What would you like to do?[/bold]")
            self.console.print("1. View available workflows")
            self.console.print("2. Start a workflow")
            self.console.print("3. Show my progress")
            self.console.print("4. Get workflow recommendation")
            self.console.print("5. Exit tutorials")

            choice = Prompt.ask("Enter your choice", choices=["1", "2", "3", "4", "5"])

            if choice == "1":
                self.tutorial.show_available_workflows()
            elif choice == "2":
                workflow_id = Prompt.ask("Enter workflow ID")
                self.tutorial.start_workflow(workflow_id)
            elif choice == "3":
                self.tutorial.show_progress()
            elif choice == "4":
                suggested = self.tutorial.suggest_next_workflow()
                if suggested:
                    self.console.print(f"[green]Recommended workflow: {suggested}[/green]")
                    if Confirm.ask("Start this workflow?"):
                        self.tutorial.start_workflow(suggested)
                else:
                    self.console.print("[yellow]No specific recommendation. Check available workflows.[/yellow]")
            elif choice == "5":
                self.console.print("[green]Happy coding with TinyCode![/green]")
                break

    def quick_tutorial(self, topic: str = "basics") -> bool:
        """Run a quick tutorial on a specific topic"""
        if topic == "basics":
            return self.tutorial.start_workflow("getting-started")
        elif topic == "coding":
            return self.tutorial.start_workflow("code-operations")
        elif topic == "projects":
            return self.tutorial.start_workflow("project-management")
        else:
            self.console.print(f"[red]Unknown tutorial topic: {topic}[/red]")
            return False
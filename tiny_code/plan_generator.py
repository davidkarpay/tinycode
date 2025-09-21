"""Plan generation system for Propose mode"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown

console = Console()

class PlanStatus(Enum):
    """Status of an execution plan"""
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    FAILED = "failed"

class ActionType(Enum):
    """Types of actions that can be planned"""
    CREATE_FILE = "create_file"
    MODIFY_FILE = "modify_file"
    DELETE_FILE = "delete_file"
    RUN_COMMAND = "run_command"
    EXECUTE_CODE = "execute_code"
    INSTALL_PACKAGE = "install_package"
    CREATE_DIRECTORY = "create_directory"
    MOVE_FILE = "move_file"
    COPY_FILE = "copy_file"

@dataclass
class PlannedAction:
    """A single action within an execution plan"""
    id: str
    action_type: ActionType
    description: str
    target_path: Optional[str] = None
    content: Optional[str] = None
    command: Optional[str] = None
    dependencies: List[str] = None
    estimated_duration: int = 5  # seconds
    risk_level: str = "LOW"
    rollback_info: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.rollback_info is None:
            self.rollback_info = {}

@dataclass
class ExecutionPlan:
    """Complete execution plan with metadata"""
    id: str
    title: str
    description: str
    user_request: str
    actions: List[PlannedAction]
    status: PlanStatus
    created_at: datetime
    updated_at: datetime
    estimated_total_duration: int = 0
    tags: List[str] = None
    risk_assessment: str = "LOW"
    requires_backup: bool = False
    requires_confirmation: bool = False

    def __post_init__(self):
        if self.tags is None:
            self.tags = []

        # Calculate total duration and risk
        self.estimated_total_duration = sum(action.estimated_duration for action in self.actions)

        # Determine overall risk level
        risk_levels = [action.risk_level for action in self.actions]
        if "CRITICAL" in risk_levels:
            self.risk_assessment = "CRITICAL"
            self.requires_confirmation = True
        elif "HIGH" in risk_levels:
            self.risk_assessment = "HIGH"
            self.requires_confirmation = True
        elif "MEDIUM" in risk_levels:
            self.risk_assessment = "MEDIUM"

        # Check if backup is needed
        self.requires_backup = any(
            action.action_type in [ActionType.MODIFY_FILE, ActionType.DELETE_FILE]
            for action in self.actions
        )

class PlanGenerator:
    """Generates execution plans from user requests"""

    def __init__(self, storage_dir: str = "data/plans"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.plans: Dict[str, ExecutionPlan] = {}
        self._load_existing_plans()

        # Common patterns for different request types
        self.request_patterns = {
            "create_file": [
                "create", "make", "generate", "write", "build", "add"
            ],
            "modify_file": [
                "fix", "update", "change", "modify", "refactor", "improve", "edit"
            ],
            "analyze": [
                "analyze", "review", "check", "examine", "explain", "understand"
            ],
            "run": [
                "run", "execute", "start", "launch", "test"
            ]
        }

    def _load_existing_plans(self):
        """Load existing plans from storage"""
        try:
            for plan_file in self.storage_dir.glob("*.json"):
                with open(plan_file, 'r') as f:
                    plan_data = json.load(f)
                    plan = self._deserialize_plan(plan_data)
                    self.plans[plan.id] = plan

            if self.plans:
                console.print(f"[cyan]Loaded {len(self.plans)} existing plans[/cyan]")
        except Exception as e:
            console.print(f"[yellow]Could not load existing plans: {e}[/yellow]")

    def analyze_request(self, user_request: str) -> Dict[str, Any]:
        """Analyze a user request to understand intent and requirements"""
        request_lower = user_request.lower()

        analysis = {
            "intent": self._determine_intent(request_lower),
            "targets": self._extract_targets(user_request),
            "requirements": self._extract_requirements(user_request),
            "complexity": self._assess_complexity(user_request),
            "risk_factors": self._identify_risk_factors(request_lower)
        }

        return analysis

    def generate_plan(self, user_request: str, title: Optional[str] = None) -> ExecutionPlan:
        """Generate an execution plan from a user request"""
        console.print(f"[yellow]Analyzing request: {user_request}[/yellow]")

        # Analyze the request
        analysis = self.analyze_request(user_request)

        # Generate plan metadata
        plan_id = str(uuid.uuid4())[:8]
        plan_title = title or self._generate_title(user_request, analysis)

        # Generate actions based on analysis
        actions = self._generate_actions(user_request, analysis)

        # Create the plan
        plan = ExecutionPlan(
            id=plan_id,
            title=plan_title,
            description=self._generate_description(user_request, analysis),
            user_request=user_request,
            actions=actions,
            status=PlanStatus.DRAFT,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            tags=self._generate_tags(analysis)
        )

        # Store the plan
        self.plans[plan_id] = plan
        self._save_plan(plan)

        console.print(f"[green]Generated plan '{plan_title}' with {len(actions)} actions[/green]")
        return plan

    def _determine_intent(self, request_lower: str) -> str:
        """Determine the primary intent of the request"""
        for intent, keywords in self.request_patterns.items():
            if any(keyword in request_lower for keyword in keywords):
                return intent
        return "general"

    def _extract_targets(self, request: str) -> List[str]:
        """Extract file paths and targets from the request"""
        targets = []

        # Look for common file extensions
        import re
        file_patterns = [
            r'\b\w+\.py\b',
            r'\b\w+\.js\b',
            r'\b\w+\.tsx?\b',
            r'\b\w+\.java\b',
            r'\b\w+\.cpp\b',
            r'\b\w+\.h\b',
            r'\b\w+\.md\b',
            r'\b\w+\.txt\b',
            r'\b\w+\.json\b',
            r'\b\w+\.yaml\b',
            r'\b\w+\.yml\b'
        ]

        for pattern in file_patterns:
            matches = re.findall(pattern, request)
            targets.extend(matches)

        # Look for directory references
        if '/' in request or '\\' in request:
            # Extract potential paths
            words = request.split()
            for word in words:
                if ('/' in word or '\\' in word) and len(word) > 1:
                    targets.append(word)

        return list(set(targets))

    def _extract_requirements(self, request: str) -> List[str]:
        """Extract specific requirements from the request"""
        requirements = []

        # Common requirement keywords
        requirement_patterns = {
            "testing": ["test", "unit test", "integration test"],
            "documentation": ["document", "docs", "readme", "comment"],
            "error_handling": ["error", "exception", "try-catch", "handle"],
            "validation": ["validate", "check", "verify"],
            "optimization": ["optimize", "performance", "fast", "efficient"],
            "security": ["secure", "auth", "permission", "sanitize"]
        }

        request_lower = request.lower()
        for requirement, keywords in requirement_patterns.items():
            if any(keyword in request_lower for keyword in keywords):
                requirements.append(requirement)

        return requirements

    def _assess_complexity(self, request: str) -> str:
        """Assess the complexity of the request"""
        complexity_indicators = {
            "simple": ["fix bug", "add comment", "rename", "delete"],
            "medium": ["refactor", "add feature", "implement", "create class"],
            "complex": ["architecture", "framework", "system", "migrate", "redesign"]
        }

        request_lower = request.lower()
        for complexity, indicators in complexity_indicators.items():
            if any(indicator in request_lower for indicator in indicators):
                return complexity

        # Default complexity based on length and keywords
        if len(request.split()) < 5:
            return "simple"
        elif len(request.split()) < 15:
            return "medium"
        else:
            return "complex"

    def _identify_risk_factors(self, request_lower: str) -> List[str]:
        """Identify potential risk factors in the request"""
        risk_factors = []

        high_risk_keywords = [
            "delete", "remove", "drop", "truncate", "destroy",
            "format", "reset", "clear", "purge"
        ]

        medium_risk_keywords = [
            "modify", "change", "update", "refactor", "migrate",
            "install", "upgrade", "configure"
        ]

        for keyword in high_risk_keywords:
            if keyword in request_lower:
                risk_factors.append(f"HIGH_RISK: {keyword}")

        for keyword in medium_risk_keywords:
            if keyword in request_lower:
                risk_factors.append(f"MEDIUM_RISK: {keyword}")

        return risk_factors

    def _generate_actions(self, request: str, analysis: Dict[str, Any]) -> List[PlannedAction]:
        """Generate specific actions based on request analysis"""
        actions = []
        intent = analysis["intent"]
        targets = analysis["targets"]
        complexity = analysis["complexity"]

        if intent == "create_file":
            for target in targets or ["new_file.py"]:
                actions.append(PlannedAction(
                    id=str(uuid.uuid4())[:8],
                    action_type=ActionType.CREATE_FILE,
                    description=f"Create file {target}",
                    target_path=target,
                    content="# Generated content will be added here",
                    estimated_duration=10 if complexity == "simple" else 30,
                    risk_level="LOW"
                ))

        elif intent == "modify_file":
            for target in targets or ["existing_file.py"]:
                actions.append(PlannedAction(
                    id=str(uuid.uuid4())[:8],
                    action_type=ActionType.MODIFY_FILE,
                    description=f"Modify file {target}",
                    target_path=target,
                    estimated_duration=20 if complexity == "simple" else 60,
                    risk_level="MEDIUM",
                    rollback_info={"backup_required": True}
                ))

        elif intent == "run":
            actions.append(PlannedAction(
                id=str(uuid.uuid4())[:8],
                action_type=ActionType.RUN_COMMAND,
                description="Execute the requested command or script",
                command=request,
                estimated_duration=15,
                risk_level="HIGH"
            ))

        else:
            # Generic analysis action
            actions.append(PlannedAction(
                id=str(uuid.uuid4())[:8],
                action_type=ActionType.RUN_COMMAND,
                description=f"Analyze and process: {request}",
                command=f"echo 'Processing: {request}'",
                estimated_duration=5,
                risk_level="LOW"
            ))

        return actions

    def _generate_title(self, request: str, analysis: Dict[str, Any]) -> str:
        """Generate a concise title for the plan"""
        intent = analysis["intent"].replace("_", " ").title()
        targets = analysis["targets"]

        if targets:
            target_str = targets[0] if len(targets) == 1 else f"{targets[0]} and {len(targets)-1} others"
            return f"{intent}: {target_str}"
        else:
            return f"{intent}: {request[:30]}..."

    def _generate_description(self, request: str, analysis: Dict[str, Any]) -> str:
        """Generate a detailed description for the plan"""
        description = f"User Request: {request}\n\n"
        description += f"Intent: {analysis['intent']}\n"
        description += f"Complexity: {analysis['complexity']}\n"

        if analysis["targets"]:
            description += f"Targets: {', '.join(analysis['targets'])}\n"

        if analysis["requirements"]:
            description += f"Requirements: {', '.join(analysis['requirements'])}\n"

        if analysis["risk_factors"]:
            description += f"Risk Factors: {', '.join(analysis['risk_factors'])}\n"

        return description

    def _generate_tags(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate tags for the plan"""
        tags = [analysis["intent"], analysis["complexity"]]
        tags.extend(analysis["requirements"])
        return list(set(tags))

    def _save_plan(self, plan: ExecutionPlan):
        """Save a plan to storage"""
        try:
            plan_file = self.storage_dir / f"{plan.id}.json"
            plan_dict = asdict(plan)

            # Convert datetime objects to strings
            plan_dict["created_at"] = plan.created_at.isoformat()
            plan_dict["updated_at"] = plan.updated_at.isoformat()
            plan_dict["status"] = plan.status.value

            # Convert enum values in actions
            for action in plan_dict["actions"]:
                action["action_type"] = action["action_type"].value

            with open(plan_file, 'w') as f:
                json.dump(plan_dict, f, indent=2)

        except Exception as e:
            console.print(f"[red]Error saving plan: {e}[/red]")

    def _deserialize_plan(self, plan_dict: Dict[str, Any]) -> ExecutionPlan:
        """Deserialize a plan from storage"""
        # Convert string dates back to datetime
        plan_dict["created_at"] = datetime.fromisoformat(plan_dict["created_at"])
        plan_dict["updated_at"] = datetime.fromisoformat(plan_dict["updated_at"])
        plan_dict["status"] = PlanStatus(plan_dict["status"])

        # Convert action enums
        for action in plan_dict["actions"]:
            action["action_type"] = ActionType(action["action_type"])

        # Convert actions to PlannedAction objects
        actions = [PlannedAction(**action) for action in plan_dict["actions"]]
        plan_dict["actions"] = actions

        return ExecutionPlan(**plan_dict)

    def get_plan(self, plan_id: str) -> Optional[ExecutionPlan]:
        """Get a plan by ID"""
        return self.plans.get(plan_id)

    def list_plans(self, status: Optional[PlanStatus] = None) -> List[ExecutionPlan]:
        """List all plans, optionally filtered by status"""
        plans = list(self.plans.values())
        if status:
            plans = [p for p in plans if p.status == status]
        return sorted(plans, key=lambda p: p.created_at, reverse=True)

    def update_plan_status(self, plan_id: str, status: PlanStatus) -> bool:
        """Update the status of a plan"""
        if plan_id not in self.plans:
            return False

        self.plans[plan_id].status = status
        self.plans[plan_id].updated_at = datetime.now()
        self._save_plan(self.plans[plan_id])
        return True

    def delete_plan(self, plan_id: str) -> bool:
        """Delete a plan"""
        if plan_id not in self.plans:
            return False

        try:
            plan_file = self.storage_dir / f"{plan_id}.json"
            if plan_file.exists():
                plan_file.unlink()
            del self.plans[plan_id]
            return True
        except Exception as e:
            console.print(f"[red]Error deleting plan: {e}[/red]")
            return False

    def show_plan_details(self, plan: ExecutionPlan):
        """Display detailed information about a plan"""
        # Plan header
        status_color = {
            PlanStatus.DRAFT: "yellow",
            PlanStatus.PENDING: "blue",
            PlanStatus.APPROVED: "green",
            PlanStatus.REJECTED: "red",
            PlanStatus.EXECUTED: "bright_green",
            PlanStatus.FAILED: "bright_red"
        }.get(plan.status, "white")

        header = f"[bold]{plan.title}[/bold]\n"
        header += f"Status: [{status_color}]{plan.status.value.upper()}[/]\n"
        header += f"Risk: {plan.risk_assessment} | Duration: ~{plan.estimated_total_duration}s\n"
        header += f"Created: {plan.created_at.strftime('%Y-%m-%d %H:%M')}"

        console.print(Panel(header, title=f"Plan {plan.id}", border_style=status_color))

        # Description
        console.print(Panel(plan.description, title="Description", border_style="blue"))

        # Actions table
        table = Table(title="Planned Actions")
        table.add_column("ID", style="dim")
        table.add_column("Type", style="cyan")
        table.add_column("Description", style="white")
        table.add_column("Target", style="yellow")
        table.add_column("Risk", style="red")
        table.add_column("Duration", style="green")

        for action in plan.actions:
            risk_color = {
                "LOW": "[green]",
                "MEDIUM": "[yellow]",
                "HIGH": "[red]",
                "CRITICAL": "[bold red]"
            }.get(action.risk_level, "[white]")

            table.add_row(
                action.id,
                action.action_type.value.replace("_", " ").title(),
                action.description,
                action.target_path or action.command or "-",
                f"{risk_color}{action.risk_level}[/]",
                f"{action.estimated_duration}s"
            )

        console.print(table)

        # Safety warnings
        if plan.requires_confirmation:
            console.print(Panel(
                "[bold red]⚠️  This plan requires explicit confirmation before execution[/bold red]",
                border_style="red"
            ))

        if plan.requires_backup:
            console.print(Panel(
                "[bold yellow]💾 This plan will create backups before modifying files[/bold yellow]",
                border_style="yellow"
            ))
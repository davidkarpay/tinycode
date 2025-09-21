"""Plan validation system for safety and compliance checking"""

import re
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

class ValidationSeverity(Enum):
    """Severity levels for validation issues"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class ValidationIssue:
    """Individual validation issue"""
    severity: ValidationSeverity
    category: str
    message: str
    action_id: Optional[str] = None
    suggestion: Optional[str] = None

@dataclass
class ValidationResult:
    """Result of plan validation"""
    is_valid: bool
    issues: List[ValidationIssue]
    complexity_score: int
    risk_assessment: str
    recommendations: List[str]

    def has_blocking_issues(self) -> bool:
        """Check if there are blocking issues that prevent execution"""
        return any(issue.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]
                  for issue in self.issues)

    def get_issues_by_severity(self, severity: ValidationSeverity) -> List[ValidationIssue]:
        """Get issues filtered by severity"""
        return [issue for issue in self.issues if issue.severity == severity]

class PlanValidator:
    """Comprehensive plan validation system"""

    def __init__(self, safety_config):
        self.safety_config = safety_config
        self.dangerous_patterns = self._load_dangerous_patterns()
        self.system_paths = self._load_system_paths()

    def _load_dangerous_patterns(self) -> Dict[str, List[str]]:
        """Load dangerous command and content patterns"""
        return {
            'dangerous_commands': [
                r'\brm\s+-rf\s+/',
                r'\bsudo\s+rm\s+',
                r'\bdel\s+/[sq]\s+',
                r'\bformat\s+[c-z]:',
                r'\bkillall\s+',
                r'\bshutdown\s+',
                r'\breboot\s+',
                r'\bhalt\s+',
                r'\bmkfs\.',
                r'\bfdisk\s+',
                r'\bdd\s+.*of=/dev/',
                r'>\s*/dev/s[dr]',
                r'\bchmod\s+777\s+/',
                r'\bchown\s+.*:\s*/',
            ],
            'suspicious_content': [
                r'eval\s*\(',
                r'exec\s*\(',
                r'__import__\s*\(',
                r'getattr\s*\(',
                r'setattr\s*\(',
                r'delattr\s*\(',
                r'compile\s*\(',
                r'open\s*\([^)]*["\']r["\']',  # read mode might be ok, but check context
                r'urllib\.request',
                r'subprocess\.',
                r'os\.system',
                r'os\.popen',
                r'shell=True',
                r'pickle\.loads',
                r'marshal\.loads',
            ],
            'network_operations': [
                r'socket\.',
                r'urllib',
                r'requests\.',
                r'http\.',
                r'ftp\.',
                r'ssh\.',
                r'telnet\.',
                r'smtplib\.',
            ]
        }

    def _load_system_paths(self) -> List[str]:
        """Load critical system paths that should be protected"""
        return [
            '/etc', '/usr', '/bin', '/sbin', '/boot', '/sys', '/proc',
            '/dev', '/var/log', '/tmp', '/root',
            'C:\\Windows', 'C:\\Program Files', 'C:\\System32',
            '/System', '/Library', '/Applications'
        ]

    def validate_plan(self, plan) -> ValidationResult:
        """Validate a complete execution plan"""
        issues = []
        complexity_score = 0
        recommendations = []

        # Basic plan structure validation
        issues.extend(self._validate_plan_structure(plan))

        # Safety configuration compliance
        config_issues, config_score = self._validate_safety_compliance(plan)
        issues.extend(config_issues)
        complexity_score += config_score

        # Individual action validation
        for action in plan.actions:
            action_issues, action_score = self._validate_action(action)
            issues.extend(action_issues)
            complexity_score += action_score

        # Cross-action validation
        issues.extend(self._validate_action_dependencies(plan.actions))

        # File system impact analysis
        fs_issues, fs_score = self._validate_filesystem_impact(plan.actions)
        issues.extend(fs_issues)
        complexity_score += fs_score

        # Generate risk assessment
        risk_assessment = self._calculate_risk_assessment(issues, complexity_score)

        # Generate recommendations
        recommendations = self._generate_recommendations(issues, plan)

        # Determine if plan is valid
        is_valid = not any(issue.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]
                          for issue in issues)

        return ValidationResult(
            is_valid=is_valid,
            issues=issues,
            complexity_score=complexity_score,
            risk_assessment=risk_assessment,
            recommendations=recommendations
        )

    def _validate_plan_structure(self, plan) -> List[ValidationIssue]:
        """Validate basic plan structure"""
        issues = []

        if not hasattr(plan, 'actions') or not plan.actions:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="Structure",
                message="Plan has no actions defined",
                suggestion="Add at least one action to the plan"
            ))

        if not hasattr(plan, 'title') or not plan.title.strip():
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="Structure",
                message="Plan has no title",
                suggestion="Add a descriptive title to the plan"
            ))

        if len(plan.actions) > self.safety_config.config.execution_limits.max_files_per_plan:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="Limits",
                message=f"Plan exceeds maximum actions limit: {len(plan.actions)} > {self.safety_config.config.execution_limits.max_files_per_plan}",
                suggestion="Reduce the number of actions or increase the limit in safety configuration"
            ))

        return issues

    def _validate_safety_compliance(self, plan) -> Tuple[List[ValidationIssue], int]:
        """Validate compliance with safety configuration"""
        issues = []
        complexity_score = 0

        # Convert plan to dict format for safety config validation
        plan_data = {
            'actions': [{'target': action.target_path or '', 'type': action.action_type.value} for action in plan.actions],
            'complexity_score': 0  # Will be calculated
        }

        violations = self.safety_config.validate_execution_request(plan_data)

        for violation in violations:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="Safety",
                message=violation,
                suggestion="Modify the plan to comply with safety restrictions"
            ))
            complexity_score += 10  # Each violation adds complexity

        return issues, complexity_score

    def _validate_action(self, action) -> Tuple[List[ValidationIssue], int]:
        """Validate individual action"""
        issues = []
        complexity_score = 0

        # Action type validation
        from .plan_generator import ActionType
        if action.action_type == ActionType.DELETE_FILE:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="Destructive",
                message=f"Action {action.action_id} performs file deletion: {action.target}",
                action_id=action.action_id,
                suggestion="Ensure backup is created before deletion"
            ))
            complexity_score += 15

        elif action.action_type == ActionType.RUN_COMMAND:
            cmd_issues, cmd_score = self._validate_command(action)
            issues.extend(cmd_issues)
            complexity_score += cmd_score

        # File path validation
        if hasattr(action, 'target_path') and action.target_path:
            path_issues = self._validate_file_path(action.target_path, action.id)
            issues.extend(path_issues)

            # Add complexity based on file type
            if action.target_path.endswith(('.exe', '.dll', '.so', '.dylib')):
                complexity_score += 20
            elif action.target_path.endswith(('.py', '.js', '.sh', '.bat')):
                complexity_score += 10

        # Content validation for file creation/modification
        if hasattr(action, 'content') and action.content:
            content_issues, content_score = self._validate_content(action.content, action.id)
            issues.extend(content_issues)
            complexity_score += content_score

        return issues, complexity_score

    def _validate_command(self, action) -> Tuple[List[ValidationIssue], int]:
        """Validate command execution actions"""
        issues = []
        complexity_score = 5  # Base complexity for commands

        command = getattr(action, 'command', '') or getattr(action, 'target_path', '')

        # Check for dangerous command patterns
        for pattern in self.dangerous_patterns['dangerous_commands']:
            if re.search(pattern, command, re.IGNORECASE):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.CRITICAL,
                    category="Dangerous Command",
                    message=f"Action {action.id} contains dangerous command pattern: {pattern}",
                    action_id=action.id,
                    suggestion="Remove or modify the dangerous command"
                ))
                complexity_score += 30

        # Check for network operations
        for pattern in self.dangerous_patterns['network_operations']:
            if re.search(pattern, command, re.IGNORECASE):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="Network Operation",
                    message=f"Action {action.id} performs network operations",
                    action_id=action.id,
                    suggestion="Ensure network operations are necessary and safe"
                ))
                complexity_score += 10

        return issues, complexity_score

    def _validate_content(self, content: str, action_id: str) -> Tuple[List[ValidationIssue], int]:
        """Validate file content for suspicious patterns"""
        issues = []
        complexity_score = 0

        # Check for suspicious content patterns
        for pattern in self.dangerous_patterns['suspicious_content']:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="Suspicious Content",
                    message=f"Action {action_id} contains suspicious pattern: {pattern}",
                    action_id=action_id,
                    suggestion="Review the code for potential security issues"
                ))
                complexity_score += 5

        # Check content length
        if len(content) > self.safety_config.config.execution_limits.max_file_size_mb * 1024 * 1024:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="Size Limit",
                message=f"Action {action_id} content exceeds size limit",
                action_id=action_id,
                suggestion="Reduce file size or increase limit in configuration"
            ))
            complexity_score += 20

        return issues, complexity_score

    def _validate_file_path(self, file_path: str, action_id: str) -> List[ValidationIssue]:
        """Validate file path safety"""
        issues = []

        # Check for system paths
        abs_path = os.path.abspath(file_path)
        for system_path in self.system_paths:
            if abs_path.startswith(system_path):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.CRITICAL,
                    category="System Path",
                    message=f"Action {action_id} targets system path: {file_path}",
                    action_id=action_id,
                    suggestion="Target files in user space instead"
                ))

        # Check for path traversal attempts
        if '..' in file_path or file_path.startswith('/'):
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="Path Traversal",
                message=f"Action {action_id} uses potentially unsafe path: {file_path}",
                action_id=action_id,
                suggestion="Use relative paths within the workspace"
            ))

        return issues

    def _validate_action_dependencies(self, actions) -> List[ValidationIssue]:
        """Validate dependencies between actions"""
        issues = []
        file_operations = {}

        # Track file operations
        for action in actions:
            if hasattr(action, 'target_path') and action.target_path:
                file_path = action.target_path
                if file_path not in file_operations:
                    file_operations[file_path] = []
                file_operations[file_path].append(action)

        # Check for conflicting operations on same files
        for file_path, file_actions in file_operations.items():
            if len(file_actions) > 1:
                from .plan_generator import ActionType
                action_types = [action.action_type for action in file_actions]

                # Check for create followed by delete
                if ActionType.CREATE_FILE in action_types and ActionType.DELETE_FILE in action_types:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        category="Conflicting Operations",
                        message=f"File {file_path} is both created and deleted in the same plan",
                        suggestion="Consider if both operations are necessary"
                    ))

                # Check for multiple modifications
                modify_count = action_types.count(ActionType.MODIFY_FILE)
                if modify_count > 1:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.INFO,
                        category="Multiple Modifications",
                        message=f"File {file_path} is modified {modify_count} times",
                        suggestion="Consider combining modifications into a single action"
                    ))

        return issues

    def _validate_filesystem_impact(self, actions) -> Tuple[List[ValidationIssue], int]:
        """Validate overall filesystem impact"""
        issues = []
        complexity_score = 0

        from .plan_generator import ActionType

        create_count = sum(1 for action in actions if action.action_type == ActionType.CREATE_FILE)
        modify_count = sum(1 for action in actions if action.action_type == ActionType.MODIFY_FILE)
        delete_count = sum(1 for action in actions if action.action_type == ActionType.DELETE_FILE)

        # High impact operations
        if delete_count > 5:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="High Impact",
                message=f"Plan deletes {delete_count} files",
                suggestion="Ensure all deletions are necessary and backed up"
            ))
            complexity_score += delete_count * 3

        if create_count > 20:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                category="High Volume",
                message=f"Plan creates {create_count} files",
                suggestion="Consider if all file creations are necessary"
            ))
            complexity_score += create_count

        return issues, complexity_score

    def _calculate_risk_assessment(self, issues: List[ValidationIssue], complexity_score: int) -> str:
        """Calculate overall risk assessment"""
        critical_count = len([i for i in issues if i.severity == ValidationSeverity.CRITICAL])
        error_count = len([i for i in issues if i.severity == ValidationSeverity.ERROR])
        warning_count = len([i for i in issues if i.severity == ValidationSeverity.WARNING])

        if critical_count > 0:
            return "CRITICAL"
        elif error_count > 0:
            return "HIGH"
        elif warning_count > 3 or complexity_score > 100:
            return "MEDIUM"
        elif warning_count > 0 or complexity_score > 50:
            return "LOW"
        else:
            return "MINIMAL"

    def _generate_recommendations(self, issues: List[ValidationIssue], plan) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []

        # Group issues by category
        categories = {}
        for issue in issues:
            if issue.category not in categories:
                categories[issue.category] = []
            categories[issue.category].append(issue)

        # Generate category-specific recommendations
        if "Dangerous Command" in categories:
            recommendations.append("Review and remove dangerous commands before execution")

        if "System Path" in categories:
            recommendations.append("Restrict operations to user workspace directories")

        if "Size Limit" in categories:
            recommendations.append("Consider breaking large operations into smaller chunks")

        if "Destructive" in categories:
            recommendations.append("Ensure comprehensive backups before destructive operations")

        if "Suspicious Content" in categories:
            recommendations.append("Review code content for security vulnerabilities")

        # General recommendations based on plan complexity
        if len(plan.actions) > 10:
            recommendations.append("Consider executing plan in phases for better control")

        if not recommendations:
            recommendations.append("Plan appears safe for execution")

        return recommendations

    def show_validation_results(self, result: ValidationResult):
        """Display validation results with Rich formatting"""

        # Main status panel
        status_color = "green" if result.is_valid else "red"
        status_text = "VALID" if result.is_valid else "INVALID"

        console.print(Panel(
            f"[bold {status_color}]Validation Status: {status_text}[/bold {status_color}]\n"
            f"Risk Assessment: [bold]{result.risk_assessment}[/bold]\n"
            f"Complexity Score: {result.complexity_score}\n"
            f"Issues Found: {len(result.issues)}",
            title="Plan Validation Results",
            border_style=status_color
        ))

        # Issues table
        if result.issues:
            issues_table = Table(title="Validation Issues")
            issues_table.add_column("Severity", style="red")
            issues_table.add_column("Category", style="cyan")
            issues_table.add_column("Message", style="white")
            issues_table.add_column("Action ID", style="dim")

            for issue in result.issues:
                severity_color = {
                    ValidationSeverity.INFO: "[blue]",
                    ValidationSeverity.WARNING: "[yellow]",
                    ValidationSeverity.ERROR: "[red]",
                    ValidationSeverity.CRITICAL: "[bold red]"
                }.get(issue.severity, "[white]")

                issues_table.add_row(
                    f"{severity_color}{issue.severity.value.upper()}[/]",
                    issue.category,
                    issue.message[:80] + "..." if len(issue.message) > 80 else issue.message,
                    issue.action_id or "N/A"
                )

            console.print(issues_table)

        # Recommendations
        if result.recommendations:
            console.print("\n[bold cyan]Recommendations:[/bold cyan]")
            for i, rec in enumerate(result.recommendations, 1):
                console.print(f"  {i}. {rec}")

        console.print()
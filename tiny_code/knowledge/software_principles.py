"""
Software Development Principles and Conventions

This module contains comprehensive software development principles, patterns,
and conventions used for code evaluation and quality assessment in TinyCode.

Includes:
- SOLID principles
- Clean Code principles (DRY, KISS, YAGNI)
- Clean Architecture patterns
- Code quality metrics
- Testing conventions
- Security standards
- Performance benchmarks
- Documentation standards
- Version control conventions
- Code review criteria
- Refactoring indicators
- DevOps maturity model
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Union
import json


class PrincipleCategory(Enum):
    """Categories of software development principles."""
    SOLID = "solid"
    CLEAN_CODE = "clean_code"
    ARCHITECTURE = "architecture"
    TESTING = "testing"
    SECURITY = "security"
    PERFORMANCE = "performance"
    DOCUMENTATION = "documentation"
    VERSION_CONTROL = "version_control"
    CODE_REVIEW = "code_review"
    REFACTORING = "refactoring"
    DEVOPS = "devops"


class SeverityLevel(Enum):
    """Severity levels for principle violations."""
    CRITICAL = "critical"  # Major architectural flaws, security issues
    HIGH = "high"         # Significant quality issues
    MEDIUM = "medium"     # Quality improvements recommended
    LOW = "low"          # Minor style/convention issues
    INFO = "info"        # Informational suggestions


@dataclass
class Principle:
    """A single software development principle."""
    name: str
    description: str
    category: PrincipleCategory
    severity: SeverityLevel
    examples: List[str] = field(default_factory=list)
    violations: List[str] = field(default_factory=list)
    best_practices: List[str] = field(default_factory=list)
    code_patterns: List[str] = field(default_factory=list)
    anti_patterns: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QualityMetric:
    """A quality metric for code evaluation."""
    name: str
    description: str
    measurement_type: str  # "numeric", "percentage", "boolean", "enum"
    threshold_good: Optional[Union[int, float, bool, str]] = None
    threshold_excellent: Optional[Union[int, float, bool, str]] = None
    higher_is_better: bool = True


class BasePrincipleSet(ABC):
    """Base class for principle sets."""

    @abstractmethod
    def get_principles(self) -> List[Principle]:
        """Return all principles in this set."""
        pass

    @abstractmethod
    def get_metrics(self) -> List[QualityMetric]:
        """Return all metrics for this principle set."""
        pass


class SOLIDPrinciples(BasePrincipleSet):
    """SOLID principles implementation."""

    def get_principles(self) -> List[Principle]:
        return [
            Principle(
                name="Single Responsibility Principle (SRP)",
                description="A class should have only one reason to change",
                category=PrincipleCategory.SOLID,
                severity=SeverityLevel.HIGH,
                examples=[
                    "A User class should only handle user data, not email sending",
                    "A FileProcessor should only process files, not log operations"
                ],
                violations=[
                    "Classes with multiple unrelated methods",
                    "Classes that handle both business logic and UI concerns",
                    "Methods that do multiple unrelated things"
                ],
                best_practices=[
                    "Keep classes focused on a single concern",
                    "Extract unrelated functionality into separate classes",
                    "Use composition over inheritance for multiple responsibilities"
                ],
                code_patterns=[
                    "class.*{[^}]*public.*private.*public.*private.*}",  # Multiple sections
                    "class.*extends.*implements.*{.*database.*ui.*network.*}"  # Mixed concerns
                ],
                anti_patterns=[
                    "GodClass", "SwissArmyKnife", "TheBlob"
                ]
            ),
            Principle(
                name="Open/Closed Principle (OCP)",
                description="Software entities should be open for extension, closed for modification",
                category=PrincipleCategory.SOLID,
                severity=SeverityLevel.MEDIUM,
                examples=[
                    "Using strategy pattern for different algorithms",
                    "Plugin architecture for extensibility"
                ],
                violations=[
                    "Modifying existing classes to add new functionality",
                    "Large switch/if-else statements for type checking",
                    "Direct modification of third-party libraries"
                ],
                best_practices=[
                    "Use interfaces and abstract classes",
                    "Implement strategy and decorator patterns",
                    "Design for extensibility from the start"
                ]
            ),
            Principle(
                name="Liskov Substitution Principle (LSP)",
                description="Objects of a superclass should be replaceable with objects of its subclasses",
                category=PrincipleCategory.SOLID,
                severity=SeverityLevel.HIGH,
                examples=[
                    "Square and Rectangle inheritance hierarchy",
                    "Consistent interface contracts across implementations"
                ],
                violations=[
                    "Subclasses that weaken preconditions",
                    "Subclasses that strengthen postconditions",
                    "Throwing exceptions not declared in base class"
                ]
            ),
            Principle(
                name="Interface Segregation Principle (ISP)",
                description="Clients should not be forced to depend on interfaces they don't use",
                category=PrincipleCategory.SOLID,
                severity=SeverityLevel.MEDIUM,
                examples=[
                    "Separating read and write interfaces",
                    "Role-based interfaces instead of fat interfaces"
                ],
                violations=[
                    "Fat interfaces with many unrelated methods",
                    "Clients implementing empty methods",
                    "Large interface with optional methods"
                ]
            ),
            Principle(
                name="Dependency Inversion Principle (DIP)",
                description="High-level modules should not depend on low-level modules. Both should depend on abstractions",
                category=PrincipleCategory.SOLID,
                severity=SeverityLevel.HIGH,
                examples=[
                    "Dependency injection for database access",
                    "Using interfaces for external services"
                ],
                violations=[
                    "Direct instantiation of concrete classes",
                    "Tight coupling to specific implementations",
                    "Missing abstraction layers"
                ]
            )
        ]

    def get_metrics(self) -> List[QualityMetric]:
        return [
            QualityMetric(
                name="class_responsibility_count",
                description="Number of distinct responsibilities per class",
                measurement_type="numeric",
                threshold_good=1,
                threshold_excellent=1,
                higher_is_better=False
            ),
            QualityMetric(
                name="coupling_between_objects",
                description="CBO - Number of classes coupled to a given class",
                measurement_type="numeric",
                threshold_good=10,
                threshold_excellent=5,
                higher_is_better=False
            )
        ]


class CleanCodePrinciples(BasePrincipleSet):
    """Clean Code principles (DRY, KISS, YAGNI, etc.)."""

    def get_principles(self) -> List[Principle]:
        return [
            Principle(
                name="Don't Repeat Yourself (DRY)",
                description="Every piece of knowledge must have a single, unambiguous representation",
                category=PrincipleCategory.CLEAN_CODE,
                severity=SeverityLevel.MEDIUM,
                examples=[
                    "Extract common functionality into functions",
                    "Use constants for repeated values",
                    "Create reusable components"
                ],
                violations=[
                    "Duplicated code blocks",
                    "Copy-paste programming",
                    "Repeated logic in multiple places"
                ],
                best_practices=[
                    "Extract methods for repeated code",
                    "Use inheritance or composition",
                    "Create utility functions and constants"
                ],
                code_patterns=[
                    r"(?s)(.*?)\n.*?\1",  # Basic duplication pattern
                    r"if.*?{.*?}.*?if.*?{.*?}"  # Similar conditional blocks
                ]
            ),
            Principle(
                name="Keep It Simple, Stupid (KISS)",
                description="Simplicity should be a key goal in design",
                category=PrincipleCategory.CLEAN_CODE,
                severity=SeverityLevel.MEDIUM,
                examples=[
                    "Simple algorithms over complex ones when performance allows",
                    "Clear, readable code over clever code",
                    "Straightforward solutions over over-engineered ones"
                ],
                violations=[
                    "Overly complex logic",
                    "Unnecessary abstraction layers",
                    "Clever but unreadable code"
                ],
                best_practices=[
                    "Prefer simplicity over cleverness",
                    "Use clear naming conventions",
                    "Avoid premature optimization"
                ]
            ),
            Principle(
                name="You Aren't Gonna Need It (YAGNI)",
                description="Don't add functionality until it's necessary",
                category=PrincipleCategory.CLEAN_CODE,
                severity=SeverityLevel.LOW,
                examples=[
                    "Implement features as needed",
                    "Avoid speculative generality",
                    "Remove unused code"
                ],
                violations=[
                    "Unused methods and classes",
                    "Over-generalized solutions",
                    "Premature abstraction"
                ]
            ),
            Principle(
                name="Meaningful Names",
                description="Use intention-revealing, searchable, pronounceable names",
                category=PrincipleCategory.CLEAN_CODE,
                severity=SeverityLevel.LOW,
                examples=[
                    "getUserById() instead of get()",
                    "isValidEmail() instead of check()",
                    "MAX_RETRY_ATTEMPTS instead of 3"
                ],
                violations=[
                    "Single letter variables (except loop counters)",
                    "Unclear abbreviations",
                    "Mental mapping required"
                ],
                code_patterns=[
                    r"\b[a-z]\b",  # Single letter variables
                    r"\b(data|info|obj|tmp|temp)\d*\b",  # Generic names
                    r"\b[a-z]{1,2}\d+\b"  # Abbreviated names with numbers
                ]
            ),
            Principle(
                name="Functions Should Be Small",
                description="Functions should be small and do one thing well",
                category=PrincipleCategory.CLEAN_CODE,
                severity=SeverityLevel.MEDIUM,
                examples=[
                    "Functions under 20 lines",
                    "Single level of abstraction",
                    "Descriptive function names"
                ],
                violations=[
                    "Functions longer than 50 lines",
                    "Functions doing multiple things",
                    "Deep nesting levels"
                ],
                metrics={
                    "max_function_length": 20,
                    "max_nesting_level": 3,
                    "max_parameters": 3
                }
            )
        ]

    def get_metrics(self) -> List[QualityMetric]:
        return [
            QualityMetric(
                name="function_length",
                description="Lines of code per function",
                measurement_type="numeric",
                threshold_good=20,
                threshold_excellent=10,
                higher_is_better=False
            ),
            QualityMetric(
                name="cyclomatic_complexity",
                description="McCabe cyclomatic complexity",
                measurement_type="numeric",
                threshold_good=10,
                threshold_excellent=5,
                higher_is_better=False
            ),
            QualityMetric(
                name="duplicate_code_percentage",
                description="Percentage of duplicated code",
                measurement_type="percentage",
                threshold_good=5.0,
                threshold_excellent=2.0,
                higher_is_better=False
            )
        ]


class TestingPrinciples(BasePrincipleSet):
    """Testing conventions and principles."""

    def get_principles(self) -> List[Principle]:
        return [
            Principle(
                name="Test Pyramid",
                description="Maintain proper balance of unit, integration, and E2E tests",
                category=PrincipleCategory.TESTING,
                severity=SeverityLevel.HIGH,
                examples=[
                    "70% unit tests, 20% integration tests, 10% E2E tests",
                    "Fast feedback with unit tests",
                    "Comprehensive integration testing"
                ],
                violations=[
                    "Too many E2E tests",
                    "Missing unit tests",
                    "Inverted test pyramid"
                ],
                metrics={
                    "unit_test_ratio": 0.7,
                    "integration_test_ratio": 0.2,
                    "e2e_test_ratio": 0.1
                }
            ),
            Principle(
                name="Test-Driven Development (TDD)",
                description="Write tests before implementation",
                category=PrincipleCategory.TESTING,
                severity=SeverityLevel.MEDIUM,
                examples=[
                    "Red-Green-Refactor cycle",
                    "Tests as specification",
                    "Incremental development"
                ]
            ),
            Principle(
                name="Arrange-Act-Assert (AAA)",
                description="Structure tests with clear setup, execution, and verification",
                category=PrincipleCategory.TESTING,
                severity=SeverityLevel.LOW,
                examples=[
                    "Clear test structure",
                    "Single assertion per test",
                    "Descriptive test names"
                ]
            ),
            Principle(
                name="Test Coverage",
                description="Maintain adequate test coverage for critical code",
                category=PrincipleCategory.TESTING,
                severity=SeverityLevel.HIGH,
                metrics={
                    "line_coverage_minimum": 80,
                    "branch_coverage_minimum": 75,
                    "critical_path_coverage": 100
                }
            )
        ]

    def get_metrics(self) -> List[QualityMetric]:
        return [
            QualityMetric(
                name="test_coverage",
                description="Percentage of code covered by tests",
                measurement_type="percentage",
                threshold_good=80.0,
                threshold_excellent=90.0,
                higher_is_better=True
            ),
            QualityMetric(
                name="test_to_code_ratio",
                description="Ratio of test code to production code",
                measurement_type="numeric",
                threshold_good=1.0,
                threshold_excellent=1.5,
                higher_is_better=True
            )
        ]


class SecurityPrinciples(BasePrincipleSet):
    """Security standards and OWASP guidelines."""

    def get_principles(self) -> List[Principle]:
        return [
            Principle(
                name="Input Validation",
                description="Validate all input data",
                category=PrincipleCategory.SECURITY,
                severity=SeverityLevel.CRITICAL,
                examples=[
                    "Sanitize user input",
                    "Use parameterized queries",
                    "Validate file uploads"
                ],
                violations=[
                    "SQL injection vulnerabilities",
                    "Cross-site scripting (XSS)",
                    "Path traversal attacks"
                ],
                code_patterns=[
                    r"execute\s*\(\s*['\"].*\+.*['\"]",  # SQL injection
                    r"innerHTML\s*=.*\+",  # XSS vulnerability
                    r"eval\s*\(",  # Code injection
                ]
            ),
            Principle(
                name="Authentication & Authorization",
                description="Implement proper authentication and authorization",
                category=PrincipleCategory.SECURITY,
                severity=SeverityLevel.CRITICAL,
                examples=[
                    "Multi-factor authentication",
                    "Role-based access control",
                    "Secure session management"
                ],
                violations=[
                    "Weak password policies",
                    "Missing authorization checks",
                    "Insecure session handling"
                ]
            ),
            Principle(
                name="Data Protection",
                description="Protect sensitive data at rest and in transit",
                category=PrincipleCategory.SECURITY,
                severity=SeverityLevel.CRITICAL,
                examples=[
                    "Encrypt sensitive data",
                    "Use HTTPS for all communications",
                    "Secure key management"
                ],
                violations=[
                    "Hardcoded passwords",
                    "Unencrypted sensitive data",
                    "Weak encryption algorithms"
                ],
                code_patterns=[
                    r"password\s*=\s*['\"][^'\"]+['\"]",  # Hardcoded passwords
                    r"api_key\s*=\s*['\"][^'\"]+['\"]",  # Hardcoded API keys
                ]
            ),
            Principle(
                name="Error Handling",
                description="Handle errors securely without information disclosure",
                category=PrincipleCategory.SECURITY,
                severity=SeverityLevel.HIGH,
                examples=[
                    "Generic error messages",
                    "Proper logging without sensitive data",
                    "Fail securely"
                ]
            )
        ]

    def get_metrics(self) -> List[QualityMetric]:
        return [
            QualityMetric(
                name="security_vulnerabilities",
                description="Number of identified security vulnerabilities",
                measurement_type="numeric",
                threshold_good=0,
                threshold_excellent=0,
                higher_is_better=False
            )
        ]


class PerformancePrinciples(BasePrincipleSet):
    """Performance benchmarks and optimization principles."""

    def get_principles(self) -> List[Principle]:
        return [
            Principle(
                name="Premature Optimization",
                description="Avoid premature optimization; measure first",
                category=PrincipleCategory.PERFORMANCE,
                severity=SeverityLevel.MEDIUM,
                examples=[
                    "Profile before optimizing",
                    "Focus on algorithmic improvements",
                    "Optimize bottlenecks only"
                ]
            ),
            Principle(
                name="Time Complexity",
                description="Consider algorithmic complexity",
                category=PrincipleCategory.PERFORMANCE,
                severity=SeverityLevel.HIGH,
                examples=[
                    "Use appropriate data structures",
                    "Avoid nested loops when possible",
                    "Consider caching for expensive operations"
                ],
                violations=[
                    "O(n²) algorithms when O(n log n) available",
                    "Unnecessary nested iterations",
                    "Missing caching for repeated calculations"
                ]
            ),
            Principle(
                name="Memory Efficiency",
                description="Use memory efficiently",
                category=PrincipleCategory.PERFORMANCE,
                severity=SeverityLevel.MEDIUM,
                examples=[
                    "Avoid memory leaks",
                    "Use appropriate data structures",
                    "Stream large datasets"
                ]
            )
        ]

    def get_metrics(self) -> List[QualityMetric]:
        return [
            QualityMetric(
                name="response_time",
                description="Average response time in milliseconds",
                measurement_type="numeric",
                threshold_good=500,
                threshold_excellent=100,
                higher_is_better=False
            ),
            QualityMetric(
                name="memory_usage",
                description="Memory usage in MB",
                measurement_type="numeric",
                threshold_good=100,
                threshold_excellent=50,
                higher_is_better=False
            )
        ]


class DocumentationPrinciples(BasePrincipleSet):
    """Documentation standards and conventions."""

    def get_principles(self) -> List[Principle]:
        return [
            Principle(
                name="Code Documentation",
                description="Document code purpose and complex logic",
                category=PrincipleCategory.DOCUMENTATION,
                severity=SeverityLevel.LOW,
                examples=[
                    "Docstrings for public methods",
                    "Comments for complex algorithms",
                    "API documentation"
                ],
                violations=[
                    "Missing docstrings",
                    "Outdated comments",
                    "Obvious comments"
                ]
            ),
            Principle(
                name="README Documentation",
                description="Maintain comprehensive README files",
                category=PrincipleCategory.DOCUMENTATION,
                severity=SeverityLevel.MEDIUM,
                examples=[
                    "Installation instructions",
                    "Usage examples",
                    "API reference"
                ]
            )
        ]

    def get_metrics(self) -> List[QualityMetric]:
        return [
            QualityMetric(
                name="documentation_coverage",
                description="Percentage of public APIs documented",
                measurement_type="percentage",
                threshold_good=70.0,
                threshold_excellent=90.0,
                higher_is_better=True
            )
        ]


class VersionControlPrinciples(BasePrincipleSet):
    """Version control conventions and best practices."""

    def get_principles(self) -> List[Principle]:
        return [
            Principle(
                name="Atomic Commits",
                description="Make small, focused commits",
                category=PrincipleCategory.VERSION_CONTROL,
                severity=SeverityLevel.LOW,
                examples=[
                    "One logical change per commit",
                    "Descriptive commit messages",
                    "Separate concerns in different commits"
                ]
            ),
            Principle(
                name="Branching Strategy",
                description="Use consistent branching strategy",
                category=PrincipleCategory.VERSION_CONTROL,
                severity=SeverityLevel.MEDIUM,
                examples=[
                    "Feature branches for new features",
                    "GitFlow or GitHub Flow",
                    "Protected main branch"
                ]
            ),
            Principle(
                name="Commit Message Format",
                description="Use conventional commit message format",
                category=PrincipleCategory.VERSION_CONTROL,
                severity=SeverityLevel.LOW,
                examples=[
                    "feat: add user authentication",
                    "fix: resolve memory leak in parser",
                    "docs: update API documentation"
                ]
            )
        ]

    def get_metrics(self) -> List[QualityMetric]:
        return []


class CodeReviewPrinciples(BasePrincipleSet):
    """Code review criteria and standards."""

    def get_principles(self) -> List[Principle]:
        return [
            Principle(
                name="Review Checklist",
                description="Use comprehensive review checklist",
                category=PrincipleCategory.CODE_REVIEW,
                severity=SeverityLevel.MEDIUM,
                examples=[
                    "Check for security vulnerabilities",
                    "Verify test coverage",
                    "Review performance implications"
                ]
            ),
            Principle(
                name="Constructive Feedback",
                description="Provide constructive, actionable feedback",
                category=PrincipleCategory.CODE_REVIEW,
                severity=SeverityLevel.LOW,
                examples=[
                    "Suggest alternatives",
                    "Explain reasoning",
                    "Recognize good practices"
                ]
            )
        ]

    def get_metrics(self) -> List[QualityMetric]:
        return []


class RefactoringPrinciples(BasePrincipleSet):
    """Refactoring indicators and guidelines."""

    def get_principles(self) -> List[Principle]:
        return [
            Principle(
                name="Code Smells",
                description="Identify and address code smells",
                category=PrincipleCategory.REFACTORING,
                severity=SeverityLevel.MEDIUM,
                examples=[
                    "Long methods",
                    "Duplicate code",
                    "Large classes",
                    "Feature envy"
                ],
                violations=[
                    "Methods longer than 20 lines",
                    "Classes with too many responsibilities",
                    "Deep inheritance hierarchies"
                ]
            ),
            Principle(
                name="Refactoring Safety",
                description="Refactor safely with tests",
                category=PrincipleCategory.REFACTORING,
                severity=SeverityLevel.HIGH,
                examples=[
                    "Ensure tests pass before refactoring",
                    "Small, incremental changes",
                    "Use automated refactoring tools"
                ]
            )
        ]

    def get_metrics(self) -> List[QualityMetric]:
        return [
            QualityMetric(
                name="technical_debt_ratio",
                description="Estimated technical debt as percentage of development time",
                measurement_type="percentage",
                threshold_good=10.0,
                threshold_excellent=5.0,
                higher_is_better=False
            )
        ]


class DevOpsPrinciples(BasePrincipleSet):
    """DevOps maturity model and practices."""

    def get_principles(self) -> List[Principle]:
        return [
            Principle(
                name="Continuous Integration",
                description="Implement continuous integration practices",
                category=PrincipleCategory.DEVOPS,
                severity=SeverityLevel.HIGH,
                examples=[
                    "Automated builds on every commit",
                    "Automated testing pipeline",
                    "Fast feedback loops"
                ]
            ),
            Principle(
                name="Infrastructure as Code",
                description="Manage infrastructure through code",
                category=PrincipleCategory.DEVOPS,
                severity=SeverityLevel.MEDIUM,
                examples=[
                    "Version-controlled infrastructure",
                    "Automated deployments",
                    "Environment consistency"
                ]
            ),
            Principle(
                name="Monitoring & Observability",
                description="Implement comprehensive monitoring",
                category=PrincipleCategory.DEVOPS,
                severity=SeverityLevel.HIGH,
                examples=[
                    "Application metrics",
                    "Log aggregation",
                    "Error tracking",
                    "Performance monitoring"
                ]
            )
        ]

    def get_metrics(self) -> List[QualityMetric]:
        return [
            QualityMetric(
                name="deployment_frequency",
                description="Number of deployments per week",
                measurement_type="numeric",
                threshold_good=1,
                threshold_excellent=5,
                higher_is_better=True
            ),
            QualityMetric(
                name="lead_time",
                description="Lead time from commit to production (hours)",
                measurement_type="numeric",
                threshold_good=24,
                threshold_excellent=4,
                higher_is_better=False
            )
        ]


class SoftwarePrinciples:
    """Main class that aggregates all software development principles."""

    def __init__(self):
        self.principle_sets = {
            PrincipleCategory.SOLID: SOLIDPrinciples(),
            PrincipleCategory.CLEAN_CODE: CleanCodePrinciples(),
            PrincipleCategory.TESTING: TestingPrinciples(),
            PrincipleCategory.SECURITY: SecurityPrinciples(),
            PrincipleCategory.PERFORMANCE: PerformancePrinciples(),
            PrincipleCategory.DOCUMENTATION: DocumentationPrinciples(),
            PrincipleCategory.VERSION_CONTROL: VersionControlPrinciples(),
            PrincipleCategory.CODE_REVIEW: CodeReviewPrinciples(),
            PrincipleCategory.REFACTORING: RefactoringPrinciples(),
            PrincipleCategory.DEVOPS: DevOpsPrinciples()
        }

    def get_all_principles(self) -> List[Principle]:
        """Get all principles from all categories."""
        principles = []
        for principle_set in self.principle_sets.values():
            principles.extend(principle_set.get_principles())
        return principles

    def get_principles_by_category(self, category: PrincipleCategory) -> List[Principle]:
        """Get principles for a specific category."""
        if category in self.principle_sets:
            return self.principle_sets[category].get_principles()
        return []

    def get_all_metrics(self) -> List[QualityMetric]:
        """Get all quality metrics from all categories."""
        metrics = []
        for principle_set in self.principle_sets.values():
            metrics.extend(principle_set.get_metrics())
        return metrics

    def get_metrics_by_category(self, category: PrincipleCategory) -> List[QualityMetric]:
        """Get metrics for a specific category."""
        if category in self.principle_sets:
            return self.principle_sets[category].get_metrics()
        return []

    def find_principle(self, name: str) -> Optional[Principle]:
        """Find a principle by name."""
        for principle in self.get_all_principles():
            if principle.name.lower() == name.lower():
                return principle
        return None

    def get_principles_by_severity(self, severity: SeverityLevel) -> List[Principle]:
        """Get all principles with a specific severity level."""
        return [p for p in self.get_all_principles() if p.severity == severity]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "categories": [cat.value for cat in PrincipleCategory],
            "principles": [
                {
                    "name": p.name,
                    "description": p.description,
                    "category": p.category.value,
                    "severity": p.severity.value,
                    "examples": p.examples,
                    "violations": p.violations,
                    "best_practices": p.best_practices,
                    "code_patterns": p.code_patterns,
                    "anti_patterns": p.anti_patterns,
                    "metrics": p.metrics
                }
                for p in self.get_all_principles()
            ],
            "metrics": [
                {
                    "name": m.name,
                    "description": m.description,
                    "measurement_type": m.measurement_type,
                    "threshold_good": m.threshold_good,
                    "threshold_excellent": m.threshold_excellent,
                    "higher_is_better": m.higher_is_better
                }
                for m in self.get_all_metrics()
            ]
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


# Common code quality thresholds and constants
QUALITY_THRESHOLDS = {
    # Code complexity
    "cyclomatic_complexity_max": 10,
    "function_length_max": 20,
    "class_length_max": 200,
    "parameter_count_max": 3,
    "nesting_depth_max": 3,

    # Test coverage
    "line_coverage_min": 80,
    "branch_coverage_min": 75,
    "mutation_score_min": 70,

    # Performance
    "response_time_max_ms": 500,
    "memory_usage_max_mb": 100,
    "cpu_usage_max_percent": 80,

    # Documentation
    "comment_density_min": 10,  # percentage
    "api_documentation_min": 90,  # percentage

    # Security
    "security_vulnerabilities_max": 0,
    "outdated_dependencies_max": 5,

    # Maintainability
    "duplicate_code_max_percent": 5,
    "technical_debt_ratio_max": 10,  # percentage
    "code_churn_max": 30,  # percentage of files changed per week
}

# Anti-patterns to detect
ANTI_PATTERNS = {
    "god_class": "Classes with too many responsibilities",
    "spaghetti_code": "Unstructured code with complex control flow",
    "copy_paste_programming": "Duplicated code blocks",
    "magic_numbers": "Hardcoded numbers without explanation",
    "dead_code": "Unreachable or unused code",
    "feature_envy": "Classes that use methods of other classes excessively",
    "shotgun_surgery": "Changes requiring modifications to many classes",
    "divergent_change": "Classes that change for multiple reasons"
}


if __name__ == "__main__":
    # Example usage
    principles = SoftwarePrinciples()

    print("=== All Software Development Principles ===")
    for category in PrincipleCategory:
        category_principles = principles.get_principles_by_category(category)
        if category_principles:
            print(f"\n{category.value.upper()}:")
            for principle in category_principles:
                print(f"  • {principle.name}: {principle.description}")

    print(f"\n=== Quality Metrics ===")
    for metric in principles.get_all_metrics():
        print(f"  • {metric.name}: {metric.description}")

    print(f"\n=== Critical Principles ===")
    critical_principles = principles.get_principles_by_severity(SeverityLevel.CRITICAL)
    for principle in critical_principles:
        print(f"  • {principle.name} ({principle.category.value})")
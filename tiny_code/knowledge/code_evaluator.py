"""
Code Evaluator for TinyCode

This module implements comprehensive code evaluation capabilities based on
software development principles, quality metrics, and best practices.

The CodeEvaluator analyzes code against established principles and provides
detailed scoring, recommendations, and improvement suggestions.
"""

import ast
import re
import os
import json
import hashlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Union, Tuple, Set
from pathlib import Path
import logging

from .software_principles import (
    SoftwarePrinciples,
    PrincipleCategory,
    SeverityLevel,
    Principle,
    QualityMetric,
    QUALITY_THRESHOLDS,
    ANTI_PATTERNS
)


class QualityDimension(Enum):
    """Quality dimensions for code evaluation."""
    CORRECTNESS = "correctness"          # Does it work as intended?
    RELIABILITY = "reliability"          # Is it robust and error-free?
    EFFICIENCY = "efficiency"           # Performance and resource usage
    MAINTAINABILITY = "maintainability" # Ease of modification
    READABILITY = "readability"         # Code clarity and documentation
    TESTABILITY = "testability"         # Ease of testing
    SECURITY = "security"               # Security vulnerabilities
    MODULARITY = "modularity"           # Separation of concerns
    REUSABILITY = "reusability"         # Code reuse potential
    SCALABILITY = "scalability"         # Ability to handle growth


class RecommendationType(Enum):
    """Types of recommendations."""
    CRITICAL_FIX = "critical_fix"       # Must fix immediately
    IMPROVEMENT = "improvement"         # Should fix soon
    SUGGESTION = "suggestion"           # Nice to have
    BEST_PRACTICE = "best_practice"     # Follow best practices
    REFACTOR = "refactor"              # Consider refactoring
    SECURITY = "security"              # Security concern
    PERFORMANCE = "performance"        # Performance optimization
    DOCUMENTATION = "documentation"    # Documentation improvement


@dataclass
class CodeMetrics:
    """Code metrics extracted from analysis."""
    lines_of_code: int = 0
    lines_of_comments: int = 0
    cyclomatic_complexity: int = 0
    function_count: int = 0
    class_count: int = 0
    average_function_length: float = 0.0
    max_function_length: int = 0
    max_nesting_depth: int = 0
    duplicate_code_blocks: int = 0
    magic_numbers: List[str] = field(default_factory=list)
    long_parameter_lists: List[str] = field(default_factory=list)
    god_classes: List[str] = field(default_factory=list)
    security_issues: List[str] = field(default_factory=list)
    performance_issues: List[str] = field(default_factory=list)
    code_smells: List[str] = field(default_factory=list)


@dataclass
class Recommendation:
    """A specific recommendation for code improvement."""
    type: RecommendationType
    severity: SeverityLevel
    principle: str
    category: PrincipleCategory
    message: str
    location: Optional[str] = None  # file:line or function name
    code_snippet: Optional[str] = None
    suggested_fix: Optional[str] = None
    rationale: str = ""
    effort_estimate: str = "medium"  # low, medium, high
    impact: str = "medium"  # low, medium, high


@dataclass
class CodeQualityScore:
    """Quality score for a specific dimension."""
    dimension: QualityDimension
    score: float  # 0.0 to 10.0
    weight: float = 1.0
    details: str = ""
    contributing_factors: List[str] = field(default_factory=list)


@dataclass
class EvaluationResult:
    """Complete evaluation result for code analysis."""
    file_path: str
    overall_score: float  # 0.0 to 10.0
    quality_scores: List[CodeQualityScore] = field(default_factory=list)
    recommendations: List[Recommendation] = field(default_factory=list)
    metrics: Optional[CodeMetrics] = None
    principles_evaluated: List[str] = field(default_factory=list)
    timestamp: str = ""
    analysis_duration: float = 0.0


class CodeEvaluator:
    """Main code evaluator class that analyzes code against software principles."""

    def __init__(self, principles_data_path: Optional[str] = None):
        """Initialize the code evaluator.

        Args:
            principles_data_path: Path to persistent principles data
        """
        self.principles = SoftwarePrinciples()
        self.logger = logging.getLogger(__name__)

        # Load or initialize persistent data
        self.data_path = principles_data_path or os.path.join("data", "knowledge", "principles.json")
        self.learned_patterns = self._load_learned_patterns()
        self.user_preferences = self._load_user_preferences()
        self.project_conventions = self._load_project_conventions()

        # Quality dimension weights (can be customized per project)
        self.dimension_weights = {
            QualityDimension.CORRECTNESS: 2.0,
            QualityDimension.SECURITY: 2.0,
            QualityDimension.RELIABILITY: 1.8,
            QualityDimension.MAINTAINABILITY: 1.5,
            QualityDimension.READABILITY: 1.3,
            QualityDimension.TESTABILITY: 1.2,
            QualityDimension.EFFICIENCY: 1.0,
            QualityDimension.MODULARITY: 1.0,
            QualityDimension.REUSABILITY: 0.8,
            QualityDimension.SCALABILITY: 0.8
        }

    def evaluate_code(self,
                     code_content: str,
                     file_path: str = "",
                     language: str = "python",
                     focus_areas: Optional[List[PrincipleCategory]] = None) -> EvaluationResult:
        """Evaluate code against software development principles.

        Args:
            code_content: The code to evaluate
            file_path: Path to the code file
            language: Programming language
            focus_areas: Specific principle categories to focus on

        Returns:
            EvaluationResult with scores and recommendations
        """
        start_time = __import__('time').time()

        result = EvaluationResult(
            file_path=file_path,
            overall_score=0.0,
            timestamp=__import__('datetime').datetime.now().isoformat()
        )

        try:
            # Extract code metrics
            result.metrics = self._extract_metrics(code_content, language)

            # Evaluate each quality dimension
            quality_scores = []
            for dimension in QualityDimension:
                score = self._evaluate_dimension(dimension, code_content, result.metrics, language)
                quality_scores.append(score)

            result.quality_scores = quality_scores

            # Calculate overall score
            result.overall_score = self._calculate_overall_score(quality_scores)

            # Generate recommendations
            result.recommendations = self._generate_recommendations(
                code_content, result.metrics, quality_scores, focus_areas
            )

            # Track evaluated principles
            result.principles_evaluated = self._get_evaluated_principles(focus_areas)

        except Exception as e:
            self.logger.error(f"Error evaluating code: {e}")
            result.overall_score = 0.0

        result.analysis_duration = __import__('time').time() - start_time
        return result

    def _extract_metrics(self, code_content: str, language: str) -> CodeMetrics:
        """Extract code metrics from the content."""
        metrics = CodeMetrics()

        lines = code_content.split('\n')
        metrics.lines_of_code = len([line for line in lines if line.strip()])
        metrics.lines_of_comments = len([line for line in lines if line.strip().startswith('#')])

        if language.lower() == "python":
            metrics = self._extract_python_metrics(code_content, metrics)
        else:
            # Basic language-agnostic metrics
            metrics = self._extract_generic_metrics(code_content, metrics)

        return metrics

    def _extract_python_metrics(self, code_content: str, metrics: CodeMetrics) -> CodeMetrics:
        """Extract Python-specific metrics using AST."""
        try:
            tree = ast.parse(code_content)

            # Count functions and classes
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    metrics.function_count += 1
                    func_length = self._get_function_length(node)
                    metrics.max_function_length = max(metrics.max_function_length, func_length)

                    # Check for long parameter lists
                    if len(node.args.args) > QUALITY_THRESHOLDS["parameter_count_max"]:
                        metrics.long_parameter_lists.append(node.name)

                elif isinstance(node, ast.ClassDef):
                    metrics.class_count += 1
                    class_length = self._get_class_length(node)
                    if class_length > QUALITY_THRESHOLDS["class_length_max"]:
                        metrics.god_classes.append(node.name)

            # Calculate average function length
            if metrics.function_count > 0:
                total_length = sum(self._get_function_length(node)
                                 for node in ast.walk(tree)
                                 if isinstance(node, ast.FunctionDef))
                metrics.average_function_length = total_length / metrics.function_count

            # Calculate cyclomatic complexity
            metrics.cyclomatic_complexity = self._calculate_cyclomatic_complexity(tree)

            # Detect magic numbers
            metrics.magic_numbers = self._find_magic_numbers(tree)

            # Detect security issues
            metrics.security_issues = self._detect_security_issues(code_content)

            # Detect performance issues
            metrics.performance_issues = self._detect_performance_issues(code_content)

            # Detect code smells
            metrics.code_smells = self._detect_code_smells(code_content, tree)

        except SyntaxError as e:
            self.logger.warning(f"Syntax error in Python code: {e}")

        return metrics

    def _extract_generic_metrics(self, code_content: str, metrics: CodeMetrics) -> CodeMetrics:
        """Extract language-agnostic metrics using regex patterns."""

        # Function detection (basic patterns)
        function_patterns = [
            r'def\s+\w+\s*\(',      # Python
            r'function\s+\w+\s*\(', # JavaScript
            r'\w+\s+\w+\s*\([^)]*\)\s*\{', # Java/C/C++
        ]

        for pattern in function_patterns:
            matches = re.findall(pattern, code_content)
            metrics.function_count += len(matches)

        # Class detection
        class_patterns = [
            r'class\s+\w+',        # Python/Java
            r'class\s+\w+\s*\{',   # JavaScript/C++
        ]

        for pattern in class_patterns:
            matches = re.findall(pattern, code_content)
            metrics.class_count += len(matches)

        # Security issues (basic patterns)
        metrics.security_issues = self._detect_security_issues(code_content)

        return metrics

    def _calculate_cyclomatic_complexity(self, tree: ast.AST) -> int:
        """Calculate McCabe cyclomatic complexity."""
        complexity = 1  # Base complexity

        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
            elif isinstance(node, (ast.Try, ast.ExceptHandler)):
                complexity += 1

        return complexity

    def _get_function_length(self, func_node: ast.FunctionDef) -> int:
        """Get the length of a function in lines."""
        if hasattr(func_node, 'end_lineno') and hasattr(func_node, 'lineno'):
            return func_node.end_lineno - func_node.lineno + 1
        return 1

    def _get_class_length(self, class_node: ast.ClassDef) -> int:
        """Get the length of a class in lines."""
        if hasattr(class_node, 'end_lineno') and hasattr(class_node, 'lineno'):
            return class_node.end_lineno - class_node.lineno + 1
        return 1

    def _find_magic_numbers(self, tree: ast.AST) -> List[str]:
        """Find magic numbers in the code."""
        magic_numbers = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                # Exclude common non-magic numbers
                if node.value not in [0, 1, -1, 2, 10, 100, 1000]:
                    magic_numbers.append(str(node.value))

        return list(set(magic_numbers))

    def _detect_security_issues(self, code_content: str) -> List[str]:
        """Detect potential security issues."""
        issues = []

        # Get security principles and their patterns
        security_principles = self.principles.get_principles_by_category(PrincipleCategory.SECURITY)

        for principle in security_principles:
            for pattern in principle.code_patterns:
                if re.search(pattern, code_content, re.IGNORECASE):
                    issues.append(f"{principle.name}: {pattern}")

        return issues

    def _detect_performance_issues(self, code_content: str) -> List[str]:
        """Detect potential performance issues."""
        issues = []

        # Nested loops
        if re.search(r'for.*:\s*.*for.*:', code_content, re.DOTALL):
            issues.append("Nested loops detected - consider algorithmic optimization")

        # String concatenation in loops
        if re.search(r'for.*:.*\+=.*str', code_content, re.DOTALL):
            issues.append("String concatenation in loop - consider using join()")

        # Global variable access in loops
        if re.search(r'for.*:.*global', code_content, re.DOTALL):
            issues.append("Global variable access in loop")

        return issues

    def _detect_code_smells(self, code_content: str, tree: ast.AST) -> List[str]:
        """Detect various code smells."""
        smells = []

        # Long method smell
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_length = self._get_function_length(node)
                if func_length > QUALITY_THRESHOLDS["function_length_max"]:
                    smells.append(f"Long method: {node.name} ({func_length} lines)")

        # Duplicate code (simple string matching)
        lines = code_content.split('\n')
        line_counts = {}
        for line in lines:
            stripped = line.strip()
            if len(stripped) > 10:  # Ignore short lines
                line_counts[stripped] = line_counts.get(stripped, 0) + 1

        duplicates = [line for line, count in line_counts.items() if count > 1]
        if duplicates:
            smells.append(f"Duplicate code detected: {len(duplicates)} repeated lines")

        return smells

    def _evaluate_dimension(self,
                          dimension: QualityDimension,
                          code_content: str,
                          metrics: CodeMetrics,
                          language: str) -> CodeQualityScore:
        """Evaluate a specific quality dimension."""

        score = 10.0  # Start with perfect score
        details = []
        factors = []

        if dimension == QualityDimension.CORRECTNESS:
            # Basic syntax check
            if language.lower() == "python":
                try:
                    ast.parse(code_content)
                    factors.append("Valid syntax")
                except SyntaxError:
                    score -= 5.0
                    factors.append("Syntax errors detected")

            # Check for obvious logic errors
            if "TODO" in code_content or "FIXME" in code_content:
                score -= 1.0
                factors.append("TODO/FIXME comments found")

        elif dimension == QualityDimension.RELIABILITY:
            # Error handling
            if language.lower() == "python":
                if "try:" not in code_content and "except:" in code_content:
                    score -= 2.0
                    factors.append("Missing proper error handling")
                elif "except:" in code_content:
                    factors.append("Error handling present")

            # Null checks
            if "if" in code_content and "None" in code_content:
                factors.append("Null checks present")

        elif dimension == QualityDimension.EFFICIENCY:
            score -= len(metrics.performance_issues) * 1.0
            if metrics.performance_issues:
                factors.extend(metrics.performance_issues)

            # Complexity penalty
            if metrics.cyclomatic_complexity > QUALITY_THRESHOLDS["cyclomatic_complexity_max"]:
                penalty = (metrics.cyclomatic_complexity - QUALITY_THRESHOLDS["cyclomatic_complexity_max"]) * 0.5
                score -= min(penalty, 3.0)
                factors.append(f"High cyclomatic complexity: {metrics.cyclomatic_complexity}")

        elif dimension == QualityDimension.MAINTAINABILITY:
            # Function length
            if metrics.max_function_length > QUALITY_THRESHOLDS["function_length_max"]:
                score -= 2.0
                factors.append(f"Long functions detected (max: {metrics.max_function_length} lines)")

            # Magic numbers
            if metrics.magic_numbers:
                score -= min(len(metrics.magic_numbers) * 0.5, 2.0)
                factors.append(f"Magic numbers: {', '.join(metrics.magic_numbers[:3])}")

            # Code smells
            score -= min(len(metrics.code_smells) * 0.5, 3.0)
            factors.extend(metrics.code_smells[:3])

        elif dimension == QualityDimension.READABILITY:
            # Comment ratio
            if metrics.lines_of_code > 0:
                comment_ratio = (metrics.lines_of_comments / metrics.lines_of_code) * 100
                if comment_ratio < QUALITY_THRESHOLDS["comment_density_min"]:
                    score -= 2.0
                    factors.append(f"Low comment density: {comment_ratio:.1f}%")
                else:
                    factors.append(f"Good comment density: {comment_ratio:.1f}%")

            # Naming conventions (basic check)
            if re.search(r'\b[a-z]\b', code_content):  # Single letter variables
                score -= 1.0
                factors.append("Single letter variable names found")

        elif dimension == QualityDimension.TESTABILITY:
            # Function size affects testability
            if metrics.average_function_length > QUALITY_THRESHOLDS["function_length_max"]:
                score -= 1.5
                factors.append("Large functions reduce testability")

            # Parameter count affects testability
            if metrics.long_parameter_lists:
                score -= 1.0
                factors.append("Functions with many parameters are hard to test")

        elif dimension == QualityDimension.SECURITY:
            score -= len(metrics.security_issues) * 2.0
            if metrics.security_issues:
                factors.extend(metrics.security_issues)
            else:
                factors.append("No obvious security issues detected")

        elif dimension == QualityDimension.MODULARITY:
            # God classes
            if metrics.god_classes:
                score -= len(metrics.god_classes) * 1.5
                factors.extend([f"Large class: {cls}" for cls in metrics.god_classes])

            # Function count per file
            if metrics.function_count > 20:
                score -= 1.0
                factors.append("High function count in single file")

        elif dimension == QualityDimension.REUSABILITY:
            # Hard to measure statically, basic heuristics
            if metrics.function_count < 3 and metrics.lines_of_code > 50:
                score -= 1.0
                factors.append("Monolithic code structure")

        elif dimension == QualityDimension.SCALABILITY:
            # Basic checks for scalability issues
            if "global" in code_content.lower():
                score -= 1.0
                factors.append("Global state usage")

        # Ensure score is within bounds
        score = max(0.0, min(10.0, score))

        return CodeQualityScore(
            dimension=dimension,
            score=score,
            weight=self.dimension_weights.get(dimension, 1.0),
            details="; ".join(factors) if factors else "No issues detected",
            contributing_factors=factors
        )

    def _calculate_overall_score(self, quality_scores: List[CodeQualityScore]) -> float:
        """Calculate weighted overall score."""
        if not quality_scores:
            return 0.0

        total_weighted_score = sum(score.score * score.weight for score in quality_scores)
        total_weight = sum(score.weight for score in quality_scores)

        return total_weighted_score / total_weight if total_weight > 0 else 0.0

    def _generate_recommendations(self,
                                code_content: str,
                                metrics: CodeMetrics,
                                quality_scores: List[CodeQualityScore],
                                focus_areas: Optional[List[PrincipleCategory]] = None) -> List[Recommendation]:
        """Generate specific recommendations based on analysis."""
        recommendations = []

        # Security recommendations (highest priority)
        for issue in metrics.security_issues:
            recommendations.append(Recommendation(
                type=RecommendationType.SECURITY,
                severity=SeverityLevel.CRITICAL,
                principle="Security Best Practices",
                category=PrincipleCategory.SECURITY,
                message=f"Security issue detected: {issue}",
                rationale="Security vulnerabilities can lead to data breaches and system compromise",
                effort_estimate="high",
                impact="high"
            ))

        # Performance recommendations
        for issue in metrics.performance_issues:
            recommendations.append(Recommendation(
                type=RecommendationType.PERFORMANCE,
                severity=SeverityLevel.MEDIUM,
                principle="Performance Optimization",
                category=PrincipleCategory.PERFORMANCE,
                message=f"Performance issue: {issue}",
                rationale="Performance issues can impact user experience and system scalability",
                effort_estimate="medium",
                impact="medium"
            ))

        # Code quality recommendations
        if metrics.max_function_length > QUALITY_THRESHOLDS["function_length_max"]:
            recommendations.append(Recommendation(
                type=RecommendationType.REFACTOR,
                severity=SeverityLevel.MEDIUM,
                principle="Functions Should Be Small",
                category=PrincipleCategory.CLEAN_CODE,
                message=f"Functions are too long (max: {metrics.max_function_length} lines)",
                suggested_fix="Break down large functions into smaller, focused functions",
                rationale="Smaller functions are easier to understand, test, and maintain",
                effort_estimate="medium",
                impact="high"
            ))

        # Complexity recommendations
        if metrics.cyclomatic_complexity > QUALITY_THRESHOLDS["cyclomatic_complexity_max"]:
            recommendations.append(Recommendation(
                type=RecommendationType.REFACTOR,
                severity=SeverityLevel.MEDIUM,
                principle="Reduce Complexity",
                category=PrincipleCategory.CLEAN_CODE,
                message=f"High cyclomatic complexity: {metrics.cyclomatic_complexity}",
                suggested_fix="Simplify conditional logic and extract complex conditions into methods",
                rationale="Lower complexity improves code readability and reduces bug likelihood",
                effort_estimate="medium",
                impact="high"
            ))

        # Magic numbers
        if metrics.magic_numbers:
            recommendations.append(Recommendation(
                type=RecommendationType.IMPROVEMENT,
                severity=SeverityLevel.LOW,
                principle="Meaningful Names",
                category=PrincipleCategory.CLEAN_CODE,
                message=f"Magic numbers found: {', '.join(metrics.magic_numbers[:3])}",
                suggested_fix="Replace magic numbers with named constants",
                rationale="Named constants improve code readability and maintainability",
                effort_estimate="low",
                impact="medium"
            ))

        # God classes
        for god_class in metrics.god_classes:
            recommendations.append(Recommendation(
                type=RecommendationType.REFACTOR,
                severity=SeverityLevel.HIGH,
                principle="Single Responsibility Principle",
                category=PrincipleCategory.SOLID,
                message=f"Large class detected: {god_class}",
                suggested_fix="Break down the class into smaller, focused classes",
                rationale="Large classes violate SRP and are difficult to maintain and test",
                effort_estimate="high",
                impact="high"
            ))

        # Documentation recommendations
        if metrics.lines_of_code > 0:
            comment_ratio = (metrics.lines_of_comments / metrics.lines_of_code) * 100
            if comment_ratio < QUALITY_THRESHOLDS["comment_density_min"]:
                recommendations.append(Recommendation(
                    type=RecommendationType.DOCUMENTATION,
                    severity=SeverityLevel.LOW,
                    principle="Code Documentation",
                    category=PrincipleCategory.DOCUMENTATION,
                    message=f"Low comment density: {comment_ratio:.1f}%",
                    suggested_fix="Add docstrings and comments for complex logic",
                    rationale="Good documentation improves code maintainability",
                    effort_estimate="low",
                    impact="medium"
                ))

        # Sort recommendations by severity and impact
        severity_order = {
            SeverityLevel.CRITICAL: 0,
            SeverityLevel.HIGH: 1,
            SeverityLevel.MEDIUM: 2,
            SeverityLevel.LOW: 3
        }

        recommendations.sort(key=lambda r: (severity_order[r.severity], r.impact != "high"))

        return recommendations

    def _get_evaluated_principles(self, focus_areas: Optional[List[PrincipleCategory]]) -> List[str]:
        """Get list of principle names that were evaluated."""
        if focus_areas:
            principles = []
            for category in focus_areas:
                principles.extend([p.name for p in self.principles.get_principles_by_category(category)])
            return principles
        else:
            return [p.name for p in self.principles.get_all_principles()]

    def get_principle_summary(self, category: Optional[PrincipleCategory] = None) -> Dict[str, Any]:
        """Get a summary of available principles."""
        if category:
            principles = self.principles.get_principles_by_category(category)
            return {
                "category": category.value,
                "principles": [
                    {
                        "name": p.name,
                        "description": p.description,
                        "severity": p.severity.value,
                        "examples": p.examples[:2]  # First 2 examples
                    }
                    for p in principles
                ]
            }
        else:
            summary = {}
            for cat in PrincipleCategory:
                principles = self.principles.get_principles_by_category(cat)
                summary[cat.value] = {
                    "count": len(principles),
                    "principles": [p.name for p in principles]
                }
            return summary

    def save_evaluation_result(self, result: EvaluationResult) -> bool:
        """Save evaluation result for learning and tracking."""
        try:
            # Create a hash of the code for tracking
            code_hash = hashlib.md5(result.file_path.encode()).hexdigest()

            # Store in learned patterns
            self.learned_patterns[code_hash] = {
                "file_path": result.file_path,
                "overall_score": result.overall_score,
                "timestamp": result.timestamp,
                "recommendations_count": len(result.recommendations),
                "critical_issues": len([r for r in result.recommendations if r.severity == SeverityLevel.CRITICAL])
            }

            self._save_learned_patterns()
            return True

        except Exception as e:
            self.logger.error(f"Failed to save evaluation result: {e}")
            return False

    def _load_learned_patterns(self) -> Dict[str, Any]:
        """Load learned patterns from persistent storage."""
        try:
            if os.path.exists(self.data_path):
                with open(self.data_path, 'r') as f:
                    data = json.load(f)
                    return data.get("learned_patterns", {})
        except Exception as e:
            self.logger.warning(f"Failed to load learned patterns: {e}")
        return {}

    def _load_user_preferences(self) -> Dict[str, Any]:
        """Load user preferences from persistent storage."""
        try:
            if os.path.exists(self.data_path):
                with open(self.data_path, 'r') as f:
                    data = json.load(f)
                    return data.get("user_preferences", {})
        except Exception as e:
            self.logger.warning(f"Failed to load user preferences: {e}")
        return {}

    def _load_project_conventions(self) -> Dict[str, Any]:
        """Load project-specific conventions from persistent storage."""
        try:
            if os.path.exists(self.data_path):
                with open(self.data_path, 'r') as f:
                    data = json.load(f)
                    return data.get("project_conventions", {})
        except Exception as e:
            self.logger.warning(f"Failed to load project conventions: {e}")
        return {}

    def _save_learned_patterns(self) -> bool:
        """Save learned patterns to persistent storage."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.data_path), exist_ok=True)

            data = {
                "learned_patterns": self.learned_patterns,
                "user_preferences": self.user_preferences,
                "project_conventions": self.project_conventions,
                "last_updated": __import__('datetime').datetime.now().isoformat()
            }

            with open(self.data_path, 'w') as f:
                json.dump(data, f, indent=2)

            return True

        except Exception as e:
            self.logger.error(f"Failed to save learned patterns: {e}")
            return False

    def update_user_preferences(self, preferences: Dict[str, Any]) -> bool:
        """Update user preferences for code evaluation."""
        try:
            self.user_preferences.update(preferences)
            return self._save_learned_patterns()
        except Exception as e:
            self.logger.error(f"Failed to update user preferences: {e}")
            return False

    def update_project_conventions(self, conventions: Dict[str, Any]) -> bool:
        """Update project-specific conventions."""
        try:
            self.project_conventions.update(conventions)
            return self._save_learned_patterns()
        except Exception as e:
            self.logger.error(f"Failed to update project conventions: {e}")
            return False

    def get_evaluation_history(self, file_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get evaluation history for a file or all files."""
        if file_path:
            code_hash = hashlib.md5(file_path.encode()).hexdigest()
            pattern = self.learned_patterns.get(code_hash)
            return [pattern] if pattern else []
        else:
            return list(self.learned_patterns.values())


if __name__ == "__main__":
    # Example usage
    evaluator = CodeEvaluator()

    # Example Python code
    sample_code = '''
def calculate_total(items):
    total = 0
    for item in items:
        if item > 0:
            total += item * 1.08  # Magic number for tax
    return total

class DataProcessor:
    def __init__(self):
        self.data = []

    def process_data(self, input_data):
        # This function is too long and does too many things
        if input_data is None:
            return None

        processed = []
        for item in input_data:
            if isinstance(item, str):
                item = item.strip().lower()
                if len(item) > 0:
                    processed.append(item)
            elif isinstance(item, int):
                if item > 0:
                    processed.append(str(item))

        # More processing...
        final_result = []
        for item in processed:
            final_result.append(item + "_processed")

        return final_result
'''

    # Evaluate the code
    result = evaluator.evaluate_code(sample_code, "example.py")

    print("=== Code Evaluation Result ===")
    print(f"Overall Score: {result.overall_score:.1f}/10.0")
    print(f"Analysis Duration: {result.analysis_duration:.3f}s")

    print("\n=== Quality Scores ===")
    for score in result.quality_scores:
        print(f"{score.dimension.value}: {score.score:.1f}/10.0 - {score.details}")

    print(f"\n=== Recommendations ({len(result.recommendations)}) ===")
    for i, rec in enumerate(result.recommendations, 1):
        print(f"{i}. [{rec.severity.value.upper()}] {rec.message}")
        if rec.suggested_fix:
            print(f"   Fix: {rec.suggested_fix}")
        print(f"   Rationale: {rec.rationale}")
        print()

    print("=== Code Metrics ===")
    if result.metrics:
        print(f"Lines of Code: {result.metrics.lines_of_code}")
        print(f"Functions: {result.metrics.function_count}")
        print(f"Classes: {result.metrics.class_count}")
        print(f"Cyclomatic Complexity: {result.metrics.cyclomatic_complexity}")
        print(f"Max Function Length: {result.metrics.max_function_length}")
        if result.metrics.magic_numbers:
            print(f"Magic Numbers: {', '.join(result.metrics.magic_numbers)}")
"""
Smart Assistant Layer for TinyCode

This module provides intelligent, context-aware assistance including proactive suggestions,
pattern recognition, learning from user behavior, and adaptive help systems.
"""

import os
import json
import time
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Set, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import re

from .nlp_interface import Intent
from .mode_manager import OperationMode
from .command_registry import CommandRegistry


class SuggestionType(Enum):
    """Types of suggestions the assistant can make"""
    NEXT_ACTION = "next_action"
    BEST_PRACTICE = "best_practice"
    WORKFLOW_OPTIMIZATION = "workflow_optimization"
    FEATURE_DISCOVERY = "feature_discovery"
    ERROR_PREVENTION = "error_prevention"
    PROJECT_IMPROVEMENT = "project_improvement"
    LEARNING_OPPORTUNITY = "learning_opportunity"


class ContextType(Enum):
    """Types of context the assistant can analyze"""
    FILE_STRUCTURE = "file_structure"
    CODE_PATTERNS = "code_patterns"
    USER_BEHAVIOR = "user_behavior"
    PROJECT_STATE = "project_state"
    ERROR_HISTORY = "error_history"
    SUCCESS_PATTERNS = "success_patterns"


@dataclass
class Suggestion:
    """A smart suggestion from the assistant"""
    id: str
    type: SuggestionType
    title: str
    description: str
    action_command: Optional[str] = None
    confidence: float = 0.0
    priority: int = 1  # 1=high, 2=medium, 3=low
    context_relevance: float = 0.0
    estimated_impact: str = "medium"  # high, medium, low
    learning_level: str = "beginner"  # beginner, intermediate, advanced
    tags: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    related_suggestions: List[str] = field(default_factory=list)


@dataclass
class UserPattern:
    """Patterns detected in user behavior"""
    pattern_type: str
    frequency: int
    last_occurrence: datetime
    success_rate: float
    context_triggers: List[str] = field(default_factory=list)
    associated_commands: List[str] = field(default_factory=list)


@dataclass
class ProjectInsight:
    """Insights about the current project"""
    project_type: Optional[str]
    languages: List[str]
    frameworks: List[str]
    complexity_score: float
    test_coverage_estimate: float
    documentation_score: float
    code_quality_indicators: Dict[str, Any] = field(default_factory=dict)
    improvement_opportunities: List[str] = field(default_factory=list)


class SmartAssistant:
    """Intelligent assistant that provides context-aware help and suggestions"""

    def __init__(self):
        self.command_registry = CommandRegistry()
        self.user_patterns: Dict[str, UserPattern] = {}
        self.suggestion_history: List[Suggestion] = []
        self.project_insights: Optional[ProjectInsight] = None
        self.context_analyzers = self._initialize_context_analyzers()
        self.suggestion_generators = self._initialize_suggestion_generators()
        self.learning_system = UserLearningSystem()
        self.workflow_optimizer = WorkflowOptimizer()

    def analyze_context_and_suggest(self,
                                   current_context: Dict[str, Any],
                                   recent_history: List[Dict[str, Any]],
                                   user_intent: Optional[Intent] = None) -> List[Suggestion]:
        """
        Analyze current context and generate intelligent suggestions

        Args:
            current_context: Current system state (files, mode, etc.)
            recent_history: Recent user actions and commands
            user_intent: Current user intent if known

        Returns:
            List of prioritized suggestions
        """
        # Update project insights
        self._update_project_insights(current_context)

        # Analyze user patterns
        self._update_user_patterns(recent_history)

        # Generate suggestions based on different contexts
        suggestions = []

        # Context-based suggestions
        suggestions.extend(self._suggest_based_on_files(current_context))
        suggestions.extend(self._suggest_based_on_mode(current_context))
        suggestions.extend(self._suggest_based_on_project_type(current_context))
        suggestions.extend(self._suggest_based_on_user_patterns())

        # Intent-based suggestions
        if user_intent:
            suggestions.extend(self._suggest_based_on_intent(user_intent, current_context))

        # Workflow optimization suggestions
        suggestions.extend(self.workflow_optimizer.suggest_optimizations(recent_history))

        # Learning opportunities
        suggestions.extend(self.learning_system.suggest_learning_opportunities(
            current_context, recent_history
        ))

        # Rank and filter suggestions
        prioritized_suggestions = self._rank_suggestions(suggestions, current_context)

        # Update suggestion history
        self.suggestion_history.extend(prioritized_suggestions)
        self._cleanup_old_suggestions()

        return prioritized_suggestions[:10]  # Return top 10 suggestions

    def _initialize_context_analyzers(self) -> Dict[ContextType, callable]:
        """Initialize context analysis functions"""
        return {
            ContextType.FILE_STRUCTURE: self._analyze_file_structure,
            ContextType.CODE_PATTERNS: self._analyze_code_patterns,
            ContextType.USER_BEHAVIOR: self._analyze_user_behavior,
            ContextType.PROJECT_STATE: self._analyze_project_state,
            ContextType.ERROR_HISTORY: self._analyze_error_history,
            ContextType.SUCCESS_PATTERNS: self._analyze_success_patterns
        }

    def _initialize_suggestion_generators(self) -> Dict[SuggestionType, callable]:
        """Initialize suggestion generation functions"""
        return {
            SuggestionType.NEXT_ACTION: self._generate_next_action_suggestions,
            SuggestionType.BEST_PRACTICE: self._generate_best_practice_suggestions,
            SuggestionType.WORKFLOW_OPTIMIZATION: self._generate_workflow_suggestions,
            SuggestionType.FEATURE_DISCOVERY: self._generate_feature_discovery_suggestions,
            SuggestionType.ERROR_PREVENTION: self._generate_error_prevention_suggestions,
            SuggestionType.PROJECT_IMPROVEMENT: self._generate_project_improvement_suggestions
        }

    def _update_project_insights(self, context: Dict[str, Any]):
        """Update insights about the current project"""
        files = context.get('available_files', [])

        # Detect languages and frameworks
        languages = self._detect_languages(files)
        frameworks = self._detect_frameworks(files)
        project_type = self._detect_project_type(files, frameworks)

        # Calculate metrics
        complexity_score = self._estimate_complexity(files)
        test_coverage = self._estimate_test_coverage(files)
        doc_score = self._estimate_documentation_score(files)

        # Identify improvement opportunities
        improvements = self._identify_improvement_opportunities(files, languages)

        self.project_insights = ProjectInsight(
            project_type=project_type,
            languages=languages,
            frameworks=frameworks,
            complexity_score=complexity_score,
            test_coverage_estimate=test_coverage,
            documentation_score=doc_score,
            improvement_opportunities=improvements
        )

    def _detect_languages(self, files: List[str]) -> List[str]:
        """Detect programming languages used in the project"""
        language_extensions = {
            'Python': ['.py', '.pyx', '.pyi'],
            'JavaScript': ['.js', '.jsx', '.mjs'],
            'TypeScript': ['.ts', '.tsx'],
            'Java': ['.java'],
            'C++': ['.cpp', '.cc', '.cxx', '.hpp', '.h'],
            'Go': ['.go'],
            'Rust': ['.rs'],
            'Ruby': ['.rb'],
            'PHP': ['.php'],
            'Swift': ['.swift'],
            'Kotlin': ['.kt'],
            'C#': ['.cs'],
            'SQL': ['.sql']
        }

        detected_languages = []
        for language, extensions in language_extensions.items():
            if any(any(file.endswith(ext) for ext in extensions) for file in files):
                detected_languages.append(language)

        return detected_languages

    def _detect_frameworks(self, files: List[str]) -> List[str]:
        """Detect frameworks and libraries used"""
        framework_indicators = {
            'React': ['package.json', '.jsx', '.tsx'],
            'Vue': ['vue.config.js', '.vue'],
            'Angular': ['angular.json', '.component.ts'],
            'Express': ['package.json'],  # Would need to check content
            'Django': ['manage.py', 'settings.py'],
            'Flask': ['app.py', 'application.py'],
            'FastAPI': ['main.py'],  # Would need to check imports
            'Spring': ['pom.xml', 'build.gradle'],
            'Laravel': ['composer.json', 'artisan'],
            'Rails': ['Gemfile', 'config.ru']
        }

        detected_frameworks = []
        file_names = [os.path.basename(f) for f in files]

        for framework, indicators in framework_indicators.items():
            if any(indicator in file_names or any(f.endswith(indicator) for f in files)
                   for indicator in indicators):
                detected_frameworks.append(framework)

        return detected_frameworks

    def _detect_project_type(self, files: List[str], frameworks: List[str]) -> Optional[str]:
        """Detect the type of project"""
        if 'Django' in frameworks or 'Flask' in frameworks or 'FastAPI' in frameworks:
            return 'Web API'
        elif 'React' in frameworks or 'Vue' in frameworks or 'Angular' in frameworks:
            return 'Frontend Application'
        elif any(f.endswith('.py') for f in files):
            if any('test' in f.lower() for f in files):
                return 'Python Library'
            else:
                return 'Python Script/Application'
        elif any(f.endswith(('.js', '.ts')) for f in files):
            return 'JavaScript/TypeScript Application'
        elif any(f.endswith('.java') for f in files):
            return 'Java Application'
        else:
            return 'Mixed/Other'

    def _estimate_complexity(self, files: List[str]) -> float:
        """Estimate project complexity (0-1 scale)"""
        complexity_factors = {
            'file_count': min(len(files) / 100, 1.0) * 0.3,
            'directory_depth': min(self._calculate_max_depth(files) / 5, 1.0) * 0.2,
            'language_diversity': min(len(self._detect_languages(files)) / 5, 1.0) * 0.3,
            'framework_count': min(len(self._detect_frameworks(files)) / 3, 1.0) * 0.2
        }

        return sum(complexity_factors.values())

    def _calculate_max_depth(self, files: List[str]) -> int:
        """Calculate maximum directory depth"""
        if not files:
            return 0
        return max(len(Path(f).parts) for f in files)

    def _estimate_test_coverage(self, files: List[str]) -> float:
        """Estimate test coverage based on file patterns"""
        code_files = [f for f in files if any(f.endswith(ext)
                     for ext in ['.py', '.js', '.ts', '.java', '.go', '.rs'])]
        test_files = [f for f in files if 'test' in f.lower() or 'spec' in f.lower()]

        if not code_files:
            return 0.0

        return min(len(test_files) / len(code_files), 1.0)

    def _estimate_documentation_score(self, files: List[str]) -> float:
        """Estimate documentation quality score"""
        doc_indicators = ['README', 'CHANGELOG', 'CONTRIBUTING', 'docs/', 'documentation/']
        doc_files = [f for f in files if any(indicator.lower() in f.lower()
                    for indicator in doc_indicators)]

        # Base score for having documentation files
        base_score = min(len(doc_files) / 3, 1.0) * 0.7

        # Bonus for README
        readme_bonus = 0.3 if any('readme' in f.lower() for f in files) else 0

        return base_score + readme_bonus

    def _identify_improvement_opportunities(self, files: List[str], languages: List[str]) -> List[str]:
        """Identify opportunities for project improvement"""
        opportunities = []

        # Test coverage
        if self._estimate_test_coverage(files) < 0.5:
            opportunities.append("Add more comprehensive tests")

        # Documentation
        if self._estimate_documentation_score(files) < 0.5:
            opportunities.append("Improve project documentation")

        # Configuration files
        config_files = ['requirements.txt', 'package.json', 'Cargo.toml', 'pom.xml']
        missing_configs = [cf for cf in config_files if not any(cf in f for f in files)]
        if 'Python' in languages and 'requirements.txt' not in [os.path.basename(f) for f in files]:
            opportunities.append("Add requirements.txt for dependency management")

        # CI/CD
        ci_indicators = ['.github/', '.gitlab-ci.yml', 'Jenkinsfile', '.travis.yml']
        if not any(indicator in str(files) for indicator in ci_indicators):
            opportunities.append("Set up continuous integration")

        # Code quality tools
        quality_files = ['.eslintrc', '.pylintrc', 'tox.ini', 'setup.cfg']
        if not any(qf in str(files) for qf in quality_files):
            opportunities.append("Add code quality tools and linting")

        return opportunities

    def _suggest_based_on_files(self, context: Dict[str, Any]) -> List[Suggestion]:
        """Generate suggestions based on current files"""
        suggestions = []
        files = context.get('available_files', [])

        if not files:
            suggestions.append(Suggestion(
                id="create_first_file",
                type=SuggestionType.NEXT_ACTION,
                title="Create your first file",
                description="Start your project by creating a main file",
                action_command="/file main.py",
                confidence=0.9,
                priority=1,
                tags=["beginner", "getting-started"]
            ))
            return suggestions

        # Suggest analyzing the main file
        main_files = [f for f in files if 'main' in f.lower() or 'app' in f.lower()]
        if main_files:
            suggestions.append(Suggestion(
                id="analyze_main_file",
                type=SuggestionType.NEXT_ACTION,
                title="Analyze your main file",
                description=f"Get insights about {main_files[0]}",
                action_command=f"/analyze {main_files[0]}",
                confidence=0.8,
                priority=1,
                tags=["analysis", "code-review"]
            ))

        # Suggest creating tests if missing
        test_files = [f for f in files if 'test' in f.lower()]
        code_files = [f for f in files if any(f.endswith(ext) for ext in ['.py', '.js', '.java'])]

        if code_files and not test_files:
            suggestions.append(Suggestion(
                id="create_tests",
                type=SuggestionType.BEST_PRACTICE,
                title="Add tests to your project",
                description="Generate tests for better code reliability",
                action_command=f"/test {code_files[0]}",
                confidence=0.7,
                priority=2,
                estimated_impact="high",
                tags=["testing", "best-practice"]
            ))

        # Suggest documentation if missing
        readme_exists = any('readme' in f.lower() for f in files)
        if not readme_exists and len(files) > 3:
            suggestions.append(Suggestion(
                id="create_readme",
                type=SuggestionType.PROJECT_IMPROVEMENT,
                title="Create project documentation",
                description="Add a README to document your project",
                confidence=0.6,
                priority=2,
                estimated_impact="medium",
                tags=["documentation", "project-management"]
            ))

        return suggestions

    def _suggest_based_on_mode(self, context: Dict[str, Any]) -> List[Suggestion]:
        """Generate suggestions based on current mode"""
        suggestions = []
        current_mode = context.get('current_mode', OperationMode.CHAT)

        if current_mode == OperationMode.CHAT:
            suggestions.append(Suggestion(
                id="mode_explanation",
                type=SuggestionType.FEATURE_DISCOVERY,
                title="Explore other modes",
                description="Switch to Propose mode to plan changes or Execute mode to make modifications",
                action_command="/mode propose",
                confidence=0.5,
                priority=3,
                learning_level="beginner",
                tags=["modes", "workflow"]
            ))

        elif current_mode == OperationMode.PROPOSE:
            suggestions.append(Suggestion(
                id="create_plan",
                type=SuggestionType.NEXT_ACTION,
                title="Create an execution plan",
                description="Plan your next development task",
                action_command="/plan",
                confidence=0.8,
                priority=1,
                tags=["planning", "workflow"]
            ))

        elif current_mode == OperationMode.EXECUTE:
            suggestions.append(Suggestion(
                id="safety_reminder",
                type=SuggestionType.BEST_PRACTICE,
                title="Safety first in Execute mode",
                description="Execute mode can modify files - backups are created automatically",
                confidence=0.7,
                priority=2,
                tags=["safety", "execute-mode"]
            ))

        return suggestions

    def _suggest_based_on_project_type(self, context: Dict[str, Any]) -> List[Suggestion]:
        """Generate suggestions based on detected project type"""
        suggestions = []

        if not self.project_insights:
            return suggestions

        project_type = self.project_insights.project_type
        languages = self.project_insights.languages

        # Python-specific suggestions
        if 'Python' in languages:
            suggestions.append(Suggestion(
                id="python_best_practices",
                type=SuggestionType.BEST_PRACTICE,
                title="Follow Python best practices",
                description="Review your code against PEP 8 and Python conventions",
                action_command="/review",
                confidence=0.6,
                priority=2,
                tags=["python", "code-quality"]
            ))

        # Web development suggestions
        if project_type in ['Web API', 'Frontend Application']:
            suggestions.append(Suggestion(
                id="web_security_review",
                type=SuggestionType.BEST_PRACTICE,
                title="Review web security practices",
                description="Check for common web security vulnerabilities",
                confidence=0.7,
                priority=2,
                estimated_impact="high",
                tags=["security", "web-development"]
            ))

        # Testing suggestions based on coverage
        if self.project_insights.test_coverage_estimate < 0.3:
            suggestions.append(Suggestion(
                id="improve_test_coverage",
                type=SuggestionType.PROJECT_IMPROVEMENT,
                title="Improve test coverage",
                description=f"Current test coverage is estimated at {self.project_insights.test_coverage_estimate:.0%}",
                confidence=0.8,
                priority=1,
                estimated_impact="high",
                tags=["testing", "quality"]
            ))

        return suggestions

    def _suggest_based_on_user_patterns(self) -> List[Suggestion]:
        """Generate suggestions based on learned user patterns"""
        suggestions = []

        # Find frequently used patterns
        frequent_patterns = [p for p in self.user_patterns.values() if p.frequency > 3]

        for pattern in frequent_patterns:
            if pattern.success_rate < 0.7:  # Pattern with low success rate
                suggestions.append(Suggestion(
                    id=f"improve_pattern_{pattern.pattern_type}",
                    type=SuggestionType.WORKFLOW_OPTIMIZATION,
                    title=f"Optimize your {pattern.pattern_type} workflow",
                    description="I've noticed this pattern could be improved",
                    confidence=0.6,
                    priority=2,
                    tags=["optimization", "learning"]
                ))

        return suggestions

    def _suggest_based_on_intent(self, intent: Intent, context: Dict[str, Any]) -> List[Suggestion]:
        """Generate suggestions based on current user intent"""
        suggestions = []

        intent_suggestions = {
            Intent.ANALYZE_CODE: [
                Suggestion(
                    id="follow_up_analysis",
                    type=SuggestionType.NEXT_ACTION,
                    title="Fix issues found in analysis",
                    description="Address any problems discovered during code analysis",
                    action_command="/fix",
                    confidence=0.7,
                    priority=1,
                    tags=["follow-up", "bug-fixing"]
                )
            ],
            Intent.FIX_BUGS: [
                Suggestion(
                    id="test_after_fix",
                    type=SuggestionType.BEST_PRACTICE,
                    title="Test your fixes",
                    description="Run tests to verify your bug fixes work correctly",
                    action_command="/test",
                    confidence=0.8,
                    priority=1,
                    tags=["testing", "verification"]
                )
            ],
            Intent.COMPLETE_CODE: [
                Suggestion(
                    id="review_completed_code",
                    type=SuggestionType.NEXT_ACTION,
                    title="Review completed code",
                    description="Check the quality and style of the newly completed code",
                    action_command="/review",
                    confidence=0.7,
                    priority=2,
                    tags=["code-review", "quality"]
                )
            ],
            Intent.GENERATE_TESTS: [
                Suggestion(
                    id="run_generated_tests",
                    type=SuggestionType.NEXT_ACTION,
                    title="Run the generated tests",
                    description="Execute the new tests to make sure they pass",
                    action_command="/run",
                    confidence=0.9,
                    priority=1,
                    tags=["testing", "execution"]
                )
            ]
        }

        return intent_suggestions.get(intent, [])

    def _update_user_patterns(self, history: List[Dict[str, Any]]):
        """Update user behavior patterns based on recent history"""
        if not history:
            return

        # Analyze command sequences
        commands = [h.get('command', '') for h in history[-10:]]
        self._update_command_patterns(commands)

        # Analyze success/failure patterns
        self._update_success_patterns(history)

        # Analyze timing patterns
        self._update_timing_patterns(history)

    def _update_command_patterns(self, commands: List[str]):
        """Update patterns in command usage"""
        # Look for common sequences
        for i in range(len(commands) - 1):
            if commands[i] and commands[i + 1]:
                pattern_key = f"{commands[i]}_{commands[i + 1]}"

                if pattern_key in self.user_patterns:
                    self.user_patterns[pattern_key].frequency += 1
                    self.user_patterns[pattern_key].last_occurrence = datetime.now()
                else:
                    self.user_patterns[pattern_key] = UserPattern(
                        pattern_type="command_sequence",
                        frequency=1,
                        last_occurrence=datetime.now(),
                        success_rate=1.0,
                        associated_commands=[commands[i], commands[i + 1]]
                    )

    def _update_success_patterns(self, history: List[Dict[str, Any]]):
        """Update success rate patterns"""
        for entry in history[-5:]:  # Last 5 entries
            command = entry.get('command', '')
            success = entry.get('success', True)

            if command:
                pattern_key = f"success_{command}"

                if pattern_key in self.user_patterns:
                    pattern = self.user_patterns[pattern_key]
                    # Update success rate with exponential moving average
                    pattern.success_rate = 0.7 * pattern.success_rate + 0.3 * (1.0 if success else 0.0)
                    pattern.frequency += 1
                else:
                    self.user_patterns[pattern_key] = UserPattern(
                        pattern_type="command_success",
                        frequency=1,
                        last_occurrence=datetime.now(),
                        success_rate=1.0 if success else 0.0,
                        associated_commands=[command]
                    )

    def _update_timing_patterns(self, history: List[Dict[str, Any]]):
        """Update timing-based patterns"""
        # This could analyze when users are most active,
        # how long they spend on tasks, etc.
        pass

    def _rank_suggestions(self, suggestions: List[Suggestion], context: Dict[str, Any]) -> List[Suggestion]:
        """Rank suggestions by relevance and importance"""
        for suggestion in suggestions:
            # Calculate relevance score
            relevance_score = self._calculate_relevance(suggestion, context)
            suggestion.context_relevance = relevance_score

        # Sort by priority (1=highest), then by relevance, then by confidence
        return sorted(suggestions,
                     key=lambda s: (s.priority, -s.context_relevance, -s.confidence))

    def _calculate_relevance(self, suggestion: Suggestion, context: Dict[str, Any]) -> float:
        """Calculate how relevant a suggestion is to current context"""
        relevance = 0.5  # Base relevance

        # Boost relevance based on current mode
        current_mode = context.get('current_mode', OperationMode.CHAT)
        if suggestion.type == SuggestionType.NEXT_ACTION and current_mode == OperationMode.EXECUTE:
            relevance += 0.3

        # Boost relevance based on project insights
        if self.project_insights:
            if 'testing' in suggestion.tags and self.project_insights.test_coverage_estimate < 0.5:
                relevance += 0.2
            if 'documentation' in suggestion.tags and self.project_insights.documentation_score < 0.5:
                relevance += 0.2

        # Boost relevance based on user patterns
        if suggestion.action_command:
            command = suggestion.action_command.split()[0]
            success_pattern_key = f"success_{command}"
            if success_pattern_key in self.user_patterns:
                success_rate = self.user_patterns[success_pattern_key].success_rate
                relevance += 0.1 * success_rate

        return min(relevance, 1.0)

    def _cleanup_old_suggestions(self):
        """Remove old suggestions from history"""
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.suggestion_history = [s for s in self.suggestion_history
                                 if hasattr(s, 'timestamp') and s.timestamp > cutoff_time]

    def get_contextual_help(self, current_situation: str, user_level: str = "beginner") -> List[str]:
        """Get contextual help messages based on current situation"""
        help_messages = []

        situation_help = {
            'no_files': [
                "Start by creating your first file with a command like '/file main.py'",
                "You can also analyze existing files by using '/analyze filename'",
                "Try '/help' to see all available commands"
            ],
            'many_files': [
                "With many files, try '/find pattern' to locate specific files",
                "Use '/tree' to see your project structure",
                "Consider using '/git-status' to see what's changed"
            ],
            'errors_found': [
                "Use '/fix filename' to automatically fix common issues",
                "Try '/explain' to understand what the errors mean",
                "Consider '/test' to create tests that prevent future errors"
            ],
            'new_user': [
                "TinyCode has three modes: Chat (safe), Propose (planning), and Execute (modifications)",
                "Start with Chat mode to explore safely",
                "Use natural language - you don't need to memorize commands"
            ]
        }

        # Add level-appropriate help
        if user_level == "beginner":
            help_messages.extend([
                "💡 Tip: You can ask me questions in natural language",
                "🛡️ I'll always ask before making changes to your files",
                "📚 Use '/help' anytime to see what I can do"
            ])
        elif user_level == "intermediate":
            help_messages.extend([
                "⚡ Pro tip: Use '/mode propose' to plan complex changes",
                "🔍 Try advanced file operations with '/find' and '/grep'",
                "🤖 I can learn your patterns and suggest optimizations"
            ])

        return help_messages.get(current_situation, help_messages)

    def get_progress_insights(self) -> Dict[str, Any]:
        """Get insights about user progress and learning"""
        return {
            'suggestions_generated': len(self.suggestion_history),
            'patterns_learned': len(self.user_patterns),
            'project_complexity': self.project_insights.complexity_score if self.project_insights else 0,
            'estimated_skill_level': self._estimate_user_skill_level(),
            'recommended_next_steps': self._get_recommended_next_steps()
        }

    def _estimate_user_skill_level(self) -> str:
        """Estimate user skill level based on behavior patterns"""
        if not self.user_patterns:
            return "beginner"

        advanced_commands = {'refactor', 'review', 'git-', 'multi-edit', 'grep'}
        advanced_usage = sum(1 for pattern in self.user_patterns.values()
                           if any(cmd in str(pattern.associated_commands) for cmd in advanced_commands))

        total_patterns = len(self.user_patterns)
        if total_patterns == 0:
            return "beginner"

        advanced_ratio = advanced_usage / total_patterns
        if advanced_ratio > 0.4:
            return "advanced"
        elif advanced_ratio > 0.2:
            return "intermediate"
        else:
            return "beginner"

    def _get_recommended_next_steps(self) -> List[str]:
        """Get recommended next steps for user progression"""
        skill_level = self._estimate_user_skill_level()

        next_steps = {
            'beginner': [
                "Try analyzing a file with natural language",
                "Experiment with different modes (chat, propose, execute)",
                "Create your first test file"
            ],
            'intermediate': [
                "Explore advanced file operations",
                "Set up automated workflows",
                "Learn about code quality tools"
            ],
            'advanced': [
                "Customize TinyCode for your workflow",
                "Contribute patterns and suggestions",
                "Optimize complex project structures"
            ]
        }

        return next_steps.get(skill_level, next_steps['beginner'])


class UserLearningSystem:
    """Tracks user learning progress and suggests educational content"""

    def __init__(self):
        self.feature_usage = {}
        self.knowledge_gaps = []
        self.learning_goals = []

    def suggest_learning_opportunities(self, context: Dict[str, Any], history: List[Dict[str, Any]]) -> List[Suggestion]:
        """Suggest learning opportunities based on usage patterns"""
        suggestions = []

        # Identify unused features
        all_commands = set(['analyze', 'fix', 'complete', 'refactor', 'test', 'review'])
        used_commands = set(h.get('command', '').split()[0] for h in history if h.get('command'))
        unused_commands = all_commands - used_commands

        for unused_cmd in unused_commands:
            if len(unused_commands) <= 3:  # Don't overwhelm with too many suggestions
                suggestions.append(Suggestion(
                    id=f"learn_{unused_cmd}",
                    type=SuggestionType.LEARNING_OPPORTUNITY,
                    title=f"Discover the /{unused_cmd} command",
                    description=f"Learn how /{unused_cmd} can improve your workflow",
                    confidence=0.6,
                    priority=3,
                    learning_level="beginner",
                    tags=["learning", "feature-discovery"]
                ))

        return suggestions


class WorkflowOptimizer:
    """Analyzes workflows and suggests optimizations"""

    def suggest_optimizations(self, history: List[Dict[str, Any]]) -> List[Suggestion]:
        """Suggest workflow optimizations based on command patterns"""
        suggestions = []

        if len(history) < 5:
            return suggestions

        # Look for inefficient patterns
        commands = [h.get('command', '') for h in history[-10:]]

        # Detect repeated file operations
        file_operations = [cmd for cmd in commands if any(op in cmd for op in ['analyze', 'fix', 'test'])]
        if len(file_operations) > 3:
            suggestions.append(Suggestion(
                id="batch_operations",
                type=SuggestionType.WORKFLOW_OPTIMIZATION,
                title="Consider batching file operations",
                description="You can work on multiple files more efficiently with planning mode",
                action_command="/mode propose",
                confidence=0.7,
                priority=2,
                tags=["efficiency", "workflow"]
            ))

        return suggestions

    def _analyze_file_structure(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze file structure for context"""
        files = context.get('available_files', [])
        current_dir = context.get('current_directory', '.')

        return {
            'total_files': len(files),
            'file_types': self._detect_languages(files),
            'frameworks': self._detect_frameworks(files),
            'structure_complexity': 'simple' if len(files) < 10 else 'moderate' if len(files) < 50 else 'complex'
        }


# Test function
def test_smart_assistant():
    """Test the smart assistant with sample scenarios"""
    assistant = SmartAssistant()

    # Mock context
    context = {
        'available_files': ['main.py', 'utils.py', 'config.json'],
        'current_mode': OperationMode.CHAT,
        'project_type': 'Python Application'
    }

    # Mock history
    history = [
        {'command': 'analyze main.py', 'success': True, 'timestamp': datetime.now()},
        {'command': 'fix main.py', 'success': False, 'timestamp': datetime.now()},
        {'command': 'analyze utils.py', 'success': True, 'timestamp': datetime.now()}
    ]

    suggestions = assistant.analyze_context_and_suggest(context, history, Intent.ANALYZE_CODE)

    print("Smart Assistant Suggestions:")
    for i, suggestion in enumerate(suggestions[:5], 1):
        print(f"{i}. {suggestion.title}")
        print(f"   {suggestion.description}")
        if suggestion.action_command:
            print(f"   Command: {suggestion.action_command}")
        print(f"   Priority: {suggestion.priority}, Confidence: {suggestion.confidence:.2f}")
        print()


if __name__ == "__main__":
    test_smart_assistant()
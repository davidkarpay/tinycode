"""
Command Translation Layer for TinyCode

This module translates natural language intents into specific TinyCode CLI commands,
handling parameter extraction, context awareness, and command validation.
"""

import os
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Set
from pathlib import Path
from enum import Enum

from .nlp_interface import Intent, IntentResult, Entity, EntityType
from .command_registry import CommandRegistry
from .mode_manager import OperationMode


class CommandType(Enum):
    """Types of commands that can be generated"""
    DIRECT = "direct"          # Direct command execution
    INTERACTIVE = "interactive"  # Requires user interaction
    CONDITIONAL = "conditional"  # Depends on context/conditions
    COMPOSITE = "composite"    # Multiple commands in sequence


@dataclass
class TranslatedCommand:
    """A natural language input translated to CLI command(s)"""
    original_input: str
    intent: Intent
    command_type: CommandType
    primary_command: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    additional_commands: List[str] = field(default_factory=list)
    requires_confirmation: bool = False
    confirmation_message: str = ""
    prerequisites: List[str] = field(default_factory=list)
    suggested_followups: List[str] = field(default_factory=list)
    explanation: str = ""
    safety_level: str = "safe"  # safe, moderate, dangerous
    mode_required: Optional[OperationMode] = None


@dataclass
class ContextInfo:
    """Context information for command translation"""
    current_directory: str
    available_files: List[str] = field(default_factory=list)
    current_mode: OperationMode = OperationMode.CHAT
    last_commands: List[str] = field(default_factory=list)
    project_type: Optional[str] = None
    git_status: Optional[Dict[str, Any]] = None
    user_preferences: Dict[str, Any] = field(default_factory=dict)


class CommandTranslator:
    """Translates natural language intents to TinyCode CLI commands"""

    def __init__(self):
        self.command_registry = CommandRegistry()
        self.file_operations_cache = {}
        self.context_analyzers = self._initialize_context_analyzers()
        self.command_templates = self._initialize_command_templates()
        self.safety_rules = self._initialize_safety_rules()

    def translate(self, intent_result: IntentResult, context: ContextInfo) -> TranslatedCommand:
        """
        Translate intent result to executable command(s)

        Args:
            intent_result: Classified intent with entities and parameters
            context: Current context information

        Returns:
            TranslatedCommand with executable CLI command(s)
        """
        # Get command template for this intent
        template = self.command_templates.get(intent_result.intent)
        if not template:
            return self._create_fallback_command(intent_result, context)

        # Extract and validate parameters
        validated_params = self._validate_parameters(intent_result, context)

        # Generate primary command
        primary_command = self._generate_primary_command(
            intent_result.intent, validated_params, context
        )

        # Determine command type and safety level
        command_type = self._determine_command_type(intent_result.intent, validated_params)
        safety_level = self._assess_safety_level(intent_result.intent, validated_params)

        # Generate additional commands if needed
        additional_commands = self._generate_additional_commands(
            intent_result.intent, validated_params, context
        )

        # Check prerequisites
        prerequisites = self._check_prerequisites(intent_result.intent, validated_params, context)

        # Generate follow-up suggestions
        followups = self._generate_followup_suggestions(intent_result.intent, validated_params, context)

        # Generate explanation
        explanation = self._generate_explanation(intent_result.intent, validated_params)

        # Check if confirmation is needed
        requires_confirmation, confirmation_msg = self._check_confirmation_needed(
            intent_result.intent, validated_params, safety_level
        )

        # Determine required mode
        mode_required = self._determine_required_mode(intent_result.intent, validated_params)

        return TranslatedCommand(
            original_input=intent_result.command_suggestion or "",
            intent=intent_result.intent,
            command_type=command_type,
            primary_command=primary_command,
            parameters=validated_params,
            additional_commands=additional_commands,
            requires_confirmation=requires_confirmation,
            confirmation_message=confirmation_msg,
            prerequisites=prerequisites,
            suggested_followups=followups,
            explanation=explanation,
            safety_level=safety_level,
            mode_required=mode_required
        )

    def _initialize_command_templates(self) -> Dict[Intent, Dict[str, Any]]:
        """Initialize command templates for each intent"""
        return {
            Intent.ANALYZE_CODE: {
                'primary': 'analyze',
                'params': ['file'],
                'safety': 'safe',
                'mode': OperationMode.CHAT
            },
            Intent.FIX_BUGS: {
                'primary': 'fix',
                'params': ['file'],
                'safety': 'moderate',
                'mode': OperationMode.EXECUTE,
                'requires_backup': True
            },
            Intent.COMPLETE_CODE: {
                'primary': 'complete',
                'params': ['file', 'requirements'],
                'safety': 'moderate',
                'mode': OperationMode.EXECUTE,
                'requires_backup': True
            },
            Intent.REFACTOR_CODE: {
                'primary': 'refactor',
                'params': ['file'],
                'safety': 'dangerous',
                'mode': OperationMode.EXECUTE,
                'requires_confirmation': True,
                'requires_backup': True
            },
            Intent.EXPLAIN_CODE: {
                'primary': 'explain',
                'params': ['file'],
                'safety': 'safe',
                'mode': OperationMode.CHAT
            },
            Intent.REVIEW_CODE: {
                'primary': 'review',
                'params': ['file'],
                'safety': 'safe',
                'mode': OperationMode.CHAT
            },
            Intent.GENERATE_TESTS: {
                'primary': 'test',
                'params': ['file'],
                'safety': 'moderate',
                'mode': OperationMode.EXECUTE
            },
            Intent.RUN_CODE: {
                'primary': 'run',
                'params': ['file'],
                'safety': 'moderate',
                'mode': OperationMode.EXECUTE,
                'requires_confirmation': True
            },
            Intent.READ_FILE: {
                'primary': 'file',
                'params': ['file'],
                'safety': 'safe',
                'mode': OperationMode.CHAT
            },
            Intent.FIND_FILES: {
                'primary': 'find',
                'params': ['pattern'],
                'safety': 'safe',
                'mode': OperationMode.CHAT
            },
            Intent.GIT_STATUS: {
                'primary': 'git-status',
                'params': [],
                'safety': 'safe',
                'mode': OperationMode.CHAT
            },
            Intent.GIT_COMMIT: {
                'primary': 'git-commit',
                'params': ['message'],
                'safety': 'moderate',
                'mode': OperationMode.EXECUTE,
                'requires_confirmation': True
            },
            Intent.CHANGE_MODE: {
                'primary': 'mode',
                'params': ['target_mode'],
                'safety': 'safe',
                'mode': None  # Can be called from any mode
            },
            Intent.GET_HELP: {
                'primary': 'help',
                'params': ['topic'],
                'safety': 'safe',
                'mode': OperationMode.CHAT
            }
        }

    def _initialize_safety_rules(self) -> Dict[str, Dict[str, Any]]:
        """Initialize safety rules for different operations"""
        return {
            'file_modification': {
                'requires_backup': True,
                'requires_confirmation': True,
                'allowed_extensions': ['.py', '.js', '.java', '.cpp', '.go', '.rs', '.rb'],
                'forbidden_patterns': ['/etc/', '/usr/', '/bin/', '/sys/']
            },
            'code_execution': {
                'requires_confirmation': True,
                'scan_for_dangerous': True,
                'dangerous_patterns': ['rm ', 'del ', 'format', 'sudo ', 'chmod 777']
            },
            'git_operations': {
                'requires_confirmation': ['push', 'reset --hard', 'rebase'],
                'safe_operations': ['status', 'log', 'diff', 'branch']
            }
        }

    def _initialize_context_analyzers(self) -> Dict[str, callable]:
        """Initialize context analysis functions"""
        return {
            'project_type': self._analyze_project_type,
            'file_structure': self._analyze_file_structure,
            'git_state': self._analyze_git_state,
            'language_context': self._analyze_language_context
        }

    def _validate_parameters(self, intent_result: IntentResult, context: ContextInfo) -> Dict[str, Any]:
        """Validate and enhance parameters from intent result"""
        params = intent_result.parameters.copy()

        # Validate file parameters
        if 'primary_file' in params:
            file_path = params['primary_file']
            validated_file = self._validate_file_path(file_path, context)
            params['primary_file'] = validated_file

        # Handle missing files by suggesting alternatives
        if intent_result.intent in [Intent.ANALYZE_CODE, Intent.FIX_BUGS, Intent.COMPLETE_CODE]:
            if 'primary_file' not in params and context.available_files:
                # Suggest most relevant file based on intent
                suggested_file = self._suggest_relevant_file(intent_result.intent, context)
                if suggested_file:
                    params['suggested_file'] = suggested_file

        # Validate and enhance pattern parameters
        if 'pattern' in params:
            params['pattern'] = self._validate_search_pattern(params['pattern'])

        # Add context-based parameters
        params.update(self._extract_context_parameters(intent_result.intent, context))

        return params

    def _validate_file_path(self, file_path: str, context: ContextInfo) -> str:
        """Validate and resolve file path"""
        # Remove quotes if present
        clean_path = file_path.strip('\'"')

        # Handle relative paths
        if not os.path.isabs(clean_path):
            full_path = os.path.join(context.current_directory, clean_path)
        else:
            full_path = clean_path

        # Check if file exists
        if os.path.exists(full_path):
            return clean_path  # Return original relative path

        # Try to find similar files
        similar_files = self._find_similar_files(clean_path, context.available_files)
        if similar_files:
            return similar_files[0]  # Return best match

        return clean_path  # Return original even if not found

    def _find_similar_files(self, target: str, available_files: List[str]) -> List[str]:
        """Find files similar to target using fuzzy matching"""
        target_lower = target.lower()
        matches = []

        for file_path in available_files:
            file_name = os.path.basename(file_path).lower()

            # Exact match
            if target_lower == file_name:
                matches.append(file_path)
                continue

            # Partial match
            if target_lower in file_name or file_name in target_lower:
                matches.append(file_path)
                continue

            # Extension match for code files
            if '.' in target_lower:
                target_ext = target_lower.split('.')[-1]
                file_ext = file_name.split('.')[-1] if '.' in file_name else ''
                if target_ext == file_ext:
                    matches.append(file_path)

        return matches[:3]  # Return top 3 matches

    def _suggest_relevant_file(self, intent: Intent, context: ContextInfo) -> Optional[str]:
        """Suggest most relevant file based on intent and context"""
        if not context.available_files:
            return None

        # Priority based on intent
        priority_extensions = {
            Intent.ANALYZE_CODE: ['.py', '.js', '.java', '.cpp'],
            Intent.FIX_BUGS: ['.py', '.js', '.java', '.cpp'],
            Intent.GENERATE_TESTS: ['.py', '.js', '.java'],
            Intent.RUN_CODE: ['.py', '.js', '.java', '.go']
        }

        relevant_extensions = priority_extensions.get(intent, [])

        # Find files with relevant extensions
        relevant_files = []
        for file_path in context.available_files:
            for ext in relevant_extensions:
                if file_path.endswith(ext):
                    relevant_files.append(file_path)
                    break

        if relevant_files:
            # Prefer main files
            main_files = [f for f in relevant_files if 'main' in f.lower()]
            if main_files:
                return main_files[0]

            # Prefer non-test files for most intents
            if intent != Intent.GENERATE_TESTS:
                non_test_files = [f for f in relevant_files if 'test' not in f.lower()]
                if non_test_files:
                    return non_test_files[0]

            return relevant_files[0]

        return context.available_files[0] if context.available_files else None

    def _generate_primary_command(self, intent: Intent, params: Dict[str, Any], context: ContextInfo) -> str:
        """Generate the primary CLI command"""
        template = self.command_templates.get(intent)
        if not template:
            return "help"

        command_parts = [template['primary']]

        # Add required parameters
        required_params = template.get('params', [])
        for param in required_params:
            if param == 'file' and 'primary_file' in params:
                command_parts.append(f'"{params["primary_file"]}"')
            elif param == 'pattern' and 'pattern' in params:
                command_parts.append(f'"{params["pattern"]}"')
            elif param == 'target_mode' and 'mode' in params:
                command_parts.append(params['mode'])
            elif param == 'message' and 'commit_message' in params:
                command_parts.append(f'"{params["commit_message"]}"')
            elif param == 'requirements' and 'requirements' in params:
                # Requirements are usually passed as context, not command args
                pass
            elif param == 'topic' and 'help_topic' in params:
                command_parts.append(params['help_topic'])

        return " ".join(command_parts)

    def _determine_command_type(self, intent: Intent, params: Dict[str, Any]) -> CommandType:
        """Determine the type of command based on intent and parameters"""
        # Interactive commands that need user input
        interactive_intents = [Intent.CHANGE_MODE, Intent.GET_HELP]
        if intent in interactive_intents:
            return CommandType.INTERACTIVE

        # Conditional commands based on missing parameters
        if intent in [Intent.ANALYZE_CODE, Intent.FIX_BUGS] and 'primary_file' not in params:
            return CommandType.CONDITIONAL

        # Composite commands that involve multiple steps
        composite_intents = [Intent.COMPLETE_CODE, Intent.GENERATE_TESTS]
        if intent in composite_intents:
            return CommandType.COMPOSITE

        return CommandType.DIRECT

    def _assess_safety_level(self, intent: Intent, params: Dict[str, Any]) -> str:
        """Assess safety level of the command"""
        template = self.command_templates.get(intent, {})
        base_safety = template.get('safety', 'safe')

        # Upgrade safety level based on parameters
        if 'primary_file' in params:
            file_path = params['primary_file']

            # Check for system files
            dangerous_paths = ['/etc/', '/usr/', '/bin/', '/sys/', 'C:\\Windows\\']
            if any(path in file_path for path in dangerous_paths):
                return 'dangerous'

            # Check for important project files
            critical_files = ['package.json', 'requirements.txt', 'Cargo.toml', 'pom.xml']
            if any(file in file_path for file in critical_files):
                return 'moderate'

        return base_safety

    def _generate_additional_commands(self, intent: Intent, params: Dict[str, Any], context: ContextInfo) -> List[str]:
        """Generate additional commands that might be useful"""
        additional = []

        # For code modification intents, suggest backup
        if intent in [Intent.FIX_BUGS, Intent.COMPLETE_CODE, Intent.REFACTOR_CODE]:
            additional.append("# Backup will be created automatically")

        # For test generation, suggest running tests
        if intent == Intent.GENERATE_TESTS:
            additional.append("# Consider running: /run <test_file>")

        # For git commit, suggest status first
        if intent == Intent.GIT_COMMIT:
            additional.append("git-status")

        return additional

    def _check_prerequisites(self, intent: Intent, params: Dict[str, Any], context: ContextInfo) -> List[str]:
        """Check prerequisites for command execution"""
        prerequisites = []

        # File existence check
        if 'primary_file' in params:
            file_path = params['primary_file']
            full_path = os.path.join(context.current_directory, file_path)
            if not os.path.exists(full_path):
                prerequisites.append(f"File does not exist: {file_path}")

        # Mode requirements
        template = self.command_templates.get(intent, {})
        required_mode = template.get('mode')
        if required_mode and context.current_mode != required_mode:
            prerequisites.append(f"Switch to {required_mode.value} mode first")

        # Git repository check
        if intent in [Intent.GIT_STATUS, Intent.GIT_COMMIT]:
            if not context.git_status:
                prerequisites.append("Not in a git repository")

        return prerequisites

    def _generate_followup_suggestions(self, intent: Intent, params: Dict[str, Any], context: ContextInfo) -> List[str]:
        """Generate suggested follow-up actions"""
        suggestions = []

        suggestion_map = {
            Intent.ANALYZE_CODE: [
                "Fix any issues found with /fix",
                "Get detailed explanation with /explain",
                "Review code quality with /review"
            ],
            Intent.FIX_BUGS: [
                "Run tests to verify fixes",
                "Review the changes made",
                "Commit changes with git"
            ],
            Intent.COMPLETE_CODE: [
                "Generate tests with /test",
                "Review code quality",
                "Add documentation"
            ],
            Intent.GENERATE_TESTS: [
                "Run the tests to verify they pass",
                "Add more comprehensive test cases",
                "Set up continuous integration"
            ],
            Intent.REFACTOR_CODE: [
                "Run tests to ensure functionality",
                "Review the refactored code",
                "Update documentation"
            ]
        }

        return suggestion_map.get(intent, [])

    def _generate_explanation(self, intent: Intent, params: Dict[str, Any]) -> str:
        """Generate human-readable explanation of what will happen"""
        explanations = {
            Intent.ANALYZE_CODE: "I'll examine your code structure, identify potential issues, and provide insights about code quality and organization.",
            Intent.FIX_BUGS: "I'll analyze your code for bugs and errors, then fix them while preserving the original functionality.",
            Intent.COMPLETE_CODE: "I'll help you write or complete code based on your requirements and the existing codebase context.",
            Intent.REFACTOR_CODE: "I'll improve your code's structure, readability, and maintainability while keeping the same functionality.",
            Intent.EXPLAIN_CODE: "I'll provide a detailed explanation of how your code works and what each part does.",
            Intent.REVIEW_CODE: "I'll assess your code quality, identify areas for improvement, and suggest best practices.",
            Intent.GENERATE_TESTS: "I'll create comprehensive test cases to verify your code works correctly and catches potential issues.",
            Intent.RUN_CODE: "I'll execute your code and show you the results, including any output or errors.",
            Intent.READ_FILE: "I'll read and display the contents of the specified file for you to review.",
            Intent.FIND_FILES: "I'll search for files matching your criteria in the current project directory."
        }

        base_explanation = explanations.get(intent, "I'll help you with your request.")

        # Add file-specific context
        if 'primary_file' in params:
            base_explanation += f" Working with: {params['primary_file']}"

        return base_explanation

    def _check_confirmation_needed(self, intent: Intent, params: Dict[str, Any], safety_level: str) -> Tuple[bool, str]:
        """Check if user confirmation is needed"""
        template = self.command_templates.get(intent, {})

        # Always require confirmation for dangerous operations
        if safety_level == 'dangerous':
            return True, f"This operation will modify code files. Are you sure you want to proceed?"

        # Check template requirements
        if template.get('requires_confirmation', False):
            operation_name = intent.value.replace('_', ' ').title()
            return True, f"Execute {operation_name}?"

        # Special cases
        if intent == Intent.RUN_CODE:
            return True, "Execute this code?"

        if intent == Intent.GIT_COMMIT:
            return True, "Commit these changes to git?"

        return False, ""

    def _determine_required_mode(self, intent: Intent, params: Dict[str, Any]) -> Optional[OperationMode]:
        """Determine the mode required for this command"""
        template = self.command_templates.get(intent, {})
        return template.get('mode')

    def _extract_context_parameters(self, intent: Intent, context: ContextInfo) -> Dict[str, Any]:
        """Extract additional parameters from context"""
        context_params = {}

        # Add current directory info
        context_params['current_directory'] = context.current_directory

        # Add project type if detected
        if context.project_type:
            context_params['project_type'] = context.project_type

        # Add file count for find operations
        if intent == Intent.FIND_FILES:
            context_params['total_files'] = len(context.available_files)

        # Add git context for git operations
        if intent in [Intent.GIT_STATUS, Intent.GIT_COMMIT] and context.git_status:
            context_params['git_status'] = context.git_status

        return context_params

    def _validate_search_pattern(self, pattern: str) -> str:
        """Validate and enhance search patterns"""
        # Remove quotes
        clean_pattern = pattern.strip('\'"')

        # Add wildcards if not present and pattern looks like a filename
        if '.' in clean_pattern and '*' not in clean_pattern and '?' not in clean_pattern:
            clean_pattern = f"*{clean_pattern}*"

        return clean_pattern

    def _create_fallback_command(self, intent_result: IntentResult, context: ContextInfo) -> TranslatedCommand:
        """Create fallback command for unknown intents"""
        return TranslatedCommand(
            original_input=intent_result.command_suggestion or "",
            intent=Intent.UNKNOWN,
            command_type=CommandType.INTERACTIVE,
            primary_command="help",
            explanation="I'm not sure what you'd like me to do. Let me show you the available commands.",
            suggested_followups=["Ask a specific question", "Use /help to see available commands"]
        )

    def _analyze_project_type(self, context: ContextInfo) -> Optional[str]:
        """Analyze project type from available files"""
        file_patterns = {
            'python': ['*.py', 'requirements.txt', 'setup.py', 'pyproject.toml'],
            'javascript': ['*.js', '*.jsx', 'package.json', 'yarn.lock'],
            'typescript': ['*.ts', '*.tsx', 'tsconfig.json'],
            'java': ['*.java', 'pom.xml', 'build.gradle'],
            'go': ['*.go', 'go.mod'],
            'rust': ['*.rs', 'Cargo.toml'],
            'ruby': ['*.rb', 'Gemfile']
        }

        for project_type, patterns in file_patterns.items():
            for pattern in patterns:
                if any(self._matches_pattern(f, pattern) for f in context.available_files):
                    return project_type

        return None

    def _matches_pattern(self, filename: str, pattern: str) -> bool:
        """Check if filename matches pattern"""
        if '*' in pattern:
            regex_pattern = pattern.replace('*', '.*')
            return bool(re.match(regex_pattern, filename))
        return filename == pattern

    def _analyze_file_structure(self, context: ContextInfo) -> Dict[str, Any]:
        """Analyze file structure of the project"""
        structure = {
            'total_files': len(context.available_files),
            'file_types': {},
            'has_tests': False,
            'has_docs': False
        }

        for file_path in context.available_files:
            ext = Path(file_path).suffix
            structure['file_types'][ext] = structure['file_types'].get(ext, 0) + 1

            if 'test' in file_path.lower():
                structure['has_tests'] = True

            if any(doc in file_path.lower() for doc in ['readme', 'doc', 'docs']):
                structure['has_docs'] = True

        return structure

    def _analyze_git_state(self, context: ContextInfo) -> Optional[Dict[str, Any]]:
        """Analyze git repository state"""
        if context.git_status:
            return {
                'has_changes': bool(context.git_status.get('modified', [])),
                'untracked_files': len(context.git_status.get('untracked', [])),
                'staged_files': len(context.git_status.get('staged', []))
            }
        return None

    def _analyze_language_context(self, context: ContextInfo) -> Optional[str]:
        """Determine primary programming language"""
        language_files = {}

        for file_path in context.available_files:
            ext = Path(file_path).suffix.lower()
            language_map = {
                '.py': 'python',
                '.js': 'javascript',
                '.jsx': 'javascript',
                '.ts': 'typescript',
                '.tsx': 'typescript',
                '.java': 'java',
                '.cpp': 'cpp',
                '.cc': 'cpp',
                '.hpp': 'cpp',
                '.go': 'go',
                '.rs': 'rust',
                '.rb': 'ruby'
            }

            language = language_map.get(ext)
            if language:
                language_files[language] = language_files.get(language, 0) + 1

        if language_files:
            return max(language_files.items(), key=lambda x: x[1])[0]

        return None


# Utility function for testing
def test_command_translator():
    """Test the command translator with sample scenarios"""
    from .nlp_interface import NLPProcessor

    nlp = NLPProcessor()
    translator = CommandTranslator()

    # Mock context
    context = ContextInfo(
        current_directory="/test/project",
        available_files=["main.py", "utils.py", "test_main.py"],
        current_mode=OperationMode.CHAT
    )

    test_inputs = [
        "Fix the bugs in main.py",
        "Analyze my code quality",
        "Create tests for the utils module",
        "What's the git status?",
        "Help me refactor this code"
    ]

    for user_input in test_inputs:
        print(f"\nInput: {user_input}")
        intent_result = nlp.process_input(user_input)
        command = translator.translate(intent_result, context)

        print(f"Primary Command: {command.primary_command}")
        print(f"Safety Level: {command.safety_level}")
        print(f"Explanation: {command.explanation}")
        if command.prerequisites:
            print(f"Prerequisites: {command.prerequisites}")
        if command.suggested_followups:
            print(f"Follow-ups: {command.suggested_followups[:2]}")


if __name__ == "__main__":
    test_command_translator()
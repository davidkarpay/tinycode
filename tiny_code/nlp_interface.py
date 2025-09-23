"""
Natural Language Processing Interface for TinyCode

This module provides natural language understanding capabilities to transform
user input into actionable commands and intents, making TinyCode more intuitive.
"""

import re
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set, Any
from enum import Enum
from pathlib import Path


class Intent(Enum):
    """Common user intents in software development"""
    # Code Operations
    ANALYZE_CODE = "analyze_code"
    FIX_BUGS = "fix_bugs"
    COMPLETE_CODE = "complete_code"
    REFACTOR_CODE = "refactor_code"
    EXPLAIN_CODE = "explain_code"
    REVIEW_CODE = "review_code"
    GENERATE_TESTS = "generate_tests"
    RUN_CODE = "run_code"

    # File Operations
    READ_FILE = "read_file"
    CREATE_FILE = "create_file"
    EDIT_FILE = "edit_file"
    DELETE_FILE = "delete_file"
    FIND_FILES = "find_files"
    COMPARE_FILES = "compare_files"

    # Project Operations
    CREATE_PROJECT = "create_project"
    SETUP_PROJECT = "setup_project"
    BUILD_PROJECT = "build_project"
    DEPLOY_PROJECT = "deploy_project"

    # Git Operations
    GIT_STATUS = "git_status"
    GIT_COMMIT = "git_commit"
    GIT_PUSH = "git_push"
    GIT_PULL = "git_pull"
    GIT_BRANCH = "git_branch"

    # Mode Operations
    CHANGE_MODE = "change_mode"
    GET_HELP = "get_help"
    SHOW_STATUS = "show_status"

    # Questions and Information
    ASK_QUESTION = "ask_question"
    GET_EXPLANATION = "get_explanation"
    REQUEST_GUIDANCE = "request_guidance"

    # Unknown Intent
    UNKNOWN = "unknown"


class EntityType(Enum):
    """Types of entities that can be extracted from user input"""
    FILE_PATH = "file_path"
    FUNCTION_NAME = "function_name"
    CLASS_NAME = "class_name"
    VARIABLE_NAME = "variable_name"
    LANGUAGE = "language"
    FRAMEWORK = "framework"
    ERROR_TYPE = "error_type"
    MODE_NAME = "mode_name"
    OPERATION_TYPE = "operation_type"


@dataclass
class Entity:
    """Extracted entity from user input"""
    type: EntityType
    value: str
    confidence: float
    start_pos: int
    end_pos: int


@dataclass
class IntentResult:
    """Result of intent classification"""
    intent: Intent
    confidence: float
    entities: List[Entity] = field(default_factory=list)
    command_suggestion: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    clarification_needed: bool = False
    clarification_questions: List[str] = field(default_factory=list)


class NLPProcessor:
    """Natural Language Processing processor for TinyCode"""

    def __init__(self):
        self.intent_patterns = self._initialize_intent_patterns()
        self.entity_patterns = self._initialize_entity_patterns()
        self.synonyms = self._initialize_synonyms()
        self.file_extensions = {
            'python': ['.py', '.pyx', '.pyi'],
            'javascript': ['.js', '.jsx', '.ts', '.tsx'],
            'java': ['.java'],
            'cpp': ['.cpp', '.cc', '.cxx', '.hpp', '.h'],
            'go': ['.go'],
            'rust': ['.rs'],
            'ruby': ['.rb'],
            'php': ['.php'],
            'html': ['.html', '.htm'],
            'css': ['.css', '.scss', '.sass'],
            'markdown': ['.md', '.markdown'],
            'yaml': ['.yml', '.yaml'],
            'json': ['.json'],
            'xml': ['.xml']
        }

    def _initialize_intent_patterns(self) -> Dict[Intent, List[str]]:
        """Initialize patterns for intent recognition"""
        return {
            Intent.ANALYZE_CODE: [
                r"analyze|examine|inspect|check|look at|review",
                r"what does.*do|how does.*work|understand",
                r"structure|organization|architecture"
            ],

            Intent.FIX_BUGS: [
                r"fix|repair|debug|solve|correct",
                r"bug|error|issue|problem|broken",
                r"not working|failing|crash"
            ],

            Intent.COMPLETE_CODE: [
                r"complete|finish|generate|write",
                r"code|function|class|method",
                r"implement|add|create"
            ],

            Intent.REFACTOR_CODE: [
                r"refactor|improve|optimize|clean up|clean",
                r"readable|maintainable|better|cleaner",
                r"restructure|reorganize"
            ],

            Intent.EXPLAIN_CODE: [
                r"explain|describe|tell me about",
                r"what is|what does|how does",
                r"documentation|comments"
            ],

            Intent.REVIEW_CODE: [
                r"review|audit|check quality",
                r"best practices|standards|conventions",
                r"code quality|performance"
            ],

            Intent.GENERATE_TESTS: [
                r"test|testing|unit test|integration test",
                r"generate.*test|create.*test|write.*test",
                r"test cases|test suite"
            ],

            Intent.RUN_CODE: [
                r"run|execute|launch|start",
                r"execute|run.*file|run.*script",
                r"launch|start.*program"
            ],

            Intent.READ_FILE: [
                r"read|open|show|display",
                r"content|what's in|view",
                r"load|get.*file"
            ],

            Intent.CREATE_FILE: [
                r"create|make|new|generate",
                r"file|document|script",
                r"touch|add.*file"
            ],

            Intent.FIND_FILES: [
                r"find|search|locate|look for",
                r"files|documents|scripts",
                r"where is|contains"
            ],

            Intent.GIT_STATUS: [
                r"git status|status|changes",
                r"what.*changed|modified",
                r"current state|repository status"
            ],

            Intent.GIT_COMMIT: [
                r"commit|save changes|check in",
                r"git commit|commit.*changes",
                r"version|snapshot"
            ],

            Intent.CHANGE_MODE: [
                r"mode|switch to|change to",
                r"chat mode|propose mode|execute mode",
                r"permissions|capabilities"
            ],

            Intent.GET_HELP: [
                r"help|how to|how do i|guide",
                r"assistance|support|tutorial",
                r"commands|options|what can"
            ],

            Intent.ASK_QUESTION: [
                r"what|how|why|when|where|which",
                r"question|ask|wondering",
                r"tell me|explain"
            ]
        }

    def _initialize_entity_patterns(self) -> Dict[EntityType, List[str]]:
        """Initialize patterns for entity extraction"""
        return {
            EntityType.FILE_PATH: [
                r"[\w\-_./\\]+\.(?:py|js|java|cpp|go|rs|rb|php|html|css|md|yml|json|xml|txt)",
                r"['\"][^'\"]+['\"]",  # Quoted file paths
                r"[\w\-_./\\]+/[\w\-_./\\]*",  # Directory paths
            ],

            EntityType.FUNCTION_NAME: [
                r"function\s+(\w+)",
                r"def\s+(\w+)",
                r"(\w+)\(\)",  # Function calls
            ],

            EntityType.CLASS_NAME: [
                r"class\s+(\w+)",
                r"(\w+)\s+class",
            ],

            EntityType.LANGUAGE: [
                r"\b(python|javascript|java|cpp|c\+\+|go|rust|ruby|php|html|css)\b",
            ],

            EntityType.MODE_NAME: [
                r"\b(chat|propose|execute)\s+mode\b",
                r"\bmode\s+(chat|propose|execute)\b",
            ],

            EntityType.ERROR_TYPE: [
                r"\b(syntax error|runtime error|type error|name error|index error)\b",
                r"\b(exception|error|bug|issue)\b",
            ]
        }

    def _initialize_synonyms(self) -> Dict[str, List[str]]:
        """Initialize synonym mappings for better intent matching"""
        return {
            'fix': ['repair', 'debug', 'solve', 'correct', 'resolve'],
            'create': ['make', 'generate', 'build', 'write', 'add'],
            'analyze': ['examine', 'inspect', 'check', 'review', 'study'],
            'explain': ['describe', 'tell', 'clarify', 'detail'],
            'run': ['execute', 'launch', 'start', 'invoke'],
            'find': ['search', 'locate', 'look for', 'discover'],
            'improve': ['optimize', 'enhance', 'refactor', 'clean up'],
            'show': ['display', 'view', 'list', 'present'],
            'help': ['assist', 'guide', 'support', 'teach']
        }

    def process_input(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> IntentResult:
        """
        Process natural language input and return intent classification with entities

        Args:
            user_input: Raw user input text
            context: Optional context information (current files, mode, etc.)

        Returns:
            IntentResult with classified intent and extracted entities
        """
        # Normalize input
        normalized_input = self._normalize_input(user_input)

        # Extract entities first
        entities = self._extract_entities(normalized_input)

        # Classify intent
        intent, confidence = self._classify_intent(normalized_input, entities)

        # Generate command suggestion
        command_suggestion = self._generate_command_suggestion(intent, entities, context)

        # Extract parameters
        parameters = self._extract_parameters(normalized_input, intent, entities)

        # Check if clarification is needed
        clarification_needed, questions = self._check_clarification_needed(
            intent, entities, parameters, context
        )

        return IntentResult(
            intent=intent,
            confidence=confidence,
            entities=entities,
            command_suggestion=command_suggestion,
            parameters=parameters,
            clarification_needed=clarification_needed,
            clarification_questions=questions
        )

    def _normalize_input(self, user_input: str) -> str:
        """Normalize user input for better processing"""
        # Convert to lowercase
        normalized = user_input.lower().strip()

        # Expand contractions
        contractions = {
            "can't": "cannot",
            "won't": "will not",
            "don't": "do not",
            "isn't": "is not",
            "aren't": "are not",
            "wasn't": "was not",
            "weren't": "were not",
            "haven't": "have not",
            "hasn't": "has not",
            "hadn't": "had not",
            "wouldn't": "would not",
            "shouldn't": "should not",
            "couldn't": "could not"
        }

        for contraction, expansion in contractions.items():
            normalized = normalized.replace(contraction, expansion)

        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized)

        return normalized

    def _extract_entities(self, text: str) -> List[Entity]:
        """Extract entities from normalized text"""
        entities = []

        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    # Extract the entity value (use group 1 if capture group exists)
                    value = match.group(1) if match.groups() else match.group(0)

                    # Calculate confidence based on pattern specificity
                    confidence = self._calculate_entity_confidence(entity_type, value, pattern)

                    entities.append(Entity(
                        type=entity_type,
                        value=value,
                        confidence=confidence,
                        start_pos=match.start(),
                        end_pos=match.end()
                    ))

        # Remove duplicates and sort by confidence
        entities = self._deduplicate_entities(entities)
        entities.sort(key=lambda e: e.confidence, reverse=True)

        return entities

    def _classify_intent(self, text: str, entities: List[Entity]) -> Tuple[Intent, float]:
        """Classify the intent of the user input"""
        intent_scores = {}

        # Score each intent based on pattern matching
        for intent, patterns in self.intent_patterns.items():
            score = 0.0
            matches = 0

            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    matches += 1
                    # Weight based on pattern specificity
                    pattern_weight = len(pattern) / 100  # Longer patterns get more weight
                    score += pattern_weight

            if matches > 0:
                # Boost score based on number of pattern matches
                score *= (1 + matches * 0.2)
                intent_scores[intent] = score

        # Boost scores based on entities
        entity_boosts = {
            Intent.READ_FILE: [EntityType.FILE_PATH],
            Intent.ANALYZE_CODE: [EntityType.FILE_PATH, EntityType.FUNCTION_NAME, EntityType.CLASS_NAME],
            Intent.FIX_BUGS: [EntityType.FILE_PATH, EntityType.ERROR_TYPE],
            Intent.CHANGE_MODE: [EntityType.MODE_NAME],
            Intent.GENERATE_TESTS: [EntityType.FILE_PATH, EntityType.FUNCTION_NAME],
            Intent.RUN_CODE: [EntityType.FILE_PATH]
        }

        for intent, relevant_entity_types in entity_boosts.items():
            if intent in intent_scores:
                for entity in entities:
                    if entity.type in relevant_entity_types:
                        intent_scores[intent] += 0.3 * entity.confidence

        # Handle special cases for questions
        if any(word in text for word in ['what', 'how', 'why', 'when', 'where', 'which']):
            if Intent.ASK_QUESTION not in intent_scores:
                intent_scores[Intent.ASK_QUESTION] = 0.5
            else:
                intent_scores[Intent.ASK_QUESTION] += 0.3

        # Determine best intent
        if intent_scores:
            best_intent = max(intent_scores.items(), key=lambda x: x[1])
            confidence = min(best_intent[1], 1.0)  # Cap at 1.0
            return best_intent[0], confidence
        else:
            return Intent.UNKNOWN, 0.0

    def _calculate_entity_confidence(self, entity_type: EntityType, value: str, pattern: str) -> float:
        """Calculate confidence score for extracted entity"""
        base_confidence = 0.7

        # Boost confidence for file paths with known extensions
        if entity_type == EntityType.FILE_PATH:
            for lang, extensions in self.file_extensions.items():
                if any(value.endswith(ext) for ext in extensions):
                    base_confidence += 0.2
                    break

        # Boost confidence for exact matches
        if len(pattern) > 20:  # Complex patterns
            base_confidence += 0.1

        # Boost confidence for common programming terms
        programming_terms = ['function', 'class', 'method', 'variable', 'file', 'script']
        if any(term in value.lower() for term in programming_terms):
            base_confidence += 0.1

        return min(base_confidence, 1.0)

    def _deduplicate_entities(self, entities: List[Entity]) -> List[Entity]:
        """Remove duplicate entities, keeping the highest confidence ones"""
        seen = {}
        deduplicated = []

        for entity in entities:
            key = (entity.type, entity.value.lower())
            if key not in seen or entity.confidence > seen[key].confidence:
                seen[key] = entity

        return list(seen.values())

    def _generate_command_suggestion(self, intent: Intent, entities: List[Entity],
                                   context: Optional[Dict[str, Any]]) -> Optional[str]:
        """Generate appropriate CLI command suggestion based on intent and entities"""

        # Get file entity if available
        file_entity = next((e for e in entities if e.type == EntityType.FILE_PATH), None)
        filename = file_entity.value if file_entity else None

        # Map intents to commands
        command_mapping = {
            Intent.ANALYZE_CODE: lambda f: f"/analyze {f}" if f else "/analyze",
            Intent.FIX_BUGS: lambda f: f"/fix {f}" if f else "/fix",
            Intent.COMPLETE_CODE: lambda f: f"/complete {f}" if f else "/complete",
            Intent.REFACTOR_CODE: lambda f: f"/refactor {f}" if f else "/refactor",
            Intent.EXPLAIN_CODE: lambda f: f"/explain {f}" if f else "/explain",
            Intent.REVIEW_CODE: lambda f: f"/review {f}" if f else "/review",
            Intent.GENERATE_TESTS: lambda f: f"/test {f}" if f else "/test",
            Intent.RUN_CODE: lambda f: f"/run {f}" if f else "/run",
            Intent.READ_FILE: lambda f: f"/file {f}" if f else "/list",
            Intent.FIND_FILES: lambda f: "/find",
            Intent.GIT_STATUS: lambda f: "/git-status",
            Intent.GIT_COMMIT: lambda f: "/git-commit",
            Intent.CHANGE_MODE: self._generate_mode_command,
            Intent.GET_HELP: lambda f: "/help"
        }

        if intent in command_mapping:
            command_generator = command_mapping[intent]
            if callable(command_generator):
                if intent == Intent.CHANGE_MODE:
                    return command_generator(entities)
                else:
                    return command_generator(filename)

        return None

    def _generate_mode_command(self, entities: List[Entity]) -> str:
        """Generate mode change command"""
        mode_entity = next((e for e in entities if e.type == EntityType.MODE_NAME), None)
        if mode_entity:
            return f"/mode {mode_entity.value}"
        return "/mode help"

    def _extract_parameters(self, text: str, intent: Intent, entities: List[Entity]) -> Dict[str, Any]:
        """Extract command parameters from text and entities"""
        parameters = {}

        # Extract file parameters
        file_entities = [e for e in entities if e.type == EntityType.FILE_PATH]
        if file_entities:
            parameters['files'] = [e.value for e in file_entities]
            parameters['primary_file'] = file_entities[0].value

        # Extract function/class names
        function_entities = [e for e in entities if e.type == EntityType.FUNCTION_NAME]
        if function_entities:
            parameters['functions'] = [e.value for e in function_entities]

        class_entities = [e for e in entities if e.type == EntityType.CLASS_NAME]
        if class_entities:
            parameters['classes'] = [e.value for e in class_entities]

        # Extract language information
        language_entities = [e for e in entities if e.type == EntityType.LANGUAGE]
        if language_entities:
            parameters['language'] = language_entities[0].value

        # Extract specific parameters based on intent
        if intent == Intent.FIND_FILES:
            # Look for search patterns
            pattern_match = re.search(r'find\s+["\']?([^"\']+)["\']?', text)
            if pattern_match:
                parameters['pattern'] = pattern_match.group(1)

        elif intent == Intent.COMPLETE_CODE:
            # Look for requirements or specifications
            requirements_match = re.search(r'(?:that|to|for)\s+(.+)', text)
            if requirements_match:
                parameters['requirements'] = requirements_match.group(1)

        return parameters

    def _check_clarification_needed(self, intent: Intent, entities: List[Entity],
                                  parameters: Dict[str, Any],
                                  context: Optional[Dict[str, Any]]) -> Tuple[bool, List[str]]:
        """Check if clarification is needed and generate appropriate questions"""
        questions = []

        # Check for missing file when file operation is intended
        file_operations = [
            Intent.ANALYZE_CODE, Intent.FIX_BUGS, Intent.COMPLETE_CODE,
            Intent.REFACTOR_CODE, Intent.EXPLAIN_CODE, Intent.REVIEW_CODE,
            Intent.GENERATE_TESTS, Intent.RUN_CODE, Intent.READ_FILE
        ]

        if intent in file_operations and 'primary_file' not in parameters:
            # Check if context has current files
            if context and context.get('current_files'):
                questions.append(f"Which file would you like me to work on? I can see: {', '.join(context['current_files'][:3])}")
            else:
                questions.append("Which file would you like me to work on?")

        # Check for vague requests
        if intent == Intent.COMPLETE_CODE and 'requirements' not in parameters:
            questions.append("What would you like me to implement or complete?")

        if intent == Intent.FIND_FILES and 'pattern' not in parameters:
            questions.append("What files are you looking for? You can specify a filename or pattern.")

        # Check for ambiguous intents
        if intent == Intent.UNKNOWN:
            questions.append("I'm not sure what you'd like me to do. Could you please clarify? For example, you can ask me to analyze code, fix bugs, or explain how something works.")

        return len(questions) > 0, questions

    def suggest_next_actions(self, intent: Intent, entities: List[Entity],
                           context: Optional[Dict[str, Any]]) -> List[str]:
        """Suggest logical next actions based on current intent and context"""
        suggestions = []

        if intent == Intent.ANALYZE_CODE:
            suggestions.extend([
                "Would you like me to fix any issues I found?",
                "Should I explain any specific parts of the code?",
                "Would you like me to suggest improvements?"
            ])

        elif intent == Intent.FIX_BUGS:
            suggestions.extend([
                "Should I run tests to verify the fixes?",
                "Would you like me to explain what I changed?",
                "Should I commit these changes to git?"
            ])

        elif intent == Intent.COMPLETE_CODE:
            suggestions.extend([
                "Would you like me to generate tests for this code?",
                "Should I add documentation or comments?",
                "Would you like me to review the code quality?"
            ])

        elif intent == Intent.GENERATE_TESTS:
            suggestions.extend([
                "Should I run these tests to make sure they pass?",
                "Would you like me to add more comprehensive test cases?",
                "Should I set up a test runner configuration?"
            ])

        return suggestions

    def get_intent_explanation(self, intent: Intent) -> str:
        """Get human-readable explanation of what an intent means"""
        explanations = {
            Intent.ANALYZE_CODE: "I'll examine your code to understand its structure and identify any potential issues.",
            Intent.FIX_BUGS: "I'll look for and fix bugs or errors in your code.",
            Intent.COMPLETE_CODE: "I'll help you write or complete code based on your requirements.",
            Intent.REFACTOR_CODE: "I'll improve your code's structure and readability while maintaining functionality.",
            Intent.EXPLAIN_CODE: "I'll explain how your code works and what it does.",
            Intent.REVIEW_CODE: "I'll assess your code quality and suggest improvements.",
            Intent.GENERATE_TESTS: "I'll create test cases to verify your code works correctly.",
            Intent.RUN_CODE: "I'll execute your code and show you the results.",
            Intent.READ_FILE: "I'll read and display the contents of a file.",
            Intent.FIND_FILES: "I'll help you locate files in your project.",
            Intent.GIT_STATUS: "I'll show you the current status of your git repository.",
            Intent.GET_HELP: "I'll provide guidance on how to use TinyCode effectively.",
            Intent.ASK_QUESTION: "I'll answer your question to the best of my ability."
        }

        return explanations.get(intent, "I'll help you with your request.")


# Utility functions for testing and validation
def test_nlp_processor():
    """Test the NLP processor with sample inputs"""
    processor = NLPProcessor()

    test_cases = [
        "Fix the bugs in main.py",
        "Can you analyze this file?",
        "How does the authenticate function work?",
        "Create a new Python class for user management",
        "What's the git status?",
        "I need help with writing tests",
        "Refactor my code to make it more readable",
        "Run the test suite"
    ]

    for test_input in test_cases:
        result = processor.process_input(test_input)
        print(f"Input: {test_input}")
        print(f"Intent: {result.intent.value} (confidence: {result.confidence:.2f})")
        print(f"Command: {result.command_suggestion}")
        if result.entities:
            print(f"Entities: {[(e.type.value, e.value) for e in result.entities]}")
        if result.clarification_needed:
            print(f"Questions: {result.clarification_questions}")
        print("-" * 50)


if __name__ == "__main__":
    test_nlp_processor()
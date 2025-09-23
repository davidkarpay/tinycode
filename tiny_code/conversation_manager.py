"""
Conversation Manager for TinyCode

This module manages multi-turn conversations, context preservation, clarifying questions,
and intelligent dialog flow to make TinyCode more intuitive and conversational.
"""

import json
import uuid
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime, timedelta
from enum import Enum

from .nlp_interface import Intent, IntentResult, NLPProcessor
from .command_translator import CommandTranslator, TranslatedCommand, ContextInfo
from .mode_manager import OperationMode


class ConversationState(Enum):
    """States of the conversation"""
    GREETING = "greeting"
    LISTENING = "listening"
    CLARIFYING = "clarifying"
    CONFIRMING = "confirming"
    EXECUTING = "executing"
    FOLLOWING_UP = "following_up"
    TEACHING = "teaching"
    ERROR_HANDLING = "error_handling"


class DialogType(Enum):
    """Types of dialog interactions"""
    COMMAND_REQUEST = "command_request"
    CLARIFICATION = "clarification"
    CONFIRMATION = "confirmation"
    QUESTION_ANSWER = "question_answer"
    GUIDANCE = "guidance"
    ERROR_RECOVERY = "error_recovery"


@dataclass
class ConversationTurn:
    """A single turn in the conversation"""
    turn_id: str
    timestamp: datetime
    user_input: str
    intent_result: Optional[IntentResult] = None
    translated_command: Optional[TranslatedCommand] = None
    system_response: str = ""
    dialog_type: DialogType = DialogType.COMMAND_REQUEST
    context_snapshot: Dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error_message: str = ""


@dataclass
class PendingAction:
    """An action waiting for user confirmation or clarification"""
    action_id: str
    command: TranslatedCommand
    created_at: datetime
    awaiting: str  # 'confirmation', 'clarification', 'input'
    clarification_questions: List[str] = field(default_factory=list)
    timeout_minutes: int = 30


@dataclass
class ConversationContext:
    """Extended context that persists across conversation turns"""
    session_id: str
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    current_topic: Optional[str] = None
    mentioned_files: Set[str] = field(default_factory=set)
    recent_commands: List[str] = field(default_factory=list)
    learning_progress: Dict[str, int] = field(default_factory=dict)  # Feature familiarity
    error_patterns: List[str] = field(default_factory=list)
    success_patterns: List[str] = field(default_factory=list)


class ConversationManager:
    """Manages multi-turn conversations with context awareness"""

    def __init__(self):
        self.nlp = NLPProcessor()
        self.translator = CommandTranslator()
        self.conversation_history: List[ConversationTurn] = []
        self.pending_actions: Dict[str, PendingAction] = {}
        self.conversation_context = ConversationContext(session_id=str(uuid.uuid4()))
        self.current_state = ConversationState.LISTENING
        self.context_info = ContextInfo(current_directory=".")
        self.response_templates = self._initialize_response_templates()
        self.clarification_strategies = self._initialize_clarification_strategies()

    def process_user_input(self, user_input: str, system_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process user input and return appropriate response with actions

        Args:
            user_input: Raw user input text
            system_context: Current system state (files, mode, etc.)

        Returns:
            Dict containing response, actions, and conversation state
        """
        # Update context from system
        if system_context:
            self._update_context_from_system(system_context)

        # Create conversation turn
        turn = ConversationTurn(
            turn_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            user_input=user_input,
            context_snapshot=asdict(self.context_info)
        )

        # Check for special conversation patterns
        if self._is_greeting(user_input):
            return self._handle_greeting(turn)

        if self._is_pending_response(user_input):
            return self._handle_pending_response(user_input, turn)

        # Process natural language input
        intent_result = self.nlp.process_input(
            user_input,
            context=self._build_nlp_context()
        )
        turn.intent_result = intent_result

        # Translate to command
        translated_command = self.translator.translate(intent_result, self.context_info)
        turn.translated_command = translated_command

        # Determine response strategy
        response = self._generate_response(turn)

        # Update conversation history and context
        self.conversation_history.append(turn)
        self._update_conversation_context(turn)

        # Clean up old pending actions
        self._cleanup_expired_actions()

        return response

    def _initialize_response_templates(self) -> Dict[str, Dict[str, str]]:
        """Initialize response templates for different scenarios"""
        return {
            'greeting': {
                'first_time': "Hello! I'm TinyCode, your AI coding assistant. I can help you analyze code, fix bugs, write tests, and much more. What would you like to work on today?",
                'returning': "Welcome back! I'm ready to help with your coding tasks. What can I do for you?",
                'mode_aware': "Hi! I'm in {mode} mode, which means I can {capabilities}. How can I assist you?"
            },
            'clarification': {
                'missing_file': "I'd be happy to help with that! Which file would you like me to work on?",
                'ambiguous_intent': "I want to make sure I understand correctly. Are you asking me to {intent_options}?",
                'missing_details': "Could you provide a bit more detail about {missing_info}?",
                'file_suggestions': "I can see these files in your project: {file_list}. Which one interests you?"
            },
            'confirmation': {
                'safe_operation': "I'll {action_description}. Sound good?",
                'moderate_risk': "I'm about to {action_description}. This will modify your files. Should I proceed?",
                'high_risk': "⚠️  This operation will {action_description}. I recommend creating a backup first. Continue anyway?"
            },
            'execution': {
                'starting': "Great! I'm {action_description}...",
                'progress': "Working on it... {progress_info}",
                'completed': "✅ Done! I've {completed_action}. {next_suggestions}",
                'error': "❌ I encountered an issue: {error_details}. Would you like me to try a different approach?"
            },
            'guidance': {
                'feature_introduction': "I noticed you're trying to {attempted_action}. Here's how I can help: {guidance}",
                'best_practice': "💡 Pro tip: {tip_content}",
                'learning_suggestion': "Since you're working with {technology}, you might find these features useful: {features}"
            }
        }

    def _initialize_clarification_strategies(self) -> Dict[Intent, Dict[str, Any]]:
        """Initialize strategies for clarifying different types of requests"""
        return {
            Intent.ANALYZE_CODE: {
                'missing_file': "Which file would you like me to analyze?",
                'multiple_files': "I see several files. Which one should I analyze first?",
                'no_files': "I don't see any code files in the current directory. Could you specify a file path?"
            },
            Intent.FIX_BUGS: {
                'missing_file': "Which file has the bugs you'd like me to fix?",
                'missing_error': "What specific error or issue are you seeing?",
                'scope_clarification': "Should I fix all bugs I find, or focus on a specific issue?"
            },
            Intent.COMPLETE_CODE: {
                'missing_requirements': "What would you like me to implement or complete?",
                'missing_context': "Could you describe what this code should do?",
                'ambiguous_scope': "Should I complete the current function, add new functionality, or something else?"
            },
            Intent.GENERATE_TESTS: {
                'missing_target': "Which functions or classes should I write tests for?",
                'test_type': "What type of tests would you like? Unit tests, integration tests, or both?",
                'coverage_level': "How comprehensive should the test coverage be?"
            }
        }

    def _is_greeting(self, user_input: str) -> bool:
        """Check if input is a greeting"""
        greetings = ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']
        return any(greeting in user_input.lower() for greeting in greetings)

    def _is_pending_response(self, user_input: str) -> bool:
        """Check if this is a response to a pending question"""
        return (
            self.current_state in [ConversationState.CLARIFYING, ConversationState.CONFIRMING] or
            bool(self.pending_actions) or
            any(word in user_input.lower() for word in ['yes', 'no', 'sure', 'okay', 'cancel'])
        )

    def _handle_greeting(self, turn: ConversationTurn) -> Dict[str, Any]:
        """Handle greeting interactions"""
        self.current_state = ConversationState.GREETING

        # Determine greeting type
        is_first_time = len(self.conversation_history) == 0
        template_key = 'first_time' if is_first_time else 'returning'

        # Check if we should be mode-aware
        if self.context_info.current_mode != OperationMode.CHAT:
            template_key = 'mode_aware'
            capabilities = self._get_mode_capabilities(self.context_info.current_mode)
            response_text = self.response_templates['greeting'][template_key].format(
                mode=self.context_info.current_mode.value,
                capabilities=capabilities
            )
        else:
            response_text = self.response_templates['greeting'][template_key]

        turn.system_response = response_text
        turn.dialog_type = DialogType.QUESTION_ANSWER
        self.current_state = ConversationState.LISTENING

        return {
            'response': response_text,
            'conversation_state': self.current_state.value,
            'actions': [],
            'requires_input': False,
            'suggestions': self._get_welcome_suggestions()
        }

    def _handle_pending_response(self, user_input: str, turn: ConversationTurn) -> Dict[str, Any]:
        """Handle responses to pending questions or confirmations"""
        # Check for confirmation responses
        if self.current_state == ConversationState.CONFIRMING:
            return self._handle_confirmation_response(user_input, turn)

        # Check for clarification responses
        if self.current_state == ConversationState.CLARIFYING:
            return self._handle_clarification_response(user_input, turn)

        # Check for pending actions
        if self.pending_actions:
            return self._handle_pending_action_response(user_input, turn)

        # Fallback to normal processing
        return self._process_normal_input(turn)

    def _handle_confirmation_response(self, user_input: str, turn: ConversationTurn) -> Dict[str, Any]:
        """Handle user's response to confirmation requests"""
        confirmation_words = ['yes', 'sure', 'okay', 'go ahead', 'proceed', 'do it']
        cancellation_words = ['no', 'cancel', 'stop', 'abort', 'nevermind']

        user_lower = user_input.lower()

        if any(word in user_lower for word in confirmation_words):
            # User confirmed - execute the pending action
            return self._execute_confirmed_action(turn)

        elif any(word in user_lower for word in cancellation_words):
            # User cancelled
            return self._cancel_pending_action(turn)

        else:
            # Unclear response - ask for clarification
            return self._ask_for_clear_confirmation(turn)

    def _handle_clarification_response(self, user_input: str, turn: ConversationTurn) -> Dict[str, Any]:
        """Handle user's response to clarification questions"""
        # Try to extract the clarification and continue processing
        enhanced_input = self._enhance_input_with_clarification(user_input)

        # Process the enhanced input
        intent_result = self.nlp.process_input(
            enhanced_input,
            context=self._build_nlp_context()
        )
        turn.intent_result = intent_result

        translated_command = self.translator.translate(intent_result, self.context_info)
        turn.translated_command = translated_command

        # Clear clarification state
        self.current_state = ConversationState.LISTENING

        return self._generate_response(turn)

    def _handle_pending_action_response(self, user_input: str, turn: ConversationTurn) -> Dict[str, Any]:
        """Handle responses to pending actions"""
        # Find the most recent pending action
        if not self.pending_actions:
            return self._process_normal_input(turn)

        action_id = list(self.pending_actions.keys())[-1]
        pending_action = self.pending_actions[action_id]

        # Process the response based on what we're awaiting
        if pending_action.awaiting == 'clarification':
            return self._process_clarification_response(user_input, pending_action, turn)
        elif pending_action.awaiting == 'confirmation':
            return self._process_confirmation_response(user_input, pending_action, turn)

        return self._process_normal_input(turn)

    def _process_normal_input(self, turn: ConversationTurn) -> Dict[str, Any]:
        """Process input through normal NLP pipeline"""
        intent_result = self.nlp.process_input(
            turn.user_input,
            context=self._build_nlp_context()
        )
        turn.intent_result = intent_result

        translated_command = self.translator.translate(intent_result, self.context_info)
        turn.translated_command = translated_command

        return self._generate_response(turn)

    def _generate_response(self, turn: ConversationTurn) -> Dict[str, Any]:
        """Generate appropriate response based on the conversation turn"""
        command = turn.translated_command

        if not command:
            return self._generate_error_response("I couldn't understand your request.", turn)

        # Check if clarification is needed
        if command.intent == Intent.UNKNOWN or turn.intent_result.clarification_needed:
            return self._generate_clarification_response(turn)

        # Check if confirmation is needed
        if command.requires_confirmation:
            return self._generate_confirmation_response(turn)

        # Check prerequisites
        if command.prerequisites:
            return self._generate_prerequisite_response(turn)

        # Generate execution response
        return self._generate_execution_response(turn)

    def _generate_clarification_response(self, turn: ConversationTurn) -> Dict[str, Any]:
        """Generate response asking for clarification"""
        self.current_state = ConversationState.CLARIFYING

        questions = []
        if turn.intent_result and turn.intent_result.clarification_questions:
            questions = turn.intent_result.clarification_questions
        else:
            # Generate questions based on intent
            questions = self._generate_context_questions(turn)

        # Create pending action for follow-up
        if turn.translated_command:
            action_id = str(uuid.uuid4())
            self.pending_actions[action_id] = PendingAction(
                action_id=action_id,
                command=turn.translated_command,
                created_at=datetime.now(),
                awaiting='clarification',
                clarification_questions=questions
            )

        response_text = questions[0] if questions else "Could you provide more details about what you'd like me to do?"

        # Add helpful suggestions
        suggestions = self._generate_clarification_suggestions(turn)

        turn.system_response = response_text
        turn.dialog_type = DialogType.CLARIFICATION

        return {
            'response': response_text,
            'conversation_state': self.current_state.value,
            'actions': [],
            'requires_input': True,
            'suggestions': suggestions,
            'clarification_questions': questions
        }

    def _generate_confirmation_response(self, turn: ConversationTurn) -> Dict[str, Any]:
        """Generate response asking for confirmation"""
        self.current_state = ConversationState.CONFIRMING

        command = turn.translated_command
        safety_level = command.safety_level

        # Choose template based on safety level
        if safety_level == 'dangerous':
            template_key = 'high_risk'
        elif safety_level == 'moderate':
            template_key = 'moderate_risk'
        else:
            template_key = 'safe_operation'

        response_text = self.response_templates['confirmation'][template_key].format(
            action_description=command.explanation
        )

        # Add command preview
        response_text += f"\n\nCommand: `{command.primary_command}`"

        # Create pending action
        action_id = str(uuid.uuid4())
        self.pending_actions[action_id] = PendingAction(
            action_id=action_id,
            command=command,
            created_at=datetime.now(),
            awaiting='confirmation'
        )

        turn.system_response = response_text
        turn.dialog_type = DialogType.CONFIRMATION

        return {
            'response': response_text,
            'conversation_state': self.current_state.value,
            'actions': [{'type': 'await_confirmation', 'action_id': action_id}],
            'requires_input': True,
            'command_preview': command.primary_command
        }

    def _generate_prerequisite_response(self, turn: ConversationTurn) -> Dict[str, Any]:
        """Generate response about missing prerequisites"""
        command = turn.translated_command
        prerequisites = command.prerequisites

        response_parts = ["I'd like to help, but there are a few things to check first:"]
        response_parts.extend([f"• {prereq}" for prereq in prerequisites])

        # Add suggestions for resolving prerequisites
        suggestions = []
        for prereq in prerequisites:
            if "Switch to" in prereq and "mode" in prereq:
                mode_name = prereq.split()[-2]  # Extract mode name
                suggestions.append(f"Switch to {mode_name} mode")
            elif "File does not exist" in prereq:
                suggestions.append("Check the file path or create the file")
            elif "Not in a git repository" in prereq:
                suggestions.append("Initialize git repository or navigate to a git project")

        response_text = "\n".join(response_parts)
        turn.system_response = response_text
        turn.dialog_type = DialogType.GUIDANCE

        return {
            'response': response_text,
            'conversation_state': self.current_state.value,
            'actions': [],
            'requires_input': False,
            'suggestions': suggestions
        }

    def _generate_execution_response(self, turn: ConversationTurn) -> Dict[str, Any]:
        """Generate response for immediate execution"""
        self.current_state = ConversationState.EXECUTING

        command = turn.translated_command
        response_text = self.response_templates['execution']['starting'].format(
            action_description=command.explanation
        )

        # Add follow-up suggestions
        followups = command.suggested_followups

        turn.system_response = response_text
        turn.dialog_type = DialogType.COMMAND_REQUEST

        self.current_state = ConversationState.LISTENING

        return {
            'response': response_text,
            'conversation_state': self.current_state.value,
            'actions': [{'type': 'execute_command', 'command': command.primary_command}],
            'requires_input': False,
            'suggestions': followups,
            'command': command.primary_command
        }

    def _generate_error_response(self, error_message: str, turn: ConversationTurn) -> Dict[str, Any]:
        """Generate error response with helpful guidance"""
        self.current_state = ConversationState.ERROR_HANDLING

        response_text = self.response_templates['execution']['error'].format(
            error_details=error_message
        )

        suggestions = [
            "Try rephrasing your request",
            "Use /help to see available commands",
            "Ask me what I can do"
        ]

        turn.system_response = response_text
        turn.dialog_type = DialogType.ERROR_RECOVERY
        turn.success = False
        turn.error_message = error_message

        return {
            'response': response_text,
            'conversation_state': self.current_state.value,
            'actions': [],
            'requires_input': False,
            'suggestions': suggestions
        }

    def _build_nlp_context(self) -> Dict[str, Any]:
        """Build context for NLP processing"""
        return {
            'current_files': list(self.context_info.available_files),
            'mentioned_files': list(self.conversation_context.mentioned_files),
            'recent_commands': self.conversation_context.recent_commands[-5:],
            'current_mode': self.context_info.current_mode.value,
            'project_type': self.context_info.project_type
        }

    def _update_context_from_system(self, system_context: Dict[str, Any]):
        """Update conversation context from system state"""
        if 'current_directory' in system_context:
            self.context_info.current_directory = system_context['current_directory']

        if 'available_files' in system_context:
            self.context_info.available_files = system_context['available_files']

        if 'current_mode' in system_context:
            self.context_info.current_mode = OperationMode(system_context['current_mode'])

        if 'project_type' in system_context:
            self.context_info.project_type = system_context['project_type']

        if 'git_status' in system_context:
            self.context_info.git_status = system_context['git_status']

    def _update_conversation_context(self, turn: ConversationTurn):
        """Update conversation context based on the turn"""
        # Update mentioned files
        if turn.translated_command and 'primary_file' in turn.translated_command.parameters:
            self.conversation_context.mentioned_files.add(
                turn.translated_command.parameters['primary_file']
            )

        # Update recent commands
        if turn.translated_command:
            self.conversation_context.recent_commands.append(turn.translated_command.primary_command)
            # Keep only last 10 commands
            self.conversation_context.recent_commands = self.conversation_context.recent_commands[-10:]

        # Track success/error patterns
        if turn.success:
            pattern = f"{turn.intent_result.intent.value if turn.intent_result else 'unknown'}"
            if pattern not in self.conversation_context.success_patterns:
                self.conversation_context.success_patterns.append(pattern)
        else:
            pattern = f"{turn.intent_result.intent.value if turn.intent_result else 'unknown'}:{turn.error_message}"
            if pattern not in self.conversation_context.error_patterns:
                self.conversation_context.error_patterns.append(pattern)

    def _cleanup_expired_actions(self):
        """Remove expired pending actions"""
        current_time = datetime.now()
        expired_actions = []

        for action_id, action in self.pending_actions.items():
            if current_time - action.created_at > timedelta(minutes=action.timeout_minutes):
                expired_actions.append(action_id)

        for action_id in expired_actions:
            del self.pending_actions[action_id]

    def _get_mode_capabilities(self, mode: OperationMode) -> str:
        """Get human-readable description of mode capabilities"""
        capabilities = {
            OperationMode.CHAT: "answer questions, analyze code, and provide guidance without making changes",
            OperationMode.PROPOSE: "create plans, design solutions, and prepare for code modifications",
            OperationMode.EXECUTE: "make code changes, fix bugs, generate files, and run commands"
        }
        return capabilities.get(mode, "assist with your coding tasks")

    def _get_welcome_suggestions(self) -> List[str]:
        """Get welcome suggestions based on context"""
        suggestions = [
            "Analyze my code quality",
            "Help me fix bugs",
            "Explain how my code works",
            "Show me what commands are available"
        ]

        # Add context-specific suggestions
        if self.context_info.available_files:
            if any(f.endswith('.py') for f in self.context_info.available_files):
                suggestions.insert(0, "Review my Python code")

        return suggestions

    def _generate_context_questions(self, turn: ConversationTurn) -> List[str]:
        """Generate context-appropriate clarification questions"""
        questions = []

        if turn.intent_result and turn.intent_result.intent != Intent.UNKNOWN:
            intent_questions = self.clarification_strategies.get(turn.intent_result.intent, {})

            # Check what's missing and ask appropriate questions
            if 'primary_file' not in turn.translated_command.parameters:
                if self.context_info.available_files:
                    file_list = ", ".join(self.context_info.available_files[:5])
                    questions.append(f"Which file should I work with? I can see: {file_list}")
                else:
                    questions.append("Which file would you like me to work on?")

            # Add intent-specific questions
            for condition, question in intent_questions.items():
                if condition == 'missing_requirements' and turn.intent_result.intent == Intent.COMPLETE_CODE:
                    questions.append(question)

        if not questions:
            questions.append("Could you provide more details about what you'd like me to do?")

        return questions

    def _generate_clarification_suggestions(self, turn: ConversationTurn) -> List[str]:
        """Generate helpful suggestions for clarification"""
        suggestions = []

        if self.context_info.available_files:
            suggestions.extend(self.context_info.available_files[:3])

        # Add common actions
        suggestions.extend([
            "analyze code",
            "fix bugs",
            "write tests",
            "explain code"
        ])

        return suggestions

    def _execute_confirmed_action(self, turn: ConversationTurn) -> Dict[str, Any]:
        """Execute a confirmed action"""
        if not self.pending_actions:
            return self._generate_error_response("No pending action to execute.", turn)

        # Get the most recent pending action
        action_id = list(self.pending_actions.keys())[-1]
        pending_action = self.pending_actions.pop(action_id)

        turn.translated_command = pending_action.command
        self.current_state = ConversationState.EXECUTING

        response_text = f"Executing: {pending_action.command.explanation}"
        turn.system_response = response_text

        self.current_state = ConversationState.LISTENING

        return {
            'response': response_text,
            'conversation_state': self.current_state.value,
            'actions': [{'type': 'execute_command', 'command': pending_action.command.primary_command}],
            'requires_input': False,
            'command': pending_action.command.primary_command
        }

    def _cancel_pending_action(self, turn: ConversationTurn) -> Dict[str, Any]:
        """Cancel a pending action"""
        if self.pending_actions:
            action_id = list(self.pending_actions.keys())[-1]
            self.pending_actions.pop(action_id)

        self.current_state = ConversationState.LISTENING

        response_text = "Okay, I've cancelled that action. What else can I help you with?"
        turn.system_response = response_text

        return {
            'response': response_text,
            'conversation_state': self.current_state.value,
            'actions': [],
            'requires_input': False,
            'suggestions': self._get_welcome_suggestions()
        }

    def _ask_for_clear_confirmation(self, turn: ConversationTurn) -> Dict[str, Any]:
        """Ask for a clearer confirmation"""
        response_text = "I'm not sure if you want me to proceed or not. Please say 'yes' to continue or 'no' to cancel."
        turn.system_response = response_text

        return {
            'response': response_text,
            'conversation_state': self.current_state.value,
            'actions': [],
            'requires_input': True,
            'suggestions': ['Yes, proceed', 'No, cancel']
        }

    def _enhance_input_with_clarification(self, user_input: str) -> str:
        """Enhance user input with context from previous clarification"""
        # For now, just return the input as-is
        # In the future, this could merge context from the pending action
        return user_input

    def _process_clarification_response(self, user_input: str, pending_action: PendingAction, turn: ConversationTurn) -> Dict[str, Any]:
        """Process response to clarification"""
        # Remove the pending action
        if pending_action.action_id in self.pending_actions:
            del self.pending_actions[pending_action.action_id]

        # Try to enhance the original command with the clarification
        enhanced_input = f"{pending_action.command.original_input} {user_input}"

        # Re-process with the enhanced input
        return self._process_normal_input(turn)

    def _process_confirmation_response(self, user_input: str, pending_action: PendingAction, turn: ConversationTurn) -> Dict[str, Any]:
        """Process response to confirmation"""
        return self._handle_confirmation_response(user_input, turn)

    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get a summary of the current conversation"""
        return {
            'session_id': self.conversation_context.session_id,
            'total_turns': len(self.conversation_history),
            'current_state': self.current_state.value,
            'pending_actions': len(self.pending_actions),
            'mentioned_files': list(self.conversation_context.mentioned_files),
            'recent_commands': self.conversation_context.recent_commands[-5:],
            'success_rate': self._calculate_success_rate()
        }

    def _calculate_success_rate(self) -> float:
        """Calculate success rate of recent interactions"""
        if not self.conversation_history:
            return 1.0

        recent_turns = self.conversation_history[-10:]  # Last 10 turns
        successful_turns = sum(1 for turn in recent_turns if turn.success)
        return successful_turns / len(recent_turns)


# Test function
def test_conversation_manager():
    """Test the conversation manager with sample dialogs"""
    manager = ConversationManager()

    test_conversations = [
        "Hello!",
        "I need to fix some bugs",
        "main.py",
        "yes",
        "Thanks! Can you also write tests?",
        "for the main.py file",
        "sure"
    ]

    for user_input in test_conversations:
        print(f"\nUser: {user_input}")
        response = manager.process_user_input(user_input)
        print(f"TinyCode: {response['response']}")
        if response.get('suggestions'):
            print(f"Suggestions: {response['suggestions'][:3]}")
        print(f"State: {response['conversation_state']}")


if __name__ == "__main__":
    test_conversation_manager()
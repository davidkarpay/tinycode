"""
Intelligent Mode Manager for TinyCode

This module provides intelligent mode management with natural language explanations,
automatic mode suggestions, and enhanced safety prompts for mode transitions.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from datetime import datetime, timedelta

from .mode_manager import OperationMode, ModeManager
from .nlp_interface import Intent
from .command_registry import CommandRegistry, DangerLevel


class ModeTransitionReason(Enum):
    """Reasons for suggesting mode transitions"""
    INTENT_REQUIRES_MODE = "intent_requires_mode"
    SAFETY_UPGRADE = "safety_upgrade"
    WORKFLOW_OPTIMIZATION = "workflow_optimization"
    USER_PATTERN = "user_pattern"
    PERMISSION_NEEDED = "permission_needed"


@dataclass
class ModeTransition:
    """A suggested or required mode transition"""
    from_mode: OperationMode
    to_mode: OperationMode
    reason: ModeTransitionReason
    urgency: str  # "required", "recommended", "optional"
    explanation: str
    benefits: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    auto_approve: bool = False


@dataclass
class SafetyPrompt:
    """Enhanced safety prompt for mode transitions"""
    message: str
    warning_level: str  # "info", "caution", "warning", "danger"
    consequences: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    user_confirmation_required: bool = True


class IntelligentModeManager:
    """Intelligent mode management with natural language support"""

    def __init__(self, base_mode_manager: ModeManager):
        self.base_manager = base_mode_manager
        self.command_registry = CommandRegistry()
        self.mode_history: List[Tuple[OperationMode, datetime]] = []
        self.transition_patterns: Dict[str, int] = {}
        self.safety_config = self._initialize_safety_config()
        self.mode_explanations = self._initialize_mode_explanations()
        self.transition_guides = self._initialize_transition_guides()

    def _initialize_safety_config(self) -> Dict[str, Dict[str, Any]]:
        """Initialize safety configuration for different transitions"""
        return {
            'chat_to_propose': {
                'warning_level': 'info',
                'auto_approve': True,
                'explanation': "Switching to planning mode to help you design solutions"
            },
            'chat_to_execute': {
                'warning_level': 'caution',
                'auto_approve': False,
                'explanation': "Execute mode can modify files and run commands",
                'consequences': [
                    "Files may be modified",
                    "Code may be executed",
                    "System commands may run"
                ],
                'recommendations': [
                    "Consider using Propose mode first to plan changes",
                    "Ensure you have backups of important files",
                    "Review what will be executed before confirming"
                ]
            },
            'propose_to_execute': {
                'warning_level': 'info',
                'auto_approve': True,
                'explanation': "Moving to execute mode to implement your approved plans"
            },
            'execute_to_chat': {
                'warning_level': 'info',
                'auto_approve': True,
                'explanation': "Returning to safe chat mode"
            },
            'propose_to_chat': {
                'warning_level': 'info',
                'auto_approve': True,
                'explanation': "Returning to safe chat mode"
            },
            'execute_to_propose': {
                'warning_level': 'info',
                'auto_approve': False,
                'explanation': "Switching to planning mode to design your next steps"
            }
        }

    def _initialize_mode_explanations(self) -> Dict[OperationMode, Dict[str, Any]]:
        """Initialize natural language explanations for each mode"""
        return {
            OperationMode.CHAT: {
                'name': 'Chat Mode',
                'description': 'Safe exploration and learning mode',
                'capabilities': [
                    'Ask questions and get explanations',
                    'Analyze code without making changes',
                    'Review files and get insights',
                    'Learn about best practices',
                    'Explore project structure'
                ],
                'limitations': [
                    'Cannot modify files',
                    'Cannot execute code',
                    'Cannot make system changes'
                ],
                'best_for': [
                    'Learning and understanding code',
                    'Getting explanations and guidance',
                    'Safe exploration of projects',
                    'Code reviews and analysis'
                ],
                'safety_level': 'Completely safe - no changes made',
                'icon': '💬',
                'color': 'green'
            },
            OperationMode.PROPOSE: {
                'name': 'Propose Mode',
                'description': 'Planning and design mode',
                'capabilities': [
                    'Create detailed execution plans',
                    'Design solutions and architectures',
                    'Plan multi-step changes',
                    'Review and approve plans',
                    'Estimate impacts and risks'
                ],
                'limitations': [
                    'Cannot execute plans automatically',
                    'Cannot modify files directly',
                    'Plans require approval to execute'
                ],
                'best_for': [
                    'Planning complex changes',
                    'Designing new features',
                    'Thinking through solutions',
                    'Collaborative planning'
                ],
                'safety_level': 'Safe - creates plans but no execution',
                'icon': '📋',
                'color': 'yellow'
            },
            OperationMode.EXECUTE: {
                'name': 'Execute Mode',
                'description': 'Full execution mode with safety checks',
                'capabilities': [
                    'Modify and create files',
                    'Execute code and commands',
                    'Implement approved plans',
                    'Make system changes',
                    'Perform git operations'
                ],
                'limitations': [
                    'Requires confirmation for risky operations',
                    'Automatic backups are created',
                    'Some operations have safety timeouts'
                ],
                'best_for': [
                    'Implementing solutions',
                    'Making code changes',
                    'Running tests and builds',
                    'Automated workflows'
                ],
                'safety_level': 'Controlled - automatic backups and confirmations',
                'icon': '⚡',
                'color': 'blue'
            }
        }

    def _initialize_transition_guides(self) -> Dict[str, Dict[str, str]]:
        """Initialize guides for mode transitions"""
        return {
            'chat_to_propose': {
                'when': "When you want to plan changes or design solutions",
                'why': "Propose mode helps you think through complex changes before implementing them",
                'how': "Say something like 'help me plan this feature' or 'I want to design a solution'"
            },
            'chat_to_execute': {
                'when': "When you're ready to make changes immediately",
                'why': "Execute mode lets you modify files and run commands",
                'how': "Say 'fix this bug' or 'implement this feature' for immediate action"
            },
            'propose_to_execute': {
                'when': "When you've approved a plan and want to implement it",
                'why': "Execute mode implements the plans you've created and approved",
                'how': "Approve your plan and say 'let's implement this' or 'execute the plan'"
            },
            'execute_to_propose': {
                'when': "When you want to plan your next steps after making changes",
                'why': "Propose mode helps you plan what to do next",
                'how': "Say 'what should I do next' or 'help me plan the next steps'"
            },
            'any_to_chat': {
                'when': "When you want to safely explore or ask questions",
                'why': "Chat mode is completely safe for learning and exploration",
                'how': "Say 'let me explore safely' or 'I want to understand this better'"
            }
        }

    def suggest_mode_transition(self,
                              current_intent: Intent,
                              current_context: Dict[str, Any],
                              command_danger_level: DangerLevel) -> Optional[ModeTransition]:
        """
        Suggest appropriate mode transition based on intent and context

        Args:
            current_intent: User's intended action
            current_context: Current system context
            command_danger_level: Danger level of the intended command

        Returns:
            ModeTransition suggestion or None if no transition needed
        """
        current_mode = self.base_manager.current_mode

        # Determine required mode based on intent
        required_mode = self._get_required_mode_for_intent(current_intent, command_danger_level)

        if required_mode and required_mode != current_mode:
            # Create transition recommendation
            transition = self._create_transition_recommendation(
                current_mode, required_mode, current_intent, command_danger_level
            )
            return transition

        # Check for workflow optimization opportunities
        optimization_transition = self._suggest_workflow_optimization(
            current_mode, current_intent, current_context
        )

        return optimization_transition

    def _get_required_mode_for_intent(self, intent: Intent, danger_level: DangerLevel) -> Optional[OperationMode]:
        """Determine the required mode for a given intent"""
        # Intents that require execute mode
        execute_intents = {
            Intent.FIX_BUGS, Intent.COMPLETE_CODE, Intent.REFACTOR_CODE,
            Intent.GENERATE_TESTS, Intent.RUN_CODE, Intent.CREATE_FILE,
            Intent.EDIT_FILE, Intent.DELETE_FILE, Intent.GIT_COMMIT,
            Intent.GIT_PUSH, Intent.GIT_PULL
        }

        # Intents that work well in propose mode
        propose_intents = {
            Intent.CREATE_PROJECT, Intent.SETUP_PROJECT, Intent.BUILD_PROJECT
        }

        # High danger operations always need execute mode with confirmation
        if danger_level in [DangerLevel.HIGH, DangerLevel.CRITICAL]:
            return OperationMode.EXECUTE

        if intent in execute_intents:
            return OperationMode.EXECUTE
        elif intent in propose_intents:
            return OperationMode.PROPOSE

        # Default: Chat mode is sufficient
        return None

    def _create_transition_recommendation(self,
                                        from_mode: OperationMode,
                                        to_mode: OperationMode,
                                        intent: Intent,
                                        danger_level: DangerLevel) -> ModeTransition:
        """Create a mode transition recommendation"""
        transition_key = f"{from_mode.value}_to_{to_mode.value}"
        safety_config = self.safety_config.get(transition_key, {})

        # Determine urgency based on intent and danger level
        if danger_level == DangerLevel.CRITICAL:
            urgency = "required"
        elif intent in [Intent.FIX_BUGS, Intent.COMPLETE_CODE]:
            urgency = "recommended"
        else:
            urgency = "optional"

        # Get benefits and risks
        benefits = self._get_transition_benefits(from_mode, to_mode, intent)
        risks = self._get_transition_risks(from_mode, to_mode, danger_level)

        # Create explanation
        explanation = self._create_transition_explanation(from_mode, to_mode, intent)

        return ModeTransition(
            from_mode=from_mode,
            to_mode=to_mode,
            reason=ModeTransitionReason.INTENT_REQUIRES_MODE,
            urgency=urgency,
            explanation=explanation,
            benefits=benefits,
            risks=risks,
            auto_approve=safety_config.get('auto_approve', False)
        )

    def _get_transition_benefits(self, from_mode: OperationMode, to_mode: OperationMode, intent: Intent) -> List[str]:
        """Get benefits of the mode transition"""
        to_mode_info = self.mode_explanations[to_mode]
        benefits = []

        if to_mode == OperationMode.EXECUTE:
            benefits.extend([
                "Can make actual changes to fix issues",
                "Can implement solutions immediately",
                "Can run tests and verify results"
            ])
        elif to_mode == OperationMode.PROPOSE:
            benefits.extend([
                "Can plan changes systematically",
                "Can review and approve plans before execution",
                "Can design complex solutions step-by-step"
            ])
        elif to_mode == OperationMode.CHAT:
            benefits.extend([
                "Completely safe exploration",
                "Can ask questions without risk",
                "Can analyze code without modifications"
            ])

        return benefits

    def _get_transition_risks(self, from_mode: OperationMode, to_mode: OperationMode, danger_level: DangerLevel) -> List[str]:
        """Get risks of the mode transition"""
        risks = []

        if to_mode == OperationMode.EXECUTE:
            risks.extend([
                "Files may be modified",
                "Code execution may have side effects"
            ])

            if danger_level in [DangerLevel.HIGH, DangerLevel.CRITICAL]:
                risks.extend([
                    "High-risk operations may be performed",
                    "Changes may be difficult to reverse"
                ])

        return risks

    def _create_transition_explanation(self, from_mode: OperationMode, to_mode: OperationMode, intent: Intent) -> str:
        """Create natural language explanation for the transition"""
        to_mode_info = self.mode_explanations[to_mode]
        intent_descriptions = {
            Intent.FIX_BUGS: "fix bugs",
            Intent.COMPLETE_CODE: "complete code",
            Intent.REFACTOR_CODE: "refactor code",
            Intent.GENERATE_TESTS: "generate tests",
            Intent.RUN_CODE: "run code",
            Intent.ANALYZE_CODE: "analyze code",
            Intent.EXPLAIN_CODE: "explain code"
        }

        intent_desc = intent_descriptions.get(intent, "perform this action")

        if to_mode == OperationMode.EXECUTE:
            return f"To {intent_desc}, I need to switch to Execute mode where I can make actual changes to your files."
        elif to_mode == OperationMode.PROPOSE:
            return f"To {intent_desc} effectively, let's switch to Propose mode where I can plan the approach first."
        else:
            return f"Switching to {to_mode_info['name']} for safe {intent_desc}."

    def _suggest_workflow_optimization(self,
                                     current_mode: OperationMode,
                                     intent: Intent,
                                     context: Dict[str, Any]) -> Optional[ModeTransition]:
        """Suggest mode transitions for workflow optimization"""
        # If user is trying to analyze in execute mode, suggest chat mode for safety
        if (current_mode == OperationMode.EXECUTE and
            intent in [Intent.ANALYZE_CODE, Intent.EXPLAIN_CODE, Intent.ASK_QUESTION]):

            return ModeTransition(
                from_mode=current_mode,
                to_mode=OperationMode.CHAT,
                reason=ModeTransitionReason.WORKFLOW_OPTIMIZATION,
                urgency="recommended",
                explanation="For safe code analysis, Chat mode is more appropriate and just as effective.",
                benefits=["Completely safe analysis", "No risk of accidental changes"],
                risks=[],
                auto_approve=True
            )

        return None

    def create_safety_prompt(self, transition: ModeTransition) -> SafetyPrompt:
        """Create an enhanced safety prompt for mode transition"""
        transition_key = f"{transition.from_mode.value}_to_{transition.to_mode.value}"
        safety_config = self.safety_config.get(transition_key, {})

        warning_level = safety_config.get('warning_level', 'info')
        consequences = safety_config.get('consequences', transition.risks)
        recommendations = safety_config.get('recommendations', [])

        # Create main message
        if transition.urgency == "required":
            message = f"🔄 I need to switch to {transition.to_mode.value.title()} mode to {transition.explanation.lower()}"
        elif transition.urgency == "recommended":
            message = f"💡 I recommend switching to {transition.to_mode.value.title()} mode. {transition.explanation}"
        else:
            message = f"ℹ️  You might want to switch to {transition.to_mode.value.title()} mode. {transition.explanation}"

        return SafetyPrompt(
            message=message,
            warning_level=warning_level,
            consequences=consequences,
            recommendations=recommendations,
            user_confirmation_required=not transition.auto_approve
        )

    def execute_mode_transition(self, transition: ModeTransition) -> bool:
        """Execute the mode transition with appropriate safety checks"""
        # Record the transition
        self._record_transition_attempt(transition)

        try:
            # Execute the transition
            self.base_manager.switch_mode(transition.to_mode)

            # Record successful transition
            self.mode_history.append((transition.to_mode, datetime.now()))
            self._update_transition_patterns(transition, success=True)

            return True

        except Exception as e:
            self._update_transition_patterns(transition, success=False)
            raise e

    def _record_transition_attempt(self, transition: ModeTransition):
        """Record attempt for analytics and learning"""
        transition_key = f"{transition.from_mode.value}_to_{transition.to_mode.value}"
        current_count = self.transition_patterns.get(transition_key, 0)
        self.transition_patterns[transition_key] = current_count + 1

    def _update_transition_patterns(self, transition: ModeTransition, success: bool):
        """Update transition patterns for learning"""
        # This could be expanded to learn user preferences and optimize suggestions
        pass

    def get_mode_explanation(self, mode: OperationMode) -> Dict[str, Any]:
        """Get comprehensive explanation of a mode"""
        return self.mode_explanations.get(mode, {})

    def get_current_mode_status(self) -> Dict[str, Any]:
        """Get current mode status with natural language description"""
        current_mode = self.base_manager.current_mode
        mode_info = self.mode_explanations[current_mode]

        return {
            'current_mode': current_mode.value,
            'name': mode_info['name'],
            'description': mode_info['description'],
            'icon': mode_info['icon'],
            'safety_level': mode_info['safety_level'],
            'capabilities': mode_info['capabilities'],
            'limitations': mode_info['limitations'],
            'time_in_mode': self._get_time_in_current_mode()
        }

    def _get_time_in_current_mode(self) -> str:
        """Get how long we've been in current mode"""
        if not self.mode_history:
            return "Unknown"

        last_transition = self.mode_history[-1]
        current_mode, transition_time = last_transition

        if current_mode == self.base_manager.current_mode:
            duration = datetime.now() - transition_time
            if duration.total_seconds() < 60:
                return "Just now"
            elif duration.total_seconds() < 3600:
                return f"{int(duration.total_seconds() // 60)} minutes"
            else:
                return f"{int(duration.total_seconds() // 3600)} hours"

        return "Unknown"

    def suggest_next_mode_actions(self, current_mode: OperationMode) -> List[str]:
        """Suggest what users can do in the current mode"""
        mode_info = self.mode_explanations[current_mode]

        suggestions = []
        if current_mode == OperationMode.CHAT:
            suggestions = [
                "Ask me to analyze your code",
                "Get explanations about how things work",
                "Review files safely without changes",
                "Switch to Propose mode to plan changes"
            ]
        elif current_mode == OperationMode.PROPOSE:
            suggestions = [
                "Ask me to plan a new feature",
                "Design a solution step-by-step",
                "Create an execution plan",
                "Switch to Execute mode to implement plans"
            ]
        elif current_mode == OperationMode.EXECUTE:
            suggestions = [
                "Fix bugs in your code",
                "Implement new features",
                "Run tests and builds",
                "Switch to Chat mode for safe exploration"
            ]

        return suggestions

    def format_mode_transition_message(self, transition: ModeTransition, safety_prompt: SafetyPrompt) -> str:
        """Format a comprehensive mode transition message"""
        lines = []

        # Main message
        lines.append(safety_prompt.message)

        # Benefits
        if transition.benefits:
            lines.append("\n✅ **Benefits:**")
            for benefit in transition.benefits:
                lines.append(f"   • {benefit}")

        # Risks/consequences
        if safety_prompt.consequences:
            warning_emoji = {
                'info': 'ℹ️',
                'caution': '⚠️',
                'warning': '⚠️',
                'danger': '🚨'
            }.get(safety_prompt.warning_level, 'ℹ️')

            lines.append(f"\n{warning_emoji} **What this means:**")
            for consequence in safety_prompt.consequences:
                lines.append(f"   • {consequence}")

        # Recommendations
        if safety_prompt.recommendations:
            lines.append("\n💡 **Recommendations:**")
            for recommendation in safety_prompt.recommendations:
                lines.append(f"   • {recommendation}")

        return "\n".join(lines)


# Test function
def test_intelligent_mode_manager():
    """Test the intelligent mode manager"""
    from .mode_manager import ModeManager

    base_manager = ModeManager()
    intelligent_manager = IntelligentModeManager(base_manager)

    # Test mode transition suggestion
    print("Testing Intelligent Mode Manager")
    print("=" * 40)

    # Test different scenarios
    scenarios = [
        (Intent.FIX_BUGS, DangerLevel.MEDIUM),
        (Intent.ANALYZE_CODE, DangerLevel.NONE),
        (Intent.REFACTOR_CODE, DangerLevel.HIGH),
        (Intent.ASK_QUESTION, DangerLevel.NONE)
    ]

    for intent, danger_level in scenarios:
        print(f"\nScenario: {intent.value} (danger: {danger_level.value})")

        transition = intelligent_manager.suggest_mode_transition(
            intent, {}, danger_level
        )

        if transition:
            safety_prompt = intelligent_manager.create_safety_prompt(transition)
            message = intelligent_manager.format_mode_transition_message(
                transition, safety_prompt
            )
            print(f"Suggested transition: {transition.from_mode.value} → {transition.to_mode.value}")
            print(f"Urgency: {transition.urgency}")
            print(f"Message: {message[:100]}...")
        else:
            print("No mode transition suggested")

    # Test mode explanations
    print(f"\n\nMode Explanations:")
    for mode in OperationMode:
        explanation = intelligent_manager.get_mode_explanation(mode)
        print(f"\n{mode.value}: {explanation.get('description', 'No description')}")


if __name__ == "__main__":
    test_intelligent_mode_manager()
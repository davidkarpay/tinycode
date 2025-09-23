"""
Self-Awareness Module for TinyCode
Provides introspection capabilities and context about its own features
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum
import json
from pathlib import Path
from .command_registry import CommandRegistry
from .mode_manager import OperationMode

class FeatureCategory(Enum):
    """Categories of TinyCode features"""
    CODE_OPERATIONS = "code_operations"
    SAFETY = "safety"
    MODES = "modes"
    COMMANDS = "commands"
    ARCHITECTURE = "architecture"
    TOOLS = "tools"

@dataclass
class FeatureInfo:
    """Information about a TinyCode feature"""
    name: str
    category: FeatureCategory
    description: str
    how_to_use: str
    examples: List[str]
    related_features: List[str]

class SelfAwareness:
    """Provides self-awareness and introspection capabilities for TinyCode"""

    def __init__(self):
        self.features = self._initialize_features()
        self.system_prompt_addition = self._generate_system_prompt()
        # Dynamic command discovery
        self.command_registry = CommandRegistry()

    def _initialize_features(self) -> Dict[str, FeatureInfo]:
        """Initialize comprehensive feature database"""
        return {
            # Core Code Operations
            "code_completion": FeatureInfo(
                name="Code Completion",
                category=FeatureCategory.CODE_OPERATIONS,
                description="Generate code completions based on context and requirements",
                how_to_use="Use /complete command followed by your code snippet",
                examples=["/complete def calculate_sum("],
                related_features=["code_generation", "refactoring"]
            ),
            "bug_fixing": FeatureInfo(
                name="Bug Fixing",
                category=FeatureCategory.CODE_OPERATIONS,
                description="Identify and fix bugs in code",
                how_to_use="Use /fix command with the problematic code",
                examples=["/fix 'TypeError in line 42'"],
                related_features=["debugging", "code_review"]
            ),
            "code_refactoring": FeatureInfo(
                name="Code Refactoring",
                category=FeatureCategory.CODE_OPERATIONS,
                description="Improve code structure without changing functionality",
                how_to_use="Use /refactor command with target code",
                examples=["/refactor 'make this function more efficient'"],
                related_features=["optimization", "code_review"]
            ),
            "code_explanation": FeatureInfo(
                name="Code Explanation",
                category=FeatureCategory.CODE_OPERATIONS,
                description="Explain how code works in detail",
                how_to_use="Use /explain command with code snippet",
                examples=["/explain 'what does this regex do?'"],
                related_features=["documentation", "teaching"]
            ),
            "test_generation": FeatureInfo(
                name="Test Generation",
                category=FeatureCategory.CODE_OPERATIONS,
                description="Generate unit tests for your code",
                how_to_use="Use /test command with function or class",
                examples=["/test generate tests for UserAuth class"],
                related_features=["quality_assurance", "coverage"]
            ),

            # Modes
            "chat_mode": FeatureInfo(
                name="Chat Mode",
                category=FeatureCategory.MODES,
                description="Safe exploration and Q&A mode. Read-only access, no file modifications allowed",
                how_to_use="Use /mode chat to switch to this mode",
                examples=["/mode chat"],
                related_features=["safety", "exploration"]
            ),
            "propose_mode": FeatureInfo(
                name="Propose Mode",
                category=FeatureCategory.MODES,
                description="Plan generation and review mode. Create execution plans without executing them",
                how_to_use="Use /mode propose to switch, then /plan to create plans",
                examples=["/mode propose", "/plan 'refactor authentication module'"],
                related_features=["planning", "review"]
            ),
            "execute_mode": FeatureInfo(
                name="Execute Mode",
                category=FeatureCategory.MODES,
                description="Execute approved plans with full capabilities and safety checks",
                how_to_use="Use /mode execute to switch, then /execute_plan <id>",
                examples=["/mode execute", "/execute_plan abc123"],
                related_features=["execution", "safety_checks"]
            ),

            # Safety Features
            "safety_levels": FeatureInfo(
                name="Safety Levels",
                category=FeatureCategory.SAFETY,
                description="Four-tier safety system: PERMISSIVE, STANDARD, STRICT, PARANOID",
                how_to_use="Use /safety command to set level",
                examples=["/safety strict"],
                related_features=["confirmation", "backups"]
            ),
            "audit_logging": FeatureInfo(
                name="Audit Logging",
                category=FeatureCategory.SAFETY,
                description="Hash-chain integrity logging with tamper detection",
                how_to_use="Automatically enabled, logs stored in data/audit_logs/",
                examples=["All operations are logged automatically"],
                related_features=["security", "forensics"]
            ),
            "automatic_backups": FeatureInfo(
                name="Automatic Backups",
                category=FeatureCategory.SAFETY,
                description="Creates backups before risky file operations",
                how_to_use="Automatic for file modifications in execute mode",
                examples=["Backups stored in data/backups/"],
                related_features=["safety", "recovery"]
            ),
            "timeout_management": FeatureInfo(
                name="Timeout Management",
                category=FeatureCategory.SAFETY,
                description="Plan (5 min) and action (30 sec) level timeout controls",
                how_to_use="Configured in safety_config.py",
                examples=["Plans timeout after 5 minutes by default"],
                related_features=["resource_limits", "safety"]
            ),
            "dangerous_pattern_detection": FeatureInfo(
                name="Dangerous Pattern Detection",
                category=FeatureCategory.SAFETY,
                description="Pre-execution validation scans for dangerous patterns",
                how_to_use="Automatic validation before execution",
                examples=["Detects rm -rf, DROP TABLE, etc."],
                related_features=["validation", "security"]
            ),

            # Architecture
            "plan_based_execution": FeatureInfo(
                name="Plan-Based Execution",
                category=FeatureCategory.ARCHITECTURE,
                description="Creates detailed execution plans with risk assessment before acting",
                how_to_use="Use /plan command in propose mode",
                examples=["/plan 'implement user authentication'"],
                related_features=["planning", "validation", "execution"]
            ),
            "rag_system": FeatureInfo(
                name="RAG System",
                category=FeatureCategory.ARCHITECTURE,
                description="Retrieval-Augmented Generation with FAISS vector store",
                how_to_use="Use /rag command or python tiny_code_rag.py",
                examples=["/rag 'search for authentication patterns'"],
                related_features=["knowledge_base", "search", "context"]
            ),
            "command_registry": FeatureInfo(
                name="Command Registry",
                category=FeatureCategory.ARCHITECTURE,
                description="31 commands categorized by safety level (NONE to CRITICAL)",
                how_to_use="Use /commands to list all available commands",
                examples=["/commands", "/help <command>"],
                related_features=["commands", "permissions"]
            ),

            # Tools
            "file_operations": FeatureInfo(
                name="File Operations",
                category=FeatureCategory.TOOLS,
                description="Read, write, edit files with safety checks",
                how_to_use="Various commands like /read, /write, /edit",
                examples=["/read main.py", "/edit config.json"],
                related_features=["filesystem", "backups"]
            ),
            "resource_monitoring": FeatureInfo(
                name="Resource Monitoring",
                category=FeatureCategory.TOOLS,
                description="CPU, memory, and disk monitoring with enforcement",
                how_to_use="Automatic monitoring during execution",
                examples=["Monitors resource usage in real-time"],
                related_features=["performance", "limits"]
            ),
            "api_server": FeatureInfo(
                name="API Server",
                category=FeatureCategory.TOOLS,
                description="Flask-based REST API with Prometheus metrics",
                how_to_use="Run python api_server.py",
                examples=["POST /complete", "POST /fix"],
                related_features=["api", "metrics", "integration"]
            )
        }

    def get_capability_summary(self) -> str:
        """Get a comprehensive summary of all capabilities"""
        summary = "TinyCode Capabilities Summary:\n\n"

        for category in FeatureCategory:
            features = [f for f in self.features.values() if f.category == category]
            if features:
                summary += f"## {category.value.replace('_', ' ').title()}\n"
                for feature in features:
                    summary += f"- **{feature.name}**: {feature.description}\n"
                summary += "\n"

        return summary

    def get_commands_list(self, dynamic: bool = True) -> str:
        """Get a formatted list of commands

        Args:
            dynamic: If True, query the actual command registry. If False, use hardcoded list.
        """
        if dynamic:
            # Dynamically query the command registry for accurate list
            commands_by_mode = {
                'CHAT': [],
                'PROPOSE': [],
                'EXECUTE': []
            }

            for cmd_name, cmd_info in self.command_registry.commands.items():
                desc = cmd_info.description
                formatted = f"/{cmd_name} - {desc}"

                if cmd_info.allowed_in_chat:
                    commands_by_mode['CHAT'].append(formatted)
                if cmd_info.allowed_in_propose:
                    commands_by_mode['PROPOSE'].append(formatted)
                if cmd_info.allowed_in_execute:
                    commands_by_mode['EXECUTE'].append(formatted)

            result = "Available Commands (from Command Registry):\n\n"
            result += "**Commands in CHAT mode:**\n"
            result += "\n".join(sorted(commands_by_mode['CHAT']))
            result += "\n\n**Additional commands in PROPOSE mode:**\n"
            propose_only = set(commands_by_mode['PROPOSE']) - set(commands_by_mode['CHAT'])
            result += "\n".join(sorted(propose_only))
            result += "\n\n**Additional commands in EXECUTE mode:**\n"
            execute_only = set(commands_by_mode['EXECUTE']) - set(commands_by_mode['PROPOSE'])
            result += "\n".join(sorted(execute_only))

            return result
        else:
            # Fallback to hardcoded list (what's actually in CLI)
            implemented_commands = [
                "/help - Show help information",
                "/mode [chat|propose|execute] - Switch operation mode",
                "/file <path> - Load a file for processing",
                "/analyze <path> - Analyze a code file",
                "/explain <path> - Explain code in file",
                "/review <path> - Review code quality",
                "/workspace <path> - Set working directory",
                "/list [pattern] - List files in workspace",
                "/plan <description> - Create execution plan",
                "/preview <plan_id> - Preview a plan",
                "/approve <plan_id> - Approve a plan",
                "/reject <plan_id> - Reject a plan",
                "/show_plan <plan_id> - Show plan details",
                "/list_plans - List all plans",
                "/execute_plan <plan_id> - Execute approved plan",
                "/complete <path> - Complete code in file",
                "/fix <path> - Fix bugs in code",
                "/refactor <path> - Refactor code",
                "/test <path> - Generate tests",
                "/run <path> - Execute a Python file",
                "/save <path> - Save last response"
            ]

            return "Available Commands:\n" + "\n".join(implemented_commands)

    def get_modes_explanation(self) -> str:
        """Get detailed explanation of operation modes"""
        return """
TinyCode Operation Modes:

1. **CHAT Mode** (Default)
   - Safe exploration and Q&A
   - Read-only file access
   - No modifications allowed
   - Perfect for understanding code and asking questions

2. **PROPOSE Mode**
   - Plan generation and review
   - Create detailed execution plans
   - Review and refine plans before execution
   - No actual changes made

3. **EXECUTE Mode**
   - Execute approved plans
   - Full capabilities with safety checks
   - Automatic backups before changes
   - Confirmation required for dangerous operations

To switch modes: /mode <mode_name>
Current mode affects what commands are available.
"""

    def get_feature_details(self, feature_name: str) -> Optional[str]:
        """Get detailed information about a specific feature"""
        feature = self.features.get(feature_name)
        if not feature:
            # Try fuzzy matching
            for key, f in self.features.items():
                if feature_name.lower() in key.lower() or feature_name.lower() in f.name.lower():
                    feature = f
                    break

        if not feature:
            return None

        details = f"""
**{feature.name}**
Category: {feature.category.value}

Description:
{feature.description}

How to use:
{feature.how_to_use}

Examples:
{chr(10).join('  ' + ex for ex in feature.examples)}

Related features:
{', '.join(feature.related_features)}
"""
        return details

    def _generate_system_prompt(self) -> str:
        """Generate system prompt addition for better self-awareness"""
        return """
I am TinyCode, an AI coding assistant with FULL FILE SYSTEM ACCESS and code execution capabilities.

CRITICAL: I MUST ask clarifying questions before suggesting any actions. I should be thoughtful, not eager.

MY ACTUAL CAPABILITIES (I can DO these things):
✓ List, find, read, and analyze files (/list, /find, /file, /tree)
✓ Fix bugs, refactor, and complete code (/fix, /refactor, /complete)
✓ Execute Python scripts (/run)
✓ Perform git operations (/git-status, /git-log, /git-branches)
✓ Access system information (/env, /processes, /sysinfo)
✓ Generate and run tests (/test)
✓ Create execution plans (/plan)

REQUIRED BEHAVIOR - ASK QUESTIONS FIRST:
• "ls" or "list files" → I should ask: "What directory? Looking for specific files?"
• "show file" or "cat" → I should ask: "Which file? What do you want to understand?"
• "fix this" → I should ask: "What's the specific issue? Can you describe the bug?"
• "run this" → I should ask: "Which file? What should it do?"
• "what's here?" → I should ask: "Which directory? Are you exploring the project structure?"

OPERATION MODES I work in:
- CHAT: Read-only exploration (current default)
- PROPOSE: Create detailed plans for review
- EXECUTE: Full modification capabilities

I must understand the user's intent and context before suggesting any commands. Be helpful but deliberate.

When asked about my model or what I'm running on, I should clearly state the specific Ollama model I'm using. This information is provided in my system context.
"""

    def enhance_prompt(self, original_prompt: str) -> str:
        """Enhance a prompt with self-awareness context"""
        if any(keyword in original_prompt.lower() for keyword in
               ['capability', 'capabilities', 'can you', 'do you', 'feature',
                'command', 'mode', 'what are you', 'how do you']):
            return f"{original_prompt}\n\n{self._generate_system_prompt()}"
        return original_prompt

    def save_to_knowledge_base(self, path: str = "data/self_knowledge.json"):
        """Save self-awareness data to a knowledge base file"""
        Path(path).parent.mkdir(parents=True, exist_ok=True)

        knowledge = {
            "capabilities": self.get_capability_summary(),
            "commands": self.get_commands_list(),
            "modes": self.get_modes_explanation(),
            "features": {
                name: {
                    "category": f.category.value,
                    "description": f.description,
                    "how_to_use": f.how_to_use,
                    "examples": f.examples,
                    "related": f.related_features
                }
                for name, f in self.features.items()
            },
            "system_prompt": self._generate_system_prompt()
        }

        with open(path, 'w') as f:
            json.dump(knowledge, f, indent=2)

        return path


# Integration helper for TinyCodeAgent
class SelfAwareAgent:
    """Mixin to add self-awareness to TinyCodeAgent"""

    def __init__(self):
        self.self_awareness = SelfAwareness()
        super().__init__()

    def process_with_awareness(self, prompt: str) -> str:
        """Process prompt with self-awareness context"""
        # Check if asking about capabilities
        if self._is_capability_question(prompt):
            context = self._get_relevant_context(prompt)
            enhanced_prompt = f"{prompt}\n\nContext about my capabilities:\n{context}"
            return enhanced_prompt
        return prompt

    def _is_capability_question(self, prompt: str) -> bool:
        """Check if prompt is asking about capabilities"""
        capability_keywords = [
            'what can', 'can you', 'do you', 'capabilities',
            'features', 'commands', 'modes', 'how do',
            'what are your', 'list your', 'available',
            'what model', 'which model', 'model are you', 'running on',
            'powered by', 'llm are you', 'language model'
        ]
        return any(kw in prompt.lower() for kw in capability_keywords)

    def _get_relevant_context(self, prompt: str) -> str:
        """Get relevant capability context for prompt"""
        sa = self.self_awareness

        if 'command' in prompt.lower():
            return sa.get_commands_list()
        elif 'mode' in prompt.lower():
            return sa.get_modes_explanation()
        elif 'capabilit' in prompt.lower() or 'feature' in prompt.lower():
            return sa.get_capability_summary()
        else:
            # Return general summary
            return sa._generate_system_prompt()


if __name__ == "__main__":
    # Test self-awareness module
    sa = SelfAwareness()

    print("=" * 60)
    print("TINYCODER SELF-AWARENESS MODULE TEST")
    print("=" * 60)

    print("\n1. Capability Summary:")
    print(sa.get_capability_summary())

    print("\n2. Commands List:")
    print(sa.get_commands_list())

    print("\n3. Modes Explanation:")
    print(sa.get_modes_explanation())

    print("\n4. Feature Details (Plan-Based Execution):")
    print(sa.get_feature_details("plan_based_execution"))

    print("\n5. Saving knowledge base...")
    path = sa.save_to_knowledge_base()
    print(f"Knowledge base saved to: {path}")
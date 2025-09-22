"""Main agent logic for Tiny Code"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from .ollama_client import OllamaClient
from .tools import CodeTools
from .prompts import *
from .self_awareness import SelfAwareness

console = Console()

class TinyCodeAgent:
    """Main coding agent powered by TinyLlama"""

    def __init__(self, model: str = "tinyllama:latest", temperature: float = 0.7):
        self.client = OllamaClient(model=model, temperature=temperature)
        self.tools = CodeTools()
        self.conversation_context = None
        self.current_file = None
        self.workspace = Path.cwd()
        self.self_awareness = SelfAwareness()

    def complete_code(self, code_context: str, requirements: str = "") -> str:
        """Complete code based on context"""
        prompt = CODE_COMPLETION_PROMPT.format(
            code_context=code_context,
            requirements=requirements or "Complete the code logically"
        )

        response = self.client.generate(prompt, system=SYSTEM_PROMPT)
        return response

    def fix_bug(self, code: str, error: str) -> str:
        """Fix bugs in code"""
        prompt = BUG_FIX_PROMPT.format(code=code, error=error)
        response = self.client.generate(prompt, system=SYSTEM_PROMPT)
        return response

    def explain_code(self, code: str) -> str:
        """Explain what code does"""
        prompt = CODE_EXPLAIN_PROMPT.format(code=code)
        response = self.client.generate(prompt, system=SYSTEM_PROMPT)
        return response

    def refactor_code(self, code: str, requirements: str = "") -> str:
        """Refactor code for improvements"""
        prompt = REFACTOR_PROMPT.format(
            code=code,
            requirements=requirements or "General improvements"
        )
        response = self.client.generate(prompt, system=SYSTEM_PROMPT)
        return response

    def generate_tests(self, code: str) -> str:
        """Generate tests for code"""
        prompt = TEST_GENERATION_PROMPT.format(code=code)
        response = self.client.generate(prompt, system=SYSTEM_PROMPT)
        return response

    def review_code(self, code: str) -> str:
        """Review code and provide feedback"""
        prompt = CODE_REVIEW_PROMPT.format(code=code)
        response = self.client.generate(prompt, system=SYSTEM_PROMPT)
        return response

    def chat(self, message: str, stream: bool = False) -> str:
        """Interactive chat with the agent"""
        # Enhance message with self-awareness if asking about capabilities
        enhanced_message = message
        if self._is_capability_question(message):
            context = self._get_capability_context(message)
            enhanced_message = f"{message}\n\nContext about my capabilities:\n{context}"

        # Use enhanced system prompt with self-awareness
        enhanced_system = SYSTEM_PROMPT + "\n\n" + self.self_awareness._generate_system_prompt()

        if stream:
            response_text = ""
            for chunk in self.client.stream_generate(
                enhanced_message,
                system=enhanced_system
            ):
                response_text += chunk
                console.print(chunk, end="")
            return response_text
        else:
            return self.client.generate(
                enhanced_message,
                system=enhanced_system
            )

    def _is_capability_question(self, message: str) -> bool:
        """Check if message is asking about capabilities"""
        capability_keywords = [
            'what can', 'can you', 'do you', 'capabilities',
            'features', 'commands', 'modes', 'how do',
            'what are your', 'list your', 'available', 'support'
        ]
        return any(kw in message.lower() for kw in capability_keywords)

    def _get_capability_context(self, message: str) -> str:
        """Get relevant capability context for message"""
        msg_lower = message.lower()

        if 'command' in msg_lower:
            return self.self_awareness.get_commands_list()
        elif 'mode' in msg_lower:
            return self.self_awareness.get_modes_explanation()
        elif any(word in msg_lower for word in ['capability', 'capabilities', 'feature', 'features']):
            return self.self_awareness.get_capability_summary()
        else:
            return self.self_awareness._generate_system_prompt()

    def analyze_file(self, filepath: str) -> Dict[str, Any]:
        """Analyze a code file"""
        code = self.tools.read_file(filepath)
        if not code:
            return {"error": f"Could not read file: {filepath}"}

        analysis = {
            "filepath": filepath,
            "functions": self.tools.extract_functions(code),
            "classes": self.tools.extract_classes(code),
            "imports": self.tools.find_imports(code),
            "metrics": self.tools.analyze_complexity(code)
        }

        return analysis

    def process_file(self, filepath: str, operation: str, **kwargs) -> str:
        """Process a file with specified operation"""
        code = self.tools.read_file(filepath)
        if not code:
            return f"Error: Could not read file {filepath}"

        self.current_file = filepath

        operations = {
            'complete': self.complete_code,
            'fix': self.fix_bug,
            'explain': self.explain_code,
            'refactor': self.refactor_code,
            'test': self.generate_tests,
            'review': self.review_code,
            'analyze': lambda c: json.dumps(self.analyze_file(filepath), indent=2)
        }

        if operation not in operations:
            return f"Unknown operation: {operation}"

        if operation == 'fix':
            result = operations[operation](code, kwargs.get('error', ''))
        elif operation in ['complete', 'refactor']:
            result = operations[operation](code, kwargs.get('requirements', ''))
        elif operation == 'analyze':
            result = operations[operation](code)
        else:
            result = operations[operation](code)

        return result

    def execute_code(self, code: str, language: str = "python") -> Dict[str, Any]:
        """Execute code and return results"""
        console.print(Panel("Executing code...", style="yellow"))
        stdout, stderr, returncode = self.tools.run_code(code, language)

        result = {
            "success": returncode == 0,
            "stdout": stdout,
            "stderr": stderr,
            "returncode": returncode
        }

        if result["success"]:
            console.print(Panel(stdout or "Code executed successfully", style="green"))
        else:
            console.print(Panel(f"Error: {stderr}", style="red"))

        return result

    def save_response(self, response: str, filepath: Optional[str] = None) -> bool:
        """Save generated response to a file"""
        if not filepath:
            filepath = f"tiny_code_output_{Path(self.current_file).stem if self.current_file else 'response'}.py"

        return self.tools.write_file(filepath, response)

    def set_workspace(self, path: str) -> None:
        """Set the working directory"""
        self.workspace = Path(path)
        os.chdir(self.workspace)
        console.print(f"[green]Workspace set to: {self.workspace}[/green]")

    def list_files(self, pattern: str = "*.py") -> List[str]:
        """List files in workspace matching pattern"""
        files = list(self.workspace.glob(pattern))
        return [str(f.relative_to(self.workspace)) for f in files]
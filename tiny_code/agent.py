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
from .knowledge import CodeEvaluator, EvaluationResult

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
        self.code_evaluator = CodeEvaluator()

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

    def review_code(self, code: str, filepath: str = "", use_principles: bool = True) -> str:
        """Review code and provide feedback with optional principle-based evaluation"""
        if use_principles:
            # Use principle-based evaluation
            evaluation = self.code_evaluator.evaluate_code(code, filepath)

            # Format the evaluation result into a comprehensive review
            review_parts = []

            # Overall assessment
            review_parts.append(f"## Code Quality Assessment")
            review_parts.append(f"**Overall Score: {evaluation.overall_score:.1f}/10.0**")
            review_parts.append("")

            # Quality dimensions
            review_parts.append("### Quality Dimensions")
            for score in evaluation.quality_scores:
                status = "✅" if score.score >= 8.0 else "⚠️" if score.score >= 6.0 else "❌"
                review_parts.append(f"- {status} **{score.dimension.value.title()}**: {score.score:.1f}/10.0")
                if score.details:
                    review_parts.append(f"  - {score.details}")
            review_parts.append("")

            # Recommendations
            if evaluation.recommendations:
                review_parts.append("### Recommendations")
                for i, rec in enumerate(evaluation.recommendations, 1):
                    severity_icon = {"critical": "🚨", "high": "⚠️", "medium": "💡", "low": "📝"}
                    icon = severity_icon.get(rec.severity.value, "💡")
                    review_parts.append(f"{i}. {icon} **{rec.message}**")
                    if rec.suggested_fix:
                        review_parts.append(f"   - **Fix**: {rec.suggested_fix}")
                    if rec.rationale:
                        review_parts.append(f"   - **Why**: {rec.rationale}")
                    review_parts.append("")

            # Code metrics
            if evaluation.metrics:
                review_parts.append("### Code Metrics")
                metrics = evaluation.metrics
                review_parts.append(f"- Lines of Code: {metrics.lines_of_code}")
                review_parts.append(f"- Functions: {metrics.function_count}")
                review_parts.append(f"- Classes: {metrics.class_count}")
                review_parts.append(f"- Cyclomatic Complexity: {metrics.cyclomatic_complexity}")
                if metrics.max_function_length > 0:
                    review_parts.append(f"- Max Function Length: {metrics.max_function_length} lines")
                review_parts.append("")

            # Save evaluation for learning
            self.code_evaluator.save_evaluation_result(evaluation)

            principled_review = "\n".join(review_parts)

            # Also get LLM-based review for additional insights
            prompt = CODE_REVIEW_PROMPT.format(code=code)
            llm_review = self.client.generate(prompt, system=SYSTEM_PROMPT)

            # Combine both reviews
            combined_review = f"{principled_review}\n\n### Additional AI Analysis\n{llm_review}"
            return combined_review
        else:
            # Use traditional LLM-based review
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

        # Use enhanced system prompt with self-awareness and model info
        model_info = f"\n\nIMPORTANT: I am currently running on the {self.client.model} model via Ollama.\n"
        enhanced_system = SYSTEM_PROMPT + model_info + self.self_awareness._generate_system_prompt()

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
            'what are your', 'list your', 'available', 'support',
            'what model', 'which model', 'model are you', 'running on',
            'powered by', 'llm are you', 'language model'
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

    def evaluate_code_principles(self, code: str, filepath: str = "", focus_areas: Optional[List[str]] = None) -> EvaluationResult:
        """Evaluate code against software development principles"""
        # Convert string focus areas to PrincipleCategory enum if provided
        principle_categories = None
        if focus_areas:
            from .knowledge.software_principles import PrincipleCategory
            principle_categories = []
            for area in focus_areas:
                try:
                    category = PrincipleCategory(area.lower())
                    principle_categories.append(category)
                except ValueError:
                    console.print(f"[yellow]Warning: Unknown principle category '{area}'[/yellow]")

        return self.code_evaluator.evaluate_code(code, filepath, focus_areas=principle_categories)

    def get_principle_summary(self, category: Optional[str] = None) -> Dict[str, Any]:
        """Get summary of available software development principles"""
        if category:
            from .knowledge.software_principles import PrincipleCategory
            try:
                cat_enum = PrincipleCategory(category.lower())
                return self.code_evaluator.get_principle_summary(cat_enum)
            except ValueError:
                return {"error": f"Unknown principle category: {category}"}
        else:
            return self.code_evaluator.get_principle_summary()

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
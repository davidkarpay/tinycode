"""Code manipulation and analysis tools"""

import os
import ast
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from pygments import highlight
from pygments.lexers import get_lexer_for_filename, PythonLexer
from pygments.formatters import TerminalFormatter
from rich.console import Console
from rich.syntax import Syntax

console = Console()

class CodeTools:
    """Tools for code manipulation and analysis"""

    @staticmethod
    def read_file(filepath: str) -> str:
        """Read a file and return its contents"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            console.print(f"[red]Error reading file {filepath}: {e}[/red]")
            return ""

    @staticmethod
    def write_file(filepath: str, content: str) -> bool:
        """Write content to a file"""
        try:
            path = Path(filepath)
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            console.print(f"[green]Successfully wrote to {filepath}[/green]")
            return True
        except Exception as e:
            console.print(f"[red]Error writing to {filepath}: {e}[/red]")
            return False

    @staticmethod
    def display_code(code: str, language: str = "python") -> None:
        """Display code with syntax highlighting"""
        syntax = Syntax(code, language, theme="monokai", line_numbers=True)
        console.print(syntax)

    @staticmethod
    def extract_functions(code: str) -> List[Dict[str, Any]]:
        """Extract function definitions from Python code"""
        functions = []
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_info = {
                        'name': node.name,
                        'args': [arg.arg for arg in node.args.args],
                        'docstring': ast.get_docstring(node),
                        'lineno': node.lineno,
                        'col_offset': node.col_offset
                    }
                    functions.append(func_info)
        except SyntaxError as e:
            console.print(f"[red]Syntax error in code: {e}[/red]")
        return functions

    @staticmethod
    def extract_classes(code: str) -> List[Dict[str, Any]]:
        """Extract class definitions from Python code"""
        classes = []
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    methods = []
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            methods.append(item.name)

                    class_info = {
                        'name': node.name,
                        'methods': methods,
                        'docstring': ast.get_docstring(node),
                        'lineno': node.lineno,
                        'bases': [base.id if isinstance(base, ast.Name) else str(base)
                                 for base in node.bases]
                    }
                    classes.append(class_info)
        except SyntaxError as e:
            console.print(f"[red]Syntax error in code: {e}[/red]")
        return classes

    @staticmethod
    def run_code(code: str, language: str = "python") -> Tuple[str, str, int]:
        """Execute code and return output, errors, and return code"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py' if language == 'python' else '',
                                        delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            if language == "python":
                result = subprocess.run(
                    ['python', temp_file],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
            else:
                result = subprocess.run(
                    temp_file,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=30
                )

            return result.stdout, result.stderr, result.returncode
        except subprocess.TimeoutExpired:
            return "", "Code execution timed out after 30 seconds", 1
        except Exception as e:
            return "", str(e), 1
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)

    @staticmethod
    def find_imports(code: str) -> List[str]:
        """Extract import statements from Python code"""
        imports = []
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    for alias in node.names:
                        imports.append(f"{module}.{alias.name}" if module else alias.name)
        except SyntaxError:
            pass
        return imports

    @staticmethod
    def get_code_context(filepath: str, line_number: int, context_lines: int = 10) -> str:
        """Get code context around a specific line"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            start = max(0, line_number - context_lines - 1)
            end = min(len(lines), line_number + context_lines)

            context = []
            for i in range(start, end):
                prefix = ">>> " if i == line_number - 1 else "    "
                context.append(f"{i+1:4d}{prefix}{lines[i].rstrip()}")

            return '\n'.join(context)
        except Exception as e:
            return f"Error getting context: {e}"

    @staticmethod
    def analyze_complexity(code: str) -> Dict[str, Any]:
        """Analyze code complexity metrics"""
        try:
            tree = ast.parse(code)

            metrics = {
                'lines': len(code.splitlines()),
                'functions': 0,
                'classes': 0,
                'imports': 0,
                'max_nesting': 0
            }

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    metrics['functions'] += 1
                elif isinstance(node, ast.ClassDef):
                    metrics['classes'] += 1
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    metrics['imports'] += 1

            return metrics
        except SyntaxError:
            return {'error': 'Could not parse code'}
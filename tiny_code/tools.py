"""Code manipulation and analysis tools with sandboxing support"""

import os
import ast
import subprocess
import tempfile
import re
import glob
import difflib
import fnmatch
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple, Union, Iterator
from dataclasses import dataclass
from pygments import highlight
from pygments.lexers import get_lexer_for_filename, PythonLexer
from pygments.formatters import TerminalFormatter
from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table
from rich.tree import Tree

from .sandbox import PathValidator, SandboxConfig, SecurityError, create_default_sandbox

console = Console()

@dataclass
class SearchResult:
    """Represents a search result with file, line, and context"""
    file_path: str
    line_number: int
    line_content: str
    match_start: int
    match_end: int
    context_before: List[str]
    context_after: List[str]

@dataclass
class FileMatch:
    """Represents a file matching a pattern"""
    path: str
    size: int
    modified_time: float
    is_binary: bool

@dataclass
class EditOperation:
    """Represents a file edit operation"""
    file_path: str
    operation: str  # 'replace', 'insert', 'delete'
    line_number: int
    old_content: str
    new_content: str
    success: bool
    error: Optional[str] = None

class AdvancedFileOperations:
    """Advanced file operations including glob, grep, and multi-file editing"""

    @staticmethod
    def find_files(pattern: str, base_path: str = ".",
                   include_hidden: bool = False,
                   max_results: int = 1000) -> List[FileMatch]:
        """Find files matching glob pattern with metadata"""
        try:
            base_path = Path(base_path).resolve()
            all_files = []

            # Handle different glob patterns
            if pattern.startswith('/'):
                # Absolute path pattern
                search_pattern = pattern
            else:
                # Relative pattern
                search_pattern = str(base_path / pattern)

            for file_path in glob.glob(search_pattern, recursive=True):
                path_obj = Path(file_path)

                # Skip hidden files unless requested
                if not include_hidden and any(part.startswith('.') for part in path_obj.parts):
                    continue

                if path_obj.is_file():
                    stat = path_obj.stat()
                    is_binary = AdvancedFileOperations._is_binary_file(str(path_obj))

                    all_files.append(FileMatch(
                        path=str(path_obj),
                        size=stat.st_size,
                        modified_time=stat.st_mtime,
                        is_binary=is_binary
                    ))

                    if len(all_files) >= max_results:
                        break

            # Sort by modification time (newest first)
            all_files.sort(key=lambda x: x.modified_time, reverse=True)
            return all_files

        except Exception as e:
            console.print(f"[red]Error finding files: {e}[/red]")
            return []

    @staticmethod
    def _is_binary_file(file_path: str) -> bool:
        """Check if a file is binary"""
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                return b'\0' in chunk
        except:
            return True

    @staticmethod
    def grep_files(pattern: str,
                   file_pattern: str = "**/*.py",
                   base_path: str = ".",
                   case_sensitive: bool = False,
                   regex: bool = False,
                   context_lines: int = 2,
                   max_matches: int = 100) -> List[SearchResult]:
        """Search for pattern in files matching file_pattern"""
        try:
            results = []
            flags = 0 if case_sensitive else re.IGNORECASE

            # Compile regex pattern
            if regex:
                search_pattern = re.compile(pattern, flags)
            else:
                # Escape special regex characters for literal search
                escaped_pattern = re.escape(pattern)
                search_pattern = re.compile(escaped_pattern, flags)

            # Find files to search
            files = AdvancedFileOperations.find_files(file_pattern, base_path)

            for file_match in files:
                if file_match.is_binary:
                    continue

                try:
                    with open(file_match.path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()

                    for line_num, line in enumerate(lines, 1):
                        match = search_pattern.search(line)
                        if match:
                            # Get context lines
                            start_context = max(0, line_num - context_lines - 1)
                            end_context = min(len(lines), line_num + context_lines)

                            context_before = [lines[i].rstrip() for i in range(start_context, line_num - 1)]
                            context_after = [lines[i].rstrip() for i in range(line_num, end_context)]

                            results.append(SearchResult(
                                file_path=file_match.path,
                                line_number=line_num,
                                line_content=line.rstrip(),
                                match_start=match.start(),
                                match_end=match.end(),
                                context_before=context_before,
                                context_after=context_after
                            ))

                            if len(results) >= max_matches:
                                break

                except Exception as e:
                    console.print(f"[yellow]Warning: Could not search in {file_match.path}: {e}[/yellow]")
                    continue

                if len(results) >= max_matches:
                    break

            return results

        except Exception as e:
            console.print(f"[red]Error during grep: {e}[/red]")
            return []

    @staticmethod
    def replace_in_files(pattern: str,
                        replacement: str,
                        file_pattern: str = "**/*.py",
                        base_path: str = ".",
                        case_sensitive: bool = False,
                        regex: bool = False,
                        dry_run: bool = True,
                        working_directory: Optional[str] = None) -> List[EditOperation]:
        """Replace pattern in multiple files"""
        try:
            operations = []
            flags = 0 if case_sensitive else re.IGNORECASE

            # Compile regex pattern
            if regex:
                search_pattern = re.compile(pattern, flags)
            else:
                escaped_pattern = re.escape(pattern)
                search_pattern = re.compile(escaped_pattern, flags)

            # Find files to modify
            files = AdvancedFileOperations.find_files(file_pattern, base_path)

            for file_match in files:
                if file_match.is_binary:
                    continue

                try:
                    with open(file_match.path, 'r', encoding='utf-8') as f:
                        original_content = f.read()

                    # Check if pattern exists in file
                    if search_pattern.search(original_content):
                        new_content = search_pattern.sub(replacement, original_content)

                        operation = EditOperation(
                            file_path=file_match.path,
                            operation='replace',
                            line_number=0,  # Full file replacement
                            old_content=original_content,
                            new_content=new_content,
                            success=True
                        )

                        # Actually perform the replacement if not dry run
                        if not dry_run:
                            try:
                                with open(file_match.path, 'w', encoding='utf-8') as f:
                                    f.write(new_content)
                                operation.success = True
                            except Exception as e:
                                operation.success = False
                                operation.error = str(e)

                        operations.append(operation)

                except Exception as e:
                    operations.append(EditOperation(
                        file_path=file_match.path,
                        operation='replace',
                        line_number=0,
                        old_content="",
                        new_content="",
                        success=False,
                        error=str(e)
                    ))

            return operations

        except Exception as e:
            console.print(f"[red]Error during replace: {e}[/red]")
            return []

    @staticmethod
    def show_file_tree(base_path: str = ".",
                      max_depth: int = 3,
                      show_hidden: bool = False,
                      file_filter: Optional[str] = None) -> Tree:
        """Generate a tree view of the file system"""
        try:
            base_path = Path(base_path).resolve()
            tree = Tree(f"📁 {base_path.name}")

            def add_to_tree(path: Path, tree_node: Tree, current_depth: int):
                if current_depth >= max_depth:
                    return

                try:
                    items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))

                    for item in items:
                        # Skip hidden files unless requested
                        if not show_hidden and item.name.startswith('.'):
                            continue

                        # Apply file filter if specified
                        if file_filter and item.is_file():
                            if not glob.fnmatch.fnmatch(item.name, file_filter):
                                continue

                        if item.is_dir():
                            dir_node = tree_node.add(f"📁 {item.name}")
                            add_to_tree(item, dir_node, current_depth + 1)
                        else:
                            # Add file size
                            try:
                                size = item.stat().st_size
                                size_str = AdvancedFileOperations._format_file_size(size)
                                tree_node.add(f"📄 {item.name} ({size_str})")
                            except:
                                tree_node.add(f"📄 {item.name}")

                except PermissionError:
                    tree_node.add("❌ Permission denied")
                except Exception as e:
                    tree_node.add(f"❌ Error: {e}")

            add_to_tree(base_path, tree, 0)
            return tree

        except Exception as e:
            error_tree = Tree("❌ Error")
            error_tree.add(str(e))
            return error_tree

    @staticmethod
    def _format_file_size(size_bytes: int) -> str:
        """Format file size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f}TB"

    @staticmethod
    def compare_files(file1: str, file2: str, context_lines: int = 3) -> str:
        """Compare two files and return diff"""
        try:
            with open(file1, 'r', encoding='utf-8') as f1:
                lines1 = f1.readlines()

            with open(file2, 'r', encoding='utf-8') as f2:
                lines2 = f2.readlines()

            diff = difflib.unified_diff(
                lines1, lines2,
                fromfile=file1,
                tofile=file2,
                n=context_lines
            )

            return ''.join(diff)

        except Exception as e:
            return f"Error comparing files: {e}"

    @staticmethod
    def analyze_directory(path: str = ".") -> Dict[str, Any]:
        """Analyze directory structure and provide statistics"""
        try:
            path_obj = Path(path).resolve()

            stats = {
                'total_files': 0,
                'total_directories': 0,
                'total_size': 0,
                'file_types': {},
                'largest_files': [],
                'recent_files': []
            }

            all_files = []

            for item in path_obj.rglob('*'):
                if item.is_file():
                    try:
                        file_stat = item.stat()
                        file_size = file_stat.st_size
                        file_ext = item.suffix.lower() or 'no_extension'

                        stats['total_files'] += 1
                        stats['total_size'] += file_size

                        # Count file types
                        stats['file_types'][file_ext] = stats['file_types'].get(file_ext, 0) + 1

                        all_files.append({
                            'path': str(item),
                            'size': file_size,
                            'modified': file_stat.st_mtime,
                            'extension': file_ext
                        })

                    except (PermissionError, OSError):
                        continue

                elif item.is_dir():
                    stats['total_directories'] += 1

            # Get largest files (top 10)
            all_files.sort(key=lambda x: x['size'], reverse=True)
            stats['largest_files'] = all_files[:10]

            # Get most recent files (top 10)
            all_files.sort(key=lambda x: x['modified'], reverse=True)
            stats['recent_files'] = all_files[:10]

            return stats

        except Exception as e:
            return {'error': str(e)}

class CodeTools:
    """Tools for code manipulation and analysis with sandbox support"""

    def __init__(self, working_directory: Optional[str] = None):
        """Initialize CodeTools with optional sandbox"""
        self.working_directory = working_directory or os.getcwd()
        self.validator = create_default_sandbox(self.working_directory)

    def _validate_and_get_safe_path(self, filepath: str, operation: str = "access") -> Tuple[str, Optional[str]]:
        """Validate path and return safe path or error message"""
        try:
            violation = self.validator.validate_path(filepath, operation)
            if violation:
                error_msg = (
                    f"Security Error: {violation.message}. "
                    f"Available files: {', '.join(self.validator.list_accessible_files()[:10])}"
                    f"{'...' if len(self.validator.list_accessible_files()) > 10 else ''}"
                )
                return "", error_msg

            safe_path = self.validator.get_safe_path(filepath)
            return str(safe_path), None
        except Exception as e:
            return "", f"Path validation error: {e}"

    def read_file(self, filepath: str) -> str:
        """Read a file and return its contents with sandbox validation"""
        safe_path, error = self._validate_and_get_safe_path(filepath, "read")
        if error:
            console.print(f"[red]{error}[/red]")
            return ""

        try:
            with open(safe_path, 'r', encoding='utf-8') as f:
                content = f.read()
            console.print(f"[green]Successfully read {len(content)} characters from {filepath}[/green]")
            return content
        except FileNotFoundError:
            available_files = self.validator.list_accessible_files()
            suggestion = f"Available files: {', '.join(available_files[:5])}" if available_files else "No accessible files found"
            error_msg = f"File not found: {filepath}. {suggestion}"
            console.print(f"[red]{error_msg}[/red]")
            return ""
        except PermissionError:
            console.print(f"[red]Permission denied: {filepath}. File may be read-only or outside working directory.[/red]")
            return ""
        except Exception as e:
            console.print(f"[red]Error reading file {filepath}: {e}[/red]")
            return ""

    def write_file(self, filepath: str, content: str, working_directory: Optional[str] = None) -> bool:
        """Write content to a file with sandbox validation"""
        # Use provided working directory or instance default
        if working_directory and working_directory != self.working_directory:
            temp_validator = create_default_sandbox(working_directory)
            violation = temp_validator.validate_path(filepath, "write")
            if violation:
                console.print(f"[red]Security Error: {violation.message}[/red]")
                return False
            safe_path = str(temp_validator.get_safe_path(filepath))
        else:
            safe_path, error = self._validate_and_get_safe_path(filepath, "write")
            if error:
                console.print(f"[red]{error}[/red]")
                return False

        try:
            path = Path(safe_path)
            path.parent.mkdir(parents=True, exist_ok=True)

            # Check content size before writing
            content_size_mb = len(content.encode('utf-8')) / (1024 * 1024)
            if content_size_mb > 10:  # 10MB limit
                console.print(f"[red]Content size ({content_size_mb:.1f}MB) exceeds 10MB limit. Consider breaking into smaller files.[/red]")
                return False

            with open(safe_path, 'w', encoding='utf-8') as f:
                f.write(content)
            console.print(f"[green]Successfully wrote {len(content)} characters to {filepath}[/green]")
            return True
        except PermissionError:
            console.print(f"[red]Permission denied writing to {filepath}. Check file permissions and working directory access.[/red]")
            return False
        except OSError as e:
            if "No space left on device" in str(e):
                console.print(f"[red]Disk full: Cannot write to {filepath}. Free up space and try again.[/red]")
            else:
                console.print(f"[red]OS error writing to {filepath}: {e}[/red]")
            return False
        except Exception as e:
            console.print(f"[red]Error writing to {filepath}: {e}[/red]")
            return False

    def read_file_safe(self, filepath: str, working_directory: str) -> str:
        """Read file with explicit working directory (standalone function)"""
        validator = create_default_sandbox(working_directory)
        violation = validator.validate_path(filepath, "read")
        if violation:
            return f"Error: {violation.message}. Available files: {', '.join(validator.list_accessible_files()[:10])}"

        try:
            safe_path = validator.get_safe_path(filepath)
            with open(safe_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            available_files = validator.list_accessible_files()
            suggestion = f"Available files: {', '.join(available_files[:5])}" if available_files else "No accessible files found"
            return f"Error: File not found: {filepath}. {suggestion}"
        except Exception as e:
            return f"Error reading file {filepath}: {e}"

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
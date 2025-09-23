"""LLM-friendly error message system for better error recovery and debugging"""

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import traceback
import json

class ErrorSeverity(Enum):
    """Severity levels for errors"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """Categories of errors for better organization"""
    FILE_NOT_FOUND = "file_not_found"
    PERMISSION_DENIED = "permission_denied"
    SYNTAX_ERROR = "syntax_error"
    TIMEOUT = "timeout"
    RESOURCE_LIMIT = "resource_limit"
    SECURITY_VIOLATION = "security_violation"
    NETWORK_ERROR = "network_error"
    DEPENDENCY_ERROR = "dependency_error"
    CONFIGURATION_ERROR = "configuration_error"
    VALIDATION_ERROR = "validation_error"
    UNKNOWN = "unknown"

@dataclass
class ErrorContext:
    """Context information for better error understanding"""
    operation: str  # What was being attempted
    file_path: Optional[str] = None
    command: Optional[str] = None
    line_number: Optional[int] = None
    working_directory: Optional[str] = None
    available_files: List[str] = None
    environment_info: Dict[str, str] = None

    def __post_init__(self):
        if self.available_files is None:
            self.available_files = []
        if self.environment_info is None:
            self.environment_info = {}

@dataclass
class LLMError:
    """LLM-friendly error with context and suggestions"""
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    context: ErrorContext
    suggestions: List[str]
    next_steps: List[str]
    code_examples: List[str] = None
    related_docs: List[str] = None

    def __post_init__(self):
        if self.code_examples is None:
            self.code_examples = []
        if self.related_docs is None:
            self.related_docs = []

    def to_llm_message(self) -> str:
        """Format error for LLM consumption"""
        parts = [
            f"❌ {self.severity.value.upper()}: {self.message}",
            ""
        ]

        # Add context information
        if self.context.file_path:
            parts.append(f"📁 File: {self.context.file_path}")
        if self.context.command:
            parts.append(f"💻 Command: {self.context.command}")
        if self.context.working_directory:
            parts.append(f"📂 Working Directory: {self.context.working_directory}")

        # Add available alternatives
        if self.context.available_files:
            files_list = ", ".join(self.context.available_files[:5])
            if len(self.context.available_files) > 5:
                files_list += f" (and {len(self.context.available_files) - 5} more)"
            parts.append(f"📋 Available files: {files_list}")

        parts.append("")

        # Add suggestions
        if self.suggestions:
            parts.append("💡 Suggestions:")
            for i, suggestion in enumerate(self.suggestions, 1):
                parts.append(f"  {i}. {suggestion}")
            parts.append("")

        # Add next steps
        if self.next_steps:
            parts.append("🔄 Next steps:")
            for i, step in enumerate(self.next_steps, 1):
                parts.append(f"  {i}. {step}")
            parts.append("")

        # Add code examples
        if self.code_examples:
            parts.append("📝 Example commands:")
            for example in self.code_examples:
                parts.append(f"  {example}")
            parts.append("")

        return "\n".join(parts).strip()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "category": self.category.value,
            "severity": self.severity.value,
            "message": self.message,
            "context": {
                "operation": self.context.operation,
                "file_path": self.context.file_path,
                "command": self.context.command,
                "line_number": self.context.line_number,
                "working_directory": self.context.working_directory,
                "available_files": self.context.available_files,
                "environment_info": self.context.environment_info
            },
            "suggestions": self.suggestions,
            "next_steps": self.next_steps,
            "code_examples": self.code_examples,
            "related_docs": self.related_docs
        }

class ErrorMessageBuilder:
    """Builder for creating LLM-friendly error messages"""

    @staticmethod
    def file_not_found(file_path: str, working_directory: str,
                      available_files: List[str] = None) -> LLMError:
        """Create file not found error with helpful context"""
        if available_files is None:
            try:
                working_path = Path(working_directory)
                available_files = [str(f.relative_to(working_path))
                                 for f in working_path.rglob("*")
                                 if f.is_file()][:10]
            except Exception:
                available_files = []

        # Suggest similar files
        suggestions = [
            f"Check the file path spelling: {file_path}",
            "Use relative paths from the working directory",
            "List available files with /list command"
        ]

        if available_files:
            # Find similar filenames
            file_name = Path(file_path).name.lower()
            similar_files = [f for f in available_files
                           if file_name in f.lower() or f.lower() in file_name]
            if similar_files:
                suggestions.append(f"Did you mean one of these? {', '.join(similar_files[:3])}")

        return LLMError(
            category=ErrorCategory.FILE_NOT_FOUND,
            severity=ErrorSeverity.ERROR,
            message=f"File not found: {file_path}",
            context=ErrorContext(
                operation="file_access",
                file_path=file_path,
                working_directory=working_directory,
                available_files=available_files
            ),
            suggestions=suggestions,
            next_steps=[
                "Use /list to see all available files",
                "Use /find <pattern> to search for files",
                "Check if the file is in a subdirectory"
            ],
            code_examples=[
                "/list",
                f"/find {Path(file_path).name}",
                "/tree"
            ]
        )

    @staticmethod
    def permission_denied(file_path: str, operation: str) -> LLMError:
        """Create permission denied error with troubleshooting steps"""
        return LLMError(
            category=ErrorCategory.PERMISSION_DENIED,
            severity=ErrorSeverity.ERROR,
            message=f"Permission denied: {operation} {file_path}",
            context=ErrorContext(
                operation=operation,
                file_path=file_path
            ),
            suggestions=[
                "File may be read-only or locked by another process",
                "Path may be outside the allowed working directory",
                "Check file permissions and ownership"
            ],
            next_steps=[
                "Try accessing files within the project directory",
                "Check if file exists and is accessible",
                "Use a different file path within the working directory"
            ],
            code_examples=[
                "ls -la " + str(Path(file_path).parent),
                f"file {file_path}",
                "/workspace to see current working directory"
            ]
        )

    @staticmethod
    def timeout_error(operation: str, timeout_seconds: int, command: str = None) -> LLMError:
        """Create timeout error with optimization suggestions"""
        suggestions = [
            f"Operation exceeded {timeout_seconds} second timeout",
            "Break the operation into smaller steps",
            "Optimize the command or process"
        ]

        next_steps = [
            "Try processing smaller chunks of data",
            "Use streaming or incremental approaches",
            "Check for infinite loops or blocking operations"
        ]

        if command:
            if "find" in command.lower():
                suggestions.append("Limit find scope with specific directories")
                next_steps.append("Use more specific search patterns")
            elif "grep" in command.lower():
                suggestions.append("Limit grep to specific file types")
                next_steps.append("Use more specific grep patterns")

        return LLMError(
            category=ErrorCategory.TIMEOUT,
            severity=ErrorSeverity.WARNING,
            message=f"Operation timed out after {timeout_seconds} seconds",
            context=ErrorContext(
                operation=operation,
                command=command
            ),
            suggestions=suggestions,
            next_steps=next_steps,
            code_examples=[
                "find . -name '*.py' | head -20",
                "grep -r 'pattern' --include='*.py' .",
                "ls -la | head -10"
            ]
        )

    @staticmethod
    def syntax_error(code: str, line_number: int, error_details: str,
                    file_path: str = None) -> LLMError:
        """Create syntax error with code context"""
        return LLMError(
            category=ErrorCategory.SYNTAX_ERROR,
            severity=ErrorSeverity.ERROR,
            message=f"Syntax error at line {line_number}: {error_details}",
            context=ErrorContext(
                operation="code_parsing",
                file_path=file_path,
                line_number=line_number
            ),
            suggestions=[
                "Check for missing brackets, quotes, or semicolons",
                "Verify proper indentation",
                "Look for typos in keywords or variable names"
            ],
            next_steps=[
                "Review the code around the error line",
                "Use a code formatter or linter",
                "Check language-specific syntax rules"
            ],
            code_examples=[
                "python -m py_compile filename.py",
                "pylint filename.py",
                "black filename.py"
            ]
        )

    @staticmethod
    def security_violation(violation_type: str, attempted_path: str,
                         working_directory: str, available_paths: List[str] = None) -> LLMError:
        """Create security violation error"""
        return LLMError(
            category=ErrorCategory.SECURITY_VIOLATION,
            severity=ErrorSeverity.CRITICAL,
            message=f"Security violation: {violation_type} - {attempted_path}",
            context=ErrorContext(
                operation="security_check",
                file_path=attempted_path,
                working_directory=working_directory,
                available_files=available_paths or []
            ),
            suggestions=[
                "Use paths within the working directory only",
                "Avoid '..' path traversal attempts",
                "Check for typos in the file path"
            ],
            next_steps=[
                "Use relative paths from the project root",
                "List accessible files with /list",
                "Stay within the project boundaries"
            ],
            code_examples=[
                "/list",
                "/workspace",
                "cat ./relative/path/to/file.txt"
            ]
        )

    @staticmethod
    def dependency_error(missing_dependency: str, operation: str) -> LLMError:
        """Create dependency error with installation suggestions"""
        return LLMError(
            category=ErrorCategory.DEPENDENCY_ERROR,
            severity=ErrorSeverity.ERROR,
            message=f"Missing dependency: {missing_dependency}",
            context=ErrorContext(
                operation=operation
            ),
            suggestions=[
                f"Install {missing_dependency} using package manager",
                "Check if dependency is available in virtual environment",
                "Verify correct package name and version"
            ],
            next_steps=[
                "Install the missing package",
                "Check requirements.txt or package.json",
                "Verify virtual environment is activated"
            ],
            code_examples=[
                f"pip install {missing_dependency}",
                f"npm install {missing_dependency}",
                "pip install -r requirements.txt"
            ]
        )

    @staticmethod
    def from_exception(exception: Exception, operation: str,
                      context: Optional[ErrorContext] = None) -> LLMError:
        """Create LLMError from Python exception"""
        if context is None:
            context = ErrorContext(operation=operation)

        # Determine category based on exception type
        category = ErrorCategory.UNKNOWN
        if isinstance(exception, FileNotFoundError):
            category = ErrorCategory.FILE_NOT_FOUND
        elif isinstance(exception, PermissionError):
            category = ErrorCategory.PERMISSION_DENIED
        elif isinstance(exception, SyntaxError):
            category = ErrorCategory.SYNTAX_ERROR
        elif isinstance(exception, TimeoutError):
            category = ErrorCategory.TIMEOUT
        elif isinstance(exception, ImportError):
            category = ErrorCategory.DEPENDENCY_ERROR

        # Get traceback for debugging
        tb_lines = traceback.format_exception(type(exception), exception, exception.__traceback__)
        error_details = "".join(tb_lines[-3:])  # Last few lines of traceback

        return LLMError(
            category=category,
            severity=ErrorSeverity.ERROR,
            message=f"{type(exception).__name__}: {str(exception)}",
            context=context,
            suggestions=[
                "Check the error details below",
                "Verify input parameters and file paths",
                "Look for common issues with this operation"
            ],
            next_steps=[
                "Review the operation that caused this error",
                "Check for prerequisite conditions",
                "Try a simpler version of the operation first"
            ],
            code_examples=[],
            related_docs=[error_details]
        )

def create_llm_error(category: ErrorCategory, message: str, **kwargs) -> LLMError:
    """Convenience function to create LLMError"""
    context = kwargs.pop('context', ErrorContext(operation="unknown"))
    suggestions = kwargs.pop('suggestions', [])
    next_steps = kwargs.pop('next_steps', [])

    return LLMError(
        category=category,
        severity=kwargs.pop('severity', ErrorSeverity.ERROR),
        message=message,
        context=context,
        suggestions=suggestions,
        next_steps=next_steps,
        **kwargs
    )

def format_error_for_llm(error: Union[LLMError, Exception, str], operation: str = "unknown") -> str:
    """Format any error for LLM consumption"""
    if isinstance(error, LLMError):
        return error.to_llm_message()
    elif isinstance(error, Exception):
        llm_error = ErrorMessageBuilder.from_exception(error, operation)
        return llm_error.to_llm_message()
    else:
        # String error message
        llm_error = create_llm_error(
            category=ErrorCategory.UNKNOWN,
            message=str(error),
            context=ErrorContext(operation=operation),
            suggestions=["Check the error message for details"],
            next_steps=["Review the operation and try again"]
        )
        return llm_error.to_llm_message()

def handle_file_operation_error(file_path: str, operation: str,
                              working_directory: str, exception: Exception) -> str:
    """Handle file operation errors with context-aware messages"""
    if isinstance(exception, FileNotFoundError):
        try:
            available_files = list(Path(working_directory).rglob("*"))[:10]
            available_names = [f.name for f in available_files if f.is_file()]
        except Exception:
            available_names = []

        error = ErrorMessageBuilder.file_not_found(
            file_path, working_directory, available_names
        )
    elif isinstance(exception, PermissionError):
        error = ErrorMessageBuilder.permission_denied(file_path, operation)
    else:
        context = ErrorContext(
            operation=operation,
            file_path=file_path,
            working_directory=working_directory
        )
        error = ErrorMessageBuilder.from_exception(exception, operation, context)

    return error.to_llm_message()
"""Enhanced file operations with dry-run mode, validation, and preview capabilities"""

import os
import shutil
import difflib
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import tempfile
import hashlib
import time

from .sandbox import PathValidator, create_default_sandbox, SecurityError
from .llm_errors import ErrorMessageBuilder, format_error_for_llm
from .metrics import record_command_metric

class OperationType(Enum):
    """Types of file operations"""
    READ = "read"
    WRITE = "write"
    REPLACE = "replace"
    DELETE = "delete"
    COPY = "copy"
    MOVE = "move"
    CREATE_DIR = "create_dir"

@dataclass
class FileOperationResult:
    """Result of a file operation"""
    success: bool
    operation_type: OperationType
    file_path: str
    message: str
    changes_preview: Optional[str] = None
    backup_path: Optional[str] = None
    files_affected: int = 0
    bytes_processed: int = 0
    execution_time: float = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "success": self.success,
            "operation_type": self.operation_type.value,
            "file_path": self.file_path,
            "message": self.message,
            "changes_preview": self.changes_preview,
            "backup_path": self.backup_path,
            "files_affected": self.files_affected,
            "bytes_processed": self.bytes_processed,
            "execution_time": self.execution_time
        }

@dataclass
class ReplaceOperation:
    """Details of a text replacement operation"""
    file_path: str
    old_text: str
    new_text: str
    line_number: int
    context_before: List[str]
    context_after: List[str]
    exact_match: bool

class EnhancedFileOperations:
    """Enhanced file operations with safety, validation, and preview capabilities"""

    def __init__(self, working_directory: str, enable_backups: bool = True):
        """
        Initialize enhanced file operations

        Args:
            working_directory: Directory to restrict operations to
            enable_backups: Whether to create backups before destructive operations
        """
        self.working_directory = Path(working_directory).resolve()
        self.validator = create_default_sandbox(str(self.working_directory))
        self.enable_backups = enable_backups
        self.backup_dir = self.working_directory / ".tinycode_backups"

        if enable_backups:
            self.backup_dir.mkdir(exist_ok=True)

    def read_file_safe(self, file_path: str, max_size_mb: float = 10) -> FileOperationResult:
        """
        Read a file with validation and size checks

        Args:
            file_path: Path to file to read
            max_size_mb: Maximum file size to read

        Returns:
            FileOperationResult with file contents or error
        """
        start_time = time.time()

        try:
            # Validate path
            violation = self.validator.validate_path(file_path, "read")
            if violation:
                return FileOperationResult(
                    success=False,
                    operation_type=OperationType.READ,
                    file_path=file_path,
                    message=f"Security violation: {violation.message}",
                    execution_time=time.time() - start_time
                )

            safe_path = self.validator.get_safe_path(file_path)

            # Check if file exists
            if not safe_path.exists():
                available_files = self.validator.list_accessible_files()
                error = ErrorMessageBuilder.file_not_found(
                    file_path, str(self.working_directory), available_files
                )
                return FileOperationResult(
                    success=False,
                    operation_type=OperationType.READ,
                    file_path=file_path,
                    message=error.to_llm_message(),
                    execution_time=time.time() - start_time
                )

            # Check file size
            file_size_mb = safe_path.stat().st_size / (1024 * 1024)
            if file_size_mb > max_size_mb:
                return FileOperationResult(
                    success=False,
                    operation_type=OperationType.READ,
                    file_path=file_path,
                    message=f"File too large ({file_size_mb:.1f}MB). Maximum size: {max_size_mb}MB. Consider reading in chunks or using streaming.",
                    execution_time=time.time() - start_time
                )

            # Read file
            with open(safe_path, 'r', encoding='utf-8') as f:
                content = f.read()

            execution_time = time.time() - start_time
            record_command_metric("read_file", execution_time, True, files_read=1)

            return FileOperationResult(
                success=True,
                operation_type=OperationType.READ,
                file_path=file_path,
                message=content,
                files_affected=1,
                bytes_processed=len(content.encode('utf-8')),
                execution_time=execution_time
            )

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = format_error_for_llm(e, f"reading {file_path}")
            record_command_metric("read_file", execution_time, False, str(e))

            return FileOperationResult(
                success=False,
                operation_type=OperationType.READ,
                file_path=file_path,
                message=error_msg,
                execution_time=execution_time
            )

    def write_file_safe(self, file_path: str, content: str,
                       dry_run: bool = False, create_backup: bool = True) -> FileOperationResult:
        """
        Write content to a file with validation and optional backup

        Args:
            file_path: Path to file to write
            content: Content to write
            dry_run: If True, show what would be done without actually doing it
            create_backup: Whether to create backup of existing file

        Returns:
            FileOperationResult with operation details
        """
        start_time = time.time()

        try:
            # Validate path
            violation = self.validator.validate_path(file_path, "write")
            if violation:
                return FileOperationResult(
                    success=False,
                    operation_type=OperationType.WRITE,
                    file_path=file_path,
                    message=f"Security violation: {violation.message}",
                    execution_time=time.time() - start_time
                )

            safe_path = self.validator.get_safe_path(file_path)

            # Check content size
            content_size_mb = len(content.encode('utf-8')) / (1024 * 1024)
            if content_size_mb > 50:  # 50MB limit
                return FileOperationResult(
                    success=False,
                    operation_type=OperationType.WRITE,
                    file_path=file_path,
                    message=f"Content too large ({content_size_mb:.1f}MB). Maximum size: 50MB. Consider breaking into smaller files.",
                    execution_time=time.time() - start_time
                )

            backup_path = None
            files_affected = 1

            # Handle dry run
            if dry_run:
                if safe_path.exists():
                    with open(safe_path, 'r', encoding='utf-8') as f:
                        existing_content = f.read()

                    # Generate diff preview
                    diff = list(difflib.unified_diff(
                        existing_content.splitlines(keepends=True),
                        content.splitlines(keepends=True),
                        fromfile=f"{file_path} (current)",
                        tofile=f"{file_path} (new)",
                        lineterm=""
                    ))
                    changes_preview = "".join(diff)
                else:
                    changes_preview = f"New file will be created with {len(content)} characters"

                return FileOperationResult(
                    success=True,
                    operation_type=OperationType.WRITE,
                    file_path=file_path,
                    message="DRY RUN: Preview of changes shown below",
                    changes_preview=changes_preview,
                    files_affected=files_affected,
                    bytes_processed=len(content.encode('utf-8')),
                    execution_time=time.time() - start_time
                )

            # Create backup if file exists and backups are enabled
            if safe_path.exists() and create_backup and self.enable_backups:
                backup_path = self._create_backup(safe_path)

            # Create parent directories
            safe_path.parent.mkdir(parents=True, exist_ok=True)

            # Write file atomically using temporary file
            temp_file = safe_path.with_suffix(safe_path.suffix + '.tmp')
            try:
                with open(temp_file, 'w', encoding='utf-8') as f:
                    f.write(content)

                # Atomic move
                temp_file.replace(safe_path)

            except Exception:
                # Cleanup temporary file on error
                if temp_file.exists():
                    temp_file.unlink()
                raise

            execution_time = time.time() - start_time
            record_command_metric("write_file", execution_time, True, files_modified=1)

            return FileOperationResult(
                success=True,
                operation_type=OperationType.WRITE,
                file_path=file_path,
                message=f"Successfully wrote {len(content)} characters to {file_path}",
                backup_path=str(backup_path) if backup_path else None,
                files_affected=files_affected,
                bytes_processed=len(content.encode('utf-8')),
                execution_time=execution_time
            )

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = format_error_for_llm(e, f"writing to {file_path}")
            record_command_metric("write_file", execution_time, False, str(e))

            return FileOperationResult(
                success=False,
                operation_type=OperationType.WRITE,
                file_path=file_path,
                message=error_msg,
                execution_time=execution_time
            )

    def replace_in_file(self, file_path: str, old_text: str, new_text: str,
                       dry_run: bool = False, create_backup: bool = True) -> FileOperationResult:
        """
        Replace text in a file with exact match validation

        Args:
            file_path: Path to file to modify
            old_text: Text to replace (must match exactly)
            new_text: Replacement text
            dry_run: If True, show what would be done without actually doing it
            create_backup: Whether to create backup of original file

        Returns:
            FileOperationResult with operation details
        """
        start_time = time.time()

        try:
            # First read the file
            read_result = self.read_file_safe(file_path)
            if not read_result.success:
                return FileOperationResult(
                    success=False,
                    operation_type=OperationType.REPLACE,
                    file_path=file_path,
                    message=f"Cannot read file for replacement: {read_result.message}",
                    execution_time=time.time() - start_time
                )

            content = read_result.message

            # Check for exact matches
            match_count = content.count(old_text)
            if match_count == 0:
                # Provide helpful error message
                lines = content.split('\n')
                similar_lines = []
                old_words = old_text.lower().split()

                for i, line in enumerate(lines):
                    line_words = line.lower().split()
                    if any(word in line_words for word in old_words):
                        similar_lines.append(f"Line {i+1}: {line[:100]}...")

                suggestion = ""
                if similar_lines:
                    suggestion = f"\nSimilar lines found:\n" + "\n".join(similar_lines[:5])

                return FileOperationResult(
                    success=False,
                    operation_type=OperationType.REPLACE,
                    file_path=file_path,
                    message=f"Text not found for replacement: '{old_text[:100]}...'{suggestion}",
                    execution_time=time.time() - start_time
                )

            elif match_count > 1:
                # Multiple matches - show context for each
                contexts = self._find_replacement_contexts(content, old_text)
                context_preview = "\n".join([
                    f"Match {i+1} at line {ctx.line_number}:\n{ctx.context_before[-1] if ctx.context_before else ''}\n> {old_text}\n{ctx.context_after[0] if ctx.context_after else ''}"
                    for i, ctx in enumerate(contexts[:3])
                ])

                return FileOperationResult(
                    success=False,
                    operation_type=OperationType.REPLACE,
                    file_path=file_path,
                    message=f"Multiple matches found ({match_count}). Text must match exactly once.\n\nContexts:\n{context_preview}",
                    execution_time=time.time() - start_time
                )

            # Single match - proceed with replacement
            new_content = content.replace(old_text, new_text)

            # Handle dry run
            if dry_run:
                # Generate diff preview
                diff = list(difflib.unified_diff(
                    content.splitlines(keepends=True),
                    new_content.splitlines(keepends=True),
                    fromfile=f"{file_path} (current)",
                    tofile=f"{file_path} (modified)",
                    lineterm=""
                ))
                changes_preview = "".join(diff)

                return FileOperationResult(
                    success=True,
                    operation_type=OperationType.REPLACE,
                    file_path=file_path,
                    message="DRY RUN: Preview of changes shown below",
                    changes_preview=changes_preview,
                    files_affected=1,
                    bytes_processed=len(new_content.encode('utf-8')),
                    execution_time=time.time() - start_time
                )

            # Perform actual replacement
            write_result = self.write_file_safe(file_path, new_content, dry_run=False, create_backup=create_backup)

            if write_result.success:
                execution_time = time.time() - start_time
                record_command_metric("replace_in_file", execution_time, True, files_modified=1)

                return FileOperationResult(
                    success=True,
                    operation_type=OperationType.REPLACE,
                    file_path=file_path,
                    message=f"Successfully replaced text in {file_path}. {len(old_text)} → {len(new_text)} characters",
                    backup_path=write_result.backup_path,
                    files_affected=1,
                    bytes_processed=len(new_content.encode('utf-8')),
                    execution_time=execution_time
                )
            else:
                return write_result

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = format_error_for_llm(e, f"replacing text in {file_path}")
            record_command_metric("replace_in_file", execution_time, False, str(e))

            return FileOperationResult(
                success=False,
                operation_type=OperationType.REPLACE,
                file_path=file_path,
                message=error_msg,
                execution_time=execution_time
            )

    def copy_file_safe(self, source_path: str, dest_path: str,
                      dry_run: bool = False) -> FileOperationResult:
        """
        Copy a file with validation

        Args:
            source_path: Source file path
            dest_path: Destination file path
            dry_run: If True, show what would be done without actually doing it

        Returns:
            FileOperationResult with operation details
        """
        start_time = time.time()

        try:
            # Validate both paths
            source_violation = self.validator.validate_path(source_path, "read")
            if source_violation:
                return FileOperationResult(
                    success=False,
                    operation_type=OperationType.COPY,
                    file_path=source_path,
                    message=f"Source path violation: {source_violation.message}",
                    execution_time=time.time() - start_time
                )

            dest_violation = self.validator.validate_path(dest_path, "write")
            if dest_violation:
                return FileOperationResult(
                    success=False,
                    operation_type=OperationType.COPY,
                    file_path=dest_path,
                    message=f"Destination path violation: {dest_violation.message}",
                    execution_time=time.time() - start_time
                )

            safe_source = self.validator.get_safe_path(source_path)
            safe_dest = self.validator.get_safe_path(dest_path)

            if not safe_source.exists():
                available_files = self.validator.list_accessible_files()
                error = ErrorMessageBuilder.file_not_found(
                    source_path, str(self.working_directory), available_files
                )
                return FileOperationResult(
                    success=False,
                    operation_type=OperationType.COPY,
                    file_path=source_path,
                    message=error.to_llm_message(),
                    execution_time=time.time() - start_time
                )

            # Check file size
            file_size = safe_source.stat().st_size
            file_size_mb = file_size / (1024 * 1024)

            if dry_run:
                message = f"Would copy {source_path} to {dest_path} ({file_size_mb:.1f}MB)"
                if safe_dest.exists():
                    message += f"\nWarning: {dest_path} already exists and would be overwritten"

                return FileOperationResult(
                    success=True,
                    operation_type=OperationType.COPY,
                    file_path=source_path,
                    message=f"DRY RUN: {message}",
                    files_affected=1,
                    bytes_processed=file_size,
                    execution_time=time.time() - start_time
                )

            # Create destination directory
            safe_dest.parent.mkdir(parents=True, exist_ok=True)

            # Copy file
            shutil.copy2(safe_source, safe_dest)

            execution_time = time.time() - start_time
            record_command_metric("copy_file", execution_time, True, files_modified=1)

            return FileOperationResult(
                success=True,
                operation_type=OperationType.COPY,
                file_path=source_path,
                message=f"Successfully copied {source_path} to {dest_path} ({file_size_mb:.1f}MB)",
                files_affected=1,
                bytes_processed=file_size,
                execution_time=execution_time
            )

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = format_error_for_llm(e, f"copying {source_path} to {dest_path}")
            record_command_metric("copy_file", execution_time, False, str(e))

            return FileOperationResult(
                success=False,
                operation_type=OperationType.COPY,
                file_path=source_path,
                message=error_msg,
                execution_time=execution_time
            )

    def _create_backup(self, file_path: Path) -> Optional[Path]:
        """Create a backup of a file"""
        try:
            timestamp = int(time.time())
            backup_name = f"{file_path.name}.backup.{timestamp}"
            backup_path = self.backup_dir / backup_name

            shutil.copy2(file_path, backup_path)
            return backup_path
        except Exception:
            return None

    def _find_replacement_contexts(self, content: str, search_text: str) -> List[ReplaceOperation]:
        """Find all occurrences of text with context"""
        lines = content.split('\n')
        contexts = []

        for i, line in enumerate(lines):
            if search_text in line:
                context_before = lines[max(0, i-2):i]
                context_after = lines[i+1:min(len(lines), i+3)]

                contexts.append(ReplaceOperation(
                    file_path="",  # Will be filled by caller
                    old_text=search_text,
                    new_text="",   # Will be filled by caller
                    line_number=i + 1,
                    context_before=context_before,
                    context_after=context_after,
                    exact_match=line.strip() == search_text.strip()
                ))

        return contexts

def create_enhanced_file_ops(working_directory: str, **kwargs) -> EnhancedFileOperations:
    """Create an EnhancedFileOperations instance with default settings"""
    return EnhancedFileOperations(working_directory, **kwargs)

# Convenience functions for common operations
def read_file_safe(file_path: str, working_directory: str) -> str:
    """Read a file safely and return content or error message"""
    ops = create_enhanced_file_ops(working_directory)
    result = ops.read_file_safe(file_path)
    return result.message

def write_file_safe(file_path: str, content: str, working_directory: str, dry_run: bool = False) -> str:
    """Write to a file safely and return result message"""
    ops = create_enhanced_file_ops(working_directory)
    result = ops.write_file_safe(file_path, content, dry_run=dry_run)
    if result.changes_preview and dry_run:
        return f"{result.message}\n\nChanges preview:\n{result.changes_preview}"
    return result.message

def replace_in_file_safe(file_path: str, old_text: str, new_text: str,
                        working_directory: str, dry_run: bool = False) -> str:
    """Replace text in file safely and return result message"""
    ops = create_enhanced_file_ops(working_directory)
    result = ops.replace_in_file(file_path, old_text, new_text, dry_run=dry_run)
    if result.changes_preview and dry_run:
        return f"{result.message}\n\nChanges preview:\n{result.changes_preview}"
    return result.message
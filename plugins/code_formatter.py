"""
Code Formatter Plugin

Provides code formatting capabilities using various formatters.
"""

import subprocess
import tempfile
import os
from pathlib import Path
from typing import Dict, List, Optional

from tiny_code.plugin_system import PluginBase, PluginMetadata, PluginCommand
from tiny_code.safety_config import SafetyLevel


class CodeFormatterPlugin(PluginBase):
    """Plugin for formatting code in various languages"""

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="code_formatter",
            version="1.0.0",
            description="Format code using various language-specific formatters",
            author="TinyCode Team",
            safety_level=SafetyLevel.PERMISSIVE,
            commands=["format", "check-format", "list-formatters"],
            dependencies=[]
        )

    def initialize(self) -> bool:
        # Define supported formatters
        self.formatters = {
            'python': {
                'black': ['black', '--line-length', '88'],
                'autopep8': ['autopep8', '--max-line-length', '88'],
                'yapf': ['yapf']
            },
            'javascript': {
                'prettier': ['prettier', '--write'],
                'eslint': ['eslint', '--fix']
            },
            'typescript': {
                'prettier': ['prettier', '--write'],
                'eslint': ['eslint', '--fix']
            },
            'json': {
                'prettier': ['prettier', '--write']
            },
            'css': {
                'prettier': ['prettier', '--write']
            },
            'html': {
                'prettier': ['prettier', '--write']
            },
            'rust': {
                'rustfmt': ['rustfmt']
            },
            'go': {
                'gofmt': ['gofmt', '-w'],
                'goimports': ['goimports', '-w']
            },
            'c': {
                'clang-format': ['clang-format', '-i']
            },
            'cpp': {
                'clang-format': ['clang-format', '-i']
            }
        }

        # Register commands
        self.register_command(PluginCommand(
            name="format",
            description="Format code file(s) using appropriate formatter",
            handler=self._format_command,
            safety_level=SafetyLevel.STANDARD
        ))

        self.register_command(PluginCommand(
            name="check-format",
            description="Check if code is properly formatted without modifying",
            handler=self._check_format_command,
            safety_level=SafetyLevel.PERMISSIVE
        ))

        self.register_command(PluginCommand(
            name="list-formatters",
            description="List available formatters for each language",
            handler=self._list_formatters_command,
            safety_level=SafetyLevel.PERMISSIVE
        ))

        return True

    def _get_file_language(self, file_path: str) -> Optional[str]:
        """Determine the language of a file based on its extension"""
        extension_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.json': 'json',
            '.css': 'css',
            '.html': 'html',
            '.htm': 'html',
            '.rs': 'rust',
            '.go': 'go',
            '.c': 'c',
            '.h': 'c',
            '.cpp': 'cpp',
            '.cxx': 'cpp',
            '.cc': 'cpp',
            '.hpp': 'cpp'
        }

        path = Path(file_path)
        return extension_map.get(path.suffix.lower())

    def _check_formatter_available(self, formatter_cmd: List[str]) -> bool:
        """Check if a formatter is available on the system"""
        try:
            subprocess.run([formatter_cmd[0], '--version'],
                         capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def _format_file(self, file_path: str, formatter: str = None, dry_run: bool = False) -> Dict[str, any]:
        """Format a single file"""
        if not os.path.exists(file_path):
            return {'success': False, 'error': f'File not found: {file_path}'}

        language = self._get_file_language(file_path)
        if not language:
            return {'success': False, 'error': f'Unsupported file type: {file_path}'}

        if language not in self.formatters:
            return {'success': False, 'error': f'No formatters available for {language}'}

        # Choose formatter
        available_formatters = {}
        for fmt_name, fmt_cmd in self.formatters[language].items():
            if self._check_formatter_available(fmt_cmd):
                available_formatters[fmt_name] = fmt_cmd

        if not available_formatters:
            return {
                'success': False,
                'error': f'No formatters installed for {language}. Available: {list(self.formatters[language].keys())}'
            }

        # Use specified formatter or first available
        if formatter and formatter in available_formatters:
            chosen_formatter = available_formatters[formatter]
            formatter_name = formatter
        else:
            formatter_name = list(available_formatters.keys())[0]
            chosen_formatter = available_formatters[formatter_name]

        try:
            if dry_run:
                # For dry run, create a temporary copy
                with tempfile.NamedTemporaryFile(mode='w', suffix=Path(file_path).suffix, delete=False) as tmp:
                    with open(file_path, 'r') as original:
                        tmp.write(original.read())
                    tmp_path = tmp.name

                # Format the temporary file
                result = subprocess.run(
                    chosen_formatter + [tmp_path],
                    capture_output=True,
                    text=True
                )

                # Check if formatting would change the file
                with open(file_path, 'r') as original:
                    original_content = original.read()
                with open(tmp_path, 'r') as formatted:
                    formatted_content = formatted.read()

                os.unlink(tmp_path)

                changes_needed = original_content != formatted_content
                return {
                    'success': True,
                    'formatter': formatter_name,
                    'changes_needed': changes_needed,
                    'file': file_path
                }
            else:
                # Format the actual file
                result = subprocess.run(
                    chosen_formatter + [file_path],
                    capture_output=True,
                    text=True
                )

                if result.returncode == 0:
                    return {
                        'success': True,
                        'formatter': formatter_name,
                        'file': file_path,
                        'output': result.stdout.strip() if result.stdout else None
                    }
                else:
                    return {
                        'success': False,
                        'error': f'Formatter failed: {result.stderr}',
                        'file': file_path
                    }

        except Exception as e:
            return {'success': False, 'error': f'Error formatting {file_path}: {str(e)}'}

    def _format_command(self, *args) -> str:
        """Handle format command"""
        if not args:
            return "Usage: format <file_path> [formatter_name]"

        file_path = args[0]
        formatter = args[1] if len(args) > 1 else None

        result = self._format_file(file_path, formatter)

        if result['success']:
            msg = f"✅ Formatted {result['file']} using {result['formatter']}"
            if result.get('output'):
                msg += f"\n{result['output']}"
            return msg
        else:
            return f"❌ {result['error']}"

    def _check_format_command(self, *args) -> str:
        """Handle check-format command"""
        if not args:
            return "Usage: check-format <file_path> [formatter_name]"

        file_path = args[0]
        formatter = args[1] if len(args) > 1 else None

        result = self._format_file(file_path, formatter, dry_run=True)

        if result['success']:
            if result['changes_needed']:
                return f"❌ {result['file']} needs formatting (would use {result['formatter']})"
            else:
                return f"✅ {result['file']} is properly formatted"
        else:
            return f"❌ {result['error']}"

    def _list_formatters_command(self, *args) -> str:
        """Handle list-formatters command"""
        output = ["Available formatters:\n"]

        for language, formatters in self.formatters.items():
            output.append(f"{language}:")
            for fmt_name, fmt_cmd in formatters.items():
                available = "✅" if self._check_formatter_available(fmt_cmd) else "❌"
                output.append(f"  {available} {fmt_name} ({fmt_cmd[0]})")
            output.append("")

        return "\n".join(output)
"""
Utilities Plugin

Provides basic utility commands for text processing and system operations.
"""

import hashlib
import base64
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

from tiny_code.plugin_system import PluginBase, PluginMetadata, PluginCommand
from tiny_code.safety_config import SafetyLevel


class UtilitiesPlugin(PluginBase):
    """Plugin for common utility operations"""

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="utilities",
            version="1.0.0",
            description="Common utility commands for text processing and data manipulation",
            author="TinyCode Team",
            safety_level=SafetyLevel.PERMISSIVE,
            commands=["hash", "encode", "decode", "uuid", "timestamp", "json-format", "count-lines"],
            dependencies=[]
        )

    def initialize(self) -> bool:
        # Register utility commands
        self.register_command(PluginCommand(
            name="hash",
            description="Generate hash of text (md5, sha1, sha256)",
            handler=self._hash_command,
            safety_level=SafetyLevel.PERMISSIVE
        ))

        self.register_command(PluginCommand(
            name="encode",
            description="Encode text (base64, url)",
            handler=self._encode_command,
            safety_level=SafetyLevel.PERMISSIVE
        ))

        self.register_command(PluginCommand(
            name="decode",
            description="Decode text (base64, url)",
            handler=self._decode_command,
            safety_level=SafetyLevel.PERMISSIVE
        ))

        self.register_command(PluginCommand(
            name="uuid",
            description="Generate UUID (v1, v4)",
            handler=self._uuid_command,
            safety_level=SafetyLevel.PERMISSIVE
        ))

        self.register_command(PluginCommand(
            name="timestamp",
            description="Get current timestamp in various formats",
            handler=self._timestamp_command,
            safety_level=SafetyLevel.PERMISSIVE
        ))

        self.register_command(PluginCommand(
            name="json-format",
            description="Format JSON string with proper indentation",
            handler=self._json_format_command,
            safety_level=SafetyLevel.PERMISSIVE
        ))

        self.register_command(PluginCommand(
            name="count-lines",
            description="Count lines, words, characters in text",
            handler=self._count_lines_command,
            safety_level=SafetyLevel.PERMISSIVE
        ))

        return True

    def _hash_command(self, algorithm: str = "sha256", text: str = None) -> str:
        """Generate hash of text"""
        if not text:
            return "Usage: hash <algorithm> <text>\nAlgorithms: md5, sha1, sha256"

        try:
            if algorithm == "md5":
                hasher = hashlib.md5()
            elif algorithm == "sha1":
                hasher = hashlib.sha1()
            elif algorithm == "sha256":
                hasher = hashlib.sha256()
            else:
                return f"❌ Unsupported algorithm: {algorithm}\nSupported: md5, sha1, sha256"

            hasher.update(text.encode('utf-8'))
            hash_value = hasher.hexdigest()

            return f"✅ {algorithm.upper()} hash:\n{hash_value}"

        except Exception as e:
            return f"❌ Error generating hash: {str(e)}"

    def _encode_command(self, method: str = "base64", text: str = None) -> str:
        """Encode text"""
        if not text:
            return "Usage: encode <method> <text>\nMethods: base64"

        try:
            if method == "base64":
                encoded = base64.b64encode(text.encode('utf-8')).decode('utf-8')
                return f"✅ Base64 encoded:\n{encoded}"
            else:
                return f"❌ Unsupported encoding method: {method}\nSupported: base64"

        except Exception as e:
            return f"❌ Error encoding: {str(e)}"

    def _decode_command(self, method: str = "base64", text: str = None) -> str:
        """Decode text"""
        if not text:
            return "Usage: decode <method> <text>\nMethods: base64"

        try:
            if method == "base64":
                decoded = base64.b64decode(text.encode('utf-8')).decode('utf-8')
                return f"✅ Base64 decoded:\n{decoded}"
            else:
                return f"❌ Unsupported decoding method: {method}\nSupported: base64"

        except Exception as e:
            return f"❌ Error decoding: {str(e)}"

    def _uuid_command(self, version: str = "v4") -> str:
        """Generate UUID"""
        try:
            if version == "v1":
                generated_uuid = str(uuid.uuid1())
            elif version == "v4":
                generated_uuid = str(uuid.uuid4())
            else:
                return f"❌ Unsupported UUID version: {version}\nSupported: v1, v4"

            return f"✅ UUID {version}:\n{generated_uuid}"

        except Exception as e:
            return f"❌ Error generating UUID: {str(e)}"

    def _timestamp_command(self, format_type: str = "iso") -> str:
        """Get current timestamp"""
        try:
            now = datetime.now()

            if format_type == "iso":
                timestamp = now.isoformat()
            elif format_type == "unix":
                timestamp = str(int(now.timestamp()))
            elif format_type == "human":
                timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
            elif format_type == "utc":
                timestamp = datetime.utcnow().isoformat() + "Z"
            else:
                return f"❌ Unsupported format: {format_type}\nSupported: iso, unix, human, utc"

            return f"✅ Current timestamp ({format_type}):\n{timestamp}"

        except Exception as e:
            return f"❌ Error generating timestamp: {str(e)}"

    def _json_format_command(self, json_string: str = None) -> str:
        """Format JSON string"""
        if not json_string:
            return "Usage: json-format <json_string>"

        try:
            parsed = json.loads(json_string)
            formatted = json.dumps(parsed, indent=2, ensure_ascii=False)
            return f"✅ Formatted JSON:\n{formatted}"

        except json.JSONDecodeError as e:
            return f"❌ Invalid JSON: {str(e)}"
        except Exception as e:
            return f"❌ Error formatting JSON: {str(e)}"

    def _count_lines_command(self, text: str = None) -> str:
        """Count lines, words, characters in text"""
        if not text:
            return "Usage: count-lines <text>"

        try:
            lines = text.split('\n')
            words = text.split()
            characters = len(text)
            characters_no_spaces = len(text.replace(' ', '').replace('\t', '').replace('\n', ''))

            result = f"""✅ Text statistics:
Lines: {len(lines)}
Words: {len(words)}
Characters: {characters}
Characters (no whitespace): {characters_no_spaces}
Average words per line: {len(words) / len(lines):.1f}
Average characters per word: {characters_no_spaces / len(words):.1f if words else 0}"""

            return result

        except Exception as e:
            return f"❌ Error counting: {str(e)}"
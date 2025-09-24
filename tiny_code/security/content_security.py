"""
Content Security Manager
Provides content filtering, size limits, and security scanning for downloaded content
"""

import hashlib
import mimetypes
import re
import logging
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
import json

logger = logging.getLogger(__name__)

@dataclass
class ContentSecurityConfig:
    """Configuration for content security settings"""
    # Size limits
    max_download_size_bytes: int = 50 * 1024 * 1024  # 50MB
    max_text_size_bytes: int = 10 * 1024 * 1024      # 10MB for text content
    max_image_size_bytes: int = 20 * 1024 * 1024     # 20MB for images

    # Content type filtering
    allowed_mime_types: List[str] = field(default_factory=lambda: [
        'text/html', 'text/plain', 'text/css', 'text/javascript',
        'application/json', 'application/xml', 'text/xml',
        'application/rss+xml', 'application/atom+xml',
        'image/jpeg', 'image/png', 'image/gif', 'image/webp'
    ])

    blocked_mime_types: List[str] = field(default_factory=lambda: [
        'application/x-executable', 'application/x-msdownload',
        'application/octet-stream', 'application/x-shockwave-flash',
        'application/x-msi', 'application/x-debian-package'
    ])

    # File extension filtering
    allowed_extensions: List[str] = field(default_factory=lambda: [
        '.html', '.htm', '.txt', '.json', '.xml', '.css', '.js',
        '.rss', '.atom', '.jpg', '.jpeg', '.png', '.gif', '.webp'
    ])

    blocked_extensions: List[str] = field(default_factory=lambda: [
        '.exe', '.msi', '.dmg', '.pkg', '.deb', '.rpm',
        '.bat', '.cmd', '.ps1', '.sh', '.scr', '.com', '.pif',
        '.dll', '.so', '.dylib'
    ])

    # Content scanning
    enable_malware_scanning: bool = True
    scan_for_suspicious_patterns: bool = True

class ContentSecurityViolation(Exception):
    """Exception raised when content security rules are violated"""
    def __init__(self, message: str, violation_type: str, details: Dict[str, Any] = None):
        super().__init__(message)
        self.violation_type = violation_type
        self.details = details or {}

class ContentSecurityManager:
    """Manages content security for downloaded data"""

    def __init__(self, config: ContentSecurityConfig = None):
        self.config = config or ContentSecurityConfig()

        # Malware signature patterns (simple heuristics)
        self.malware_patterns = [
            # Common malware signatures (bytes patterns in hex)
            b'MZ\x90\x00',  # Windows PE header
            b'PK\x03\x04',  # ZIP header (could contain malware)
            # JavaScript-based malware patterns
            rb'eval\s*\(\s*unescape\s*\(',
            rb'document\.write\s*\(\s*unescape\s*\(',
            # Suspicious scripts
            rb'<script[^>]*>[\s\S]*?(?:eval|unescape|fromCharCode)[\s\S]*?</script>',
        ]

        # Suspicious content patterns
        self.suspicious_patterns = [
            # Obfuscated JavaScript
            rb'var\s+[a-zA-Z_$][a-zA-Z0-9_$]*\s*=\s*[\'"]\w{50,}[\'"]',
            # Base64 encoded executables
            rb'data:application/octet-stream;base64,',
            # Excessive redirects
            rb'<meta\s+http-equiv=["\']refresh["\'][^>]*url=',
            # Suspicious iframes
            rb'<iframe[^>]*src=["\'](?:data:|javascript:|about:)[^>]*>',
        ]

        self.scan_results: List[Dict[str, Any]] = []

    def validate_content(
        self,
        content: bytes,
        content_type: Optional[str] = None,
        filename: Optional[str] = None,
        url: Optional[str] = None
    ) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """
        Validate downloaded content for security compliance

        Returns:
            Tuple of (is_valid, error_message, scan_results)
        """
        scan_results = {
            "timestamp": datetime.now().isoformat(),
            "url": url,
            "filename": filename,
            "content_type": content_type,
            "size_bytes": len(content),
            "checks_performed": [],
            "violations_found": [],
            "risk_level": "low"
        }

        try:
            # Check content size
            size_check = self._check_content_size(content, content_type)
            scan_results["checks_performed"].append("size_check")
            if not size_check[0]:
                scan_results["violations_found"].append({"type": "size_limit", "message": size_check[1]})
                scan_results["risk_level"] = "high"
                return False, size_check[1], scan_results

            # Check content type
            if content_type:
                type_check = self._check_content_type(content_type)
                scan_results["checks_performed"].append("content_type_check")
                if not type_check[0]:
                    scan_results["violations_found"].append({"type": "content_type", "message": type_check[1]})
                    scan_results["risk_level"] = "high"
                    return False, type_check[1], scan_results

            # Check file extension
            if filename:
                ext_check = self._check_file_extension(filename)
                scan_results["checks_performed"].append("extension_check")
                if not ext_check[0]:
                    scan_results["violations_found"].append({"type": "file_extension", "message": ext_check[1]})
                    scan_results["risk_level"] = "high"
                    return False, ext_check[1], scan_results

            # Perform malware scanning
            if self.config.enable_malware_scanning:
                malware_check = self._scan_for_malware(content)
                scan_results["checks_performed"].append("malware_scan")
                if malware_check[1]:  # Suspicious patterns found
                    scan_results["violations_found"].extend([
                        {"type": "malware_pattern", "pattern": pattern}
                        for pattern in malware_check[1]
                    ])
                    scan_results["risk_level"] = "critical"
                    return False, f"Malware patterns detected: {', '.join(malware_check[1])}", scan_results

            # Perform suspicious content scanning
            if self.config.scan_for_suspicious_patterns:
                suspicious_check = self._scan_for_suspicious_content(content)
                scan_results["checks_performed"].append("suspicious_content_scan")
                if suspicious_check[1]:  # Suspicious patterns found
                    scan_results["violations_found"].extend([
                        {"type": "suspicious_pattern", "pattern": pattern}
                        for pattern in suspicious_check[1]
                    ])
                    if scan_results["risk_level"] == "low":
                        scan_results["risk_level"] = "medium"

            # Log scan results
            self.scan_results.append(scan_results)

            # Clean up old results (keep last 1000)
            if len(self.scan_results) > 1000:
                self.scan_results = self.scan_results[-1000:]

            return True, None, scan_results

        except Exception as e:
            logger.error(f"Error during content validation: {e}")
            scan_results["violations_found"].append({"type": "validation_error", "message": str(e)})
            scan_results["risk_level"] = "high"
            return False, f"Content validation error: {str(e)}", scan_results

    def _check_content_size(self, content: bytes, content_type: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """Check if content size is within limits"""
        size = len(content)

        # Check general size limit
        if size > self.config.max_download_size_bytes:
            return False, f"Content size ({size} bytes) exceeds maximum allowed ({self.config.max_download_size_bytes} bytes)"

        # Check type-specific limits
        if content_type:
            if content_type.startswith('text/') and size > self.config.max_text_size_bytes:
                return False, f"Text content size ({size} bytes) exceeds limit ({self.config.max_text_size_bytes} bytes)"
            elif content_type.startswith('image/') and size > self.config.max_image_size_bytes:
                return False, f"Image size ({size} bytes) exceeds limit ({self.config.max_image_size_bytes} bytes)"

        return True, None

    def _check_content_type(self, content_type: str) -> Tuple[bool, Optional[str]]:
        """Check if content type is allowed"""
        content_type_lower = content_type.lower()

        # Check blocked types first
        for blocked_type in self.config.blocked_mime_types:
            if blocked_type.lower() in content_type_lower:
                return False, f"Content type '{content_type}' is blocked"

        # Check allowed types
        type_allowed = False
        for allowed_type in self.config.allowed_mime_types:
            if allowed_type.lower() in content_type_lower:
                type_allowed = True
                break

        if not type_allowed:
            return False, f"Content type '{content_type}' is not in allowed list"

        return True, None

    def _check_file_extension(self, filename: str) -> Tuple[bool, Optional[str]]:
        """Check if file extension is allowed"""
        filename_lower = filename.lower()

        # Check blocked extensions
        for blocked_ext in self.config.blocked_extensions:
            if filename_lower.endswith(blocked_ext.lower()):
                return False, f"File extension '{blocked_ext}' is blocked"

        # Check allowed extensions
        ext_allowed = False
        for allowed_ext in self.config.allowed_extensions:
            if filename_lower.endswith(allowed_ext.lower()):
                ext_allowed = True
                break

        # If no extension matches allowed list, block it
        if not ext_allowed and '.' in filename_lower:
            return False, f"File extension not in allowed list"

        return True, None

    def _scan_for_malware(self, content: bytes) -> Tuple[bool, List[str]]:
        """Scan content for malware patterns"""
        detected_patterns = []

        for i, pattern in enumerate(self.malware_patterns):
            if pattern in content:
                detected_patterns.append(f"malware_pattern_{i}")

        is_clean = len(detected_patterns) == 0
        return is_clean, detected_patterns

    def _scan_for_suspicious_content(self, content: bytes) -> Tuple[bool, List[str]]:
        """Scan content for suspicious patterns"""
        detected_patterns = []

        try:
            # Try to decode as text for pattern matching
            try:
                text_content = content.decode('utf-8', errors='ignore')
                text_bytes = text_content.encode('utf-8')
            except:
                text_bytes = content

            for i, pattern in enumerate(self.suspicious_patterns):
                if re.search(pattern, text_bytes, re.IGNORECASE | re.DOTALL):
                    detected_patterns.append(f"suspicious_pattern_{i}")

        except Exception as e:
            logger.warning(f"Error during suspicious content scanning: {e}")

        is_clean = len(detected_patterns) == 0
        return is_clean, detected_patterns

    def get_content_hash(self, content: bytes) -> str:
        """Generate SHA-256 hash of content"""
        return hashlib.sha256(content).hexdigest()

    def get_security_statistics(self) -> Dict[str, Any]:
        """Get security scanning statistics"""
        if not self.scan_results:
            return {"message": "No scans performed yet"}

        total_scans = len(self.scan_results)
        violations = sum(1 for result in self.scan_results if result["violations_found"])

        risk_levels = {}
        violation_types = {}

        for result in self.scan_results:
            risk_level = result["risk_level"]
            risk_levels[risk_level] = risk_levels.get(risk_level, 0) + 1

            for violation in result["violations_found"]:
                v_type = violation["type"]
                violation_types[v_type] = violation_types.get(v_type, 0) + 1

        return {
            "total_scans": total_scans,
            "violations_found": violations,
            "clean_scans": total_scans - violations,
            "risk_level_distribution": risk_levels,
            "violation_type_distribution": violation_types,
            "malware_scanning_enabled": self.config.enable_malware_scanning,
            "suspicious_pattern_scanning_enabled": self.config.scan_for_suspicious_patterns
        }

    def export_scan_log(self, filepath: str):
        """Export scan results for analysis"""
        log_data = {
            "export_timestamp": datetime.now().isoformat(),
            "config": {
                "max_download_size_bytes": self.config.max_download_size_bytes,
                "enable_malware_scanning": self.config.enable_malware_scanning,
                "scan_for_suspicious_patterns": self.config.scan_for_suspicious_patterns,
                "allowed_mime_types_count": len(self.config.allowed_mime_types),
                "blocked_mime_types_count": len(self.config.blocked_mime_types)
            },
            "scan_results": self.scan_results,
            "statistics": self.get_security_statistics()
        }

        with open(filepath, 'w') as f:
            json.dump(log_data, f, indent=2)

        logger.info(f"Content security log exported to {filepath}")

# Convenience function
def create_default_content_security() -> ContentSecurityManager:
    """Create ContentSecurityManager with safe default settings"""
    config = ContentSecurityConfig(
        max_download_size_bytes=25 * 1024 * 1024,  # 25MB conservative limit
        enable_malware_scanning=True,
        scan_for_suspicious_patterns=True
    )
    return ContentSecurityManager(config)
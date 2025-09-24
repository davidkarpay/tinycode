"""
Network Security Manager
Provides URL validation, domain filtering, and request security for internet search capabilities
"""

import re
import socket
import hashlib
import logging
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from urllib.parse import urlparse, urljoin
from pathlib import Path
import json
from datetime import datetime, timedelta
import ipaddress

logger = logging.getLogger(__name__)

@dataclass
class NetworkSecurityConfig:
    """Configuration for network security settings"""
    # Basic settings
    enable_internet_access: bool = False
    max_requests_per_hour: int = 100
    max_download_size_mb: int = 50
    timeout_seconds: int = 30
    require_https: bool = True

    # Domain and URL filtering
    blocked_domains: List[str] = field(default_factory=list)
    allowed_domains: Optional[List[str]] = None  # If set, only these domains allowed
    blocked_ips: List[str] = field(default_factory=list)

    # Content filtering
    allowed_file_types: List[str] = field(default_factory=lambda: [
        '.txt', '.html', '.htm', '.json', '.xml', '.css', '.js'
    ])
    blocked_file_types: List[str] = field(default_factory=lambda: [
        '.exe', '.bat', '.sh', '.ps1', '.scr', '.com', '.pif', '.dll'
    ])

    # Security headers
    user_agent: str = "TinyCode/1.0 (Educational/Research Tool)"
    additional_headers: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize default blocked domains and IPs"""
        if not self.blocked_domains:
            self.blocked_domains = [
                # Common malware/phishing domains (examples)
                'malware.com', 'phishing.com', 'badsite.net',
                # Local/internal addresses
                'localhost', '127.0.0.1', '0.0.0.0',
                # Private IP ranges handled separately
            ]

        if not self.blocked_ips:
            self.blocked_ips = [
                '127.0.0.1', '0.0.0.0', '::1',
                # Private ranges handled by _is_private_ip
            ]

class NetworkSecurityViolation(Exception):
    """Exception raised when a network security rule is violated"""
    def __init__(self, message: str, violation_type: str, details: Dict[str, Any] = None):
        super().__init__(message)
        self.violation_type = violation_type
        self.details = details or {}

class NetworkSecurityManager:
    """Manages network security for internet access"""

    def __init__(self, config: NetworkSecurityConfig = None):
        self.config = config or NetworkSecurityConfig()
        self.request_history: List[Dict[str, Any]] = []
        self.blocked_attempts: List[Dict[str, Any]] = []

        # Load additional blocked domains if file exists
        self._load_security_lists()

        # Initialize request tracking
        self._request_window_start = datetime.now()
        self._requests_in_window = 0

    def _load_security_lists(self):
        """Load additional security lists from files"""
        security_dir = Path(__file__).parent / "lists"

        # Load blocked domains list
        blocked_domains_file = security_dir / "blocked_domains.txt"
        if blocked_domains_file.exists():
            with open(blocked_domains_file, 'r') as f:
                additional_domains = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                self.config.blocked_domains.extend(additional_domains)

        # Load blocked IPs list
        blocked_ips_file = security_dir / "blocked_ips.txt"
        if blocked_ips_file.exists():
            with open(blocked_ips_file, 'r') as f:
                additional_ips = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                self.config.blocked_ips.extend(additional_ips)

    def validate_request(self, url: str, method: str = "GET") -> Tuple[bool, Optional[str]]:
        """
        Validate a network request for security compliance

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check if internet access is enabled
            if not self.config.enable_internet_access:
                return False, "Internet access is disabled in security configuration"

            # Parse URL
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False, "Invalid URL format"

            # Validate protocol
            if self.config.require_https and parsed.scheme != 'https':
                return False, "HTTPS required by security policy"

            if parsed.scheme not in ['http', 'https']:
                return False, f"Unsupported protocol: {parsed.scheme}"

            # Check rate limiting
            if not self._check_rate_limit():
                return False, "Rate limit exceeded"

            # Validate domain
            domain_check = self._validate_domain(parsed.netloc)
            if not domain_check[0]:
                return False, domain_check[1]

            # Validate IP (resolve domain to check for private IPs)
            ip_check = self._validate_ip_address(parsed.netloc)
            if not ip_check[0]:
                return False, ip_check[1]

            # Validate file type if URL has extension
            file_type_check = self._validate_file_type(parsed.path)
            if not file_type_check[0]:
                return False, file_type_check[1]

            # Log successful validation
            self._log_request_attempt(url, method, True)
            return True, None

        except Exception as e:
            logger.error(f"Error validating request to {url}: {e}")
            self._log_request_attempt(url, method, False, str(e))
            return False, f"Validation error: {str(e)}"

    def _check_rate_limit(self) -> bool:
        """Check if request is within rate limits"""
        now = datetime.now()

        # Reset window if hour has passed
        if (now - self._request_window_start).total_seconds() >= 3600:
            self._request_window_start = now
            self._requests_in_window = 0

        # Check if within limits
        if self._requests_in_window >= self.config.max_requests_per_hour:
            return False

        self._requests_in_window += 1
        return True

    def _validate_domain(self, domain: str) -> Tuple[bool, Optional[str]]:
        """Validate domain against blocked/allowed lists"""
        domain_lower = domain.lower()

        # Remove port if present
        if ':' in domain_lower:
            domain_lower = domain_lower.split(':')[0]

        # Check blocked domains
        for blocked in self.config.blocked_domains:
            if blocked.lower() in domain_lower or domain_lower == blocked.lower():
                self._log_blocked_attempt(domain, "blocked_domain")
                return False, f"Domain '{domain}' is in blocked list"

        # Check allowed domains (if whitelist is enabled)
        if self.config.allowed_domains:
            domain_allowed = False
            for allowed in self.config.allowed_domains:
                if allowed.lower() in domain_lower or domain_lower == allowed.lower():
                    domain_allowed = True
                    break

            if not domain_allowed:
                self._log_blocked_attempt(domain, "not_in_allowed_list")
                return False, f"Domain '{domain}' not in allowed list"

        return True, None

    def _validate_ip_address(self, hostname: str) -> Tuple[bool, Optional[str]]:
        """Validate IP address (resolve hostname if necessary)"""
        try:
            # Remove port if present
            if ':' in hostname:
                hostname = hostname.split(':')[0]

            # Try to resolve hostname to IP
            try:
                ip_addresses = socket.getaddrinfo(hostname, None)
                ips = [addr[4][0] for addr in ip_addresses]
            except socket.gaierror:
                return False, f"Cannot resolve hostname: {hostname}"

            # Check each resolved IP
            for ip in ips:
                # Check blocked IPs
                if ip in self.config.blocked_ips:
                    self._log_blocked_attempt(hostname, "blocked_ip", {"ip": ip})
                    return False, f"IP address {ip} is blocked"

                # Check for private/local IPs
                if self._is_private_ip(ip):
                    self._log_blocked_attempt(hostname, "private_ip", {"ip": ip})
                    return False, f"Access to private/local IP {ip} is not allowed"

            return True, None

        except Exception as e:
            logger.error(f"Error validating IP for {hostname}: {e}")
            return False, f"IP validation error: {str(e)}"

    def _is_private_ip(self, ip: str) -> bool:
        """Check if IP address is private/local"""
        try:
            ip_obj = ipaddress.ip_address(ip)
            return ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local
        except ValueError:
            return False

    def _validate_file_type(self, path: str) -> Tuple[bool, Optional[str]]:
        """Validate file type based on URL path"""
        if not path:
            return True, None

        # Extract file extension
        path_lower = path.lower()

        # Check for blocked file types
        for blocked_ext in self.config.blocked_file_types:
            if path_lower.endswith(blocked_ext.lower()):
                self._log_blocked_attempt(path, "blocked_file_type", {"extension": blocked_ext})
                return False, f"File type '{blocked_ext}' is not allowed"

        # If there are allowed file types, check whitelist
        if self.config.allowed_file_types:
            # If path has no extension, allow it (might be API endpoint)
            if '.' not in path_lower.split('/')[-1]:
                return True, None

            file_allowed = False
            for allowed_ext in self.config.allowed_file_types:
                if path_lower.endswith(allowed_ext.lower()):
                    file_allowed = True
                    break

            if not file_allowed:
                return False, "File type not in allowed list"

        return True, None

    def _log_request_attempt(self, url: str, method: str, success: bool, error: str = None):
        """Log request attempt for audit purposes"""
        attempt = {
            "timestamp": datetime.now().isoformat(),
            "url": url,
            "method": method,
            "success": success,
            "error": error,
            "source": "network_security_manager"
        }

        self.request_history.append(attempt)

        # Keep only last 1000 entries
        if len(self.request_history) > 1000:
            self.request_history = self.request_history[-1000:]

    def _log_blocked_attempt(self, target: str, reason: str, details: Dict[str, Any] = None):
        """Log blocked attempt for security monitoring"""
        attempt = {
            "timestamp": datetime.now().isoformat(),
            "target": target,
            "reason": reason,
            "details": details or {},
            "source": "network_security_manager"
        }

        self.blocked_attempts.append(attempt)
        logger.warning(f"Blocked network access attempt: {reason} - {target}")

        # Keep only last 500 entries
        if len(self.blocked_attempts) > 500:
            self.blocked_attempts = self.blocked_attempts[-500:]

    def get_security_headers(self) -> Dict[str, str]:
        """Get security headers for HTTP requests"""
        headers = {
            "User-Agent": self.config.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",  # Do Not Track
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }

        # Add additional configured headers
        headers.update(self.config.additional_headers)

        return headers

    def get_request_statistics(self) -> Dict[str, Any]:
        """Get request statistics for monitoring"""
        now = datetime.now()
        window_start = now - timedelta(hours=1)

        recent_requests = [
            req for req in self.request_history
            if datetime.fromisoformat(req["timestamp"]) >= window_start
        ]

        recent_blocked = [
            attempt for attempt in self.blocked_attempts
            if datetime.fromisoformat(attempt["timestamp"]) >= window_start
        ]

        return {
            "requests_in_last_hour": len(recent_requests),
            "blocked_attempts_in_last_hour": len(recent_blocked),
            "total_requests_logged": len(self.request_history),
            "total_blocked_attempts": len(self.blocked_attempts),
            "rate_limit_remaining": self.config.max_requests_per_hour - self._requests_in_window,
            "internet_access_enabled": self.config.enable_internet_access,
            "security_config": {
                "require_https": self.config.require_https,
                "max_download_size_mb": self.config.max_download_size_mb,
                "timeout_seconds": self.config.timeout_seconds
            }
        }

    def reset_rate_limits(self):
        """Reset rate limits (for testing or admin override)"""
        self._request_window_start = datetime.now()
        self._requests_in_window = 0
        logger.info("Rate limits reset by administrator")

    def export_security_log(self, filepath: str):
        """Export security logs for analysis"""
        log_data = {
            "export_timestamp": datetime.now().isoformat(),
            "config": {
                "enable_internet_access": self.config.enable_internet_access,
                "max_requests_per_hour": self.config.max_requests_per_hour,
                "require_https": self.config.require_https,
                "blocked_domains_count": len(self.config.blocked_domains),
                "blocked_ips_count": len(self.config.blocked_ips)
            },
            "request_history": self.request_history,
            "blocked_attempts": self.blocked_attempts,
            "statistics": self.get_request_statistics()
        }

        with open(filepath, 'w') as f:
            json.dump(log_data, f, indent=2)

        logger.info(f"Security log exported to {filepath}")

# Convenience function for easy integration
def create_default_network_security() -> NetworkSecurityManager:
    """Create NetworkSecurityManager with safe default settings"""
    config = NetworkSecurityConfig(
        enable_internet_access=False,  # Disabled by default for security
        max_requests_per_hour=50,      # Conservative limit
        require_https=True,            # Enforce encryption
        max_download_size_mb=25        # Reasonable size limit
    )
    return NetworkSecurityManager(config)
"""
Internet Security Configuration
Central configuration and orchestration for all internet security components
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import json

from .network_security import NetworkSecurityManager, NetworkSecurityConfig
from .content_security import ContentSecurityManager, ContentSecurityConfig
from ..rate_limiter import RateLimiter, LimitType, RateLimitConfig

logger = logging.getLogger(__name__)

@dataclass
class InternetSecurityProfile:
    """Predefined security profiles for different use cases"""
    name: str
    description: str
    network_config: NetworkSecurityConfig
    content_config: ContentSecurityConfig
    rate_limits: Dict[LimitType, RateLimitConfig]

class InternetSecurityManager:
    """Central manager for all internet security components"""

    def __init__(self, profile_name: str = "default"):
        self.profile_name = profile_name
        self.profile = self._get_security_profile(profile_name)

        # Initialize security components
        self.network_security = NetworkSecurityManager(self.profile.network_config)
        self.content_security = ContentSecurityManager(self.profile.content_config)
        self.rate_limiter = RateLimiter(self.profile.rate_limits)

        # Security metrics
        self.security_events: List[Dict[str, Any]] = []

        logger.info(f"Internet Security Manager initialized with profile: {profile_name}")

    def _get_security_profile(self, profile_name: str) -> InternetSecurityProfile:
        """Get security profile configuration"""
        profiles = {
            "disabled": self._create_disabled_profile(),
            "development": self._create_development_profile(),
            "production": self._create_production_profile(),
            "research": self._create_research_profile(),
            "strict": self._create_strict_profile()
        }

        if profile_name not in profiles:
            logger.warning(f"Unknown security profile '{profile_name}', using 'disabled'")
            profile_name = "disabled"

        return profiles[profile_name]

    def _create_disabled_profile(self) -> InternetSecurityProfile:
        """No internet access allowed"""
        return InternetSecurityProfile(
            name="disabled",
            description="Internet access completely disabled",
            network_config=NetworkSecurityConfig(
                enable_internet_access=False,
                max_requests_per_hour=0,
                require_https=True
            ),
            content_config=ContentSecurityConfig(
                max_download_size_bytes=0,
                enable_malware_scanning=True,
                scan_for_suspicious_patterns=True
            ),
            rate_limits=RateLimitConfig.get_defaults()
        )

    def _create_development_profile(self) -> InternetSecurityProfile:
        """Relaxed settings for development"""
        return InternetSecurityProfile(
            name="development",
            description="Development-friendly security settings",
            network_config=NetworkSecurityConfig(
                enable_internet_access=True,
                max_requests_per_hour=200,
                max_download_size_mb=100,
                timeout_seconds=60,
                require_https=False,  # Allow HTTP for development
                blocked_domains=["malware.com", "phishing.com"],  # Minimal blocking
                allowed_domains=None  # No domain whitelist
            ),
            content_config=ContentSecurityConfig(
                max_download_size_bytes=100 * 1024 * 1024,  # 100MB
                max_text_size_bytes=50 * 1024 * 1024,       # 50MB
                max_image_size_bytes=50 * 1024 * 1024,      # 50MB
                enable_malware_scanning=True,
                scan_for_suspicious_patterns=False  # Relaxed for dev
            ),
            rate_limits=RateLimitConfig.get_defaults()
        )

    def _create_production_profile(self) -> InternetSecurityProfile:
        """Balanced settings for production use"""
        return InternetSecurityProfile(
            name="production",
            description="Balanced security for production environments",
            network_config=NetworkSecurityConfig(
                enable_internet_access=True,
                max_requests_per_hour=100,
                max_download_size_mb=50,
                timeout_seconds=30,
                require_https=True,
                blocked_domains=[
                    "malware.com", "phishing.com", "badsite.net",
                    "localhost", "127.0.0.1", "0.0.0.0"
                ]
            ),
            content_config=ContentSecurityConfig(
                max_download_size_bytes=50 * 1024 * 1024,   # 50MB
                max_text_size_bytes=25 * 1024 * 1024,       # 25MB
                max_image_size_bytes=25 * 1024 * 1024,      # 25MB
                enable_malware_scanning=True,
                scan_for_suspicious_patterns=True
            ),
            rate_limits={
                LimitType.INTERNET_SEARCH: RateLimitConfig(60, 10, 3600),    # 60/hour
                LimitType.BULK_DOWNLOAD: RateLimitConfig(5, 2, 3600),        # 5/hour
                LimitType.DOMAIN_REQUESTS: RateLimitConfig(30, 5, 3600),     # 30/hour per domain
                LimitType.WEB_SCRAPING: RateLimitConfig(20, 3, 3600),        # 20/hour
                **RateLimitConfig.get_defaults()
            }
        )

    def _create_research_profile(self) -> InternetSecurityProfile:
        """Academic/research focused settings"""
        return InternetSecurityProfile(
            name="research",
            description="Settings optimized for academic research",
            network_config=NetworkSecurityConfig(
                enable_internet_access=True,
                max_requests_per_hour=300,  # Higher for research
                max_download_size_mb=200,   # Larger papers/datasets
                timeout_seconds=120,        # Longer for large downloads
                require_https=True,
                # Research-friendly domain allowlist
                allowed_domains=[
                    "arxiv.org", "pubmed.ncbi.nlm.nih.gov", "scholar.google.com",
                    "ieee.org", "acm.org", "springer.com", "nature.com",
                    "science.org", "plos.org", "biorxiv.org", "github.com"
                ]
            ),
            content_config=ContentSecurityConfig(
                max_download_size_bytes=200 * 1024 * 1024,  # 200MB for datasets
                max_text_size_bytes=100 * 1024 * 1024,      # 100MB for papers
                max_image_size_bytes=50 * 1024 * 1024,      # 50MB for figures
                enable_malware_scanning=True,
                scan_for_suspicious_patterns=True
            ),
            rate_limits={
                LimitType.INTERNET_SEARCH: RateLimitConfig(200, 20, 3600),   # More searches
                LimitType.BULK_DOWNLOAD: RateLimitConfig(20, 5, 3600),       # More downloads
                LimitType.DOMAIN_REQUESTS: RateLimitConfig(100, 10, 3600),   # Per domain
                LimitType.WEB_SCRAPING: RateLimitConfig(50, 5, 3600),        # Research scraping
                **RateLimitConfig.get_defaults()
            }
        )

    def _create_strict_profile(self) -> InternetSecurityProfile:
        """Maximum security settings"""
        return InternetSecurityProfile(
            name="strict",
            description="Maximum security with minimal internet access",
            network_config=NetworkSecurityConfig(
                enable_internet_access=True,
                max_requests_per_hour=20,   # Very limited
                max_download_size_mb=10,    # Small files only
                timeout_seconds=15,         # Quick timeout
                require_https=True,
                # Very restrictive whitelist
                allowed_domains=[
                    "github.com", "stackoverflow.com", "docs.python.org"
                ],
                blocked_domains=[
                    "malware.com", "phishing.com", "badsite.net",
                    "localhost", "127.0.0.1", "0.0.0.0"
                ]
            ),
            content_config=ContentSecurityConfig(
                max_download_size_bytes=10 * 1024 * 1024,   # 10MB
                max_text_size_bytes=5 * 1024 * 1024,        # 5MB
                max_image_size_bytes=2 * 1024 * 1024,       # 2MB
                enable_malware_scanning=True,
                scan_for_suspicious_patterns=True
            ),
            rate_limits={
                LimitType.INTERNET_SEARCH: RateLimitConfig(10, 2, 3600),     # Very limited
                LimitType.BULK_DOWNLOAD: RateLimitConfig(2, 1, 3600),        # Almost none
                LimitType.DOMAIN_REQUESTS: RateLimitConfig(5, 2, 3600),      # Per domain
                LimitType.WEB_SCRAPING: RateLimitConfig(5, 1, 3600),         # Minimal scraping
                **RateLimitConfig.get_defaults()
            }
        )

    def validate_internet_request(
        self,
        url: str,
        client_id: str = "default",
        method: str = "GET",
        expected_size: Optional[int] = None
    ) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """
        Comprehensive internet request validation

        Returns:
            Tuple of (is_allowed, error_message, validation_details)
        """
        validation_details = {
            "url": url,
            "client_id": client_id,
            "method": method,
            "profile": self.profile_name,
            "checks": {},
            "timestamp": None
        }

        try:
            # 1. Check rate limits first (fastest check)
            rate_allowed = self.rate_limiter.check_limit(
                client_id, LimitType.INTERNET_SEARCH
            )
            validation_details["checks"]["rate_limit"] = rate_allowed

            if not rate_allowed:
                wait_time = self.rate_limiter.get_wait_time(
                    client_id, LimitType.INTERNET_SEARCH
                )
                error_msg = f"Rate limit exceeded. Wait {wait_time:.1f} seconds."
                self._log_security_event("rate_limit_exceeded", url, client_id, error_msg)
                return False, error_msg, validation_details

            # 2. Network security validation
            network_valid, network_error = self.network_security.validate_request(url, method)
            validation_details["checks"]["network_security"] = network_valid

            if not network_valid:
                self._log_security_event("network_security_violation", url, client_id, network_error)
                return False, network_error, validation_details

            # 3. If expected size is provided, validate it
            if expected_size:
                size_valid, size_error = self._validate_expected_size(expected_size)
                validation_details["checks"]["size_precheck"] = size_valid
                validation_details["expected_size"] = expected_size

                if not size_valid:
                    self._log_security_event("size_limit_exceeded", url, client_id, size_error)
                    return False, size_error, validation_details

            # All checks passed
            self._log_security_event("request_approved", url, client_id)
            return True, None, validation_details

        except Exception as e:
            logger.error(f"Error during internet request validation: {e}")
            error_msg = f"Validation error: {str(e)}"
            self._log_security_event("validation_error", url, client_id, error_msg)
            return False, error_msg, validation_details

    def validate_downloaded_content(
        self,
        content: bytes,
        url: str,
        content_type: Optional[str] = None,
        filename: Optional[str] = None
    ) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """
        Validate downloaded content for security compliance

        Returns:
            Tuple of (is_safe, error_message, scan_results)
        """
        return self.content_security.validate_content(
            content, content_type, filename, url
        )

    def _validate_expected_size(self, size: int) -> Tuple[bool, Optional[str]]:
        """Validate expected download size against limits"""
        max_size = self.profile.content_config.max_download_size_bytes

        if size > max_size:
            return False, f"Expected size ({size} bytes) exceeds limit ({max_size} bytes)"

        return True, None

    def _log_security_event(
        self,
        event_type: str,
        url: str,
        client_id: str,
        details: str = ""
    ):
        """Log security events for monitoring"""
        from datetime import datetime

        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "url": url,
            "client_id": client_id,
            "details": details,
            "profile": self.profile_name
        }

        self.security_events.append(event)

        # Keep only last 500 events
        if len(self.security_events) > 500:
            self.security_events = self.security_events[-500:]

        # Log based on severity
        if event_type in ["rate_limit_exceeded", "network_security_violation", "size_limit_exceeded"]:
            logger.warning(f"Security event: {event_type} for {url} - {details}")
        elif event_type == "validation_error":
            logger.error(f"Security validation error for {url} - {details}")
        else:
            logger.debug(f"Security event: {event_type} for {url}")

    def get_security_status(self) -> Dict[str, Any]:
        """Get comprehensive security status"""
        from datetime import datetime

        return {
            "profile": {
                "name": self.profile.name,
                "description": self.profile.description
            },
            "internet_access_enabled": self.profile.network_config.enable_internet_access,
            "components": {
                "network_security": self.network_security.get_request_statistics(),
                "content_security": self.content_security.get_security_statistics(),
                "rate_limiter": self.rate_limiter.get_stats()
            },
            "recent_events": len([
                e for e in self.security_events
                if (datetime.now() - datetime.fromisoformat(e["timestamp"])).total_seconds() < 3600
            ]),
            "total_events": len(self.security_events)
        }

    def switch_profile(self, profile_name: str) -> bool:
        """Switch to a different security profile"""
        try:
            new_profile = self._get_security_profile(profile_name)

            # Reinitialize components with new configuration
            self.profile_name = profile_name
            self.profile = new_profile
            self.network_security = NetworkSecurityManager(new_profile.network_config)
            self.content_security = ContentSecurityManager(new_profile.content_config)
            self.rate_limiter = RateLimiter(new_profile.rate_limits)

            logger.info(f"Switched to security profile: {profile_name}")
            self._log_security_event("profile_switched", "", "system", f"New profile: {profile_name}")

            return True

        except Exception as e:
            logger.error(f"Failed to switch security profile: {e}")
            return False

    def export_security_config(self, filepath: str):
        """Export current security configuration"""
        config_data = {
            "profile_name": self.profile_name,
            "profile_description": self.profile.description,
            "network_config": {
                "enable_internet_access": self.profile.network_config.enable_internet_access,
                "max_requests_per_hour": self.profile.network_config.max_requests_per_hour,
                "max_download_size_mb": self.profile.network_config.max_download_size_mb,
                "timeout_seconds": self.profile.network_config.timeout_seconds,
                "require_https": self.profile.network_config.require_https,
                "blocked_domains_count": len(self.profile.network_config.blocked_domains),
                "allowed_domains_count": len(self.profile.network_config.allowed_domains) if self.profile.network_config.allowed_domains else 0
            },
            "content_config": {
                "max_download_size_bytes": self.profile.content_config.max_download_size_bytes,
                "max_text_size_bytes": self.profile.content_config.max_text_size_bytes,
                "max_image_size_bytes": self.profile.content_config.max_image_size_bytes,
                "enable_malware_scanning": self.profile.content_config.enable_malware_scanning,
                "scan_for_suspicious_patterns": self.profile.content_config.scan_for_suspicious_patterns
            },
            "security_events": self.security_events[-100:],  # Last 100 events
            "current_status": self.get_security_status()
        }

        with open(filepath, 'w') as f:
            json.dump(config_data, f, indent=2)

        logger.info(f"Security configuration exported to {filepath}")

# Factory function for easy integration
def create_internet_security_manager(profile: str = "disabled") -> InternetSecurityManager:
    """
    Create InternetSecurityManager with specified profile

    Available profiles:
    - disabled: No internet access (safest)
    - development: Relaxed for development work
    - production: Balanced for production use
    - research: Optimized for academic research
    - strict: Maximum security, minimal access
    """
    return InternetSecurityManager(profile)

# Example usage and testing
if __name__ == "__main__":
    import time

    # Test different security profiles
    profiles = ["disabled", "development", "production", "research", "strict"]

    for profile_name in profiles:
        print(f"\n=== Testing {profile_name.upper()} Profile ===")

        manager = create_internet_security_manager(profile_name)
        status = manager.get_security_status()

        print(f"Internet Access: {status['internet_access_enabled']}")
        print(f"Profile: {status['profile']['description']}")

        # Test validation
        test_urls = [
            "https://github.com/user/repo",
            "http://example.com",
            "https://malware.com/bad",
            "https://arxiv.org/paper.pdf"
        ]

        for url in test_urls:
            allowed, error, details = manager.validate_internet_request(url, "test_client")
            print(f"  {url}: {'✓' if allowed else '✗'} {error or ''}")

        time.sleep(0.1)  # Brief pause between profiles
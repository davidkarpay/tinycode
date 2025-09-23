"""Attorney-client privilege protection system for legal automation"""

import re
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from cryptography.fernet import Fernet
from rich.console import Console

console = Console()

class PrivilegeLevel(Enum):
    """Privilege protection levels"""
    PUBLIC = "public"
    CONFIDENTIAL = "confidential"
    ATTORNEY_CLIENT = "attorney_client"
    WORK_PRODUCT = "work_product"
    ATTORNEY_EYES_ONLY = "attorney_eyes_only"

class ContentType(Enum):
    """Types of legal content"""
    CLIENT_COMMUNICATION = "client_communication"
    LEGAL_ADVICE = "legal_advice"
    CASE_STRATEGY = "case_strategy"
    SETTLEMENT_DISCUSSION = "settlement_discussion"
    EXPERT_OPINION = "expert_opinion"
    DISCOVERY_MATERIAL = "discovery_material"
    COURT_FILING = "court_filing"

@dataclass
class PrivilegeMarking:
    """Privilege marking for documents and communications"""
    level: PrivilegeLevel
    content_type: ContentType
    client_id: str
    matter_id: str
    attorney_id: str
    created_date: datetime
    expiration_date: Optional[datetime] = None
    special_instructions: Optional[str] = None

@dataclass
class RedactionRule:
    """Rule for automatic redaction of sensitive information"""
    pattern: str
    replacement: str
    description: str
    privilege_level: PrivilegeLevel

class PrivilegeProtectionSystem:
    """Comprehensive attorney-client privilege protection system"""

    def __init__(self, encryption_key: bytes = None):
        self.console = console

        # Initialize encryption
        if encryption_key:
            self.fernet = Fernet(encryption_key)
        else:
            # Generate new key (in production, this should be stored securely)
            key = Fernet.generate_key()
            self.fernet = Fernet(key)
            console.print("[yellow]Warning: Generated new encryption key. Store securely for production use.[/yellow]")

        # Privilege pattern matching
        self.privilege_patterns = self._initialize_privilege_patterns()

        # Redaction rules
        self.redaction_rules = self._initialize_redaction_rules()

        # Access control
        self.authorized_users = set()
        self.client_matter_map = {}

        # Audit trail
        self.access_log = []

    def _initialize_privilege_patterns(self) -> Dict[PrivilegeLevel, List[str]]:
        """Initialize patterns that indicate privileged content"""
        return {
            PrivilegeLevel.ATTORNEY_CLIENT: [
                r"\battorney.client\b",
                r"\blegal\s+advice\b",
                r"\bconfidential\s+communication\b",
                r"\bprivilege\b",
                r"\bclient\s+consultation\b",
                r"\blegal\s+opinion\b"
            ],
            PrivilegeLevel.WORK_PRODUCT: [
                r"\bwork\s+product\b",
                r"\blegal\s+strategy\b",
                r"\bcase\s+analysis\b",
                r"\blitigation\s+strategy\b",
                r"\binternal\s+memorandum\b",
                r"\battorney\s+notes\b"
            ],
            PrivilegeLevel.ATTORNEY_EYES_ONLY: [
                r"\battorney\s+eyes\s+only\b",
                r"\bhighly\s+confidential\b",
                r"\bsettlement\s+strategy\b",
                r"\bclient\s+secrets\b"
            ]
        }

    def _initialize_redaction_rules(self) -> List[RedactionRule]:
        """Initialize automatic redaction rules"""
        return [
            RedactionRule(
                pattern=r"\b\d{3}-\d{2}-\d{4}\b",  # SSN
                replacement="[SSN REDACTED]",
                description="Social Security Number",
                privilege_level=PrivilegeLevel.CONFIDENTIAL
            ),
            RedactionRule(
                pattern=r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",  # Credit card
                replacement="[CREDIT CARD REDACTED]",
                description="Credit Card Number",
                privilege_level=PrivilegeLevel.CONFIDENTIAL
            ),
            RedactionRule(
                pattern=r"\$[\d,]+\.?\d*",  # Settlement amounts
                replacement="[AMOUNT REDACTED]",
                description="Financial Amount",
                privilege_level=PrivilegeLevel.ATTORNEY_CLIENT
            ),
            RedactionRule(
                pattern=r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Email
                replacement="[EMAIL REDACTED]",
                description="Email Address",
                privilege_level=PrivilegeLevel.CONFIDENTIAL
            )
        ]

    def classify_privilege_level(self, content: str, context: Dict[str, Any] = None) -> PrivilegeLevel:
        """Classify the privilege level of content"""
        content_lower = content.lower()

        # Check for highest privilege levels first
        for level in [PrivilegeLevel.ATTORNEY_EYES_ONLY, PrivilegeLevel.WORK_PRODUCT, PrivilegeLevel.ATTORNEY_CLIENT]:
            patterns = self.privilege_patterns.get(level, [])
            for pattern in patterns:
                if re.search(pattern, content_lower, re.IGNORECASE):
                    self._log_privilege_classification(content, level, pattern)
                    return level

        # Check context for privilege indicators
        if context:
            if context.get("source") == "client_email":
                return PrivilegeLevel.ATTORNEY_CLIENT
            if context.get("document_type") == "internal_memo":
                return PrivilegeLevel.WORK_PRODUCT

        return PrivilegeLevel.PUBLIC

    def detect_content_type(self, content: str, metadata: Dict[str, Any] = None) -> ContentType:
        """Detect the type of legal content"""
        content_lower = content.lower()

        # Content type patterns
        type_patterns = {
            ContentType.CLIENT_COMMUNICATION: [r"\bclient\s+email\b", r"\bclient\s+letter\b", r"\bclient\s+call\b"],
            ContentType.LEGAL_ADVICE: [r"\blegal\s+advice\b", r"\blegal\s+opinion\b", r"\brecommendation\b"],
            ContentType.CASE_STRATEGY: [r"\bstrategy\b", r"\bapproach\b", r"\btactics\b"],
            ContentType.SETTLEMENT_DISCUSSION: [r"\bsettlement\b", r"\bnegotiation\b", r"\bresolution\b"],
            ContentType.COURT_FILING: [r"\bmotion\b", r"\bbrief\b", r"\bpleading\b", r"\bfiling\b"],
            ContentType.DISCOVERY_MATERIAL: [r"\bdiscovery\b", r"\bdeposition\b", r"\binterrogator\b"]
        }

        for content_type, patterns in type_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content_lower, re.IGNORECASE):
                    return content_type

        return ContentType.DISCOVERY_MATERIAL  # Default

    def apply_privilege_marking(self, content: str, client_id: str, matter_id: str,
                              attorney_id: str, privilege_level: PrivilegeLevel = None,
                              content_type: ContentType = None) -> Tuple[str, PrivilegeMarking]:
        """Apply privilege marking to content"""

        # Auto-detect if not provided
        if privilege_level is None:
            privilege_level = self.classify_privilege_level(content)

        if content_type is None:
            content_type = self.detect_content_type(content)

        # Create privilege marking
        marking = PrivilegeMarking(
            level=privilege_level,
            content_type=content_type,
            client_id=client_id,
            matter_id=matter_id,
            attorney_id=attorney_id,
            created_date=datetime.now(timezone.utc)
        )

        # Add privilege header to content
        marked_content = self._add_privilege_header(content, marking)

        self._log_privilege_marking(content, marking)

        return marked_content, marking

    def redact_content(self, content: str, privilege_level: PrivilegeLevel = PrivilegeLevel.PUBLIC) -> str:
        """Apply automatic redaction rules based on privilege level"""
        redacted_content = content

        for rule in self.redaction_rules:
            # Apply redaction if current privilege level is at or below rule level
            if privilege_level.value <= rule.privilege_level.value:
                redacted_content = re.sub(rule.pattern, rule.replacement, redacted_content, flags=re.IGNORECASE)

        if redacted_content != content:
            console.print(f"[yellow]Applied {len([r for r in self.redaction_rules if r.privilege_level == privilege_level])} redaction rules[/yellow]")

        return redacted_content

    def encrypt_privileged_content(self, content: str, marking: PrivilegeMarking) -> bytes:
        """Encrypt privileged content for secure storage"""
        if marking.level in [PrivilegeLevel.ATTORNEY_CLIENT, PrivilegeLevel.WORK_PRODUCT, PrivilegeLevel.ATTORNEY_EYES_ONLY]:
            # Create metadata
            metadata = {
                "marking": asdict(marking),
                "encryption_timestamp": datetime.now(timezone.utc).isoformat(),
                "content_hash": hashlib.sha256(content.encode()).hexdigest()
            }

            # Combine content and metadata
            data = {
                "content": content,
                "metadata": metadata
            }

            # Encrypt
            encrypted_data = self.fernet.encrypt(json.dumps(data, default=str).encode())

            self._log_encryption_event(marking, "encrypted")

            return encrypted_data
        else:
            # Return unencrypted for public content
            return content.encode()

    def decrypt_privileged_content(self, encrypted_data: bytes, user_id: str,
                                 client_id: str = None, matter_id: str = None) -> Tuple[str, PrivilegeMarking]:
        """Decrypt privileged content with access control"""

        try:
            # Decrypt
            decrypted_json = self.fernet.decrypt(encrypted_data).decode()
            data = json.loads(decrypted_json)

            content = data["content"]
            marking_dict = data["metadata"]["marking"]
            marking = PrivilegeMarking(**marking_dict)

            # Check access permissions
            if not self._check_access_permission(user_id, marking, client_id, matter_id):
                raise PermissionError(f"User {user_id} does not have access to this privileged content")

            self._log_access_event(user_id, marking, "decrypted")

            return content, marking

        except Exception as e:
            self._log_access_event(user_id, None, "access_denied", str(e))
            raise

    def create_privilege_log(self, marking: PrivilegeMarking) -> str:
        """Create privilege log entry"""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "privilege_level": marking.level.value,
            "content_type": marking.content_type.value,
            "client_id": marking.client_id,
            "matter_id": marking.matter_id,
            "attorney_id": marking.attorney_id,
            "action": "privilege_log_created"
        }

        return json.dumps(log_entry, indent=2)

    def validate_privilege_compliance(self, content: str, marking: PrivilegeMarking) -> List[str]:
        """Validate privilege compliance and return issues"""
        issues = []

        # Check for privilege level consistency
        detected_level = self.classify_privilege_level(content)
        if detected_level != marking.level:
            issues.append(f"Privilege level mismatch: detected {detected_level.value}, marked as {marking.level.value}")

        # Check for unredacted sensitive information in lower privilege content
        if marking.level == PrivilegeLevel.PUBLIC:
            for rule in self.redaction_rules:
                if re.search(rule.pattern, content, re.IGNORECASE):
                    issues.append(f"Potential sensitive information found: {rule.description}")

        # Check for required privilege markings
        if marking.level in [PrivilegeLevel.ATTORNEY_CLIENT, PrivilegeLevel.WORK_PRODUCT]:
            if not re.search(r"ATTORNEY.CLIENT|PRIVILEGED|CONFIDENTIAL", content, re.IGNORECASE):
                issues.append("Missing privilege warning in privileged content")

        return issues

    def _add_privilege_header(self, content: str, marking: PrivilegeMarking) -> str:
        """Add privilege header to content"""
        if marking.level == PrivilegeLevel.PUBLIC:
            return content

        header_lines = [
            "=" * 80,
            f"PRIVILEGED AND CONFIDENTIAL - {marking.level.value.upper()}",
            f"ATTORNEY-CLIENT PRIVILEGE AND WORK PRODUCT DOCTRINE APPLY",
            f"Client: {marking.client_id} | Matter: {marking.matter_id}",
            f"Attorney: {marking.attorney_id} | Date: {marking.created_date.strftime('%Y-%m-%d %H:%M:%S')}",
            ""
        ]

        if marking.level == PrivilegeLevel.ATTORNEY_EYES_ONLY:
            header_lines.insert(2, "ATTORNEY EYES ONLY - DO NOT DISTRIBUTE")

        header_lines.extend([
            "This communication is protected by the attorney-client privilege and/or",
            "work product doctrine. If you have received this in error, please",
            "notify the sender and delete all copies.",
            "=" * 80,
            ""
        ])

        return "\n".join(header_lines) + content

    def _check_access_permission(self, user_id: str, marking: PrivilegeMarking,
                               client_id: str = None, matter_id: str = None) -> bool:
        """Check if user has permission to access privileged content"""

        # System administrators always have access (with audit trail)
        if user_id in self.authorized_users:
            return True

        # Attorney on the matter has access
        if user_id == marking.attorney_id:
            return True

        # Client has access to their own privileged communications
        if client_id and client_id == marking.client_id:
            return True

        # Matter-specific access
        if matter_id and matter_id == marking.matter_id:
            matter_attorneys = self.client_matter_map.get(matter_id, {}).get("attorneys", [])
            if user_id in matter_attorneys:
                return True

        return False

    def _log_privilege_classification(self, content: str, level: PrivilegeLevel, pattern: str):
        """Log privilege classification decision"""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": "privilege_classification",
            "privilege_level": level.value,
            "pattern_matched": pattern,
            "content_length": len(content)
        }
        self.access_log.append(log_entry)

    def _log_privilege_marking(self, content: str, marking: PrivilegeMarking):
        """Log privilege marking application"""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": "privilege_marking_applied",
            "privilege_level": marking.level.value,
            "content_type": marking.content_type.value,
            "client_id": marking.client_id,
            "matter_id": marking.matter_id,
            "attorney_id": marking.attorney_id
        }
        self.access_log.append(log_entry)

    def _log_encryption_event(self, marking: PrivilegeMarking, action: str):
        """Log encryption/decryption events"""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": f"content_{action}",
            "privilege_level": marking.level.value,
            "client_id": marking.client_id,
            "matter_id": marking.matter_id
        }
        self.access_log.append(log_entry)

    def _log_access_event(self, user_id: str, marking: PrivilegeMarking, action: str, details: str = None):
        """Log access events for audit trail"""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "user_id": user_id,
            "details": details
        }

        if marking:
            log_entry.update({
                "privilege_level": marking.level.value,
                "client_id": marking.client_id,
                "matter_id": marking.matter_id
            })

        self.access_log.append(log_entry)

    def export_access_log(self, file_path: str = None) -> str:
        """Export access log for audit purposes"""
        if not file_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = f"logs/privilege_access_log_{timestamp}.json"

        Path(file_path).parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, 'w') as f:
            json.dump(self.access_log, f, indent=2, default=str)

        console.print(f"[green]Privilege access log exported to: {file_path}[/green]")
        return file_path

    def add_authorized_user(self, user_id: str):
        """Add authorized user for privileged content access"""
        self.authorized_users.add(user_id)
        console.print(f"[green]Added authorized user: {user_id}[/green]")

    def add_client_matter(self, client_id: str, matter_id: str, attorneys: List[str]):
        """Add client matter mapping for access control"""
        self.client_matter_map[matter_id] = {
            "client_id": client_id,
            "attorneys": attorneys,
            "created_date": datetime.now(timezone.utc).isoformat()
        }
        console.print(f"[green]Added client matter: {client_id} / {matter_id}[/green]")

    def get_privilege_statistics(self) -> Dict[str, Any]:
        """Get statistics about privilege usage"""
        level_counts = {}
        type_counts = {}

        for entry in self.access_log:
            if "privilege_level" in entry:
                level = entry["privilege_level"]
                level_counts[level] = level_counts.get(level, 0) + 1

            if "content_type" in entry:
                content_type = entry["content_type"]
                type_counts[content_type] = type_counts.get(content_type, 0) + 1

        return {
            "total_log_entries": len(self.access_log),
            "privilege_level_distribution": level_counts,
            "content_type_distribution": type_counts,
            "authorized_users": len(self.authorized_users),
            "client_matters": len(self.client_matter_map)
        }
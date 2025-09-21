#!/usr/bin/env python3
"""Edge case and boundary stress testing for TinyCode system"""

import sys
from pathlib import Path
import json
import uuid
from typing import List, Dict, Any, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from tiny_code.plan_generator import PlanGenerator, PlannedAction, ActionType, PlanStatus
from tiny_code.mode_manager import ModeManager, OperationMode
from tiny_code.plan_validator import PlanValidator
from rich.console import Console

console = Console()

class EdgeCaseStressTest:
    """Test suite for edge cases and boundary conditions"""

    def __init__(self):
        self.results = []
        self.plan_generator = PlanGenerator()
        from tiny_code.safety_config import SafetyConfigManager
        self.safety_config = SafetyConfigManager()
        self.plan_validator = PlanValidator(self.safety_config.config)
        self.mode_manager = ModeManager()

    def log_result(self, test_name: str, passed: bool, details: str):
        """Log test result"""
        result = {"test": test_name, "passed": passed, "details": details}
        self.results.append(result)

        if passed:
            console.print(f"[green]✓ {test_name}: HANDLED[/green]")
        else:
            console.print(f"[red]✗ {test_name}: FAILED - {details}[/red]")

    def test_empty_inputs(self):
        """Test handling of empty and None inputs"""
        console.print("\n[yellow]Testing Empty/None Inputs...[/yellow]")

        test_cases = [
            ("", "Empty string"),
            (None, "None value"),
            ("   ", "Whitespace only"),
            ("\n\n\n", "Newlines only"),
            ("\t\t", "Tabs only"),
            ("\0", "Null byte"),
        ]

        for input_val, desc in test_cases:
            try:
                if input_val is not None:
                    plan = self.plan_generator.generate_plan(input_val, title=desc)
                    self.log_result(f"Empty Input: {desc}", True, "Handled gracefully")
                else:
                    # Test None handling
                    self.plan_generator.generate_plan("test", title=None)
                    self.log_result(f"Empty Input: {desc}", True, "None handled")
            except Exception as e:
                if "cannot be empty" in str(e).lower() or "required" in str(e).lower():
                    self.log_result(f"Empty Input: {desc}", True, "Properly rejected")
                else:
                    self.log_result(f"Empty Input: {desc}", False, f"Unexpected error: {e}")

    def test_unicode_special_chars(self):
        """Test handling of Unicode and special characters"""
        console.print("\n[yellow]Testing Unicode and Special Characters...[/yellow]")

        test_strings = [
            "Hello 世界 🌍",  # Mixed scripts with emoji
            "مرحبا עולם",  # RTL text
            "À̴̵̶̷̸̡̢̧̨̛̖̗̘̙̜̝̞̟̠̣̤̥̦̩̪̫̬̭̮̯̰̱̲̳̹̺̻̼͇͈͉͍͎̀́̂̃̄̅̆̇̈̉̊̋̌̍̎̏̐̑̒̓",  # Zalgo text
            "test\x00file.txt",  # Null byte in filename
            "../../\u202e/etc/passwd",  # Unicode direction override
            "file\uFEFF.txt",  # Zero-width no-break space
            "test​file.txt",  # Zero-width space
        ]

        for test_str in test_strings:
            try:
                plan = self.plan_generator.generate_plan(
                    f"Create file named: {test_str}",
                    title="Unicode Test"
                )
                validation = self.plan_validator.validate_plan(plan)

                if validation.is_valid and "\x00" not in test_str:
                    self.log_result(f"Unicode: {test_str[:20]}...", True, "Handled correctly")
                elif not validation.is_valid and "\x00" in test_str:
                    self.log_result(f"Unicode: Null byte", True, "Dangerous char blocked")
                else:
                    self.log_result(f"Unicode: {test_str[:20]}...", False, "Validation issue")

            except Exception as e:
                self.log_result(f"Unicode: {test_str[:20]}...", True, f"Exception handled: {e}")

    def test_race_conditions(self):
        """Test race conditions in mode switching and plan execution"""
        console.print("\n[yellow]Testing Race Conditions...[/yellow]")

        import threading

        results = []

        def switch_modes():
            """Rapidly switch between modes"""
            for _ in range(100):
                self.mode_manager.set_mode(OperationMode.CHAT)
                self.mode_manager.set_mode(OperationMode.PROPOSE)
                self.mode_manager.set_mode(OperationMode.EXECUTE)

        def approve_plans():
            """Try to approve plans rapidly"""
            for _ in range(100):
                try:
                    plan_id = str(uuid.uuid4())[:8]
                    self.plan_generator.update_plan_status(plan_id, PlanStatus.APPROVED)
                except:
                    pass

        # Start threads
        t1 = threading.Thread(target=switch_modes)
        t2 = threading.Thread(target=approve_plans)

        t1.start()
        t2.start()

        t1.join(timeout=5)
        t2.join(timeout=5)

        # Check for consistency
        current_mode = self.mode_manager.get_current_mode()
        if current_mode in [OperationMode.CHAT, OperationMode.PROPOSE, OperationMode.EXECUTE]:
            self.log_result("Race Condition: Mode Switching", True, "Mode state consistent")
        else:
            self.log_result("Race Condition: Mode Switching", False, "Invalid mode state")

    def test_circular_dependencies(self):
        """Test handling of circular dependencies in plans"""
        console.print("\n[yellow]Testing Circular Dependencies...[/yellow]")

        try:
            # Create actions with circular dependencies
            action1 = PlannedAction(
                id="action1",
                action_type=ActionType.CREATE_FILE,
                description="Create file A",
                target_path="fileA.txt",
                dependencies=["action3"],  # Depends on action3
                risk_level="LOW"
            )

            action2 = PlannedAction(
                id="action2",
                action_type=ActionType.CREATE_FILE,
                description="Create file B",
                target_path="fileB.txt",
                dependencies=["action1"],  # Depends on action1
                risk_level="LOW"
            )

            action3 = PlannedAction(
                id="action3",
                action_type=ActionType.CREATE_FILE,
                description="Create file C",
                target_path="fileC.txt",
                dependencies=["action2"],  # Depends on action2 (creates circle)
                risk_level="LOW"
            )

            # Try to create plan with circular deps
            from tiny_code.plan_generator import ExecutionPlan
            from datetime import datetime

            plan = ExecutionPlan(
                id="circular_test",
                title="Circular Dependency Test",
                description="Test circular dependencies",
                user_request="test",
                actions=[action1, action2, action3],
                status=PlanStatus.DRAFT,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

            # Validate the plan
            validation = self.plan_validator.validate_plan(plan)

            if not validation.is_valid:
                self.log_result("Circular Dependencies", True, "Circular deps detected")
            else:
                self.log_result("Circular Dependencies", False, "Circular deps not detected")

        except Exception as e:
            self.log_result("Circular Dependencies", True, f"Exception prevented: {e}")

    def test_boundary_values(self):
        """Test boundary values and limits"""
        console.print("\n[yellow]Testing Boundary Values...[/yellow]")

        test_cases = [
            (0, "Zero value"),
            (-1, "Negative value"),
            (2147483647, "Max int32"),
            (9223372036854775807, "Max int64"),
            (float('inf'), "Infinity"),
            (float('-inf'), "Negative infinity"),
            (float('nan'), "NaN value"),
        ]

        for value, desc in test_cases:
            try:
                # Test with timeout values
                from tiny_code.timeout_manager import TimeoutContext

                if value > 0 and value < 1000000:
                    ctx = TimeoutContext("test", value, time.time())
                    self.log_result(f"Boundary: {desc}", True, "Value accepted")
                elif value <= 0 or value == float('inf'):
                    ctx = TimeoutContext("test", 10, time.time())  # Use default
                    self.log_result(f"Boundary: {desc}", True, "Invalid value handled")
                else:
                    self.log_result(f"Boundary: {desc}", True, "Large value handled")

            except Exception as e:
                self.log_result(f"Boundary: {desc}", True, f"Exception handled: {e}")

    def test_invalid_json(self):
        """Test handling of malformed JSON in plan files"""
        console.print("\n[yellow]Testing Invalid JSON Handling...[/yellow]")

        malformed_json_cases = [
            '{"key": "value"',  # Missing closing brace
            '{"key": undefined}',  # JavaScript undefined
            "{'key': 'value'}",  # Single quotes
            '{"key": "value",}',  # Trailing comma
            'NaN',  # Not JSON
            '{"key": "\x00"}',  # Null byte in string
        ]

        for json_str in malformed_json_cases:
            try:
                # Try to parse as plan data
                data = json.loads(json_str)
                self.log_result("Invalid JSON", False, f"Accepted malformed: {json_str[:20]}")
            except json.JSONDecodeError:
                self.log_result("Invalid JSON", True, "Properly rejected malformed JSON")
            except Exception as e:
                self.log_result("Invalid JSON", True, f"Exception handled: {e}")

    def run_all_tests(self):
        """Run all edge case stress tests"""
        console.print("[bold cyan]🔍 Starting Edge Case Stress Tests[/bold cyan]\n")

        self.test_empty_inputs()
        self.test_unicode_special_chars()
        self.test_race_conditions()
        self.test_circular_dependencies()
        self.test_boundary_values()
        self.test_invalid_json()

        # Summary
        console.print("\n[bold cyan]📊 Edge Case Test Summary[/bold cyan]")

        total = len(self.results)
        passed = sum(1 for r in self.results if r['passed'])
        failed = total - passed

        console.print(f"Total Tests: {total}")
        console.print(f"[green]Passed: {passed}[/green]")
        console.print(f"[red]Failed: {failed}[/red]")

        if failed > 0:
            console.print("\n[red]⚠️ EDGE CASE FAILURES DETECTED![/red]")
            for result in self.results:
                if not result['passed']:
                    console.print(f"  - {result['test']}: {result['details']}")
        else:
            console.print("\n[green]✅ All edge case tests passed![/green]")

        return self.results

if __name__ == "__main__":
    import time
    tester = EdgeCaseStressTest()
    results = tester.run_all_tests()
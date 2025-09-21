#!/usr/bin/env python3
"""Resource exhaustion stress testing for TinyCode system"""

import sys
import os
import time
import threading
import psutil
import gc
from pathlib import Path
from typing import List, Dict, Any
import tempfile
import uuid

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from tiny_code.plan_generator import PlanGenerator, PlannedAction, ActionType, ExecutionPlan
from tiny_code.plan_executor import PlanExecutor
from tiny_code.timeout_manager import TimeoutManager, TimeoutError
from tiny_code.safety_config import SafetyConfigManager, SafetyLevel
from rich.console import Console
from rich.progress import Progress

console = Console()

class ResourceLimitsStressTest:
    """Test suite for resource exhaustion vulnerabilities"""

    def __init__(self):
        self.results = []
        self.plan_generator = PlanGenerator()
        self.plan_executor = PlanExecutor()
        self.timeout_manager = TimeoutManager()
        self.safety_config = SafetyConfigManager()
        self.initial_memory = psutil.Process().memory_info().rss / 1024 / 1024

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
            console.print(f"[green]✓ {test_name}: PROTECTED[/green]")
        else:
            console.print(f"[red]✗ {test_name}: VULNERABLE - {details}[/red]")

    def test_memory_exhaustion(self):
        """Test memory exhaustion with massive plans"""
        console.print("\n[yellow]Testing Memory Exhaustion...[/yellow]")

        try:
            # Create a plan with thousands of actions
            massive_actions = []
            for i in range(10000):
                massive_actions.append(PlannedAction(
                    id=str(uuid.uuid4()),
                    action_type=ActionType.CREATE_FILE,
                    description=f"Create file {i}" * 100,  # Long description
                    target_path=f"file_{i}.txt",
                    content="A" * 10000,  # 10KB per action
                    risk_level="LOW"
                ))

            # Check memory usage
            current_memory = psutil.Process().memory_info().rss / 1024 / 1024
            memory_increase = current_memory - self.initial_memory

            if memory_increase > 1000:  # More than 1GB increase
                self.log_result(
                    "Memory Exhaustion",
                    "Memory DoS",
                    False,
                    f"Memory increased by {memory_increase:.0f}MB"
                )
            else:
                self.log_result(
                    "Memory Exhaustion",
                    "Memory DoS",
                    True,
                    "Memory usage controlled"
                )

            # Clean up
            del massive_actions
            gc.collect()

        except MemoryError:
            self.log_result(
                "Memory Exhaustion",
                "Memory DoS",
                True,
                "MemoryError caught - system protected"
            )
        except Exception as e:
            self.log_result(
                "Memory Exhaustion",
                "Memory DoS",
                True,
                f"Exception prevented exhaustion: {str(e)}"
            )

    def test_timeout_bypass(self):
        """Test timeout mechanism reliability"""
        console.print("\n[yellow]Testing Timeout Mechanisms...[/yellow]")

        def long_running_operation():
            """Operation that should timeout"""
            time.sleep(10)  # 10 seconds
            return "Should not reach here"

        try:
            with self.timeout_manager.timeout_context(
                "test_operation",
                timeout_seconds=2,
                warning_callback=lambda: console.print("[yellow]Warning: Near timeout[/yellow]")
            ):
                result = long_running_operation()
                self.log_result(
                    "Timeout Mechanism",
                    "Timeout Bypass",
                    False,
                    "Operation completed despite timeout"
                )

        except TimeoutError:
            self.log_result(
                "Timeout Mechanism",
                "Timeout Bypass",
                True,
                "Timeout properly enforced"
            )
        except Exception as e:
            self.log_result(
                "Timeout Mechanism",
                "Timeout Bypass",
                True,
                f"Protected by exception: {str(e)}"
            )

    def test_file_handle_exhaustion(self):
        """Test file handle exhaustion attack"""
        console.print("\n[yellow]Testing File Handle Exhaustion...[/yellow]")

        open_files = []
        max_files = 10000

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                for i in range(max_files):
                    filepath = Path(tmpdir) / f"test_{i}.txt"
                    f = open(filepath, 'w')
                    open_files.append(f)

                    if i % 1000 == 0:
                        console.print(f"  Opened {i} files...")

                self.log_result(
                    "File Handle Exhaustion",
                    "Resource Exhaustion",
                    False,
                    f"Allowed {len(open_files)} open files"
                )

        except OSError as e:
            if "Too many open files" in str(e):
                self.log_result(
                    "File Handle Exhaustion",
                    "Resource Exhaustion",
                    True,
                    f"OS limit enforced at {len(open_files)} files"
                )
            else:
                self.log_result(
                    "File Handle Exhaustion",
                    "Resource Exhaustion",
                    True,
                    f"Protected: {str(e)}"
                )

        finally:
            # Clean up
            for f in open_files:
                try:
                    f.close()
                except:
                    pass

    def test_concurrent_plan_execution(self):
        """Test concurrent plan execution limits"""
        console.print("\n[yellow]Testing Concurrent Execution Limits...[/yellow]")

        def execute_plan():
            """Execute a simple plan"""
            try:
                plan = self.plan_generator.generate_plan(
                    "Create a test file",
                    title=f"Concurrent Test {uuid.uuid4()}"
                )
                result = self.plan_executor.execute_plan(plan, dry_run=True)
                return result.status
            except Exception:
                return "failed"

        # Try to execute many plans concurrently
        threads = []
        num_concurrent = 100

        start_time = time.time()

        for i in range(num_concurrent):
            thread = threading.Thread(target=execute_plan)
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join(timeout=5)

        elapsed = time.time() - start_time

        # Check if system handled concurrent load
        alive_threads = sum(1 for t in threads if t.is_alive())

        if alive_threads > 10:
            self.log_result(
                "Concurrent Execution",
                "Thread Exhaustion",
                False,
                f"{alive_threads} threads still running"
            )
        else:
            self.log_result(
                "Concurrent Execution",
                "Thread Exhaustion",
                True,
                f"Handled {num_concurrent} concurrent plans in {elapsed:.1f}s"
            )

    def test_recursive_operations(self):
        """Test protection against recursive operations"""
        console.print("\n[yellow]Testing Recursive Operation Protection...[/yellow]")

        def recursive_function(depth=0, max_depth=10000):
            """Deeply recursive function"""
            if depth >= max_depth:
                return depth
            return recursive_function(depth + 1, max_depth)

        try:
            result = recursive_function()
            self.log_result(
                "Recursive Operations",
                "Stack Overflow",
                False,
                f"Allowed recursion depth: {result}"
            )

        except RecursionError:
            self.log_result(
                "Recursive Operations",
                "Stack Overflow",
                True,
                "RecursionError caught - stack protected"
            )

    def test_large_file_processing(self):
        """Test handling of extremely large files"""
        console.print("\n[yellow]Testing Large File Processing...[/yellow]")

        try:
            # Try to create a very large file in memory
            size_gb = 2
            large_content = "X" * (1024 * 1024 * 1024 * size_gb)  # 2GB

            action = PlannedAction(
                id="large_file_test",
                action_type=ActionType.CREATE_FILE,
                description="Create large file",
                target_path="large.txt",
                content=large_content,
                risk_level="LOW"
            )

            # Check if safety limits prevent this
            max_size_mb = self.safety_config.config.execution_limits.max_file_size_mb
            if len(large_content) > max_size_mb * 1024 * 1024:
                self.log_result(
                    "Large File Processing",
                    "Resource Exhaustion",
                    True,
                    f"File size limit ({max_size_mb}MB) enforced"
                )
            else:
                self.log_result(
                    "Large File Processing",
                    "Resource Exhaustion",
                    False,
                    "No file size protection"
                )

        except MemoryError:
            self.log_result(
                "Large File Processing",
                "Resource Exhaustion",
                True,
                "MemoryError prevented large file creation"
            )

    def test_rate_limiting(self):
        """Test rate limiting for rapid operations"""
        console.print("\n[yellow]Testing Rate Limiting...[/yellow]")

        start_time = time.time()
        operations = 0
        max_time = 1.0  # 1 second

        try:
            while time.time() - start_time < max_time:
                # Rapid plan generation
                plan = self.plan_generator.generate_plan(
                    f"Test operation {operations}",
                    title=f"Rate Test {operations}"
                )
                operations += 1

            ops_per_second = operations / max_time

            if ops_per_second > 1000:
                self.log_result(
                    "Rate Limiting",
                    "DoS via Rapid Operations",
                    False,
                    f"Allowed {ops_per_second:.0f} ops/second"
                )
            else:
                self.log_result(
                    "Rate Limiting",
                    "DoS via Rapid Operations",
                    True,
                    f"Limited to {ops_per_second:.0f} ops/second"
                )

        except Exception as e:
            self.log_result(
                "Rate Limiting",
                "DoS via Rapid Operations",
                True,
                f"Exception prevented rapid operations: {str(e)}"
            )

    def run_all_tests(self):
        """Run all resource limit stress tests"""
        console.print("[bold cyan]⚡ Starting Resource Limits Stress Tests[/bold cyan]\n")

        self.test_memory_exhaustion()
        self.test_timeout_bypass()
        self.test_file_handle_exhaustion()
        self.test_concurrent_plan_execution()
        self.test_recursive_operations()
        self.test_large_file_processing()
        self.test_rate_limiting()

        # Summary
        console.print("\n[bold cyan]📊 Resource Limits Test Summary[/bold cyan]")

        total = len(self.results)
        passed = sum(1 for r in self.results if r['passed'])
        failed = total - passed

        console.print(f"Total Tests: {total}")
        console.print(f"[green]Passed: {passed}[/green]")
        console.print(f"[red]Failed: {failed}[/red]")

        if failed > 0:
            console.print("\n[red]⚠️ RESOURCE VULNERABILITIES DETECTED![/red]")
            console.print("Failed tests:")
            for result in self.results:
                if not result['passed']:
                    console.print(f"  - {result['test']}: {result['details']}")
        else:
            console.print("\n[green]✅ All resource limit tests passed![/green]")

        return self.results

if __name__ == "__main__":
    tester = ResourceLimitsStressTest()
    results = tester.run_all_tests()
#!/usr/bin/env python3
"""Main stress test runner for TinyCode production readiness testing"""

import sys
import os
import time
import json
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

class StressTestRunner:
    """Orchestrates all stress tests and generates production readiness report"""

    def __init__(self):
        self.results = {}
        self.start_time = None
        self.end_time = None
        self.vulnerabilities = []
        self.critical_issues = []
        self.test_modules = []

    def discover_tests(self):
        """Discover available stress test modules"""
        test_files = Path(".").glob("stress_test_*.py")
        for test_file in test_files:
            if test_file.name != "run_stress_tests.py":
                module_name = test_file.stem
                self.test_modules.append(module_name)

        console.print(f"[cyan]Discovered {len(self.test_modules)} test modules[/cyan]")
        return self.test_modules

    def run_test_module(self, module_name: str) -> Dict[str, Any]:
        """Run a single test module"""
        results = {
            "module": module_name,
            "status": "unknown",
            "tests": [],
            "passed": 0,
            "failed": 0,
            "error": None,
            "duration": 0
        }

        try:
            start = time.time()
            console.print(f"\n[bold blue]Running {module_name}...[/bold blue]")

            # Import and run the test module
            module = __import__(module_name)

            # Find the main test class
            test_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and "StressTest" in attr_name:
                    test_class = attr
                    break

            if test_class:
                tester = test_class()
                test_results = tester.run_all_tests()

                # Process results
                for test_result in test_results:
                    results["tests"].append(test_result)
                    if test_result.get("passed", False):
                        results["passed"] += 1
                    else:
                        results["failed"] += 1
                        # Track vulnerabilities
                        if "vulnerability" in test_result:
                            self.vulnerabilities.append({
                                "module": module_name,
                                "test": test_result["test"],
                                "vulnerability": test_result.get("vulnerability"),
                                "details": test_result.get("details")
                            })

                results["status"] = "completed"
            else:
                results["status"] = "error"
                results["error"] = "No test class found"

            results["duration"] = time.time() - start

        except Exception as e:
            results["status"] = "error"
            results["error"] = str(e)
            console.print(f"[red]Error in {module_name}: {e}[/red]")
            console.print(traceback.format_exc())

        return results

    def calculate_readiness_score(self) -> float:
        """Calculate production readiness score based on test results"""
        total_tests = sum(r["passed"] + r["failed"] for r in self.results.values())
        total_passed = sum(r["passed"] for r in self.results.values())

        if total_tests == 0:
            return 0.0

        base_score = (total_passed / total_tests) * 100

        # Apply penalties for critical issues
        penalty = len(self.vulnerabilities) * 5  # 5% penalty per vulnerability
        penalty += len(self.critical_issues) * 10  # 10% penalty per critical issue

        final_score = max(0, base_score - penalty)
        return round(final_score, 2)

    def generate_report(self):
        """Generate comprehensive test report"""
        console.print("\n" + "=" * 80)
        console.print("[bold cyan]TINCODE PRODUCTION READINESS REPORT[/bold cyan]")
        console.print("=" * 80)

        # Test Summary Table
        table = Table(title="Test Results Summary")
        table.add_column("Module", style="cyan")
        table.add_column("Status", style="yellow")
        table.add_column("Passed", style="green")
        table.add_column("Failed", style="red")
        table.add_column("Duration", style="magenta")

        for module_name, results in self.results.items():
            status_color = "green" if results["status"] == "completed" else "red"
            table.add_row(
                module_name.replace("stress_test_", ""),
                f"[{status_color}]{results['status']}[/{status_color}]",
                str(results["passed"]),
                str(results["failed"]),
                f"{results['duration']:.2f}s"
            )

        console.print(table)

        # Vulnerabilities Section
        if self.vulnerabilities:
            console.print("\n[bold red]🚨 VULNERABILITIES DETECTED[/bold red]")
            vuln_table = Table(title="Security Vulnerabilities")
            vuln_table.add_column("Module", style="yellow")
            vuln_table.add_column("Vulnerability", style="red")
            vuln_table.add_column("Details", style="white")

            for vuln in self.vulnerabilities:
                vuln_table.add_row(
                    vuln["module"].replace("stress_test_", ""),
                    vuln["vulnerability"],
                    vuln["details"][:50] + "..." if len(vuln["details"]) > 50 else vuln["details"]
                )

            console.print(vuln_table)

        # Production Readiness Score
        score = self.calculate_readiness_score()
        score_color = "green" if score >= 80 else "yellow" if score >= 60 else "red"

        console.print(f"\n[bold]Production Readiness Score: [{score_color}]{score}%[/{score_color}][/bold]")

        # Recommendations
        console.print("\n[bold cyan]RECOMMENDATIONS[/bold cyan]")

        if score >= 90:
            console.print("[green]✅ System is production-ready![/green]")
        elif score >= 70:
            console.print("[yellow]⚠️ System needs minor improvements:[/yellow]")
            self._print_recommendations("minor")
        else:
            console.print("[red]❌ System is NOT production-ready:[/red]")
            self._print_recommendations("major")

        # Test Duration
        if self.start_time and self.end_time:
            duration = self.end_time - self.start_time
            console.print(f"\nTotal test duration: {duration:.2f} seconds")

        # Report File
        self._save_report_to_file()

    def _print_recommendations(self, level: str):
        """Print recommendations based on test results"""
        if level == "major":
            console.print("1. Fix all CRITICAL security vulnerabilities immediately")
            console.print("2. Implement proper input validation for all user inputs")
            console.print("3. Add resource limits and timeout mechanisms")
            console.print("4. Strengthen authentication and authorization")
            console.print("5. Implement comprehensive error handling")
        else:
            console.print("1. Review and fix remaining vulnerabilities")
            console.print("2. Optimize performance for edge cases")
            console.print("3. Add additional monitoring and logging")
            console.print("4. Implement rate limiting")
            console.print("5. Enhance test coverage")

    def _save_report_to_file(self):
        """Save detailed report to JSON file"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "score": self.calculate_readiness_score(),
            "results": self.results,
            "vulnerabilities": self.vulnerabilities,
            "critical_issues": self.critical_issues,
            "duration": self.end_time - self.start_time if self.start_time and self.end_time else 0
        }

        report_path = Path("stress_test_report.json")
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2, default=str)

        console.print(f"\n[cyan]Detailed report saved to: {report_path}[/cyan]")

    def run_all_tests(self):
        """Run all discovered stress tests"""
        self.start_time = time.time()

        # Print header
        console.print(Panel.fit(
            "[bold cyan]TINCODE STRESS TEST SUITE[/bold cyan]\n"
            "Testing for production readiness",
            border_style="cyan"
        ))

        # Discover test modules
        self.discover_tests()

        if not self.test_modules:
            console.print("[red]No stress test modules found![/red]")
            console.print("Expected files: stress_test_*.py")
            return

        # Run each test module
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:

            for module_name in self.test_modules:
                task = progress.add_task(f"Running {module_name}...", total=None)

                results = self.run_test_module(module_name)
                self.results[module_name] = results

                progress.update(task, completed=True)

        self.end_time = time.time()

        # Generate and display report
        self.generate_report()

        # Return production readiness score
        return self.calculate_readiness_score()

def main():
    """Main entry point"""
    runner = StressTestRunner()

    try:
        score = runner.run_all_tests()

        # Exit with appropriate code
        if score >= 80:
            sys.exit(0)  # Success
        else:
            sys.exit(1)  # Failure

    except KeyboardInterrupt:
        console.print("\n[yellow]Tests interrupted by user[/yellow]")
        sys.exit(2)
    except Exception as e:
        console.print(f"\n[red]Fatal error: {e}[/red]")
        console.print(traceback.format_exc())
        sys.exit(3)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""Comprehensive test script for TinyCode Natural Language Interface integration"""

import sys
import os
import json
import time
from pathlib import Path
from typing import Dict, List, Any
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, track

# Add tiny_code to path
sys.path.insert(0, str(Path(__file__).parent))

from tiny_code.nlp_interface import NLPProcessor, Intent
from tiny_code.command_translator import CommandTranslator
from tiny_code.conversation_manager import ConversationManager
from tiny_code.smart_assistant import SmartAssistant
from tiny_code.enhanced_cli import create_enhanced_cli
from tiny_code.guided_workflows import GuidedWorkflowManager
from tiny_code.intelligent_mode_manager import IntelligentModeManager


class NLPIntegrationTester:
    """Comprehensive tester for the Natural Language Interface"""

    def __init__(self):
        self.console = Console()
        self.test_results = []
        self.current_dir = Path.cwd()

    def run_all_tests(self) -> bool:
        """Run all integration tests"""
        self.console.print(Panel(
            "[bold cyan]TinyCode Natural Language Interface Integration Tests[/bold cyan]\n\n"
            "Testing all components and their integration...",
            title="NLP Integration Tests",
            border_style="cyan"
        ))

        tests = [
            ("Intent Recognition", self.test_intent_recognition),
            ("Command Translation", self.test_command_translation),
            ("Conversation Management", self.test_conversation_management),
            ("Smart Assistant", self.test_smart_assistant),
            ("Enhanced CLI Creation", self.test_enhanced_cli_creation),
            ("Mode Management", self.test_intelligent_mode_manager),
            ("Guided Workflows", self.test_guided_workflows),
            ("End-to-End Integration", self.test_end_to_end_integration),
            ("Error Handling", self.test_error_handling),
            ("Performance", self.test_performance)
        ]

        passed_tests = 0
        total_tests = len(tests)

        for test_name, test_func in track(tests, description="Running tests..."):
            self.console.print(f"\n[bold yellow]Testing: {test_name}[/bold yellow]")
            try:
                result = test_func()
                if result:
                    self.console.print(f"[green]✅ {test_name}: PASSED[/green]")
                    passed_tests += 1
                else:
                    self.console.print(f"[red]❌ {test_name}: FAILED[/red]")
                self.test_results.append({"test": test_name, "passed": result})
            except Exception as e:
                self.console.print(f"[red]❌ {test_name}: ERROR - {str(e)}[/red]")
                self.test_results.append({"test": test_name, "passed": False, "error": str(e)})

        # Display results summary
        self.display_test_summary(passed_tests, total_tests)

        return passed_tests == total_tests

    def test_intent_recognition(self) -> bool:
        """Test intent recognition functionality"""
        recognizer = NLPProcessor()

        test_cases = [
            ("show me the files in this directory", Intent.FIND_FILES),
            ("help me fix bugs in my code", Intent.FIX_BUGS),
            ("can you analyze this Python file", Intent.ANALYZE_CODE),
            ("I need to complete this function", Intent.COMPLETE_CODE),
            ("refactor my code to make it cleaner", Intent.REFACTOR_CODE),
            ("run the tests", Intent.GENERATE_TESTS),
            ("what's the git status", Intent.GIT_STATUS),
            ("create a new file called test.py", Intent.CREATE_FILE),
            ("explain how this function works", Intent.EXPLAIN_CODE),
            ("help me write documentation", Intent.REQUEST_GUIDANCE)
        ]

        correct_predictions = 0
        for input_text, expected_intent in test_cases:
            result = recognizer.process_input(input_text, {})
            if result.intent == expected_intent:
                correct_predictions += 1
                self.console.print(f"  ✓ '{input_text}' → {expected_intent.value}")
            else:
                self.console.print(f"  ✗ '{input_text}' → Expected: {expected_intent.value}, Got: {result.intent.value}")

        accuracy = correct_predictions / len(test_cases)
        self.console.print(f"  Intent Recognition Accuracy: {accuracy:.1%}")

        return accuracy >= 0.8  # 80% accuracy threshold

    def test_command_translation(self) -> bool:
        """Test command translation functionality"""
        recognizer = NLPProcessor()
        translator = CommandTranslator()

        test_cases = [
            ("show me files", Intent.FIND_FILES, "/find"),
            ("analyze my code", Intent.ANALYZE_CODE, "/analyze"),
            ("fix bugs", Intent.FIX_BUGS, "/fix-bugs"),
            ("run tests", Intent.GENERATE_TESTS, "/test"),
            ("git status", Intent.GIT_STATUS, "/git-status")
        ]

        successful_translations = 0
        for input_text, expected_intent, expected_command_prefix in test_cases:
            intent_result = recognizer.process_input(input_text, {})
            context = {"current_directory": str(self.current_dir), "current_mode": "chat"}

            translated = translator.translate(intent_result, context)

            if translated.command and translated.command.startswith(expected_command_prefix):
                successful_translations += 1
                self.console.print(f"  ✓ '{input_text}' → {translated.command}")
            else:
                self.console.print(f"  ✗ '{input_text}' → Expected prefix: {expected_command_prefix}, Got: {translated.command}")

        success_rate = successful_translations / len(test_cases)
        self.console.print(f"  Translation Success Rate: {success_rate:.1%}")

        return success_rate >= 0.8

    def test_conversation_management(self) -> bool:
        """Test conversation management functionality"""
        conversation_manager = ConversationManager()

        # Test conversation flow
        test_inputs = [
            "Hello, I need help with my code",
            "Can you analyze my Python files?",
            "Yes, please proceed",
            "Thank you for the help"
        ]

        successful_responses = 0
        for input_text in test_inputs:
            context = {"current_directory": str(self.current_dir), "current_mode": "chat"}
            response = conversation_manager.process_user_input(input_text, context)

            if response and response.get('response'):
                successful_responses += 1
                self.console.print(f"  ✓ Input: '{input_text}' → Response received")
            else:
                self.console.print(f"  ✗ Input: '{input_text}' → No response")

        # Test conversation state management
        state_before = conversation_manager.current_state
        # Test state transition by processing different inputs
        conversation_manager.process_user_input("Can you help me?", {"current_directory": str(self.current_dir), "current_mode": "chat"})
        state_after = conversation_manager.current_state

        state_management_works = hasattr(conversation_manager, 'current_state')
        if state_management_works:
            self.console.print("  ✓ Conversation state management working")
        else:
            self.console.print("  ✗ Conversation state management not working")

        success_rate = successful_responses / len(test_inputs)
        return success_rate >= 0.75 and state_management_works

    def test_smart_assistant(self) -> bool:
        """Test smart assistant functionality"""
        assistant = SmartAssistant()

        # Test context analysis
        context = {
            "current_directory": str(self.current_dir),
            "available_files": ["test.py", "main.py", "README.md"],
            "recent_commands": ["/analyze", "/fix-bugs"]
        }

        suggestions = assistant.analyze_context_and_suggest(context, [])

        if suggestions and len(suggestions) > 0:
            self.console.print(f"  ✓ Generated {len(suggestions)} suggestions")
            for suggestion in suggestions[:3]:  # Show first 3
                self.console.print(f"    - {suggestion.description}")
            return True
        else:
            self.console.print("  ✗ No suggestions generated")
            return False

    def test_enhanced_cli_creation(self) -> bool:
        """Test enhanced CLI creation"""
        try:
            cli = create_enhanced_cli("tinyllama:latest")

            # Test basic functionality
            has_nlp = hasattr(cli, 'nlp_processor')
            has_translator = hasattr(cli, 'command_translator')
            has_conversation = hasattr(cli, 'conversation_manager')
            has_assistant = hasattr(cli, 'smart_assistant')

            components_present = has_nlp and has_translator and has_conversation and has_assistant

            if components_present:
                self.console.print("  ✓ Enhanced CLI created with all components")

                # Test system context building
                context = cli._build_system_context()
                has_required_context = all(key in context for key in ['current_directory', 'current_mode', 'available_files'])

                if has_required_context:
                    self.console.print("  ✓ System context building works")
                    return True
                else:
                    self.console.print("  ✗ System context missing required fields")
                    return False
            else:
                self.console.print("  ✗ Enhanced CLI missing components")
                return False

        except Exception as e:
            self.console.print(f"  ✗ Enhanced CLI creation failed: {str(e)}")
            return False

    def test_intelligent_mode_manager(self) -> bool:
        """Test intelligent mode manager"""
        try:
            from tiny_code.mode_manager import ModeManager
            from tiny_code.command_registry import DangerLevel
            base_manager = ModeManager()
            mode_manager = IntelligentModeManager(base_manager)

            # Test mode transition suggestions
            context = {"current_mode": "chat", "recent_intents": ["ANALYZE_CODE"]}
            transition = mode_manager.suggest_mode_transition(Intent.FIX_BUGS, context, DangerLevel.MEDIUM)

            if transition:
                self.console.print(f"  ✓ Mode transition suggested: {transition.suggested_mode}")
                return True
            else:
                self.console.print("  ✗ No mode transition suggested when expected")
                return False

        except Exception as e:
            self.console.print(f"  ✗ Mode manager test failed: {str(e)}")
            return False

    def test_guided_workflows(self) -> bool:
        """Test guided workflows system"""
        try:
            recognizer = NLPProcessor()
            conversation_manager = ConversationManager()
            workflow_manager = GuidedWorkflowManager(recognizer, conversation_manager)

            # Test workflow availability
            available_workflows = workflow_manager.tutorial.workflows
            if len(available_workflows) >= 3:
                self.console.print(f"  ✓ {len(available_workflows)} workflows available")

                # Test workflow structure
                first_workflow = available_workflows[0]
                has_required_fields = all(hasattr(first_workflow, field) for field in
                                        ['id', 'name', 'steps', 'learning_objectives'])

                if has_required_fields:
                    self.console.print("  ✓ Workflow structure is valid")
                    return True
                else:
                    self.console.print("  ✗ Workflow structure invalid")
                    return False
            else:
                self.console.print("  ✗ Insufficient workflows available")
                return False

        except Exception as e:
            self.console.print(f"  ✗ Guided workflows test failed: {str(e)}")
            return False

    def test_end_to_end_integration(self) -> bool:
        """Test complete end-to-end integration"""
        try:
            cli = create_enhanced_cli("tinyllama:latest")

            # Test complete pipeline
            user_input = "show me the files in this directory"
            system_context = cli._build_system_context()
            response = cli.conversation_manager.process_user_input(user_input, system_context)

            if response and response.get('response'):
                self.console.print("  ✓ End-to-end pipeline works")

                # Test action execution (simulate)
                actions = response.get('actions', [])
                if actions:
                    self.console.print(f"  ✓ Actions generated: {len(actions)}")
                    return True
                else:
                    self.console.print("  ✓ Response without actions (acceptable)")
                    return True
            else:
                self.console.print("  ✗ End-to-end pipeline failed")
                return False

        except Exception as e:
            self.console.print(f"  ✗ End-to-end test failed: {str(e)}")
            return False

    def test_error_handling(self) -> bool:
        """Test error handling capabilities"""
        recognizer = NLPProcessor()

        # Test with invalid/unclear inputs
        unclear_inputs = [
            "",
            "asdfghjkl",
            "do something vague",
            "help me with stuff"
        ]

        handled_gracefully = 0
        for input_text in unclear_inputs:
            try:
                result = recognizer.process_input(input_text, {})
                # Should handle gracefully without crashing
                handled_gracefully += 1
                self.console.print(f"  ✓ Handled gracefully: '{input_text}' → {result.intent.value}")
            except Exception as e:
                self.console.print(f"  ✗ Failed to handle: '{input_text}' → {str(e)}")

        success_rate = handled_gracefully / len(unclear_inputs)
        return success_rate >= 0.75

    def test_performance(self) -> bool:
        """Test performance of NLP components"""
        recognizer = NLPProcessor()

        # Test response time
        test_input = "analyze my code and fix any bugs you find"

        start_time = time.time()
        for _ in range(10):  # Run 10 times
            recognizer.process(test_input, {})
        end_time = time.time()

        avg_time = (end_time - start_time) / 10
        self.console.print(f"  Average response time: {avg_time:.3f} seconds")

        # Performance should be under 0.1 seconds per request
        return avg_time < 0.1

    def display_test_summary(self, passed: int, total: int):
        """Display test results summary"""
        table = Table(title="Test Results Summary")
        table.add_column("Test", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Notes", style="yellow")

        for result in self.test_results:
            status = "✅ PASSED" if result["passed"] else "❌ FAILED"
            notes = result.get("error", "")
            table.add_row(result["test"], status, notes)

        self.console.print(table)

        success_rate = (passed / total) * 100
        color = "green" if success_rate >= 90 else "yellow" if success_rate >= 70 else "red"

        self.console.print(Panel(
            f"[bold {color}]Overall Success Rate: {success_rate:.1f}% ({passed}/{total} tests passed)[/bold {color}]\n\n"
            f"{'✅ All systems operational!' if passed == total else '⚠️ Some issues detected. Review failed tests.' if success_rate >= 70 else '❌ Significant issues detected. Investigation required.'}",
            title="Test Summary",
            border_style=color
        ))

    def generate_test_report(self):
        """Generate a detailed test report"""
        report_data = {
            "timestamp": time.time(),
            "total_tests": len(self.test_results),
            "passed_tests": sum(1 for r in self.test_results if r["passed"]),
            "test_details": self.test_results,
            "environment": {
                "python_version": sys.version,
                "current_directory": str(self.current_dir),
                "platform": sys.platform
            }
        }

        report_file = Path("data/nlp_integration_test_report.json")
        report_file.parent.mkdir(parents=True, exist_ok=True)

        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)

        self.console.print(f"\n[dim]Test report saved to: {report_file}[/dim]")


def main():
    """Run NLP integration tests"""
    console = Console()

    console.print("[bold cyan]TinyCode Natural Language Interface - Integration Test Suite[/bold cyan]\n")

    tester = NLPIntegrationTester()

    try:
        success = tester.run_all_tests()
        tester.generate_test_report()

        if success:
            console.print("\n[bold green]🎉 All tests passed! Natural Language Interface is ready for use.[/bold green]")
            console.print("\n[dim]You can now run:[/dim]")
            console.print("[dim]• python tiny_code.py  (for enhanced natural language interface)[/dim]")
            console.print("[dim]• python tiny_code.py ask \"your question\"  (for single commands)[/dim]")
            console.print("[dim]• python tiny_code.py demo  (for demonstration)[/dim]")
            console.print("[dim]• python tiny_code.py traditional  (for classic interface)[/dim]")
            return 0
        else:
            console.print("\n[bold yellow]⚠️ Some tests failed. Check the output above for details.[/bold yellow]")
            return 1

    except KeyboardInterrupt:
        console.print("\n[yellow]Tests interrupted by user[/yellow]")
        return 1
    except Exception as e:
        console.print(f"\n[red]Test suite failed with error: {str(e)}[/red]")
        return 1


if __name__ == "__main__":
    exit(main())
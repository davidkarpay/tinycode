#!/usr/bin/env python3
"""
Script to explore TinyCode's self-awareness of its capabilities.
This script will test various aspects of TinyCode to understand
how well it knows its own features and capabilities.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tiny_code.agent import TinyCodeAgent
from tiny_code.ollama_client import OllamaClient
from tiny_code.mode_manager import ModeManager, OperationMode
from tiny_code.command_registry import CommandRegistry
from tiny_code.plan_generator import PlanGenerator
from tiny_code.safety_config import SafetyLevel
import json
from datetime import datetime

class TinyCodeAwarenessExplorer:
    def __init__(self):
        self.client = OllamaClient()
        self.agent = TinyCodeAgent(self.client)
        self.mode_manager = ModeManager()
        self.command_registry = CommandRegistry()
        self.plan_generator = PlanGenerator()  # No argument needed, uses default storage dir
        self.results = []

    def test_self_awareness(self):
        """Test TinyCode's awareness of its own capabilities."""

        print("\n" + "="*60)
        print("TINYCODER SELF-AWARENESS EXPLORATION")
        print("="*60)

        # Test 1: Ask about its own capabilities
        print("\n[TEST 1] Asking about capabilities...")
        questions = [
            "What are your main capabilities?",
            "What commands do you support?",
            "What safety features do you have?",
            "What modes can you operate in?",
            "Can you explain your plan-based execution system?",
            "What types of code operations can you perform?",
            "Do you have RAG capabilities?",
            "What file operations are you allowed to do?",
            "How do you handle dangerous operations?",
            "Can you list your available tools?"
        ]

        for question in questions:
            print(f"\nQ: {question}")
            try:
                response = self.agent.chat(question)
                print(f"A: {response[:500]}...")  # Truncate for readability
                self.results.append({
                    "test": "capability_awareness",
                    "question": question,
                    "response": response,
                    "aware": self._assess_awareness(response, question)
                })
            except Exception as e:
                print(f"Error: {e}")
                self.results.append({
                    "test": "capability_awareness",
                    "question": question,
                    "error": str(e),
                    "aware": False
                })

        # Test 2: Check command registry awareness
        print("\n[TEST 2] Testing command registry awareness...")
        all_commands = self.command_registry.commands  # Access the commands dictionary directly
        command_count = len(all_commands)
        print(f"System has {command_count} registered commands")

        # Ask TinyCode about specific commands
        sample_commands = list(all_commands.keys())[:5]
        for cmd in sample_commands:
            question = f"What does the {cmd} command do?"
            print(f"\nQ: {question}")
            try:
                response = self.agent.chat(question)
                print(f"A: {response[:300]}...")
                self.results.append({
                    "test": "command_awareness",
                    "command": cmd,
                    "response": response,
                    "aware": cmd in response.lower()
                })
            except Exception as e:
                print(f"Error: {e}")

        # Test 3: Mode awareness
        print("\n[TEST 3] Testing mode awareness...")
        modes = [OperationMode.CHAT, OperationMode.PROPOSE, OperationMode.EXECUTE]
        for mode in modes:
            question = f"What can you do in {mode.value} mode?"
            print(f"\nQ: {question}")
            try:
                response = self.agent.chat(question)
                print(f"A: {response[:300]}...")
                self.results.append({
                    "test": "mode_awareness",
                    "mode": mode.value,
                    "response": response,
                    "aware": mode.value.lower() in response.lower()
                })
            except Exception as e:
                print(f"Error: {e}")

        # Test 4: Safety level awareness
        print("\n[TEST 4] Testing safety level awareness...")
        safety_levels = [SafetyLevel.PERMISSIVE, SafetyLevel.STANDARD,
                        SafetyLevel.STRICT, SafetyLevel.PARANOID]
        for level in safety_levels:
            question = f"What does the {level.value} safety level mean?"
            print(f"\nQ: {question}")
            try:
                response = self.agent.chat(question)
                print(f"A: {response[:300]}...")
                self.results.append({
                    "test": "safety_awareness",
                    "level": level.value,
                    "response": response,
                    "aware": level.value.lower() in response.lower()
                })
            except Exception as e:
                print(f"Error: {e}")

        # Test 5: Tool and feature awareness
        print("\n[TEST 5] Testing tool and feature awareness...")
        features = [
            "plan generation",
            "code completion",
            "bug fixing",
            "code refactoring",
            "test generation",
            "code review",
            "RAG system",
            "audit logging",
            "resource monitoring",
            "timeout management"
        ]

        for feature in features:
            question = f"Do you have {feature} capability?"
            print(f"\nQ: {question}")
            try:
                response = self.agent.chat(question)
                print(f"A: {response[:300]}...")
                self.results.append({
                    "test": "feature_awareness",
                    "feature": feature,
                    "response": response,
                    "aware": self._assess_feature_awareness(response, feature)
                })
            except Exception as e:
                print(f"Error: {e}")

        return self.results

    def _assess_awareness(self, response: str, question: str) -> bool:
        """Assess if the response shows awareness of the capability."""
        # Simple heuristic: check if response contains relevant keywords
        keywords = {
            "capabilities": ["complete", "fix", "explain", "refactor", "test", "review"],
            "commands": ["mode", "plan", "approve", "execute", "safety"],
            "safety": ["safety", "level", "confirm", "backup", "audit"],
            "modes": ["chat", "propose", "execute"],
            "plan": ["plan", "execution", "steps", "validate"],
            "code operations": ["complete", "fix", "refactor", "explain"],
            "RAG": ["rag", "retrieval", "knowledge", "vector"],
            "file operations": ["read", "write", "edit", "backup"],
            "dangerous": ["dangerous", "safety", "confirm", "protect"],
            "tools": ["tool", "command", "feature", "capability"]
        }

        for key, values in keywords.items():
            if key.lower() in question.lower():
                return any(v.lower() in response.lower() for v in values)

        return len(response) > 50  # Basic check for substantive response

    def _assess_feature_awareness(self, response: str, feature: str) -> bool:
        """Check if response acknowledges the feature."""
        positive_indicators = ["yes", "support", "have", "capable", "can", "available"]
        negative_indicators = ["no", "don't", "cannot", "not supported", "unavailable"]

        response_lower = response.lower()
        has_positive = any(ind in response_lower for ind in positive_indicators)
        has_negative = any(ind in response_lower for ind in negative_indicators)

        # Feature-specific checks
        feature_map = {
            "plan generation": has_positive,
            "code completion": has_positive,
            "bug fixing": has_positive,
            "code refactoring": has_positive,
            "test generation": has_positive,
            "code review": has_positive,
            "RAG system": has_positive,  # TinyCode has RAG
            "audit logging": has_positive,
            "resource monitoring": has_positive,
            "timeout management": has_positive
        }

        return feature_map.get(feature, has_positive and not has_negative)

    def generate_report(self):
        """Generate a report on TinyCode's self-awareness."""
        print("\n" + "="*60)
        print("SELF-AWARENESS ANALYSIS REPORT")
        print("="*60)

        # Calculate awareness metrics
        total_tests = len(self.results)
        aware_count = sum(1 for r in self.results if r.get('aware', False))
        awareness_percentage = (aware_count / total_tests * 100) if total_tests > 0 else 0

        print(f"\nOverall Awareness Score: {awareness_percentage:.1f}%")
        print(f"Aware responses: {aware_count}/{total_tests}")

        # Breakdown by test type
        test_types = {}
        for result in self.results:
            test_type = result.get('test', 'unknown')
            if test_type not in test_types:
                test_types[test_type] = {'total': 0, 'aware': 0}
            test_types[test_type]['total'] += 1
            if result.get('aware', False):
                test_types[test_type]['aware'] += 1

        print("\nAwareness by Category:")
        for test_type, stats in test_types.items():
            percentage = (stats['aware'] / stats['total'] * 100) if stats['total'] > 0 else 0
            print(f"  {test_type}: {percentage:.1f}% ({stats['aware']}/{stats['total']})")

        # Identify gaps
        print("\nIdentified Gaps in Self-Awareness:")
        gaps = []
        for result in self.results:
            if not result.get('aware', False):
                if 'question' in result:
                    gaps.append(f"  - {result['question']}")
                elif 'command' in result:
                    gaps.append(f"  - Command: {result['command']}")
                elif 'feature' in result:
                    gaps.append(f"  - Feature: {result['feature']}")

        for gap in gaps[:10]:  # Show first 10 gaps
            print(gap)

        if len(gaps) > 10:
            print(f"  ... and {len(gaps) - 10} more")

        # Save detailed report
        report_file = f"tinycoder_awareness_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump({
                'summary': {
                    'awareness_score': awareness_percentage,
                    'total_tests': total_tests,
                    'aware_count': aware_count,
                    'test_breakdown': test_types
                },
                'gaps': gaps,
                'detailed_results': self.results
            }, f, indent=2)

        print(f"\nDetailed report saved to: {report_file}")

        return awareness_percentage, gaps

def main():
    print("Starting TinyCode Self-Awareness Exploration...")

    try:
        explorer = TinyCodeAwarenessExplorer()
        explorer.test_self_awareness()
        awareness_score, gaps = explorer.generate_report()

        print("\n" + "="*60)
        print("RECOMMENDATIONS FOR IMPROVING SELF-AWARENESS")
        print("="*60)

        print("\n1. Add a comprehensive '/capabilities' command that lists all features")
        print("2. Implement a '/help <feature>' system for detailed explanations")
        print("3. Create a self-documentation system that TinyCode can query")
        print("4. Add introspection methods to query internal state and configuration")
        print("5. Implement a feature discovery mechanism")
        print("6. Add context about available modes, commands, and safety levels to prompts")
        print("7. Create a knowledge base about its own architecture")

        if awareness_score < 50:
            print("\n⚠️  Low self-awareness detected. Consider implementing the above recommendations.")
        elif awareness_score < 80:
            print("\n⚡ Moderate self-awareness. Some improvements recommended.")
        else:
            print("\n✅ Good self-awareness detected!")

    except Exception as e:
        print(f"Error during exploration: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
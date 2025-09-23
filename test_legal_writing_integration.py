#!/usr/bin/env python3
"""
Test script for legal writing knowledge integration

This script tests all components of the legal writing knowledge system
to ensure they work correctly and integrate properly with TinyCode.
"""

import sys
import traceback
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_writing_principles():
    """Test the Legal Writing Principles module"""
    print("Testing Legal Writing Principles module...")

    try:
        from tiny_code.legal.writing_principles import (
            LegalWritingPrinciples, LegalDocumentType, AnalysisStructure
        )

        principles = LegalWritingPrinciples()

        # Test getting all principles
        all_principles = principles.get_all_principles()
        print(f"✓ Loaded {len(all_principles)} legal writing principles")

        # Test getting principles by category
        categories = principles.get_principle_categories()
        print(f"✓ Found {len(categories)} principle categories: {', '.join(categories)}")

        for category in categories:
            category_principles = principles.get_principles_by_category(category)
            print(f"  - {category}: {len(category_principles)} principles")

        # Test analysis frameworks
        for framework in AnalysisStructure:
            framework_details = principles.get_analysis_framework(framework)
            if framework_details:
                print(f"✓ {framework.value.upper()} framework loaded with {len(framework_details['components'])} components")

        # Test citation validation
        test_citations = [
            ("Brown v. Board of Education, 347 U.S. 483 (1954)", "case_citation"),
            ("42 U.S.C. § 1983", "statute_citation"),
            ("17 C.F.R. § 240.10b-5", "regulation_citation")
        ]

        for citation, citation_type in test_citations:
            is_valid, errors = principles.validate_citation_format(citation, citation_type)
            status = "✓" if is_valid else "✗"
            print(f"{status} Citation validation for {citation_type}: {citation}")
            if errors:
                for error in errors[:2]:  # Show first 2 errors
                    print(f"    Error: {error}")

        return True

    except Exception as e:
        print(f"✗ Error testing writing principles: {e}")
        traceback.print_exc()
        return False

def test_writing_evaluator():
    """Test the Legal Writing Evaluator module"""
    print("\nTesting Legal Writing Evaluator module...")

    try:
        from tiny_code.legal.writing_evaluator import LegalWritingEvaluator
        from tiny_code.legal.writing_principles import LegalDocumentType

        evaluator = LegalWritingEvaluator()

        # Test with sample legal text
        sample_brief = """
        BRIEF OF APPELLANT

        STATEMENT OF ISSUES
        Whether the trial court erred in granting defendant's motion to dismiss.

        STATEMENT OF FACTS
        Plaintiff filed suit against defendant on January 1, 2024. The case involves
        contract interpretation. The trial court granted defendant's motion to dismiss
        on procedural grounds.

        ARGUMENT
        I. THE TRIAL COURT ERRED IN DISMISSING THE COMPLAINT

        The applicable standard for motions to dismiss is well established. In Brown v.
        Board of Education, 347 U.S. 483 (1954), the Court held that complaints should
        not be dismissed unless it appears beyond doubt that plaintiff can prove no set
        of facts entitling relief.

        Here, plaintiff's complaint states a valid claim. The facts alleged show that
        defendant breached the contract by failing to perform. Therefore, dismissal was
        inappropriate.

        CONCLUSION
        For the foregoing reasons, this Court should reverse the trial court's order.
        """

        print("Evaluating sample legal brief...")
        analysis = evaluator.evaluate_document(sample_brief, LegalDocumentType.BRIEF)

        print(f"✓ Document analysis completed")
        print(f"  Overall Score: {analysis.overall_score:.1f}/10.0")
        print(f"  Document Type: {analysis.document_type.value if analysis.document_type else 'Unknown'}")
        print(f"  Analysis Framework: {analysis.analysis_framework_used.value if analysis.analysis_framework_used else 'Not detected'}")
        print(f"  Word Count: {analysis.word_count}")
        print(f"  Issues Found: {len(analysis.issues)}")
        print(f"  Strengths Identified: {len(analysis.strengths)}")

        # Test quality dimensions
        print("Quality Dimension Scores:")
        for quality_dim, score in analysis.quality_scores.items():
            print(f"  - {quality_dim.value.replace('_', ' ').title()}: {score.score:.1f}/10.0")

        # Test report generation
        report = evaluator.format_analysis_report(analysis)
        print(f"✓ Generated analysis report ({len(report)} characters)")

        return True

    except Exception as e:
        print(f"✗ Error testing writing evaluator: {e}")
        traceback.print_exc()
        return False

def test_document_templates():
    """Test the Document Templates module"""
    print("\nTesting Document Templates module...")

    try:
        from tiny_code.legal.document_templates import LegalDocumentTemplates
        from tiny_code.legal.writing_principles import LegalDocumentType

        templates = LegalDocumentTemplates()

        # Test getting available templates
        available_templates = templates.get_available_templates()
        print(f"✓ Loaded {len(available_templates)} document templates")

        for template in available_templates:
            print(f"  - {template.name}: {len(template.sections)} sections")

        # Test specific template generation
        for doc_type in [LegalDocumentType.BRIEF, LegalDocumentType.MEMORANDUM, LegalDocumentType.MOTION]:
            template = templates.get_template(doc_type)
            if template:
                print(f"✓ {doc_type.value.title()} template loaded")

                # Test outline generation
                outline = templates.generate_document_outline(doc_type, include_instructions=False)
                print(f"  Generated outline ({len(outline)} characters)")

                # Test complete template generation
                complete_template = templates.generate_complete_template(doc_type, include_instructions=False)
                print(f"  Generated complete template ({len(complete_template)} characters)")

                # Test structure validation
                sample_content = "This is a sample document with basic structure."
                is_valid, issues = templates.validate_document_structure(sample_content, doc_type)
                status = "✓" if is_valid else "✗"
                print(f"  {status} Structure validation (issues: {len(issues)})")

        return True

    except Exception as e:
        print(f"✗ Error testing document templates: {e}")
        traceback.print_exc()
        return False

def test_command_registry_integration():
    """Test that legal writing commands are properly registered"""
    print("\nTesting Command Registry integration...")

    try:
        from tiny_code.command_registry import CommandRegistry

        registry = CommandRegistry()

        # Check that legal writing commands are registered
        legal_writing_commands = [
            'writing_principles',
            'writing_evaluate',
            'document_templates',
            'generate_template',
            'citation_check',
            'irac_analysis',
            'writing_score'
        ]

        for command in legal_writing_commands:
            if command in registry.commands:
                cmd_info = registry.commands[command]
                print(f"✓ Command '{command}' registered")
                print(f"  Category: {cmd_info.category.value}")
                print(f"  Danger Level: {cmd_info.danger_level.value}")
                print(f"  Available in PARALEGAL: {cmd_info.allowed_in_paralegal}")
            else:
                print(f"✗ Command '{command}' not found in registry")
                return False

        return True

    except Exception as e:
        print(f"✗ Error testing command registry: {e}")
        traceback.print_exc()
        return False

def test_cli_integration():
    """Test that CLI command handlers exist"""
    print("\nTesting CLI integration...")

    try:
        from tiny_code.cli import TinyCodeCLI

        # Create CLI instance (this will test imports and initialization)
        cli = TinyCodeCLI()

        # Check that legal writing command handlers exist
        legal_writing_handlers = [
            'writing_principles_cmd',
            'writing_evaluate_cmd',
            'document_templates_cmd',
            'generate_template_cmd',
            'citation_check_cmd',
            'irac_analysis_cmd',
            'writing_score_cmd'
        ]

        for handler in legal_writing_handlers:
            if hasattr(cli, handler):
                print(f"✓ Handler '{handler}' exists")
                # Verify it's callable
                method = getattr(cli, handler)
                if callable(method):
                    print(f"  Handler is callable")
                else:
                    print(f"✗ Handler is not callable")
                    return False
            else:
                print(f"✗ Handler '{handler}' not found")
                return False

        return True

    except Exception as e:
        print(f"✗ Error testing CLI integration: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("TINYCODE LEGAL WRITING KNOWLEDGE INTEGRATION TEST")
    print("=" * 60)

    tests = [
        ("Writing Principles", test_writing_principles),
        ("Writing Evaluator", test_writing_evaluator),
        ("Document Templates", test_document_templates),
        ("Command Registry", test_command_registry_integration),
        ("CLI Integration", test_cli_integration)
    ]

    results = []

    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"✗ Test '{test_name}' failed with exception: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "PASS" if success else "FAIL"
        print(f"{test_name:20} : {status}")

    print(f"\n{passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Legal writing knowledge integration is working correctly.")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
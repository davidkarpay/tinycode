#!/usr/bin/env python3
"""
Demo script for TinyCode Legal Writing Knowledge System

This script demonstrates the key features of the legal writing knowledge
system that has been integrated into TinyCode.
"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def demo_writing_principles():
    """Demonstrate writing principles functionality"""
    print("=" * 60)
    print("LEGAL WRITING PRINCIPLES")
    print("=" * 60)

    from tiny_code.legal.writing_principles import LegalWritingPrinciples

    principles = LegalWritingPrinciples()

    # Show overview
    print("Available Principle Categories:")
    categories = principles.get_principle_categories()
    for category in categories:
        category_principles = principles.get_principles_by_category(category)
        print(f"  • {category.replace('_', ' ').title()}: {len(category_principles)} principles")

    # Show details for one category
    print(f"\nClarity & Precision Principles:")
    clarity_principles = principles.get_principles_by_category("clarity_precision")
    for principle in clarity_principles:
        print(f"\n  {principle.name} ({principle.importance} Priority)")
        print(f"    {principle.description}")
        if principle.best_practices:
            print(f"    Best Practices:")
            for practice in principle.best_practices[:2]:
                print(f"      • {practice}")

def demo_citation_validation():
    """Demonstrate citation validation"""
    print("\n" + "=" * 60)
    print("CITATION VALIDATION")
    print("=" * 60)

    from tiny_code.legal.writing_principles import LegalWritingPrinciples

    principles = LegalWritingPrinciples()

    test_citations = [
        ("Brown v. Board of Education, 347 U.S. 483 (1954)", "case_citation"),
        ("42 U.S.C. § 1983", "statute_citation"),
        ("Wrong Format Case", "case_citation"),
        ("17 C.F.R. § 240.10b-5", "regulation_citation")
    ]

    for citation, citation_type in test_citations:
        print(f"\nValidating: {citation}")
        is_valid, errors = principles.validate_citation_format(citation, citation_type)

        if is_valid:
            print("  ✓ Valid citation format")
        else:
            print("  ✗ Citation format issues:")
            for error in errors[:2]:  # Show first 2 errors
                print(f"    • {error}")

def demo_analysis_frameworks():
    """Demonstrate analysis frameworks"""
    print("\n" + "=" * 60)
    print("LEGAL ANALYSIS FRAMEWORKS")
    print("=" * 60)

    from tiny_code.legal.writing_principles import LegalWritingPrinciples, AnalysisStructure

    principles = LegalWritingPrinciples()

    for framework in [AnalysisStructure.IRAC, AnalysisStructure.CRAC]:
        framework_details = principles.get_analysis_framework(framework)
        print(f"\n{framework_details['name']} Framework:")
        print(f"  {framework_details['description']}")
        print(f"  Best for: {', '.join(framework_details['best_for'])}")
        print(f"  Components:")
        for component in framework_details['components']:
            print(f"    • {component['name']}: {component['description']}")

def demo_document_evaluation():
    """Demonstrate document evaluation"""
    print("\n" + "=" * 60)
    print("DOCUMENT EVALUATION")
    print("=" * 60)

    from tiny_code.legal.writing_evaluator import LegalWritingEvaluator
    from tiny_code.legal.writing_principles import LegalDocumentType

    evaluator = LegalWritingEvaluator()

    # Sample problematic legal text for demonstration
    sample_text = """
    This case is about a contract dispute. The defendant basically did not
    perform their obligations under the agreement. Obviously, this is a clear
    breach of contract. The plaintiff is definitely entitled to damages.

    The law says that contracts must be performed. This rule applies here.
    Therefore, plaintiff should win.
    """

    print("Evaluating sample legal text:")
    print(f"Text: {sample_text.strip()[:100]}...")

    analysis = evaluator.evaluate_document(sample_text, LegalDocumentType.MEMORANDUM)

    print(f"\nEvaluation Results:")
    print(f"  Overall Score: {analysis.overall_score:.1f}/10.0")
    print(f"  Word Count: {analysis.word_count}")

    print(f"\nQuality Scores:")
    for quality_dim, score in analysis.quality_scores.items():
        color_desc = "Good" if score.score >= 7 else "Fair" if score.score >= 5 else "Needs Work"
        print(f"  {quality_dim.value.replace('_', ' ').title():20} {score.score:4.1f}/10.0 ({color_desc})")

    print(f"\nKey Issues Found:")
    for issue in analysis.issues[:3]:  # Show top 3 issues
        print(f"  • {issue.description}")
        print(f"    Suggestion: {issue.suggestion}")

def demo_document_templates():
    """Demonstrate document templates"""
    print("\n" + "=" * 60)
    print("DOCUMENT TEMPLATES")
    print("=" * 60)

    from tiny_code.legal.document_templates import LegalDocumentTemplates
    from tiny_code.legal.writing_principles import LegalDocumentType

    templates = LegalDocumentTemplates()

    print("Available Templates:")
    available_templates = templates.get_available_templates()
    for template in available_templates:
        print(f"  • {template.name}: {len(template.sections)} sections")
        if template.analysis_framework:
            print(f"    Framework: {template.analysis_framework.value.upper()}")

    # Show brief template structure
    print(f"\nLegal Brief Template Structure:")
    brief_template = templates.get_template(LegalDocumentType.BRIEF)
    for i, section in enumerate(brief_template.sections, 1):
        required = "(Required)" if section.required else "(Optional)"
        print(f"  {i}. {section.name} {required}")
        print(f"     {section.description}")

def demo_cli_commands():
    """Show available CLI commands"""
    print("\n" + "=" * 60)
    print("AVAILABLE CLI COMMANDS")
    print("=" * 60)

    commands = [
        ("/writing_principles", "Show legal writing principles and best practices"),
        ("/writing_evaluate <file>", "Evaluate document against writing principles"),
        ("/document_templates", "Show available legal document templates"),
        ("/generate_template <type>", "Generate document template"),
        ("/citation_check <citation>", "Validate citation format"),
        ("/irac_analysis <framework>", "Show IRAC/CRAC/CREAC framework details"),
        ("/writing_score <file>", "Get writing quality score and analysis")
    ]

    print("TinyCode now includes these legal writing commands:")
    for command, description in commands:
        print(f"  {command:30} {description}")

    print(f"\nExample usage:")
    print('  /writing_principles clarity_precision')
    print('  /citation_check "Brown v. Board, 347 U.S. 483 (1954)"')
    print('  /irac_analysis crac')
    print('  /generate_template memorandum')

def main():
    """Run the complete demonstration"""
    print("TinyCode Legal Writing Knowledge System")
    print("Comprehensive Legal Writing Analysis & Templates")

    demo_writing_principles()
    demo_citation_validation()
    demo_analysis_frameworks()
    demo_document_evaluation()
    demo_document_templates()
    demo_cli_commands()

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("✅ Legal Writing Principles: 9 principles across 5 categories")
    print("✅ Analysis Frameworks: IRAC, CRAC, CREAC with detailed guidance")
    print("✅ Citation Validation: Case law, statutes, and regulations")
    print("✅ Document Evaluation: 8-dimension quality scoring system")
    print("✅ Document Templates: 5 template types with complete structures")
    print("✅ CLI Integration: 7 new commands available in TinyCode")
    print("\n🎯 TinyCode now has persistent legal writing knowledge that")
    print("   will help users create better legal documents and improve")
    print("   their legal writing skills across all sessions.")

if __name__ == "__main__":
    main()
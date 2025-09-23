"""
Legal Writing Principles and Best Practices Module

This module contains comprehensive legal writing principles, standards, and best practices
for evaluating and improving legal documents, briefs, memoranda, and other legal writing.

Based on 2024 legal writing standards and established best practices.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple, Set
import re


class LegalDocumentType(Enum):
    """Types of legal documents"""
    BRIEF = "brief"
    MEMORANDUM = "memorandum"
    CLIENT_LETTER = "client_letter"
    CONTRACT = "contract"
    MOTION = "motion"
    OPINION_LETTER = "opinion_letter"
    DEMAND_LETTER = "demand_letter"
    PLEADING = "pleading"
    DISCOVERY = "discovery"
    RESEARCH_MEMO = "research_memo"


class AnalysisStructure(Enum):
    """Legal analysis structures"""
    IRAC = "irac"  # Issue, Rule, Application, Conclusion
    CRAC = "crac"  # Conclusion, Rule, Application, Conclusion
    CREAC = "creac"  # Conclusion, Rule, Explanation, Application, Conclusion


class WritingQuality(Enum):
    """Writing quality dimensions"""
    CLARITY = "clarity"
    ORGANIZATION = "organization"
    PERSUASIVENESS = "persuasiveness"
    PROFESSIONAL_TONE = "professional_tone"
    CITATION_ACCURACY = "citation_accuracy"
    LEGAL_REASONING = "legal_reasoning"
    GRAMMAR_STYLE = "grammar_style"
    AUTHORITY_SUPPORT = "authority_support"


@dataclass
class LegalWritingPrinciple:
    """A legal writing principle with examples and evaluation criteria"""
    name: str
    category: str
    description: str
    importance: str  # High, Medium, Low
    examples: List[str] = field(default_factory=list)
    violations: List[str] = field(default_factory=list)
    best_practices: List[str] = field(default_factory=list)
    evaluation_criteria: List[str] = field(default_factory=list)


@dataclass
class CitationStandard:
    """Citation format standards and rules"""
    name: str
    format_pattern: str
    description: str
    examples: List[str] = field(default_factory=list)
    common_errors: List[str] = field(default_factory=list)


@dataclass
class DocumentStructure:
    """Standard structure for legal documents"""
    document_type: LegalDocumentType
    required_sections: List[str]
    optional_sections: List[str]
    section_order: List[str]
    formatting_requirements: Dict[str, str] = field(default_factory=dict)


class LegalWritingPrinciples:
    """Comprehensive legal writing principles and standards"""

    def __init__(self):
        self.principles = self._initialize_principles()
        self.citation_standards = self._initialize_citation_standards()
        self.document_structures = self._initialize_document_structures()
        self.analysis_frameworks = self._initialize_analysis_frameworks()

    def _initialize_principles(self) -> Dict[str, List[LegalWritingPrinciple]]:
        """Initialize comprehensive legal writing principles"""

        principles = {
            "clarity_precision": [
                LegalWritingPrinciple(
                    name="Plain Language",
                    category="clarity_precision",
                    description="Use clear, understandable language that conveys meaning precisely",
                    importance="High",
                    examples=[
                        "Use 'before' instead of 'prior to'",
                        "Use 'help' instead of 'assist'",
                        "Use 'use' instead of 'utilize'"
                    ],
                    violations=[
                        "Legal jargon without explanation",
                        "Unnecessarily complex sentence structures",
                        "Ambiguous pronoun references"
                    ],
                    best_practices=[
                        "Define technical terms when first used",
                        "Use active voice when possible",
                        "Limit sentences to 25 words or fewer",
                        "Avoid nominalizations (turning verbs into nouns)"
                    ],
                    evaluation_criteria=[
                        "Sentence length and complexity",
                        "Use of plain language alternatives",
                        "Clarity of pronoun references",
                        "Definition of technical terms"
                    ]
                ),
                LegalWritingPrinciple(
                    name="Precision and Accuracy",
                    category="clarity_precision",
                    description="Choose words that convey exact meaning without ambiguity",
                    importance="High",
                    examples=[
                        "Use 'shall' for mandatory obligations",
                        "Use 'may' for permissive actions",
                        "Use specific dates rather than 'recently' or 'soon'"
                    ],
                    violations=[
                        "Vague time references",
                        "Ambiguous quantifiers",
                        "Inconsistent terminology"
                    ],
                    best_practices=[
                        "Use consistent terminology throughout document",
                        "Specify exact timeframes and deadlines",
                        "Quantify when possible (avoid 'many', 'several')",
                        "Use parallel structure in lists"
                    ],
                    evaluation_criteria=[
                        "Consistency of terminology",
                        "Specificity of time references",
                        "Precision of quantitative statements",
                        "Clarity of obligations and permissions"
                    ]
                )
            ],

            "organization_structure": [
                LegalWritingPrinciple(
                    name="Logical Organization",
                    category="organization_structure",
                    description="Present arguments in logical order with clear transitions",
                    importance="High",
                    examples=[
                        "Strongest arguments first",
                        "Chronological order for facts",
                        "General to specific organization"
                    ],
                    violations=[
                        "Random ordering of arguments",
                        "Missing transitions between sections",
                        "Burying important points"
                    ],
                    best_practices=[
                        "Create detailed outline before writing",
                        "Use headings and subheadings effectively",
                        "Provide clear transitions between sections",
                        "Front-load important information"
                    ],
                    evaluation_criteria=[
                        "Logical flow of arguments",
                        "Effective use of headings",
                        "Quality of transitions",
                        "Placement of key information"
                    ]
                ),
                LegalWritingPrinciple(
                    name="IRAC/CRAC Structure",
                    category="organization_structure",
                    description="Use structured analysis frameworks for legal reasoning",
                    importance="High",
                    examples=[
                        "Clear issue identification",
                        "Complete rule statements",
                        "Thorough fact application"
                    ],
                    violations=[
                        "Missing components of analysis",
                        "Incomplete rule statements",
                        "Failure to apply law to facts"
                    ],
                    best_practices=[
                        "Begin with clear issue statement",
                        "Provide comprehensive rule explanation",
                        "Apply rules systematically to facts",
                        "Draw logical conclusions"
                    ],
                    evaluation_criteria=[
                        "Completeness of IRAC/CRAC structure",
                        "Quality of issue identification",
                        "Thoroughness of rule explanation",
                        "Strength of application section"
                    ]
                )
            ],

            "persuasion_argumentation": [
                LegalWritingPrinciple(
                    name="Logical Argumentation",
                    category="persuasion_argumentation",
                    description="Build compelling arguments through logical reasoning",
                    importance="High",
                    examples=[
                        "Syllogistic reasoning structure",
                        "Analogical reasoning with precedent",
                        "Policy-based arguments"
                    ],
                    violations=[
                        "Circular reasoning",
                        "False dichotomies",
                        "Ad hominem attacks"
                    ],
                    best_practices=[
                        "Support each argument with authority",
                        "Address counterarguments",
                        "Use analogical reasoning effectively",
                        "Build from strongest to weakest points"
                    ],
                    evaluation_criteria=[
                        "Logical consistency of arguments",
                        "Quality of supporting authority",
                        "Treatment of counterarguments",
                        "Persuasive force of reasoning"
                    ]
                ),
                LegalWritingPrinciple(
                    name="Authority Integration",
                    category="persuasion_argumentation",
                    description="Effectively integrate and analyze legal authorities",
                    importance="High",
                    examples=[
                        "Synthesizing multiple cases",
                        "Distinguishing adverse authority",
                        "Hierarchical authority analysis"
                    ],
                    violations=[
                        "Quote dropping without analysis",
                        "Ignoring adverse authority",
                        "Mischaracterizing holdings"
                    ],
                    best_practices=[
                        "Explain rather than just cite authority",
                        "Synthesize multiple sources",
                        "Address contrary authority",
                        "Use most recent and relevant authority"
                    ],
                    evaluation_criteria=[
                        "Quality of authority explanation",
                        "Synthesis of multiple sources",
                        "Treatment of adverse authority",
                        "Currency and relevance of citations"
                    ]
                )
            ],

            "citation_research": [
                LegalWritingPrinciple(
                    name="Proper Citation Format",
                    category="citation_research",
                    description="Follow consistent citation format throughout document",
                    importance="High",
                    examples=[
                        "Bluebook citation format",
                        "Consistent short form citations",
                        "Proper parenthetical explanations"
                    ],
                    violations=[
                        "Inconsistent citation format",
                        "Missing or incorrect pinpoint citations",
                        "Improper short form usage"
                    ],
                    best_practices=[
                        "Use current Bluebook rules",
                        "Include pinpoint citations",
                        "Provide parenthetical explanations when helpful",
                        "Use string citations effectively"
                    ],
                    evaluation_criteria=[
                        "Consistency with citation format",
                        "Accuracy of citations",
                        "Appropriate use of short forms",
                        "Quality of parenthetical explanations"
                    ]
                )
            ],

            "style_tone": [
                LegalWritingPrinciple(
                    name="Professional Tone",
                    category="style_tone",
                    description="Maintain appropriate professional tone throughout",
                    importance="High",
                    examples=[
                        "Formal but accessible language",
                        "Respectful treatment of opposing parties",
                        "Confident assertion of arguments"
                    ],
                    violations=[
                        "Overly casual language",
                        "Disrespectful characterizations",
                        "Tentative or apologetic tone"
                    ],
                    best_practices=[
                        "Use active voice predominantly",
                        "Avoid colloquialisms and slang",
                        "Maintain respectful tone even when arguing",
                        "Project confidence in legal positions"
                    ],
                    evaluation_criteria=[
                        "Appropriateness of tone",
                        "Use of active vs. passive voice",
                        "Professional language choices",
                        "Confidence of assertion"
                    ]
                ),
                LegalWritingPrinciple(
                    name="Conciseness",
                    category="style_tone",
                    description="Express ideas efficiently without unnecessary words",
                    importance="Medium",
                    examples=[
                        "Eliminate redundant phrases",
                        "Use strong verbs instead of weak verb + adverb",
                        "Combine related sentences"
                    ],
                    violations=[
                        "Wordy expressions",
                        "Redundant phrases",
                        "Weak verb constructions"
                    ],
                    best_practices=[
                        "Eliminate unnecessary words",
                        "Use specific verbs",
                        "Avoid throat-clearing phrases",
                        "Combine choppy sentences"
                    ],
                    evaluation_criteria=[
                        "Efficiency of expression",
                        "Elimination of redundancy",
                        "Strength of verb choices",
                        "Sentence variety and flow"
                    ]
                )
            ]
        }

        return principles

    def _initialize_citation_standards(self) -> Dict[str, CitationStandard]:
        """Initialize citation format standards"""

        return {
            "case_citation": CitationStandard(
                name="Case Citation",
                format_pattern=r"(.+)\s+v\.\s+(.+),\s+(\d+)\s+(.+)\s+(\d+)\s+\((\d{4})\)",
                description="Standard format for case citations following Bluebook rules",
                examples=[
                    "Brown v. Board of Education, 347 U.S. 483 (1954)",
                    "Marbury v. Madison, 5 U.S. (1 Cranch) 137 (1803)",
                    "Miranda v. Arizona, 384 U.S. 436, 444 (1966)"
                ],
                common_errors=[
                    "Missing pinpoint citations",
                    "Incorrect court abbreviations",
                    "Wrong date format",
                    "Inconsistent spacing"
                ]
            ),
            "statute_citation": CitationStandard(
                name="Statute Citation",
                format_pattern=r"(\d+)\s+(.+)\s+§\s+(\d+)",
                description="Standard format for statute citations",
                examples=[
                    "42 U.S.C. § 1983",
                    "15 U.S.C. § 78j(b)",
                    "Fla. Stat. § 95.11"
                ],
                common_errors=[
                    "Missing section symbol",
                    "Incorrect spacing around section symbol",
                    "Wrong abbreviation format"
                ]
            ),
            "regulation_citation": CitationStandard(
                name="Regulation Citation",
                format_pattern=r"(\d+)\s+C\.F\.R\.\s+§\s+(\d+)",
                description="Standard format for federal regulation citations",
                examples=[
                    "17 C.F.R. § 240.10b-5",
                    "29 C.F.R. § 1630.2(g)"
                ],
                common_errors=[
                    "Incorrect C.F.R. abbreviation",
                    "Missing periods in abbreviation"
                ]
            )
        }

    def _initialize_document_structures(self) -> Dict[LegalDocumentType, DocumentStructure]:
        """Initialize standard document structures"""

        return {
            LegalDocumentType.BRIEF: DocumentStructure(
                document_type=LegalDocumentType.BRIEF,
                required_sections=[
                    "Cover Page",
                    "Table of Contents",
                    "Table of Authorities",
                    "Statement of Issues",
                    "Statement of Facts",
                    "Argument",
                    "Conclusion"
                ],
                optional_sections=[
                    "Summary of Argument",
                    "Statement of Standard of Review",
                    "Appendix"
                ],
                section_order=[
                    "Cover Page",
                    "Table of Contents",
                    "Table of Authorities",
                    "Statement of Issues",
                    "Summary of Argument",
                    "Statement of Facts",
                    "Statement of Standard of Review",
                    "Argument",
                    "Conclusion",
                    "Appendix"
                ],
                formatting_requirements={
                    "font": "Times New Roman 12pt",
                    "spacing": "Double-spaced",
                    "margins": "1 inch all sides",
                    "page_numbering": "Bottom center"
                }
            ),
            LegalDocumentType.MEMORANDUM: DocumentStructure(
                document_type=LegalDocumentType.MEMORANDUM,
                required_sections=[
                    "Header (To/From/Date/Re)",
                    "Question Presented",
                    "Brief Answer",
                    "Statement of Facts",
                    "Discussion",
                    "Conclusion"
                ],
                optional_sections=[
                    "Summary",
                    "Recommendations"
                ],
                section_order=[
                    "Header",
                    "Question Presented",
                    "Brief Answer",
                    "Summary",
                    "Statement of Facts",
                    "Discussion",
                    "Conclusion",
                    "Recommendations"
                ],
                formatting_requirements={
                    "font": "Times New Roman 12pt",
                    "spacing": "Single or 1.5 spaced",
                    "margins": "1 inch all sides"
                }
            )
        }

    def _initialize_analysis_frameworks(self) -> Dict[AnalysisStructure, Dict[str, Any]]:
        """Initialize legal analysis frameworks"""

        return {
            AnalysisStructure.IRAC: {
                "name": "IRAC",
                "description": "Issue, Rule, Application, Conclusion - primarily for objective analysis",
                "components": [
                    {
                        "name": "Issue",
                        "description": "Legal question to be resolved",
                        "requirements": [
                            "Clear statement of legal issue",
                            "Narrow, specific framing",
                            "Single sentence preferred"
                        ]
                    },
                    {
                        "name": "Rule",
                        "description": "Relevant legal principles and authorities",
                        "requirements": [
                            "Complete statement of applicable law",
                            "Synthesis of multiple authorities",
                            "Clear rule formulation"
                        ]
                    },
                    {
                        "name": "Application",
                        "description": "Application of rule to specific facts",
                        "requirements": [
                            "Systematic application of law to facts",
                            "Analogical reasoning with precedent",
                            "Address counterarguments"
                        ]
                    },
                    {
                        "name": "Conclusion",
                        "description": "Answer to the legal issue",
                        "requirements": [
                            "Direct answer to issue posed",
                            "Brief and definitive",
                            "Consistent with analysis"
                        ]
                    }
                ],
                "best_for": ["Legal memoranda", "Exam answers", "Objective analysis"]
            },
            AnalysisStructure.CRAC: {
                "name": "CRAC",
                "description": "Conclusion, Rule, Application, Conclusion - for persuasive writing",
                "components": [
                    {
                        "name": "Conclusion (Initial)",
                        "description": "Upfront statement of position",
                        "requirements": [
                            "Clear statement of desired outcome",
                            "Confident assertion",
                            "Sets roadmap for argument"
                        ]
                    },
                    {
                        "name": "Rule",
                        "description": "Legal framework supporting position",
                        "requirements": [
                            "Favorable presentation of law",
                            "Emphasis on supportive authority",
                            "Strategic synthesis of rules"
                        ]
                    },
                    {
                        "name": "Application",
                        "description": "Persuasive application to facts",
                        "requirements": [
                            "Emphasize favorable facts",
                            "Distinguish adverse authority",
                            "Build compelling narrative"
                        ]
                    },
                    {
                        "name": "Conclusion (Final)",
                        "description": "Restatement and call to action",
                        "requirements": [
                            "Reinforce key arguments",
                            "Clear request for relief",
                            "Persuasive final appeal"
                        ]
                    }
                ],
                "best_for": ["Briefs", "Motions", "Persuasive writing"]
            },
            AnalysisStructure.CREAC: {
                "name": "CREAC",
                "description": "Conclusion, Rule, Explanation, Application, Conclusion - enhanced persuasive structure",
                "components": [
                    {
                        "name": "Conclusion (Initial)",
                        "description": "Clear statement of position",
                        "requirements": [
                            "Definitive position statement",
                            "Preview of argument structure"
                        ]
                    },
                    {
                        "name": "Rule",
                        "description": "Statement of governing law",
                        "requirements": [
                            "Accurate rule statement",
                            "Proper citation format"
                        ]
                    },
                    {
                        "name": "Explanation",
                        "description": "Detailed explanation of rule through cases",
                        "requirements": [
                            "Case law synthesis",
                            "Policy rationale",
                            "Rule development over time"
                        ]
                    },
                    {
                        "name": "Application",
                        "description": "Application to case facts",
                        "requirements": [
                            "Analogical reasoning",
                            "Fact-to-fact comparison",
                            "Persuasive argumentation"
                        ]
                    },
                    {
                        "name": "Conclusion (Final)",
                        "description": "Summary and outcome",
                        "requirements": [
                            "Restate conclusion",
                            "Summarize key points"
                        ]
                    }
                ],
                "best_for": ["Complex briefs", "Appellate arguments", "Detailed analysis"]
            }
        }

    def get_principles_by_category(self, category: str) -> List[LegalWritingPrinciple]:
        """Get all principles in a specific category"""
        return self.principles.get(category, [])

    def get_all_principles(self) -> List[LegalWritingPrinciple]:
        """Get all legal writing principles"""
        all_principles = []
        for category_principles in self.principles.values():
            all_principles.extend(category_principles)
        return all_principles

    def get_document_structure(self, doc_type: LegalDocumentType) -> Optional[DocumentStructure]:
        """Get standard structure for document type"""
        return self.document_structures.get(doc_type)

    def get_analysis_framework(self, structure: AnalysisStructure) -> Optional[Dict[str, Any]]:
        """Get details for analysis framework"""
        return self.analysis_frameworks.get(structure)

    def get_citation_standard(self, citation_type: str) -> Optional[CitationStandard]:
        """Get citation standard for specific type"""
        return self.citation_standards.get(citation_type)

    def validate_citation_format(self, citation: str, citation_type: str) -> Tuple[bool, List[str]]:
        """Validate citation format against standards"""
        standard = self.get_citation_standard(citation_type)
        if not standard:
            return False, [f"Unknown citation type: {citation_type}"]

        errors = []
        pattern = re.compile(standard.format_pattern)

        if not pattern.match(citation.strip()):
            errors.append(f"Citation does not match expected format for {citation_type}")
            errors.append(f"Expected pattern: {standard.description}")

            # Check for common errors
            for error in standard.common_errors:
                errors.append(f"Common error: {error}")

        return len(errors) == 0, errors

    def get_principle_categories(self) -> List[str]:
        """Get list of all principle categories"""
        return list(self.principles.keys())

    def search_principles(self, query: str) -> List[LegalWritingPrinciple]:
        """Search principles by keyword"""
        query = query.lower()
        matching_principles = []

        for principle in self.get_all_principles():
            if (query in principle.name.lower() or
                query in principle.description.lower() or
                any(query in example.lower() for example in principle.examples) or
                any(query in practice.lower() for practice in principle.best_practices)):
                matching_principles.append(principle)

        return matching_principles
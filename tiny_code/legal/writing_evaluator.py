"""
Legal Writing Evaluator

This module provides comprehensive evaluation capabilities for legal documents,
analyzing them against established legal writing principles and best practices.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple, Set
import re
from datetime import datetime

from .writing_principles import (
    LegalWritingPrinciples, LegalWritingPrinciple, LegalDocumentType,
    AnalysisStructure, WritingQuality, DocumentStructure
)


class SeverityLevel(Enum):
    """Severity levels for writing issues"""
    CRITICAL = "critical"  # Major issues that significantly impact document quality
    HIGH = "high"         # Important issues that should be addressed
    MEDIUM = "medium"     # Moderate issues that improve quality when fixed
    LOW = "low"          # Minor issues or suggestions for improvement
    INFO = "info"        # Informational feedback


class IssueType(Enum):
    """Types of writing issues"""
    CLARITY = "clarity"
    ORGANIZATION = "organization"
    CITATION = "citation"
    STRUCTURE = "structure"
    TONE = "tone"
    GRAMMAR = "grammar"
    ANALYSIS = "analysis"
    AUTHORITY = "authority"


@dataclass
class WritingIssue:
    """A specific writing issue found in the document"""
    type: IssueType
    severity: SeverityLevel
    description: str
    location: str  # Section, paragraph, or line reference
    suggestion: str
    principle_violated: Optional[str] = None
    line_number: Optional[int] = None
    character_position: Optional[int] = None


@dataclass
class QualityScore:
    """Quality score for a specific dimension"""
    dimension: WritingQuality
    score: float  # 0.0 to 10.0
    max_score: float = 10.0
    weight: float = 1.0
    issues: List[WritingIssue] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)


@dataclass
class DocumentAnalysis:
    """Complete analysis of a legal document"""
    document_type: Optional[LegalDocumentType]
    overall_score: float
    quality_scores: Dict[WritingQuality, QualityScore]
    issues: List[WritingIssue]
    strengths: List[str]
    recommendations: List[str]
    structure_analysis: Dict[str, Any]
    citation_analysis: Dict[str, Any]
    analysis_framework_used: Optional[AnalysisStructure]
    word_count: int
    readability_metrics: Dict[str, float]
    evaluation_timestamp: datetime = field(default_factory=datetime.now)


class LegalWritingEvaluator:
    """Comprehensive legal writing evaluation system"""

    def __init__(self):
        self.principles = LegalWritingPrinciples()
        self.quality_weights = self._initialize_quality_weights()

    def _initialize_quality_weights(self) -> Dict[WritingQuality, float]:
        """Initialize weighting for different quality dimensions"""
        return {
            WritingQuality.CLARITY: 1.5,           # Most important
            WritingQuality.LEGAL_REASONING: 1.5,   # Most important
            WritingQuality.ORGANIZATION: 1.3,
            WritingQuality.CITATION_ACCURACY: 1.2,
            WritingQuality.AUTHORITY_SUPPORT: 1.2,
            WritingQuality.PERSUASIVENESS: 1.1,
            WritingQuality.PROFESSIONAL_TONE: 1.0,
            WritingQuality.GRAMMAR_STYLE: 0.8      # Important but less than substantive issues
        }

    def evaluate_document(self,
                         content: str,
                         document_type: Optional[LegalDocumentType] = None,
                         analysis_framework: Optional[AnalysisStructure] = None) -> DocumentAnalysis:
        """Comprehensive evaluation of a legal document"""

        # Basic document metrics
        word_count = len(content.split())
        readability_metrics = self._calculate_readability_metrics(content)

        # Detect document type if not provided
        if not document_type:
            document_type = self._detect_document_type(content)

        # Detect analysis framework if not provided
        if not analysis_framework:
            analysis_framework = self._detect_analysis_framework(content)

        # Evaluate each quality dimension
        quality_scores = {}
        all_issues = []
        all_strengths = []

        for quality_dim in WritingQuality:
            score = self._evaluate_quality_dimension(content, quality_dim, document_type)
            quality_scores[quality_dim] = score
            all_issues.extend(score.issues)
            all_strengths.extend(score.strengths)

        # Structure analysis
        structure_analysis = self._analyze_document_structure(content, document_type)
        all_issues.extend(structure_analysis.get('issues', []))

        # Citation analysis
        citation_analysis = self._analyze_citations(content)
        all_issues.extend(citation_analysis.get('issues', []))

        # Calculate overall score
        overall_score = self._calculate_overall_score(quality_scores)

        # Generate recommendations
        recommendations = self._generate_recommendations(all_issues, quality_scores)

        return DocumentAnalysis(
            document_type=document_type,
            overall_score=overall_score,
            quality_scores=quality_scores,
            issues=all_issues,
            strengths=all_strengths,
            recommendations=recommendations,
            structure_analysis=structure_analysis,
            citation_analysis=citation_analysis,
            analysis_framework_used=analysis_framework,
            word_count=word_count,
            readability_metrics=readability_metrics
        )

    def _evaluate_quality_dimension(self,
                                   content: str,
                                   dimension: WritingQuality,
                                   document_type: Optional[LegalDocumentType]) -> QualityScore:
        """Evaluate a specific quality dimension"""

        issues = []
        strengths = []
        base_score = 7.0  # Start with good baseline

        if dimension == WritingQuality.CLARITY:
            clarity_analysis = self._analyze_clarity(content)
            issues.extend(clarity_analysis['issues'])
            strengths.extend(clarity_analysis['strengths'])
            base_score = clarity_analysis['score']

        elif dimension == WritingQuality.ORGANIZATION:
            org_analysis = self._analyze_organization(content)
            issues.extend(org_analysis['issues'])
            strengths.extend(org_analysis['strengths'])
            base_score = org_analysis['score']

        elif dimension == WritingQuality.LEGAL_REASONING:
            reasoning_analysis = self._analyze_legal_reasoning(content)
            issues.extend(reasoning_analysis['issues'])
            strengths.extend(reasoning_analysis['strengths'])
            base_score = reasoning_analysis['score']

        elif dimension == WritingQuality.CITATION_ACCURACY:
            citation_analysis = self._analyze_citation_quality(content)
            issues.extend(citation_analysis['issues'])
            strengths.extend(citation_analysis['strengths'])
            base_score = citation_analysis['score']

        elif dimension == WritingQuality.PROFESSIONAL_TONE:
            tone_analysis = self._analyze_professional_tone(content)
            issues.extend(tone_analysis['issues'])
            strengths.extend(tone_analysis['strengths'])
            base_score = tone_analysis['score']

        elif dimension == WritingQuality.PERSUASIVENESS:
            persuasion_analysis = self._analyze_persuasiveness(content)
            issues.extend(persuasion_analysis['issues'])
            strengths.extend(persuasion_analysis['strengths'])
            base_score = persuasion_analysis['score']

        elif dimension == WritingQuality.AUTHORITY_SUPPORT:
            authority_analysis = self._analyze_authority_support(content)
            issues.extend(authority_analysis['issues'])
            strengths.extend(authority_analysis['strengths'])
            base_score = authority_analysis['score']

        elif dimension == WritingQuality.GRAMMAR_STYLE:
            grammar_analysis = self._analyze_grammar_style(content)
            issues.extend(grammar_analysis['issues'])
            strengths.extend(grammar_analysis['strengths'])
            base_score = grammar_analysis['score']

        return QualityScore(
            dimension=dimension,
            score=base_score,
            weight=self.quality_weights.get(dimension, 1.0),
            issues=issues,
            strengths=strengths
        )

    def _analyze_clarity(self, content: str) -> Dict[str, Any]:
        """Analyze document clarity"""
        issues = []
        strengths = []
        score = 7.0

        sentences = self._split_into_sentences(content)

        # Check sentence length
        long_sentences = [s for s in sentences if len(s.split()) > 25]
        if long_sentences:
            severity = SeverityLevel.MEDIUM if len(long_sentences) < 5 else SeverityLevel.HIGH
            issues.append(WritingIssue(
                type=IssueType.CLARITY,
                severity=severity,
                description=f"Found {len(long_sentences)} sentences over 25 words",
                location="Throughout document",
                suggestion="Break long sentences into shorter, clearer statements",
                principle_violated="Plain Language"
            ))
            score -= min(2.0, len(long_sentences) * 0.3)
        else:
            strengths.append("Maintains appropriate sentence length for clarity")

        # Check for passive voice overuse
        passive_sentences = self._detect_passive_voice(sentences)
        passive_ratio = len(passive_sentences) / len(sentences) if sentences else 0
        if passive_ratio > 0.3:
            issues.append(WritingIssue(
                type=IssueType.CLARITY,
                severity=SeverityLevel.MEDIUM,
                description=f"High passive voice usage: {passive_ratio:.1%} of sentences",
                location="Throughout document",
                suggestion="Use active voice to improve clarity and directness",
                principle_violated="Plain Language"
            ))
            score -= passive_ratio * 2
        elif passive_ratio < 0.15:
            strengths.append("Effective use of active voice for clarity")

        # Check for legal jargon without explanation
        jargon_terms = self._detect_unexplained_jargon(content)
        if jargon_terms:
            issues.append(WritingIssue(
                type=IssueType.CLARITY,
                severity=SeverityLevel.MEDIUM,
                description=f"Unexplained legal terms: {', '.join(jargon_terms[:5])}",
                location="Throughout document",
                suggestion="Define technical terms when first used",
                principle_violated="Plain Language"
            ))
            score -= min(1.5, len(jargon_terms) * 0.2)

        # Check for ambiguous pronouns
        ambiguous_pronouns = self._detect_ambiguous_pronouns(content)
        if ambiguous_pronouns:
            issues.append(WritingIssue(
                type=IssueType.CLARITY,
                severity=SeverityLevel.MEDIUM,
                description="Potential ambiguous pronoun references found",
                location="Multiple locations",
                suggestion="Ensure pronouns have clear antecedents",
                principle_violated="Precision and Accuracy"
            ))
            score -= 0.5

        return {
            'score': max(0.0, min(10.0, score)),
            'issues': issues,
            'strengths': strengths
        }

    def _analyze_organization(self, content: str) -> Dict[str, Any]:
        """Analyze document organization"""
        issues = []
        strengths = []
        score = 7.0

        # Check for headings
        headings = self._extract_headings(content)
        if not headings:
            issues.append(WritingIssue(
                type=IssueType.ORGANIZATION,
                severity=SeverityLevel.HIGH,
                description="No clear headings or section breaks found",
                location="Document structure",
                suggestion="Use headings to organize content and guide readers",
                principle_violated="Logical Organization"
            ))
            score -= 2.0
        else:
            strengths.append(f"Good use of headings ({len(headings)} sections)")

        # Check for transitions
        paragraphs = content.split('\n\n')
        transition_words = ['however', 'therefore', 'furthermore', 'moreover', 'consequently',
                          'additionally', 'similarly', 'in contrast', 'on the other hand']

        paragraphs_with_transitions = sum(1 for p in paragraphs
                                        if any(word in p.lower() for word in transition_words))

        if len(paragraphs) > 5 and paragraphs_with_transitions < len(paragraphs) * 0.3:
            issues.append(WritingIssue(
                type=IssueType.ORGANIZATION,
                severity=SeverityLevel.MEDIUM,
                description="Limited use of transition words between paragraphs",
                location="Throughout document",
                suggestion="Add transition words to improve flow between ideas",
                principle_violated="Logical Organization"
            ))
            score -= 1.0

        return {
            'score': max(0.0, min(10.0, score)),
            'issues': issues,
            'strengths': strengths
        }

    def _analyze_legal_reasoning(self, content: str) -> Dict[str, Any]:
        """Analyze quality of legal reasoning"""
        issues = []
        strengths = []
        score = 7.0

        # Check for IRAC/CRAC structure indicators
        has_issue = bool(re.search(r'\b(issue|question|whether)\b', content, re.IGNORECASE))
        has_rule = bool(re.search(r'\b(rule|law|statute|case law|holding)\b', content, re.IGNORECASE))
        has_application = bool(re.search(r'\b(apply|application|here|in this case)\b', content, re.IGNORECASE))
        has_conclusion = bool(re.search(r'\b(conclusion|therefore|thus|accordingly)\b', content, re.IGNORECASE))

        structure_score = sum([has_issue, has_rule, has_application, has_conclusion])
        if structure_score < 3:
            issues.append(WritingIssue(
                type=IssueType.ANALYSIS,
                severity=SeverityLevel.HIGH,
                description="Missing elements of structured legal analysis (IRAC/CRAC)",
                location="Document structure",
                suggestion="Ensure all elements of legal analysis are present",
                principle_violated="IRAC/CRAC Structure"
            ))
            score -= 2.0
        elif structure_score == 4:
            strengths.append("Complete structured legal analysis framework")

        # Check for case citations (basic pattern)
        case_citations = re.findall(r'\b\w+\s+v\.\s+\w+', content)
        if not case_citations:
            issues.append(WritingIssue(
                type=IssueType.AUTHORITY,
                severity=SeverityLevel.MEDIUM,
                description="No case law citations found",
                location="Legal analysis sections",
                suggestion="Support arguments with relevant case law",
                principle_violated="Authority Integration"
            ))
            score -= 1.0
        else:
            strengths.append(f"References {len(case_citations)} case law authorities")

        return {
            'score': max(0.0, min(10.0, score)),
            'issues': issues,
            'strengths': strengths
        }

    def _analyze_citation_quality(self, content: str) -> Dict[str, Any]:
        """Analyze citation format and quality"""
        issues = []
        strengths = []
        score = 8.0

        # Find potential citations
        citations = self._extract_citations(content)

        if not citations:
            issues.append(WritingIssue(
                type=IssueType.CITATION,
                severity=SeverityLevel.MEDIUM,
                description="No citations found in document",
                location="Throughout document",
                suggestion="Include proper citations to support legal arguments"
            ))
            score -= 2.0
        else:
            # Validate citation formats
            format_errors = 0
            for citation in citations:
                is_valid, errors = self._validate_citation_format(citation)
                if not is_valid:
                    format_errors += 1

            if format_errors > 0:
                error_rate = format_errors / len(citations)
                severity = SeverityLevel.HIGH if error_rate > 0.5 else SeverityLevel.MEDIUM
                issues.append(WritingIssue(
                    type=IssueType.CITATION,
                    severity=severity,
                    description=f"Citation format errors in {format_errors}/{len(citations)} citations",
                    location="Citation references",
                    suggestion="Review and correct citation format according to Bluebook rules",
                    principle_violated="Proper Citation Format"
                ))
                score -= error_rate * 3
            else:
                strengths.append("Proper citation formatting throughout document")

        return {
            'score': max(0.0, min(10.0, score)),
            'issues': issues,
            'strengths': strengths
        }

    def _analyze_professional_tone(self, content: str) -> Dict[str, Any]:
        """Analyze professional tone and style"""
        issues = []
        strengths = []
        score = 7.0

        # Check for inappropriate casual language
        casual_words = ['basically', 'obviously', 'clearly', 'definitely', 'totally',
                       'really', 'very', 'quite', 'pretty much', 'sort of', 'kind of']
        found_casual = [word for word in casual_words if word in content.lower()]

        if found_casual:
            issues.append(WritingIssue(
                type=IssueType.TONE,
                severity=SeverityLevel.MEDIUM,
                description=f"Casual language found: {', '.join(found_casual[:3])}",
                location="Throughout document",
                suggestion="Use more formal, professional language",
                principle_violated="Professional Tone"
            ))
            score -= min(1.5, len(found_casual) * 0.3)

        # Check for confident assertion vs. tentative language
        tentative_phrases = ['it seems', 'it appears', 'perhaps', 'maybe', 'might be', 'could be']
        tentative_count = sum(content.lower().count(phrase) for phrase in tentative_phrases)

        if tentative_count > 3:
            issues.append(WritingIssue(
                type=IssueType.TONE,
                severity=SeverityLevel.MEDIUM,
                description="Excessive tentative language undermines confidence",
                location="Throughout document",
                suggestion="Use more assertive language in legal arguments",
                principle_violated="Professional Tone"
            ))
            score -= min(1.0, tentative_count * 0.2)

        return {
            'score': max(0.0, min(10.0, score)),
            'issues': issues,
            'strengths': strengths
        }

    def _analyze_persuasiveness(self, content: str) -> Dict[str, Any]:
        """Analyze persuasive elements"""
        issues = []
        strengths = []
        score = 6.0  # Lower baseline for persuasiveness

        # Check for argument structure
        argument_indicators = ['because', 'since', 'therefore', 'thus', 'consequently',
                             'as a result', 'this demonstrates', 'this shows']

        indicator_count = sum(content.lower().count(indicator) for indicator in argument_indicators)
        if indicator_count < 3:
            issues.append(WritingIssue(
                type=IssueType.ANALYSIS,
                severity=SeverityLevel.MEDIUM,
                description="Limited use of logical connectors in arguments",
                location="Argument sections",
                suggestion="Use more logical connectors to strengthen argument flow",
                principle_violated="Logical Argumentation"
            ))
            score -= 1.0
        else:
            strengths.append("Good use of logical argument structure")
            score += 1.0

        return {
            'score': max(0.0, min(10.0, score)),
            'issues': issues,
            'strengths': strengths
        }

    def _analyze_authority_support(self, content: str) -> Dict[str, Any]:
        """Analyze use of legal authorities"""
        issues = []
        strengths = []
        score = 7.0

        # Check for variety of authorities
        authorities = {
            'cases': len(re.findall(r'\b\w+\s+v\.\s+\w+', content)),
            'statutes': len(re.findall(r'\b\d+\s+U\.S\.C\.\s+§\s+\d+', content)),
            'regulations': len(re.findall(r'\b\d+\s+C\.F\.R\.\s+§\s+\d+', content))
        }

        total_authorities = sum(authorities.values())
        if total_authorities == 0:
            issues.append(WritingIssue(
                type=IssueType.AUTHORITY,
                severity=SeverityLevel.HIGH,
                description="No legal authorities cited",
                location="Throughout document",
                suggestion="Include relevant case law, statutes, or regulations",
                principle_violated="Authority Integration"
            ))
            score -= 3.0
        elif total_authorities < 3:
            issues.append(WritingIssue(
                type=IssueType.AUTHORITY,
                severity=SeverityLevel.MEDIUM,
                description="Limited legal authority support",
                location="Argument sections",
                suggestion="Include additional supporting authorities",
                principle_violated="Authority Integration"
            ))
            score -= 1.0
        else:
            strengths.append(f"Good authority support with {total_authorities} citations")

        return {
            'score': max(0.0, min(10.0, score)),
            'issues': issues,
            'strengths': strengths
        }

    def _analyze_grammar_style(self, content: str) -> Dict[str, Any]:
        """Analyze grammar and style issues"""
        issues = []
        strengths = []
        score = 8.0

        # Check for common grammar issues (basic patterns)
        grammar_issues = []

        # Check for subject-verb agreement (basic)
        if re.search(r'\b(data|criteria|phenomena)\s+is\b', content):
            grammar_issues.append("Potential subject-verb disagreement with plural nouns")

        # Check for comma splices (basic detection)
        comma_splices = re.findall(r'[a-z]+,\s+[a-z]+\s+[a-z]+\s+[a-z]+', content)
        if len(comma_splices) > 3:
            grammar_issues.append("Potential comma splice errors")

        if grammar_issues:
            issues.append(WritingIssue(
                type=IssueType.GRAMMAR,
                severity=SeverityLevel.LOW,
                description=f"Grammar concerns: {'; '.join(grammar_issues)}",
                location="Various locations",
                suggestion="Review for grammar and style consistency"
            ))
            score -= len(grammar_issues) * 0.5

        return {
            'score': max(0.0, min(10.0, score)),
            'issues': issues,
            'strengths': strengths
        }

    # Helper methods for analysis

    def _split_into_sentences(self, content: str) -> List[str]:
        """Split content into sentences"""
        # Basic sentence splitting
        sentences = re.split(r'[.!?]+\s+', content)
        return [s.strip() for s in sentences if s.strip()]

    def _detect_passive_voice(self, sentences: List[str]) -> List[str]:
        """Detect passive voice in sentences"""
        passive_patterns = [
            r'\b(was|were|is|are|been|be)\s+\w+ed\b',
            r'\b(was|were|is|are|been|be)\s+\w+en\b'
        ]

        passive_sentences = []
        for sentence in sentences:
            if any(re.search(pattern, sentence, re.IGNORECASE) for pattern in passive_patterns):
                passive_sentences.append(sentence)

        return passive_sentences

    def _detect_unexplained_jargon(self, content: str) -> List[str]:
        """Detect legal jargon that may need explanation"""
        jargon_terms = [
            'res judicata', 'collateral estoppel', 'prima facie', 'de novo',
            'sua sponte', 'inter alia', 'voir dire', 'mandamus', 'certiorari'
        ]

        found_jargon = []
        content_lower = content.lower()

        for term in jargon_terms:
            if term in content_lower:
                # Check if term is explained (basic check)
                term_index = content_lower.find(term)
                surrounding_text = content_lower[max(0, term_index-50):term_index+100]
                if not any(explain_word in surrounding_text
                          for explain_word in ['means', 'is', 'refers to', 'defined as']):
                    found_jargon.append(term)

        return found_jargon

    def _detect_ambiguous_pronouns(self, content: str) -> List[str]:
        """Detect potentially ambiguous pronouns"""
        # Basic detection - look for pronouns that might be ambiguous
        ambiguous_patterns = [
            r'\bthis\s+(?!is|was|will|can|should|must)',
            r'\bthat\s+(?!is|was|will|can|should|must)',
            r'\bit\s+(?!is|was|will|can|should|must)'
        ]

        ambiguous_uses = []
        for pattern in ambiguous_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            ambiguous_uses.extend(matches)

        return ambiguous_uses

    def _extract_headings(self, content: str) -> List[str]:
        """Extract headings from content"""
        # Look for common heading patterns
        heading_patterns = [
            r'^[A-Z][A-Z\s]+$',  # ALL CAPS headings
            r'^\d+\.\s+[A-Z]',    # Numbered headings
            r'^[IVX]+\.\s+',      # Roman numeral headings
        ]

        headings = []
        for line in content.split('\n'):
            line = line.strip()
            if any(re.match(pattern, line) for pattern in heading_patterns):
                headings.append(line)

        return headings

    def _extract_citations(self, content: str) -> List[str]:
        """Extract potential citations from content"""
        citation_patterns = [
            r'\b\w+\s+v\.\s+\w+,\s+\d+\s+\w+\s+\d+',  # Case citations
            r'\b\d+\s+U\.S\.C\.\s+§\s+\d+',           # USC citations
            r'\b\d+\s+C\.F\.R\.\s+§\s+\d+',           # CFR citations
        ]

        citations = []
        for pattern in citation_patterns:
            citations.extend(re.findall(pattern, content))

        return citations

    def _validate_citation_format(self, citation: str) -> Tuple[bool, List[str]]:
        """Validate citation format"""
        # Use the citation validator from writing_principles
        if 'v.' in citation:
            return self.principles.validate_citation_format(citation, 'case_citation')
        elif 'U.S.C.' in citation:
            return self.principles.validate_citation_format(citation, 'statute_citation')
        elif 'C.F.R.' in citation:
            return self.principles.validate_citation_format(citation, 'regulation_citation')
        else:
            return True, []  # Unknown format, don't flag as error

    def _detect_document_type(self, content: str) -> Optional[LegalDocumentType]:
        """Attempt to detect document type from content"""
        content_lower = content.lower()

        if any(word in content_lower for word in ['memorandum', 'memo', 'to:', 'from:']):
            return LegalDocumentType.MEMORANDUM
        elif any(word in content_lower for word in ['brief', 'appellant', 'appellee']):
            return LegalDocumentType.BRIEF
        elif any(word in content_lower for word in ['motion', 'moves', 'respectfully requests']):
            return LegalDocumentType.MOTION

        return None

    def _detect_analysis_framework(self, content: str) -> Optional[AnalysisStructure]:
        """Attempt to detect analysis framework used"""
        content_lower = content.lower()

        # Look for IRAC indicators
        irac_score = sum(1 for word in ['issue', 'rule', 'application', 'conclusion']
                        if word in content_lower)

        # Look for CRAC indicators (conclusion first)
        has_early_conclusion = bool(re.search(r'^.{0,200}conclusion', content_lower, re.DOTALL))

        if irac_score >= 3:
            if has_early_conclusion:
                return AnalysisStructure.CRAC
            else:
                return AnalysisStructure.IRAC

        return None

    def _analyze_document_structure(self, content: str, document_type: Optional[LegalDocumentType]) -> Dict[str, Any]:
        """Analyze document structure against standards"""
        issues = []

        if document_type:
            expected_structure = self.principles.get_document_structure(document_type)
            if expected_structure:
                # Check for required sections
                missing_sections = []
                for section in expected_structure.required_sections:
                    if section.lower() not in content.lower():
                        missing_sections.append(section)

                if missing_sections:
                    issues.append(WritingIssue(
                        type=IssueType.STRUCTURE,
                        severity=SeverityLevel.HIGH,
                        description=f"Missing required sections: {', '.join(missing_sections)}",
                        location="Document structure",
                        suggestion=f"Include all required sections for {document_type.value}",
                        principle_violated="Document Structure"
                    ))

        return {'issues': issues}

    def _analyze_citations(self, content: str) -> Dict[str, Any]:
        """Analyze citation usage and format"""
        issues = []
        citations = self._extract_citations(content)

        # Additional citation analysis beyond basic format
        if citations:
            # Check for pinpoint citations
            citations_without_pinpoints = [c for c in citations if not re.search(r'\d+$', c)]
            if len(citations_without_pinpoints) > len(citations) * 0.5:
                issues.append(WritingIssue(
                    type=IssueType.CITATION,
                    severity=SeverityLevel.MEDIUM,
                    description="Many citations lack pinpoint references",
                    location="Citation references",
                    suggestion="Include specific page or section references in citations"
                ))

        return {'issues': issues}

    def _calculate_readability_metrics(self, content: str) -> Dict[str, float]:
        """Calculate basic readability metrics"""
        sentences = self._split_into_sentences(content)
        words = content.split()

        if not sentences or not words:
            return {}

        avg_sentence_length = len(words) / len(sentences)
        avg_word_length = sum(len(word) for word in words) / len(words)

        return {
            'average_sentence_length': avg_sentence_length,
            'average_word_length': avg_word_length,
            'total_sentences': len(sentences),
            'total_words': len(words)
        }

    def _calculate_overall_score(self, quality_scores: Dict[WritingQuality, QualityScore]) -> float:
        """Calculate weighted overall score"""
        total_weighted_score = 0.0
        total_weight = 0.0

        for quality_score in quality_scores.values():
            weight = quality_score.weight
            total_weighted_score += quality_score.score * weight
            total_weight += weight

        return total_weighted_score / total_weight if total_weight > 0 else 0.0

    def _generate_recommendations(self, issues: List[WritingIssue],
                                quality_scores: Dict[WritingQuality, QualityScore]) -> List[str]:
        """Generate actionable recommendations based on analysis"""
        recommendations = []

        # Group issues by severity
        critical_issues = [i for i in issues if i.severity == SeverityLevel.CRITICAL]
        high_issues = [i for i in issues if i.severity == SeverityLevel.HIGH]

        if critical_issues:
            recommendations.append(f"Address {len(critical_issues)} critical issues immediately")

        if high_issues:
            recommendations.append(f"Prioritize fixing {len(high_issues)} high-priority issues")

        # Identify lowest-scoring dimensions
        lowest_scores = sorted(quality_scores.items(), key=lambda x: x[1].score)[:3]
        for quality_dim, score in lowest_scores:
            if score.score < 6.0:
                recommendations.append(f"Focus on improving {quality_dim.value} (current score: {score.score:.1f})")

        return recommendations

    def format_analysis_report(self, analysis: DocumentAnalysis) -> str:
        """Format analysis results into a readable report"""
        report_lines = []

        # Header
        report_lines.append("LEGAL WRITING ANALYSIS REPORT")
        report_lines.append("=" * 50)
        report_lines.append(f"Document Type: {analysis.document_type.value if analysis.document_type else 'Unknown'}")
        report_lines.append(f"Analysis Framework: {analysis.analysis_framework_used.value if analysis.analysis_framework_used else 'Not detected'}")
        report_lines.append(f"Word Count: {analysis.word_count}")
        report_lines.append(f"Overall Score: {analysis.overall_score:.1f}/10.0")
        report_lines.append("")

        # Quality Scores
        report_lines.append("QUALITY DIMENSIONS")
        report_lines.append("-" * 30)
        for quality_dim, score in analysis.quality_scores.items():
            report_lines.append(f"{quality_dim.value.title():20} {score.score:4.1f}/10.0")
        report_lines.append("")

        # Issues by Severity
        if analysis.issues:
            issues_by_severity = {}
            for issue in analysis.issues:
                if issue.severity not in issues_by_severity:
                    issues_by_severity[issue.severity] = []
                issues_by_severity[issue.severity].append(issue)

            report_lines.append("ISSUES IDENTIFIED")
            report_lines.append("-" * 30)

            for severity in [SeverityLevel.CRITICAL, SeverityLevel.HIGH, SeverityLevel.MEDIUM, SeverityLevel.LOW]:
                if severity in issues_by_severity:
                    report_lines.append(f"\n{severity.value.upper()} PRIORITY:")
                    for issue in issues_by_severity[severity]:
                        report_lines.append(f"  • {issue.description}")
                        report_lines.append(f"    Suggestion: {issue.suggestion}")

        # Strengths
        if analysis.strengths:
            report_lines.append("\nSTRENGTHS")
            report_lines.append("-" * 30)
            for strength in analysis.strengths:
                report_lines.append(f"  • {strength}")

        # Recommendations
        if analysis.recommendations:
            report_lines.append("\nRECOMMENDATIONS")
            report_lines.append("-" * 30)
            for i, rec in enumerate(analysis.recommendations, 1):
                report_lines.append(f"  {i}. {rec}")

        return "\n".join(report_lines)
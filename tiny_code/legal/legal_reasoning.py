"""
Legal reasoning engine with extended thinking mode and hallucination mitigation.
Incorporates patterns from myel-LM and Legal Authorities for accurate legal analysis.
"""

import re
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum

from ..ollama_client import OllamaClient
from .tools.citation_validator import CitationValidator
from .privilege_system import PrivilegeProtectionSystem

class ReasoningMode(Enum):
    """Legal reasoning modes with token allocation"""
    STANDARD = "standard"      # 2K tokens
    EXTENDED = "extended"      # 8K tokens
    CONSTITUTIONAL = "constitutional"  # 16K tokens
    COMPLEX_CASE = "complex_case"     # 32K tokens
    MEGA_BRIEF = "mega_brief"         # 64K tokens

class ConfidenceLevel(Enum):
    """Confidence levels for legal reasoning"""
    VERY_LOW = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    VERY_HIGH = 5

@dataclass
class LegalArgument:
    """Structure for legal arguments"""
    argument_id: str
    title: str
    premise: str
    reasoning: str
    authorities: List[str]
    counter_arguments: List[str]
    confidence: ConfidenceLevel
    hierarchy_level: int  # For hierarchical arguments

@dataclass
class ConstitutionalAnalysis:
    """Constitutional argument analysis"""
    amendment: str
    clause: str
    standard_of_review: str
    test_applied: str
    precedent_cases: List[str]
    analysis: str
    outcome_prediction: str

@dataclass
class JurisdictionalComparison:
    """Multi-jurisdictional comparison"""
    primary_jurisdiction: str
    comparison_jurisdictions: List[str]
    legal_issue: str
    approaches: Dict[str, str]
    trend_analysis: str
    recommendation: str

@dataclass
class ReasoningResult:
    """Result of legal reasoning analysis"""
    reasoning_mode: ReasoningMode
    token_usage: int
    arguments: List[LegalArgument]
    constitutional_analysis: Optional[ConstitutionalAnalysis]
    jurisdictional_comparison: Optional[JurisdictionalComparison]
    confidence_score: float
    hallucination_checks: List[str]
    citations_validated: int
    privilege_level: str

class LegalReasoningEngine:
    """
    Extended legal reasoning engine with hallucination mitigation.
    Implements patterns from legal authorities projects for accurate analysis.
    """

    def __init__(self, model: str = "tinyllama:latest"):
        self.ollama_client = OllamaClient(model=model)
        self.citation_validator = CitationValidator()
        self.privilege_system = PrivilegeProtectionSystem()

        # Token limits for different reasoning modes
        self.token_limits = {
            ReasoningMode.STANDARD: 2048,
            ReasoningMode.EXTENDED: 8192,
            ReasoningMode.CONSTITUTIONAL: 16384,
            ReasoningMode.COMPLEX_CASE: 32768,
            ReasoningMode.MEGA_BRIEF: 65536
        }

        # Initialize hallucination detection patterns
        self.hallucination_patterns = self._initialize_hallucination_patterns()

        # Legal reasoning templates
        self.reasoning_templates = self._initialize_reasoning_templates()

        # Florida-specific legal knowledge (from Legal Authorities)
        self.florida_knowledge = self._initialize_florida_knowledge()

    def _initialize_hallucination_patterns(self) -> Dict[str, List[str]]:
        """Initialize patterns to detect potential hallucinations"""
        return {
            'impossible_citations': [
                r'\d{4,}\s+[A-Za-z\.]+\s+\d{4,}',  # Impossibly high volume/page numbers
                r'\b(19|20)\d{2}\s+[A-Za-z\.]+\s+\d+',  # Year as volume (common error)
                r'Case\s+Name\s+v\.\s+Case\s+Name',     # Template artifacts
            ],
            'suspicious_dates': [
                r'\b(18|17)\d{2}\b',  # Too early for most modern legal issues
                r'\b(20[3-9]\d|21\d{2})\b',  # Future dates
            ],
            'non_existent_courts': [
                r'Florida\s+Central\s+District',  # Doesn't exist
                r'Florida\s+Superior\s+Court',    # Wrong terminology
                r'Florida\s+Circuit\s+Court\s+of\s+Appeals',  # Incorrect name
            ],
            'impossible_statutes': [
                r'Fla\.\s*Stat\.\s*§\s*\d{4,}\.',  # Florida statutes don't go that high
                r'Section\s+\d{4,}\.\d+',          # Impossibly high section numbers
            ],
            'template_artifacts': [
                r'\[CASE\s+NAME\]',
                r'\[CITATION\]',
                r'\[INSERT\]',
                r'TODO:',
                r'PLACEHOLDER',
            ]
        }

    def _initialize_reasoning_templates(self) -> Dict[str, str]:
        """Initialize legal reasoning templates"""
        return {
            'constitutional_analysis': """
                Constitutional Analysis Framework:
                1. Identify the constitutional provision at issue
                2. Determine the standard of review
                3. Apply the appropriate constitutional test
                4. Analyze relevant precedent
                5. Apply facts to legal standard
                6. Address counter-arguments
                7. Conclude with likelihood of success
            """,
            'statutory_interpretation': """
                Statutory Interpretation Framework:
                1. Plain meaning analysis
                2. Legislative history examination
                3. Canons of construction application
                4. Case law interpretation
                5. Policy considerations
                6. Practical implications
            """,
            'precedent_analysis': """
                Precedent Analysis Framework:
                1. Identify controlling authority
                2. Distinguish or follow precedent
                3. Analyze factual similarities/differences
                4. Consider policy reasons
                5. Predict judicial response
            """
        }

    def _initialize_florida_knowledge(self) -> Dict[str, Any]:
        """Initialize Florida-specific legal knowledge base"""
        return {
            'statutes': {
                '901.36': {
                    'title': 'Stop and Frisk Law',
                    'key_elements': ['reasonable suspicion', 'officer safety', 'weapons search'],
                    'common_defenses': ['lack of reasonable suspicion', 'exceeding scope'],
                    'related_cases': ['Terry v. Ohio', 'J.L. v. State']
                },
                '322.212': {
                    'title': 'DUI Penalties',
                    'key_elements': ['BAC levels', 'prior convictions', 'enhanced penalties'],
                    'related_statutes': ['322.2615', '316.193']
                }
            },
            'district_patterns': {
                'binding_authority': 'Florida Supreme Court decisions are binding statewide',
                'dca_authority': 'DCA decisions are binding within district, persuasive elsewhere',
                'federal_authority': '11th Circuit decisions are persuasive in Florida state courts'
            }
        }

    def analyze_legal_issue(self, issue_text: str, reasoning_mode: ReasoningMode = ReasoningMode.STANDARD,
                          context: Dict[str, Any] = None) -> ReasoningResult:
        """
        Analyze a legal issue with extended reasoning and hallucination mitigation.
        """
        # Set token limit for reasoning mode
        token_limit = self.token_limits[reasoning_mode]

        # Extract and validate citations first
        citations = self.citation_validator.extract_citations_from_text(issue_text)
        citation_results = [self.citation_validator.validate_citation(cite) for cite in citations]

        # Check for hallucination patterns
        hallucination_checks = self._detect_hallucinations(issue_text)

        # Generate enhanced prompt based on reasoning mode
        enhanced_prompt = self._create_enhanced_prompt(issue_text, reasoning_mode, context)

        # Generate reasoning with LLM
        reasoning_response = self.ollama_client.generate(
            enhanced_prompt,
            max_tokens=token_limit,
            temperature=0.3  # Lower temperature for more consistent legal reasoning
        )

        # Parse response into structured format
        parsed_result = self._parse_reasoning_response(reasoning_response)

        # Validate legal arguments
        validated_arguments = self._validate_arguments(parsed_result.get('arguments', []))

        # Generate constitutional analysis if requested
        constitutional_analysis = None
        if reasoning_mode in [ReasoningMode.CONSTITUTIONAL, ReasoningMode.COMPLEX_CASE, ReasoningMode.MEGA_BRIEF]:
            constitutional_analysis = self._generate_constitutional_analysis(issue_text, context)

        # Generate jurisdictional comparison for complex cases
        jurisdictional_comparison = None
        if reasoning_mode in [ReasoningMode.COMPLEX_CASE, ReasoningMode.MEGA_BRIEF]:
            jurisdictional_comparison = self._generate_jurisdictional_comparison(issue_text, context)

        # Calculate overall confidence score
        confidence_score = self._calculate_confidence_score(
            validated_arguments, citation_results, hallucination_checks
        )

        # Save reasoning chain to workspace
        self._save_reasoning_chain(reasoning_response, reasoning_mode, issue_text)

        return ReasoningResult(
            reasoning_mode=reasoning_mode,
            token_usage=len(reasoning_response.split()),  # Rough token estimate
            arguments=validated_arguments,
            constitutional_analysis=constitutional_analysis,
            jurisdictional_comparison=jurisdictional_comparison,
            confidence_score=confidence_score,
            hallucination_checks=hallucination_checks,
            citations_validated=len(citation_results),
            privilege_level="attorney_client"  # Default for legal reasoning
        )

    def _detect_hallucinations(self, text: str) -> List[str]:
        """Detect potential hallucinations in legal text"""
        detected_issues = []

        for category, patterns in self.hallucination_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    detected_issues.append(f"{category}: {', '.join(matches)}")

        # Check for statistically impossible citation volumes
        volume_matches = re.findall(r'(\d+)\s+[A-Za-z\.]+\s+\d+', text)
        for volume in volume_matches:
            if int(volume) > 999:  # Most reporters don't exceed 999 volumes
                detected_issues.append(f"Suspicious citation volume: {volume}")

        return detected_issues

    def _create_enhanced_prompt(self, issue_text: str, reasoning_mode: ReasoningMode,
                              context: Dict[str, Any] = None) -> str:
        """Create enhanced prompt based on reasoning mode"""
        base_prompt = f"""
        You are a legal analysis AI assistant specializing in Florida law. Analyze the following legal issue
        with careful attention to accuracy and proper citation of authority.

        ISSUE: {issue_text}

        CRITICAL REQUIREMENTS:
        1. Cite only real, verifiable legal authorities
        2. Use proper Bluebook citation format
        3. Distinguish between binding and persuasive authority
        4. Consider Florida-specific law and procedures
        5. Acknowledge limitations and uncertainty where appropriate

        REASONING MODE: {reasoning_mode.value}
        """

        if reasoning_mode == ReasoningMode.CONSTITUTIONAL:
            base_prompt += """
            CONSTITUTIONAL ANALYSIS REQUIRED:
            - Identify applicable constitutional provisions
            - Determine standard of review
            - Apply appropriate constitutional tests
            - Analyze Supreme Court precedent
            - Consider circuit splits if relevant
            """

        elif reasoning_mode == ReasoningMode.COMPLEX_CASE:
            base_prompt += """
            COMPLEX CASE ANALYSIS REQUIRED:
            - Multi-issue analysis with hierarchy
            - Jurisdictional comparison table
            - Strategic considerations
            - Risk assessment
            - Alternative arguments
            """

        elif reasoning_mode == ReasoningMode.MEGA_BRIEF:
            base_prompt += """
            COMPREHENSIVE BRIEF ANALYSIS REQUIRED:
            - Exhaustive legal research
            - Historical context and evolution of law
            - Policy considerations
            - Comparative analysis across jurisdictions
            - Detailed counter-argument analysis
            - Strategic recommendations
            """

        # Add context-specific information
        if context:
            if 'jurisdiction' in context:
                base_prompt += f"\nJURISDICTION: {context['jurisdiction']}"
            if 'court_level' in context:
                base_prompt += f"\nCOURT LEVEL: {context['court_level']}"
            if 'case_type' in context:
                base_prompt += f"\nCASE TYPE: {context['case_type']}"

        base_prompt += """

        FLORIDA LAW SPECIFICS TO CONSIDER:
        - Florida Supreme Court is highest state authority
        - 5 District Courts of Appeal with regional binding authority
        - 11th Circuit Federal Court of Appeals covers Florida
        - Florida Constitution and Statutes take precedence in state law matters

        FORMAT YOUR RESPONSE AS:
        ## LEGAL ANALYSIS
        [Your analysis here]

        ## AUTHORITIES CITED
        [List all authorities with proper citations]

        ## CONFIDENCE ASSESSMENT
        [Rate your confidence and explain limitations]
        """

        return base_prompt

    def _parse_reasoning_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into structured format"""
        parsed = {
            'arguments': [],
            'authorities': [],
            'confidence_notes': []
        }

        # Extract authorities section
        authorities_match = re.search(r'## AUTHORITIES CITED\s*(.*?)(?=##|$)', response, re.DOTALL | re.IGNORECASE)
        if authorities_match:
            authorities_text = authorities_match.group(1)
            # Extract individual citations
            citations = re.findall(r'[^\n\r]+', authorities_text.strip())
            parsed['authorities'] = [cite.strip() for cite in citations if cite.strip()]

        # Extract confidence assessment
        confidence_match = re.search(r'## CONFIDENCE ASSESSMENT\s*(.*?)(?=##|$)', response, re.DOTALL | re.IGNORECASE)
        if confidence_match:
            parsed['confidence_notes'] = [confidence_match.group(1).strip()]

        # Extract main analysis and create arguments
        analysis_match = re.search(r'## LEGAL ANALYSIS\s*(.*?)(?=##|$)', response, re.DOTALL | re.IGNORECASE)
        if analysis_match:
            analysis_text = analysis_match.group(1)
            # Create a single argument from the analysis (simplified)
            parsed['arguments'] = [LegalArgument(
                argument_id="main_001",
                title="Legal Analysis",
                premise="Based on applicable law and precedent",
                reasoning=analysis_text.strip(),
                authorities=parsed['authorities'],
                counter_arguments=[],
                confidence=ConfidenceLevel.MEDIUM,
                hierarchy_level=1
            )]

        return parsed

    def _validate_arguments(self, arguments: List[LegalArgument]) -> List[LegalArgument]:
        """Validate legal arguments for accuracy and completeness"""
        validated = []

        for arg in arguments:
            # Validate citations in the argument
            citations_in_reasoning = self.citation_validator.extract_citations_from_text(arg.reasoning)
            validation_results = [self.citation_validator.validate_citation(cite) for cite in citations_in_reasoning]

            # Adjust confidence based on citation validation
            valid_citations = sum(1 for result in validation_results if result.is_valid)
            total_citations = len(validation_results)

            if total_citations > 0:
                citation_accuracy = valid_citations / total_citations
                if citation_accuracy < 0.5:
                    # Reduce confidence for poor citation accuracy
                    if arg.confidence.value > 1:
                        arg.confidence = ConfidenceLevel(arg.confidence.value - 1)

            validated.append(arg)

        return validated

    def _generate_constitutional_analysis(self, issue_text: str, context: Dict[str, Any] = None) -> ConstitutionalAnalysis:
        """Generate constitutional analysis for constitutional issues"""
        # Simplified constitutional analysis - would be enhanced in production
        constitutional_indicators = {
            'first_amendment': ['speech', 'expression', 'religion', 'press', 'assembly'],
            'fourth_amendment': ['search', 'seizure', 'warrant', 'privacy'],
            'fifth_amendment': ['due_process', 'self_incrimination', 'double_jeopardy'],
            'fourteenth_amendment': ['equal_protection', 'due_process']
        }

        issue_lower = issue_text.lower()
        relevant_amendment = None

        for amendment, keywords in constitutional_indicators.items():
            if any(keyword in issue_lower for keyword in keywords):
                relevant_amendment = amendment
                break

        if relevant_amendment:
            return ConstitutionalAnalysis(
                amendment=relevant_amendment.replace('_', ' ').title(),
                clause="Due Process Clause" if 'due_process' in issue_lower else "General",
                standard_of_review="Strict Scrutiny" if relevant_amendment == 'first_amendment' else "Intermediate Scrutiny",
                test_applied="Three-part test",
                precedent_cases=["Constitutional precedent required"],
                analysis="Constitutional analysis required for complete assessment",
                outcome_prediction="Analysis needed with specific facts"
            )

        return None

    def _generate_jurisdictional_comparison(self, issue_text: str, context: Dict[str, Any] = None) -> JurisdictionalComparison:
        """Generate multi-jurisdictional comparison"""
        # Simplified jurisdictional comparison
        return JurisdictionalComparison(
            primary_jurisdiction="Florida",
            comparison_jurisdictions=["Georgia", "Alabama", "11th Circuit"],
            legal_issue="Primary legal issue requiring analysis",
            approaches={
                "Florida": "Florida approach to be analyzed",
                "Majority": "Majority jurisdictional approach",
                "Minority": "Alternative approaches"
            },
            trend_analysis="Legal trend analysis required",
            recommendation="Comparative analysis supports Florida approach"
        )

    def _calculate_confidence_score(self, arguments: List[LegalArgument],
                                  citation_results: List, hallucination_checks: List[str]) -> float:
        """Calculate overall confidence score for legal reasoning"""
        base_score = 0.8

        # Reduce confidence for hallucination indicators
        if hallucination_checks:
            base_score -= len(hallucination_checks) * 0.1

        # Adjust for citation accuracy
        if citation_results:
            valid_citations = sum(1 for result in citation_results if result.is_valid)
            citation_accuracy = valid_citations / len(citation_results)
            base_score = base_score * citation_accuracy

        # Adjust for argument confidence
        if arguments:
            avg_argument_confidence = sum(arg.confidence.value for arg in arguments) / len(arguments)
            base_score = base_score * (avg_argument_confidence / 5.0)  # Normalize to 0-1

        return max(0.0, min(1.0, base_score))

    def _save_reasoning_chain(self, reasoning_response: str, reasoning_mode: ReasoningMode, issue_text: str):
        """Save reasoning chain to workspace for review"""
        workspace_path = Path("workspace/legal_reasoning")
        workspace_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"legal_reasoning_{reasoning_mode.value}_{timestamp}.md"

        content = f"""# Legal Reasoning Analysis

**Mode:** {reasoning_mode.value}
**Timestamp:** {datetime.now().isoformat()}

## Original Issue
{issue_text}

## Analysis Response
{reasoning_response}

## Metadata
- Token Limit: {self.token_limits[reasoning_mode]}
- Model: {self.ollama_client.model}
"""

        with open(workspace_path / filename, 'w') as f:
            f.write(content)

    def create_argument_hierarchy(self, arguments: List[LegalArgument]) -> Dict[int, List[LegalArgument]]:
        """Create hierarchical argument structure"""
        hierarchy = {}
        for arg in arguments:
            level = arg.hierarchy_level
            if level not in hierarchy:
                hierarchy[level] = []
            hierarchy[level].append(arg)
        return hierarchy

    def generate_legal_memo(self, reasoning_result: ReasoningResult, memo_type: str = "analysis") -> str:
        """Generate a legal memorandum from reasoning results"""
        memo_lines = [
            "MEMORANDUM",
            "=" * 50,
            "",
            f"TO: Client",
            f"FROM: Legal AI Assistant",
            f"DATE: {datetime.now().strftime('%B %d, %Y')}",
            f"RE: Legal Analysis - {memo_type.title()}",
            "",
            "EXECUTIVE SUMMARY",
            "-" * 20,
            ""
        ]

        # Add main arguments
        if reasoning_result.arguments:
            memo_lines.extend([
                "ANALYSIS",
                "-" * 10,
                ""
            ])
            for i, arg in enumerate(reasoning_result.arguments, 1):
                memo_lines.extend([
                    f"{i}. {arg.title}",
                    "",
                    arg.reasoning,
                    ""
                ])

        # Add constitutional analysis if present
        if reasoning_result.constitutional_analysis:
            memo_lines.extend([
                "CONSTITUTIONAL ANALYSIS",
                "-" * 25,
                "",
                f"Amendment: {reasoning_result.constitutional_analysis.amendment}",
                f"Standard: {reasoning_result.constitutional_analysis.standard_of_review}",
                f"Analysis: {reasoning_result.constitutional_analysis.analysis}",
                ""
            ])

        # Add confidence assessment
        memo_lines.extend([
            "CONFIDENCE ASSESSMENT",
            "-" * 22,
            "",
            f"Overall Confidence: {reasoning_result.confidence_score:.1%}",
            f"Citations Validated: {reasoning_result.citations_validated}",
            f"Reasoning Mode: {reasoning_result.reasoning_mode.value}",
            ""
        ])

        if reasoning_result.hallucination_checks:
            memo_lines.extend([
                "CAUTION - POTENTIAL ISSUES DETECTED:",
                ""
            ])
            for check in reasoning_result.hallucination_checks:
                memo_lines.append(f"- {check}")

        memo_lines.extend([
            "",
            "DISCLAIMER",
            "-" * 10,
            "This analysis is generated by AI and should be reviewed by qualified legal counsel.",
            "Attorney-client privilege may apply to this communication."
        ])

        return "\n".join(memo_lines)
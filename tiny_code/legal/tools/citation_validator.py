"""
Citation validator for legal documents with Florida law specifics and authority hierarchy.
Incorporates lessons from myel-LM and Legal Authorities projects for accurate citation validation.
"""

import re
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path

class CitationFormat(Enum):
    """Supported citation formats"""
    BLUEBOOK = "bluebook"
    ALWD = "alwd"
    FLORIDA_RULES = "florida_rules"

class AuthorityLevel(Enum):
    """Authority levels for legal precedent"""
    BINDING = "binding"
    BINDING_DISTRICT = "binding_district"
    PERSUASIVE_HIGH = "persuasive_high"
    PERSUASIVE = "persuasive"
    SECONDARY = "secondary"

class JurisdictionType(Enum):
    """Types of jurisdictions"""
    FLORIDA_SUPREME = "florida_supreme"
    FLORIDA_DCA = "florida_dca"
    FEDERAL_CIRCUIT = "federal_circuit"
    US_SUPREME = "us_supreme"
    OTHER_STATE = "other_state"
    FEDERAL_DISTRICT = "federal_district"

@dataclass
class CitationValidationResult:
    """Result of citation validation"""
    is_valid: bool
    format_issues: List[str]
    authority_level: AuthorityLevel
    jurisdiction: JurisdictionType
    confidence_score: float
    standardized_citation: str
    bluebook_citation: str
    authority_weight: float
    shepard_status: Optional[str] = None
    related_authorities: List[str] = None

@dataclass
class FloridaDistrictInfo:
    """Information about Florida District Courts of Appeal"""
    district_num: int
    name: str
    counties: List[str]
    binding_authority: bool

class CitationValidator:
    """
    Comprehensive citation validator with Florida law specifics.
    Based on patterns and authority hierarchy from legal authorities projects.
    """

    def __init__(self):
        self.citation_patterns = self._initialize_citation_patterns()
        self.florida_districts = self._initialize_florida_districts()
        self.authority_weights = self._initialize_authority_weights()
        self.shepard_indicators = self._initialize_shepard_indicators()

        # Florida-specific patterns from Legal Authorities project
        self.florida_patterns = {
            'statutes': [
                r'(?:Fla\.\s*Stat\.\s*(?:§\s*)?|Florida\s+Statute\s*)\s*(\d+\.\d+)',
                r'(?:Section\s*|§\s*)(\d+\.\d+)',
                r'\b(\d{1,3}\.\d{2,4})\b',  # Common statute format
            ],
            'rules': [
                r'Fla\.\s*R\.\s*(?:Civ\.\s*P\.|Crim\.\s*P\.|App\.\s*P\.|Evid\.)\s*(\d+(?:\.\d+)?)',
                r'Florida\s+Rule\s+of\s+(?:Civil|Criminal|Appellate)\s+Procedure\s+(\d+(?:\.\d+)?)',
            ],
            'constitutional': [
                r'Fla\.\s*Const\.\s*[Aa]rt\.\s*([IVX]+),?\s*§\s*(\d+)',
                r'Florida\s+Constitution\s+Article\s+([IVX]+),?\s+Section\s+(\d+)',
            ]
        }

    def _initialize_citation_patterns(self) -> Dict[str, List[str]]:
        """Initialize citation regex patterns based on legal authorities analysis"""
        return {
            # Florida case citations
            'florida_cases': [
                r'\b\d+\s+So\.\s?(?:2d|3d)\s+\d+\b',  # Southern Reporter
                r'\b\d{4}\s+WL\s+\d+\b',              # Westlaw citations
                r'\b\d+\s+Fla\.\s+\d+\b',            # Florida Reports
                r'\b\d+\s+Fla\.\s+Supp\.\s+(?:2d\s+)?\d+\b',  # Florida Supplement
            ],

            # Federal citations
            'federal_cases': [
                r'\b\d+\s+U\.S\.\s+\d+\b',           # U.S. Reports
                r'\b\d+\s+S\.\s?Ct\.\s+\d+\b',      # Supreme Court Reporter
                r'\b\d+\s+F\.\s?(?:2d|3d)\s+\d+\b', # Federal Reporter
                r'\b\d+\s+F\.\s?Supp\.\s?(?:2d|3d)?\s+\d+\b', # Federal Supplement
            ],

            # Other state citations (from myel-LM authority patterns)
            'other_state': [
                r'\b\d+\s+[A-Z][a-z]+\.?\s+(?:2d|3d)?\s+\d+\b',  # Generic state reporters
                r'\b\d+\s+[A-Z]{2,4}\.?\s+(?:2d|3d)?\s+\d+\b',   # State abbreviation reporters
            ],

            # Parallel citations
            'parallel': [
                r'\b\d+\s+So\.\s?(?:2d|3d)\s+\d+,\s+\d+\s+Fla\.\s+\d+\b',
            ]
        }

    def _initialize_florida_districts(self) -> Dict[str, FloridaDistrictInfo]:
        """Initialize Florida District Court information from myel-LM patterns"""
        return {
            'fladca1': FloridaDistrictInfo(
                district_num=1,
                name='First District Court of Appeal',
                counties=['Escambia', 'Okaloosa', 'Santa Rosa', 'Walton', 'Holmes', 'Washington',
                         'Jackson', 'Calhoun', 'Gulf', 'Liberty', 'Franklin', 'Gadsden', 'Leon',
                         'Wakulla', 'Jefferson', 'Madison', 'Taylor', 'Hamilton', 'Suwannee',
                         'Lafayette', 'Dixie', 'Columbia', 'Baker', 'Union', 'Bradford', 'Gilchrist',
                         'Levy', 'Alachua', 'Nassau', 'Duval', 'Clay'],
                binding_authority=True
            ),
            'fladca2': FloridaDistrictInfo(
                district_num=2,
                name='Second District Court of Appeal',
                counties=['Hillsborough', 'Manatee', 'Sarasota', 'DeSoto',
                         'Hardee', 'Highlands', 'Polk', 'Charlotte', 'Glades', 'Hendry', 'Lee', 'Collier'],
                binding_authority=True
            ),
            'fladca3': FloridaDistrictInfo(
                district_num=3,
                name='Third District Court of Appeal',
                counties=['Miami-Dade', 'Monroe'],
                binding_authority=True
            ),
            'fladca4': FloridaDistrictInfo(
                district_num=4,
                name='Fourth District Court of Appeal',
                counties=['Palm Beach', 'Broward', 'St. Lucie', 'Martin', 'Indian River', 'Okeechobee'],
                binding_authority=True
            ),
            'fladca5': FloridaDistrictInfo(
                district_num=5,
                name='Fifth District Court of Appeal',
                counties=['St. Johns', 'Flagler', 'Putnam', 'Marion', 'Citrus', 'Hernando', 'Sumter',
                         'Lake', 'Volusia', 'Seminole', 'Orange', 'Osceola', 'Brevard'],
                binding_authority=True
            ),
            'fladca6': FloridaDistrictInfo(
                district_num=6,
                name='Sixth District Court of Appeal',
                counties=['Pinellas', 'Pasco'],
                binding_authority=True
            )
        }

    def _initialize_authority_weights(self) -> Dict[AuthorityLevel, float]:
        """Initialize authority weight values from legal rules engine"""
        return {
            AuthorityLevel.BINDING: 1.0,
            AuthorityLevel.BINDING_DISTRICT: 0.9,
            AuthorityLevel.PERSUASIVE_HIGH: 0.7,
            AuthorityLevel.PERSUASIVE: 0.5,
            AuthorityLevel.SECONDARY: 0.3
        }

    def _initialize_shepard_indicators(self) -> Dict[str, float]:
        """Initialize Shepard's treatment indicators and their impact on authority"""
        return {
            'overruled': -1.0,
            'reversed': -0.9,
            'superseded': -0.8,
            'questioned': -0.4,
            'criticized': -0.3,
            'limited': -0.2,
            'distinguished': -0.1,
            'neutral': 0.0,
            'followed': 0.3,
            'cited': 0.2,
            'affirmed': 0.5,
            'explained': 0.1
        }

    def validate_citation(self, citation: str, context: Dict[str, str] = None) -> CitationValidationResult:
        """
        Validate a legal citation and determine its authority level.
        Incorporates Florida hierarchy and hallucination mitigation.
        """
        citation = citation.strip()

        # Basic format validation
        format_issues = self._check_citation_format(citation)

        # Determine jurisdiction and authority level
        jurisdiction = self._determine_jurisdiction(citation)
        authority_level = self._determine_authority_level(citation, jurisdiction, context)

        # Calculate confidence and authority weight
        confidence_score = self._calculate_confidence_score(citation, format_issues)
        authority_weight = self.authority_weights[authority_level]

        # Standardize citation format
        standardized_citation = self._standardize_citation(citation)
        bluebook_citation = self._convert_to_bluebook(citation)

        # Check for hallucination patterns (from Legal Authorities anti-hallucination)
        confidence_score = self._apply_hallucination_mitigation(citation, confidence_score)

        return CitationValidationResult(
            is_valid=len(format_issues) == 0,
            format_issues=format_issues,
            authority_level=authority_level,
            jurisdiction=jurisdiction,
            confidence_score=confidence_score,
            standardized_citation=standardized_citation,
            bluebook_citation=bluebook_citation,
            authority_weight=authority_weight,
            related_authorities=self._find_related_authorities(citation)
        )

    def validate_multiple_citations(self, text: str) -> List[CitationValidationResult]:
        """Extract and validate all citations in a text"""
        citations = self.extract_citations_from_text(text)
        return [self.validate_citation(cite) for cite in citations]

    def extract_citations_from_text(self, text: str) -> List[str]:
        """Extract all citations from text using Florida-aware patterns"""
        citations = []

        # Use all citation patterns
        for category, patterns in self.citation_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                citations.extend(matches)

        # Also extract Florida statute citations
        for pattern in self.florida_patterns['statutes']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            citations.extend([f"Fla. Stat. § {match}" for match in matches])

        # Remove duplicates while preserving order
        seen = set()
        unique_citations = []
        for cite in citations:
            if cite not in seen:
                seen.add(cite)
                unique_citations.append(cite)

        return unique_citations

    def _check_citation_format(self, citation: str) -> List[str]:
        """Check citation format against Bluebook rules"""
        issues = []

        # Check for common format issues
        if not re.search(r'\d', citation):
            issues.append("Citation missing volume or page numbers")

        # Check spacing in Florida citations
        if 'So.' in citation and not re.search(r'\d+\s+So\.\s?(?:2d|3d)\s+\d+', citation):
            issues.append("Incorrect spacing in Southern Reporter citation")

        # Check for missing jurisdictional information
        if re.search(r'\d+\s+So\.\s?(?:2d|3d)\s+\d+', citation):
            if not re.search(r'\(Fla\.|\(Fla\.\s+(?:1st|2nd|3rd|4th|5th)\s+DCA', citation):
                issues.append("Missing court information for Florida case")

        # Check year format
        year_match = re.search(r'\((\d{4})\)', citation)
        if year_match:
            year = int(year_match.group(1))
            if year < 1800 or year > datetime.now().year:
                issues.append(f"Suspicious year: {year}")

        return issues

    def _determine_jurisdiction(self, citation: str) -> JurisdictionType:
        """Determine jurisdiction from citation format"""
        citation_lower = citation.lower()

        # Florida Supreme Court
        if re.search(r'\(fla\.\s+\d{4}\)', citation_lower) and 'dca' not in citation_lower:
            return JurisdictionType.FLORIDA_SUPREME

        # Florida DCA
        if re.search(r'\(fla\.\s+(?:1st|2nd|3rd|4th|5th)\s+dca', citation_lower):
            return JurisdictionType.FLORIDA_DCA

        # U.S. Supreme Court
        if re.search(r'\d+\s+u\.s\.\s+\d+', citation_lower):
            return JurisdictionType.US_SUPREME

        # Federal Circuit (including 11th Circuit covering Florida)
        if re.search(r'\d+\s+f\.\s?(?:2d|3d)\s+\d+', citation_lower):
            return JurisdictionType.FEDERAL_CIRCUIT

        # Federal District
        if re.search(r'\d+\s+f\.\s?supp', citation_lower):
            return JurisdictionType.FEDERAL_DISTRICT

        # Other state
        return JurisdictionType.OTHER_STATE

    def _determine_authority_level(self, citation: str, jurisdiction: JurisdictionType,
                                 context: Dict[str, str] = None) -> AuthorityLevel:
        """
        Determine authority level based on jurisdiction and context.
        Implements Florida legal hierarchy from myel-LM legal rules engine.
        """
        # Florida Supreme Court is binding statewide
        if jurisdiction == JurisdictionType.FLORIDA_SUPREME:
            return AuthorityLevel.BINDING

        # U.S. Supreme Court is binding on federal issues
        if jurisdiction == JurisdictionType.US_SUPREME:
            return AuthorityLevel.BINDING

        # Florida DCA - binding within district, persuasive outside
        if jurisdiction == JurisdictionType.FLORIDA_DCA:
            if context and 'county' in context:
                county = context['county']
                # Check if county is within the DCA's jurisdiction
                for district_info in self.florida_districts.values():
                    if county in district_info.counties:
                        return AuthorityLevel.BINDING_DISTRICT
            return AuthorityLevel.PERSUASIVE_HIGH

        # Federal Circuit (11th Circuit covers Florida)
        if jurisdiction == JurisdictionType.FEDERAL_CIRCUIT:
            return AuthorityLevel.PERSUASIVE_HIGH

        # Federal District
        if jurisdiction == JurisdictionType.FEDERAL_DISTRICT:
            return AuthorityLevel.PERSUASIVE

        # Other state courts
        return AuthorityLevel.PERSUASIVE

    def _calculate_confidence_score(self, citation: str, format_issues: List[str]) -> float:
        """Calculate confidence score for citation validity"""
        base_score = 1.0

        # Reduce confidence for format issues
        base_score -= len(format_issues) * 0.2

        # Increase confidence for recognized patterns
        if any(re.search(pattern, citation) for patterns in self.citation_patterns.values()
               for pattern in patterns):
            base_score += 0.1

        # Increase confidence for proper court identification
        if re.search(r'\([^)]+\s+\d{4}\)', citation):
            base_score += 0.1

        return max(0.0, min(1.0, base_score))

    def _apply_hallucination_mitigation(self, citation: str, confidence_score: float) -> float:
        """
        Apply hallucination mitigation techniques based on Legal Authorities patterns.
        Reduces confidence for suspicious patterns.
        """
        # Check for suspicious volume numbers (too high)
        volume_match = re.search(r'^(\d+)\s+', citation)
        if volume_match:
            volume = int(volume_match.group(1))
            if volume > 1000:  # Suspicious for most reporters
                confidence_score *= 0.7

        # Check for impossible date ranges
        year_match = re.search(r'\((\d{4})\)', citation)
        if year_match:
            year = int(year_match.group(1))
            current_year = datetime.now().year
            if year > current_year or year < 1776:  # Outside reasonable legal range
                confidence_score *= 0.3

        # Check for non-existent reporters
        suspicious_reporters = ['Fake Rep.', 'Invalid.', 'Test Rep.']
        if any(reporter in citation for reporter in suspicious_reporters):
            confidence_score *= 0.1

        return confidence_score

    def _standardize_citation(self, citation: str) -> str:
        """Standardize citation format"""
        # Basic standardization - can be enhanced
        standardized = citation

        # Standardize spacing
        standardized = re.sub(r'\s+', ' ', standardized)

        # Standardize punctuation
        standardized = re.sub(r'So\.2d', 'So. 2d', standardized)
        standardized = re.sub(r'So\.3d', 'So. 3d', standardized)

        return standardized.strip()

    def _convert_to_bluebook(self, citation: str) -> str:
        """Convert citation to Bluebook format"""
        # Simplified Bluebook conversion
        bluebook = self._standardize_citation(citation)

        # Add proper spacing and formatting
        bluebook = re.sub(r'(\d+)\s+So\.\s?(2d|3d)\s+(\d+)', r'\1 So. \2 \3', bluebook)

        return bluebook

    def _find_related_authorities(self, citation: str) -> List[str]:
        """Find related authorities (simplified implementation)"""
        related = []

        # For Florida cases, suggest checking related DCA decisions
        if 'So.' in citation and 'Fla.' in citation:
            related.append("Check related Florida DCA decisions")
            related.append("Verify current status with Shepard's")

        return related

    def get_florida_district_for_county(self, county: str) -> Optional[FloridaDistrictInfo]:
        """Get the Florida DCA district for a given county"""
        for district_info in self.florida_districts.values():
            if county in district_info.counties:
                return district_info
        return None

    def generate_citation_report(self, citations: List[str]) -> Dict[str, any]:
        """Generate comprehensive citation validation report"""
        results = [self.validate_citation(cite) for cite in citations]

        # Aggregate statistics
        total_citations = len(results)
        valid_citations = sum(1 for r in results if r.is_valid)

        authority_distribution = {}
        jurisdiction_distribution = {}

        for result in results:
            auth_level = result.authority_level.value
            jurisdiction = result.jurisdiction.value

            authority_distribution[auth_level] = authority_distribution.get(auth_level, 0) + 1
            jurisdiction_distribution[jurisdiction] = jurisdiction_distribution.get(jurisdiction, 0) + 1

        return {
            "summary": {
                "total_citations": total_citations,
                "valid_citations": valid_citations,
                "validation_rate": valid_citations / total_citations if total_citations > 0 else 0,
                "average_confidence": sum(r.confidence_score for r in results) / total_citations if total_citations > 0 else 0
            },
            "authority_distribution": authority_distribution,
            "jurisdiction_distribution": jurisdiction_distribution,
            "detailed_results": [asdict(result) for result in results],
            "recommendations": self._generate_recommendations(results)
        }

    def _generate_recommendations(self, results: List[CitationValidationResult]) -> List[str]:
        """Generate recommendations for citation improvement"""
        recommendations = []

        invalid_count = sum(1 for r in results if not r.is_valid)
        if invalid_count > 0:
            recommendations.append(f"Fix {invalid_count} invalid citations")

        low_confidence = sum(1 for r in results if r.confidence_score < 0.7)
        if low_confidence > 0:
            recommendations.append(f"Review {low_confidence} citations with low confidence scores")

        binding_count = sum(1 for r in results if r.authority_level == AuthorityLevel.BINDING)
        if binding_count == 0:
            recommendations.append("Consider adding binding authority to strengthen arguments")

        return recommendations
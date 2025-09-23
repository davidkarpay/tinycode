"""
Legal authority hierarchy system for TinyCode legal automation.
Based on patterns from myel-LM legal rules engine for Florida law hierarchy.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path

class AuthorityType(Enum):
    """Types of legal authorities"""
    BINDING = "binding"
    PERSUASIVE = "persuasive"
    SECONDARY = "secondary"

class CourtLevel(Enum):
    """Court hierarchy levels"""
    US_SUPREME = "us_supreme"
    FEDERAL_CIRCUIT = "federal_circuit"
    FEDERAL_DISTRICT = "federal_district"
    STATE_SUPREME = "state_supreme"
    STATE_APPELLATE = "state_appellate"
    STATE_TRIAL = "state_trial"

class RelationshipType(Enum):
    """Types of case relationships (from myel-LM patterns)"""
    OVERRULES = "overrules"
    REVERSES = "reverses"
    DISTINGUISHES = "distinguishes"
    MODIFIES = "modifies"
    QUESTIONS = "questions"
    FOLLOWS = "follows"
    AFFIRMS = "affirms"
    APPLIES = "applies"
    CITES = "cites"

@dataclass
class FloridaDistrict:
    """Florida District Court of Appeal information"""
    district_num: int
    name: str
    counties: List[str]
    geographic_region: str

@dataclass
class LegalAuthority:
    """Legal authority with hierarchy information"""
    citation: str
    court: str
    jurisdiction: str
    court_level: CourtLevel
    year: int
    authority_type: AuthorityType
    authority_weight: float
    case_name: Optional[str] = None
    holding: Optional[str] = None
    key_facts: List[str] = None
    legal_issues: List[str] = None

@dataclass
class AuthorityRelationship:
    """Relationship between legal authorities"""
    source_citation: str
    target_citation: str
    relationship_type: RelationshipType
    impact_score: float
    description: str
    date_established: datetime

class LegalAuthorityHierarchy:
    """
    Legal authority hierarchy system implementing Florida law precedence rules.
    Based on myel-LM legal rules engine patterns.
    """

    def __init__(self):
        # Initialize Florida district information (from myel-LM)
        self.florida_districts = self._initialize_florida_districts()

        # Authority weight system (from myel-LM authority weights)
        self.authority_weights = {
            AuthorityType.BINDING: 1.0,
            'binding_district': 0.9,
            'persuasive_high': 0.7,
            AuthorityType.PERSUASIVE: 0.5,
            AuthorityType.SECONDARY: 0.3
        }

        # Relationship impact scores (from myel-LM relationship impacts)
        self.relationship_impacts = {
            RelationshipType.OVERRULES: -1.0,
            RelationshipType.REVERSES: -0.9,
            RelationshipType.DISTINGUISHES: -0.5,
            RelationshipType.MODIFIES: -0.3,
            RelationshipType.QUESTIONS: -0.2,
            RelationshipType.FOLLOWS: 0.5,
            RelationshipType.AFFIRMS: 0.7,
            RelationshipType.APPLIES: 0.6,
            RelationshipType.CITES: 0.3
        }

        # Authority database
        self.authorities: Dict[str, LegalAuthority] = {}
        self.relationships: List[AuthorityRelationship] = []

        # Court hierarchy mapping
        self.court_hierarchy = self._initialize_court_hierarchy()

    def _initialize_florida_districts(self) -> Dict[str, FloridaDistrict]:
        """Initialize Florida District Court information from myel-LM patterns"""
        return {
            'fladca1': FloridaDistrict(
                district_num=1,
                name='First District Court of Appeal',
                counties=['Escambia', 'Okaloosa', 'Santa Rosa', 'Walton', 'Holmes', 'Washington',
                         'Jackson', 'Calhoun', 'Gulf', 'Liberty', 'Franklin', 'Gadsden', 'Leon',
                         'Wakulla', 'Jefferson', 'Madison', 'Taylor', 'Hamilton', 'Suwannee',
                         'Lafayette', 'Dixie', 'Columbia', 'Baker', 'Union', 'Bradford', 'Gilchrist',
                         'Levy', 'Alachua', 'Nassau', 'Duval', 'Clay'],
                geographic_region='North Florida'
            ),
            'fladca2': FloridaDistrict(
                district_num=2,
                name='Second District Court of Appeal',
                counties=['Hillsborough', 'Manatee', 'Sarasota', 'DeSoto',
                         'Hardee', 'Highlands', 'Polk', 'Charlotte', 'Glades', 'Hendry', 'Lee', 'Collier'],
                geographic_region='West Central Florida'
            ),
            'fladca3': FloridaDistrict(
                district_num=3,
                name='Third District Court of Appeal',
                counties=['Miami-Dade', 'Monroe'],
                geographic_region='South Florida'
            ),
            'fladca4': FloridaDistrict(
                district_num=4,
                name='Fourth District Court of Appeal',
                counties=['Palm Beach', 'Broward', 'St. Lucie', 'Martin', 'Indian River', 'Okeechobee'],
                geographic_region='Southeast Florida'
            ),
            'fladca5': FloridaDistrict(
                district_num=5,
                name='Fifth District Court of Appeal',
                counties=['St. Johns', 'Flagler', 'Putnam', 'Marion', 'Citrus', 'Hernando', 'Sumter',
                         'Lake', 'Volusia', 'Seminole', 'Orange', 'Osceola', 'Brevard'],
                geographic_region='Central Florida'
            ),
            'fladca6': FloridaDistrict(
                district_num=6,
                name='Sixth District Court of Appeal',
                counties=['Pinellas', 'Pasco'],
                geographic_region='West Central Florida'
            )
        }

    def _initialize_court_hierarchy(self) -> Dict[str, Dict[str, any]]:
        """Initialize court hierarchy with precedence rules"""
        return {
            'us_supreme': {
                'level': CourtLevel.US_SUPREME,
                'binding_scope': 'nationwide',
                'authority_weight': 1.0,
                'precedence_rank': 1
            },
            'ca11': {  # 11th Circuit (covers Florida)
                'level': CourtLevel.FEDERAL_CIRCUIT,
                'binding_scope': 'circuit',
                'authority_weight': 0.8,
                'precedence_rank': 2
            },
            'flsc': {  # Florida Supreme Court
                'level': CourtLevel.STATE_SUPREME,
                'binding_scope': 'statewide',
                'authority_weight': 1.0,
                'precedence_rank': 1  # For state law issues
            },
            'fladca': {  # Florida DCAs
                'level': CourtLevel.STATE_APPELLATE,
                'binding_scope': 'district',
                'authority_weight': 0.9,
                'precedence_rank': 3
            },
            'federal_district': {
                'level': CourtLevel.FEDERAL_DISTRICT,
                'binding_scope': 'district',
                'authority_weight': 0.6,
                'precedence_rank': 4
            }
        }

    def determine_authority_level(self, authority: LegalAuthority, query_context: Dict[str, str] = None) -> Tuple[AuthorityType, float, List[str]]:
        """
        Determine authority level for a given authority in context.
        Implements myel-LM legal rules engine logic.
        """
        reasoning = []

        # Check if this is a Florida authority
        if authority.jurisdiction != 'florida':
            # Federal courts in 11th Circuit
            if authority.court in ['ca11', '11th_circuit'] or 'fl' in authority.court.lower():
                authority_type = AuthorityType.PERSUASIVE
                weight = 0.7
                reasoning.append('Federal court with Florida jurisdiction - persuasive authority')

            # U.S. Supreme Court
            elif authority.court == 'scotus' or 'supreme' in authority.court.lower():
                authority_type = AuthorityType.BINDING
                weight = 1.0
                reasoning.append('U.S. Supreme Court is binding on federal issues')

            # Other state supreme courts
            elif 'supreme' in authority.court.lower():
                authority_type = AuthorityType.PERSUASIVE
                weight = 0.6
                reasoning.append('Out-of-state supreme court - persuasive authority')

            else:
                authority_type = AuthorityType.PERSUASIVE
                weight = 0.4
                reasoning.append('Out-of-state authority - limited persuasive value')

        else:
            # Florida authorities
            if authority.court == 'flsc' or 'florida supreme' in authority.court.lower():
                authority_type = AuthorityType.BINDING
                weight = 1.0
                reasoning.append('Florida Supreme Court - binding statewide')

            elif 'dca' in authority.court.lower() or 'district court of appeal' in authority.court.lower():
                # Check if we're in the same district
                if query_context and 'county' in query_context:
                    county = query_context['county']
                    district_info = self._get_district_for_county(county)

                    if district_info and self._is_same_district(authority.court, district_info):
                        authority_type = AuthorityType.BINDING
                        weight = 0.9
                        reasoning.append(f'Florida DCA decision - binding within {district_info.name}')
                    else:
                        authority_type = AuthorityType.PERSUASIVE
                        weight = 0.7
                        reasoning.append('Florida DCA decision - persuasive outside district')
                else:
                    authority_type = AuthorityType.PERSUASIVE
                    weight = 0.7
                    reasoning.append('Florida DCA decision - persuasive authority')

            else:
                authority_type = AuthorityType.PERSUASIVE
                weight = 0.5
                reasoning.append('Florida trial court - persuasive authority')

        return authority_type, weight, reasoning

    def _get_district_for_county(self, county: str) -> Optional[FloridaDistrict]:
        """Get the Florida DCA district for a given county"""
        for district_info in self.florida_districts.values():
            if county in district_info.counties:
                return district_info
        return None

    def _is_same_district(self, court_name: str, district_info: FloridaDistrict) -> bool:
        """Check if court name matches the district"""
        court_lower = court_name.lower()
        district_indicators = [
            f'{district_info.district_num}',
            f'{district_info.district_num}st' if district_info.district_num == 1 else f'{district_info.district_num}th',
            f'fladca{district_info.district_num}',
            district_info.name.lower()
        ]

        return any(indicator in court_lower for indicator in district_indicators)

    def add_authority(self, authority: LegalAuthority) -> None:
        """Add a legal authority to the hierarchy system"""
        # Determine authority level
        authority_type, weight, reasoning = self.determine_authority_level(authority)

        # Update authority with calculated values
        authority.authority_type = authority_type
        authority.authority_weight = weight

        # Store in database
        self.authorities[authority.citation] = authority

    def add_relationship(self, source_citation: str, target_citation: str,
                        relationship_type: RelationshipType, description: str = "") -> None:
        """Add a relationship between authorities"""
        impact_score = self.relationship_impacts.get(relationship_type, 0.0)

        relationship = AuthorityRelationship(
            source_citation=source_citation,
            target_citation=target_citation,
            relationship_type=relationship_type,
            impact_score=impact_score,
            description=description,
            date_established=datetime.now()
        )

        self.relationships.append(relationship)

    def calculate_effective_authority_weight(self, citation: str) -> float:
        """
        Calculate effective authority weight considering relationships.
        Implements myel-LM relationship impact calculations.
        """
        if citation not in self.authorities:
            return 0.0

        base_weight = self.authorities[citation].authority_weight

        # Find relationships affecting this authority
        affecting_relationships = [
            rel for rel in self.relationships
            if rel.target_citation == citation
        ]

        # Apply relationship impacts
        total_impact = 0.0
        for rel in affecting_relationships:
            total_impact += rel.impact_score

        # Calculate effective weight (cannot go below 0)
        effective_weight = max(0.0, base_weight + (total_impact * 0.1))  # Scale impact

        return min(1.0, effective_weight)  # Cap at 1.0

    def rank_authorities(self, citations: List[str], query_context: Dict[str, str] = None) -> List[Tuple[str, float]]:
        """Rank authorities by their effective weight and relevance"""
        ranked = []

        for citation in citations:
            if citation in self.authorities:
                effective_weight = self.calculate_effective_authority_weight(citation)

                # Apply recency bonus for more recent cases
                authority = self.authorities[citation]
                current_year = datetime.now().year
                years_old = current_year - authority.year
                recency_factor = max(0.8, 1.0 - (years_old * 0.01))  # Small penalty for older cases

                final_score = effective_weight * recency_factor
                ranked.append((citation, final_score))

        # Sort by score (highest first)
        ranked.sort(key=lambda x: x[1], reverse=True)
        return ranked

    def generate_authority_analysis(self, citations: List[str], query_context: Dict[str, str] = None) -> Dict[str, any]:
        """Generate comprehensive authority analysis"""
        analysis = {
            'total_authorities': len(citations),
            'binding_authorities': [],
            'persuasive_authorities': [],
            'authority_distribution': {},
            'jurisdiction_analysis': {},
            'relationship_impacts': [],
            'recommendations': []
        }

        for citation in citations:
            if citation not in self.authorities:
                continue

            authority = self.authorities[citation]
            effective_weight = self.calculate_effective_authority_weight(citation)

            # Categorize by authority type
            if authority.authority_type == AuthorityType.BINDING:
                analysis['binding_authorities'].append({
                    'citation': citation,
                    'weight': effective_weight,
                    'court': authority.court
                })
            else:
                analysis['persuasive_authorities'].append({
                    'citation': citation,
                    'weight': effective_weight,
                    'court': authority.court
                })

            # Track jurisdiction distribution
            jurisdiction = authority.jurisdiction
            if jurisdiction not in analysis['jurisdiction_analysis']:
                analysis['jurisdiction_analysis'][jurisdiction] = {
                    'count': 0,
                    'total_weight': 0.0,
                    'authorities': []
                }
            analysis['jurisdiction_analysis'][jurisdiction]['count'] += 1
            analysis['jurisdiction_analysis'][jurisdiction]['total_weight'] += effective_weight
            analysis['jurisdiction_analysis'][jurisdiction]['authorities'].append(citation)

        # Generate recommendations
        if not analysis['binding_authorities']:
            analysis['recommendations'].append("Consider adding binding authority to strengthen arguments")

        if len(analysis['persuasive_authorities']) > len(analysis['binding_authorities']) * 3:
            analysis['recommendations'].append("High ratio of persuasive to binding authority - focus on strongest precedents")

        return analysis

    def check_conflicting_authorities(self, citations: List[str]) -> List[Dict[str, any]]:
        """Check for conflicting authorities in a set of citations"""
        conflicts = []

        for i, citation1 in enumerate(citations):
            for citation2 in citations[i+1:]:
                # Check for direct conflicts through relationships
                conflicting_relationships = [
                    rel for rel in self.relationships
                    if ((rel.source_citation == citation1 and rel.target_citation == citation2) or
                        (rel.source_citation == citation2 and rel.target_citation == citation1)) and
                       rel.relationship_type in [RelationshipType.OVERRULES, RelationshipType.REVERSES,
                                               RelationshipType.DISTINGUISHES]
                ]

                for rel in conflicting_relationships:
                    conflicts.append({
                        'authority1': rel.source_citation,
                        'authority2': rel.target_citation,
                        'conflict_type': rel.relationship_type.value,
                        'description': rel.description,
                        'impact_score': rel.impact_score
                    })

        return conflicts

    def export_hierarchy_data(self, file_path: str = None) -> str:
        """Export hierarchy data to JSON file"""
        if not file_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = f"data/legal/authority_hierarchy_{timestamp}.json"

        Path(file_path).parent.mkdir(parents=True, exist_ok=True)

        export_data = {
            'authorities': {citation: asdict(authority) for citation, authority in self.authorities.items()},
            'relationships': [asdict(rel) for rel in self.relationships],
            'florida_districts': {key: asdict(district) for key, district in self.florida_districts.items()},
            'export_timestamp': datetime.now().isoformat(),
            'total_authorities': len(self.authorities),
            'total_relationships': len(self.relationships)
        }

        with open(file_path, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)

        return file_path

    def load_hierarchy_data(self, file_path: str) -> bool:
        """Load hierarchy data from JSON file"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)

            # Load authorities
            for citation, auth_data in data.get('authorities', {}).items():
                authority = LegalAuthority(**auth_data)
                self.authorities[citation] = authority

            # Load relationships
            for rel_data in data.get('relationships', []):
                rel_data['date_established'] = datetime.fromisoformat(rel_data['date_established'])
                rel_data['relationship_type'] = RelationshipType(rel_data['relationship_type'])
                relationship = AuthorityRelationship(**rel_data)
                self.relationships.append(relationship)

            return True

        except Exception as e:
            print(f"Error loading hierarchy data: {e}")
            return False

    def get_hierarchy_statistics(self) -> Dict[str, any]:
        """Get statistics about the authority hierarchy"""
        authority_by_type = {}
        authority_by_jurisdiction = {}
        authority_by_court_level = {}

        for authority in self.authorities.values():
            # By authority type
            auth_type = authority.authority_type.value
            authority_by_type[auth_type] = authority_by_type.get(auth_type, 0) + 1

            # By jurisdiction
            jurisdiction = authority.jurisdiction
            authority_by_jurisdiction[jurisdiction] = authority_by_jurisdiction.get(jurisdiction, 0) + 1

            # By court level
            court_level = authority.court_level.value
            authority_by_court_level[court_level] = authority_by_court_level.get(court_level, 0) + 1

        relationship_by_type = {}
        for relationship in self.relationships:
            rel_type = relationship.relationship_type.value
            relationship_by_type[rel_type] = relationship_by_type.get(rel_type, 0) + 1

        return {
            'total_authorities': len(self.authorities),
            'total_relationships': len(self.relationships),
            'authority_by_type': authority_by_type,
            'authority_by_jurisdiction': authority_by_jurisdiction,
            'authority_by_court_level': authority_by_court_level,
            'relationship_by_type': relationship_by_type,
            'florida_districts': len(self.florida_districts)
        }
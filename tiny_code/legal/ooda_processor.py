"""OODA Loop processor for legal analysis and case strategy development"""

import json
import uuid
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table

console = Console()

class OODAPhase(Enum):
    """OODA Loop phases for legal analysis"""
    OBSERVE = "observe"
    ORIENT = "orient"
    DECIDE = "decide"
    ACT = "act"

class ConfidenceLevel(Enum):
    """Confidence levels for legal analysis"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    VERY_HIGH = 4

@dataclass
class SourceReference:
    """Reference to legal source with citation"""
    source_type: str  # case, statute, regulation, article
    citation: str
    summary: str
    confidence: ConfidenceLevel
    timestamp: datetime

@dataclass
class ObservationResult:
    """Results from the Observe phase"""
    case_id: str
    facts: Dict[str, Any]
    sources: List[SourceReference]
    timeline: List[Dict[str, Any]]
    parties: List[Dict[str, str]]
    jurisdiction: str
    case_type: str
    confidence_score: float

@dataclass
class LegalIssue:
    """Identified legal issue"""
    issue_id: str
    description: str
    applicable_law: List[str]
    precedents: List[SourceReference]
    complexity: ConfidenceLevel
    priority: int

@dataclass
class OrientationResult:
    """Results from the Orient phase"""
    legal_issues: List[LegalIssue]
    precedent_map: Dict[str, List[SourceReference]]
    constitutional_considerations: List[str]
    procedural_requirements: List[str]
    strategic_assessment: Dict[str, Any]

@dataclass
class LegalStrategy:
    """Legal strategy with options"""
    strategy_id: str
    name: str
    description: str
    arguments: List[str]
    risks: List[str]
    success_probability: float
    timeline: List[Dict[str, Any]]
    required_resources: List[str]

@dataclass
class DecisionResult:
    """Results from the Decide phase"""
    recommended_strategy: LegalStrategy
    alternative_strategies: List[LegalStrategy]
    tactical_plan: List[Dict[str, Any]]
    deadline_analysis: Dict[str, Any]
    confidence_assessment: ConfidenceLevel

@dataclass
class ActionResult:
    """Results from the Act phase"""
    documents_generated: List[str]
    tasks_created: List[Dict[str, Any]]
    deadlines_set: List[Dict[str, Any]]
    follow_up_actions: List[str]
    execution_status: str

class LegalOODAProcessor:
    """Implements OODA Loop pattern for legal case analysis and strategy"""

    def __init__(self, audit_logger=None, case_database_path: str = "data/legal"):
        self.audit_logger = audit_logger
        self.case_database_path = Path(case_database_path)
        self.case_database_path.mkdir(parents=True, exist_ok=True)

        # Initialize legal reasoning log
        self.reasoning_log_path = Path("logs/legal_reasoning.json")
        self.reasoning_log_path.parent.mkdir(parents=True, exist_ok=True)

        # Current case tracking
        self.current_case_id = None
        self.phase_results = {}

    def start_case_analysis(self, case_name: str, client_id: str = None) -> str:
        """Start a new case analysis with OODA loop"""
        case_id = f"case_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        self.current_case_id = case_id

        # Initialize case record
        case_record = {
            "case_id": case_id,
            "case_name": case_name,
            "client_id": client_id,
            "start_time": datetime.now(timezone.utc).isoformat(),
            "current_phase": OODAPhase.OBSERVE.value,
            "phase_results": {},
            "audit_trail": []
        }

        # Save case record
        case_file = self.case_database_path / f"{case_id}.json"
        with open(case_file, 'w') as f:
            json.dump(case_record, f, indent=2, default=str)

        console.print(Panel(
            f"[bold green]Started legal analysis for case: {case_name}[/bold green]\n"
            f"Case ID: {case_id}\n"
            f"Ready to begin OBSERVE phase",
            title="OODA Legal Analysis",
            border_style="magenta"
        ))

        self._log_reasoning_event("case_started", {
            "case_id": case_id,
            "case_name": case_name,
            "client_id": client_id
        })

        return case_id

    def observe(self, case_facts: Dict[str, Any], sources: List[Dict[str, Any]] = None) -> ObservationResult:
        """Observe phase: Gather case facts with source tracking"""
        if not self.current_case_id:
            raise ValueError("No active case. Start case analysis first.")

        console.print("[cyan]🔍 OBSERVE Phase: Gathering case facts and sources...[/cyan]")

        # Process sources
        source_refs = []
        if sources:
            for source in sources:
                source_ref = SourceReference(
                    source_type=source.get("type", "unknown"),
                    citation=source.get("citation", ""),
                    summary=source.get("summary", ""),
                    confidence=ConfidenceLevel(source.get("confidence", 2)),
                    timestamp=datetime.now(timezone.utc)
                )
                source_refs.append(source_ref)

        # Create observation result
        observation = ObservationResult(
            case_id=self.current_case_id,
            facts=case_facts,
            sources=source_refs,
            timeline=case_facts.get("timeline", []),
            parties=case_facts.get("parties", []),
            jurisdiction=case_facts.get("jurisdiction", "unknown"),
            case_type=case_facts.get("case_type", "general"),
            confidence_score=self._calculate_confidence(case_facts, source_refs)
        )

        # Store results
        self.phase_results[OODAPhase.OBSERVE] = observation
        self._save_phase_results()

        # Log reasoning
        self._log_reasoning_event("observe_completed", {
            "case_id": self.current_case_id,
            "fact_count": len(case_facts),
            "source_count": len(source_refs),
            "confidence_score": observation.confidence_score
        })

        # Display results
        self._display_observation_results(observation)

        return observation

    def orient(self, observations: ObservationResult = None) -> OrientationResult:
        """Orient phase: Legal issue identification and precedent mapping"""
        if not observations:
            observations = self.phase_results.get(OODAPhase.OBSERVE)
            if not observations:
                raise ValueError("No observation results available. Complete OBSERVE phase first.")

        console.print("[yellow]🧭 ORIENT Phase: Identifying legal issues and mapping precedents...[/yellow]")

        # Identify legal issues
        legal_issues = self._identify_legal_issues(observations)

        # Map precedents
        precedent_map = self._map_precedents(legal_issues, observations.sources)

        # Analyze constitutional considerations
        constitutional_considerations = self._analyze_constitutional_issues(observations, legal_issues)

        # Determine procedural requirements
        procedural_requirements = self._determine_procedural_requirements(observations)

        # Strategic assessment
        strategic_assessment = self._conduct_strategic_assessment(observations, legal_issues)

        orientation = OrientationResult(
            legal_issues=legal_issues,
            precedent_map=precedent_map,
            constitutional_considerations=constitutional_considerations,
            procedural_requirements=procedural_requirements,
            strategic_assessment=strategic_assessment
        )

        # Store results
        self.phase_results[OODAPhase.ORIENT] = orientation
        self._save_phase_results()

        self._log_reasoning_event("orient_completed", {
            "case_id": self.current_case_id,
            "legal_issues_count": len(legal_issues),
            "constitutional_issues": len(constitutional_considerations)
        })

        self._display_orientation_results(orientation)

        return orientation

    def decide(self, orientation: OrientationResult = None) -> DecisionResult:
        """Decide phase: Strategy formulation with confidence scoring"""
        if not orientation:
            orientation = self.phase_results.get(OODAPhase.ORIENT)
            if not orientation:
                raise ValueError("No orientation results available. Complete ORIENT phase first.")

        console.print("[red]⚖️ DECIDE Phase: Formulating legal strategy and tactics...[/red]")

        # Generate strategic options
        strategies = self._generate_legal_strategies(orientation)

        # Select recommended strategy
        recommended_strategy = self._select_recommended_strategy(strategies)

        # Create tactical plan
        tactical_plan = self._create_tactical_plan(recommended_strategy, orientation)

        # Analyze deadlines
        deadline_analysis = self._analyze_deadlines(orientation)

        # Assess confidence
        confidence_assessment = self._assess_decision_confidence(recommended_strategy, orientation)

        decision = DecisionResult(
            recommended_strategy=recommended_strategy,
            alternative_strategies=[s for s in strategies if s.strategy_id != recommended_strategy.strategy_id],
            tactical_plan=tactical_plan,
            deadline_analysis=deadline_analysis,
            confidence_assessment=confidence_assessment
        )

        # Store results
        self.phase_results[OODAPhase.DECIDE] = decision
        self._save_phase_results()

        self._log_reasoning_event("decide_completed", {
            "case_id": self.current_case_id,
            "recommended_strategy": recommended_strategy.name,
            "confidence": confidence_assessment.value
        })

        self._display_decision_results(decision)

        return decision

    def act(self, decision: DecisionResult = None) -> ActionResult:
        """Act phase: Document generation and tactic execution"""
        if not decision:
            decision = self.phase_results.get(OODAPhase.DECIDE)
            if not decision:
                raise ValueError("No decision results available. Complete DECIDE phase first.")

        console.print("[green]🎯 ACT Phase: Executing strategy and generating documents...[/green]")

        # Generate documents
        documents_generated = self._generate_legal_documents(decision)

        # Create tasks
        tasks_created = self._create_action_tasks(decision)

        # Set deadlines
        deadlines_set = self._set_legal_deadlines(decision)

        # Plan follow-up actions
        follow_up_actions = self._plan_follow_up_actions(decision)

        action = ActionResult(
            documents_generated=documents_generated,
            tasks_created=tasks_created,
            deadlines_set=deadlines_set,
            follow_up_actions=follow_up_actions,
            execution_status="completed"
        )

        # Store results
        self.phase_results[OODAPhase.ACT] = action
        self._save_phase_results()

        self._log_reasoning_event("act_completed", {
            "case_id": self.current_case_id,
            "documents_generated": len(documents_generated),
            "tasks_created": len(tasks_created)
        })

        self._display_action_results(action)

        return action

    def generate_markdown_report(self) -> str:
        """Generate comprehensive markdown report of OODA analysis"""
        if not self.current_case_id or not self.phase_results:
            raise ValueError("No complete OODA analysis available")

        report_lines = [
            f"# Legal Analysis Report - Case {self.current_case_id}",
            "",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Executive Summary",
            ""
        ]

        # Add phase summaries
        for phase in OODAPhase:
            if phase in self.phase_results:
                report_lines.extend(self._generate_phase_markdown(phase, self.phase_results[phase]))

        report_content = "\n".join(report_lines)

        # Save report
        report_path = Path(f"workspace/legal_reasoning/{self.current_case_id}_analysis.md")
        report_path.parent.mkdir(parents=True, exist_ok=True)

        with open(report_path, 'w') as f:
            f.write(report_content)

        console.print(f"[green]📄 Markdown report saved: {report_path}[/green]")

        return report_content

    def _calculate_confidence(self, facts: Dict[str, Any], sources: List[SourceReference]) -> float:
        """Calculate confidence score based on fact completeness and source quality"""
        fact_score = min(len(facts) / 10.0, 1.0)  # Normalize to 0-1

        if not sources:
            source_score = 0.0
        else:
            source_scores = [s.confidence.value / 4.0 for s in sources]  # Normalize to 0-1
            source_score = sum(source_scores) / len(source_scores)

        return (fact_score + source_score) / 2.0

    def _identify_legal_issues(self, observations: ObservationResult) -> List[LegalIssue]:
        """Identify legal issues from observations"""
        # Simplified legal issue identification
        # In practice, this would use more sophisticated legal analysis

        issues = []
        case_type = observations.case_type.lower()

        if "contract" in case_type:
            issues.append(LegalIssue(
                issue_id="contract_001",
                description="Contract formation and validity",
                applicable_law=["UCC", "Common Law Contracts"],
                precedents=[],
                complexity=ConfidenceLevel.MEDIUM,
                priority=1
            ))

        if "tort" in case_type or "negligence" in case_type:
            issues.append(LegalIssue(
                issue_id="tort_001",
                description="Duty of care and breach analysis",
                applicable_law=["Tort Law", "Negligence Standards"],
                precedents=[],
                complexity=ConfidenceLevel.HIGH,
                priority=1
            ))

        return issues

    def _map_precedents(self, issues: List[LegalIssue], sources: List[SourceReference]) -> Dict[str, List[SourceReference]]:
        """Map precedents to legal issues"""
        precedent_map = {}

        for issue in issues:
            relevant_sources = [s for s in sources if s.source_type == "case"]
            precedent_map[issue.issue_id] = relevant_sources

        return precedent_map

    def _analyze_constitutional_issues(self, observations: ObservationResult, issues: List[LegalIssue]) -> List[str]:
        """Analyze constitutional considerations"""
        constitutional_issues = []

        # Check for common constitutional issues
        facts_text = str(observations.facts).lower()

        if any(term in facts_text for term in ["speech", "expression", "protest"]):
            constitutional_issues.append("First Amendment - Freedom of Speech")

        if any(term in facts_text for term in ["search", "seizure", "warrant"]):
            constitutional_issues.append("Fourth Amendment - Search and Seizure")

        if any(term in facts_text for term in ["due process", "hearing", "notice"]):
            constitutional_issues.append("Fifth/Fourteenth Amendment - Due Process")

        return constitutional_issues

    def _determine_procedural_requirements(self, observations: ObservationResult) -> List[str]:
        """Determine procedural requirements based on jurisdiction and case type"""
        requirements = []

        jurisdiction = observations.jurisdiction.lower()
        case_type = observations.case_type.lower()

        if "federal" in jurisdiction:
            requirements.append("Federal Rules of Civil Procedure")

        if "criminal" in case_type:
            requirements.append("Criminal procedure rules")
            requirements.append("Speedy trial requirements")

        if "civil" in case_type:
            requirements.append("Civil procedure rules")
            requirements.append("Discovery deadlines")

        return requirements

    def _conduct_strategic_assessment(self, observations: ObservationResult, issues: List[LegalIssue]) -> Dict[str, Any]:
        """Conduct strategic assessment"""
        return {
            "complexity_level": max([issue.complexity.value for issue in issues], default=1),
            "estimated_duration": "6-12 months",  # Simplified
            "resource_requirements": ["Legal research", "Expert witnesses", "Document review"],
            "success_likelihood": "Medium to High",
            "key_risks": ["Procedural missteps", "Insufficient evidence", "Adverse precedent"]
        }

    def _generate_legal_strategies(self, orientation: OrientationResult) -> List[LegalStrategy]:
        """Generate possible legal strategies"""
        strategies = []

        # Generate strategies based on legal issues
        for i, issue in enumerate(orientation.legal_issues):
            strategy = LegalStrategy(
                strategy_id=f"strategy_{i+1}",
                name=f"Strategy for {issue.description}",
                description=f"Comprehensive approach to address {issue.description}",
                arguments=[f"Argument based on {law}" for law in issue.applicable_law],
                risks=["Unfavorable precedent", "Procedural challenges"],
                success_probability=0.7,  # Simplified
                timeline=[{"phase": "Research", "duration": "2 weeks"}],
                required_resources=["Legal research", "Document preparation"]
            )
            strategies.append(strategy)

        return strategies

    def _select_recommended_strategy(self, strategies: List[LegalStrategy]) -> LegalStrategy:
        """Select the recommended strategy"""
        if not strategies:
            raise ValueError("No strategies available")

        # Select strategy with highest success probability
        return max(strategies, key=lambda s: s.success_probability)

    def _create_tactical_plan(self, strategy: LegalStrategy, orientation: OrientationResult) -> List[Dict[str, Any]]:
        """Create detailed tactical plan"""
        return [
            {"step": 1, "action": "Complete legal research", "deadline": "2 weeks", "responsible": "Legal team"},
            {"step": 2, "action": "Draft initial pleadings", "deadline": "1 month", "responsible": "Attorney"},
            {"step": 3, "action": "File documents", "deadline": "6 weeks", "responsible": "Legal staff"}
        ]

    def _analyze_deadlines(self, orientation: OrientationResult) -> Dict[str, Any]:
        """Analyze legal deadlines"""
        return {
            "statute_of_limitations": "Within 2 years",
            "filing_deadlines": ["30 days for response", "60 days for discovery"],
            "court_deadlines": "TBD based on court schedule"
        }

    def _assess_decision_confidence(self, strategy: LegalStrategy, orientation: OrientationResult) -> ConfidenceLevel:
        """Assess confidence in decision"""
        # Simplified confidence assessment
        issue_complexity = max([issue.complexity.value for issue in orientation.legal_issues], default=1)

        if strategy.success_probability > 0.8 and issue_complexity <= 2:
            return ConfidenceLevel.VERY_HIGH
        elif strategy.success_probability > 0.6:
            return ConfidenceLevel.HIGH
        elif strategy.success_probability > 0.4:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW

    def _generate_legal_documents(self, decision: DecisionResult) -> List[str]:
        """Generate legal documents based on strategy"""
        documents = []

        strategy = decision.recommended_strategy

        # Generate document templates based on strategy
        if "contract" in strategy.name.lower():
            documents.extend(["Contract_Draft.docx", "Contract_Analysis.pdf"])
        if "motion" in strategy.name.lower():
            documents.extend(["Motion_Draft.docx", "Supporting_Brief.pdf"])

        return documents

    def _create_action_tasks(self, decision: DecisionResult) -> List[Dict[str, Any]]:
        """Create actionable tasks"""
        tasks = []

        for step in decision.tactical_plan:
            task = {
                "id": f"task_{step['step']}",
                "title": step["action"],
                "deadline": step["deadline"],
                "assigned_to": step["responsible"],
                "status": "pending"
            }
            tasks.append(task)

        return tasks

    def _set_legal_deadlines(self, decision: DecisionResult) -> List[Dict[str, Any]]:
        """Set legal deadlines and calendar entries"""
        deadlines = []

        for item, deadline in decision.deadline_analysis.items():
            if isinstance(deadline, str) and deadline != "TBD based on court schedule":
                deadlines.append({
                    "type": item,
                    "deadline": deadline,
                    "calendar_entry": True,
                    "reminder_days": [30, 14, 7, 1]
                })

        return deadlines

    def _plan_follow_up_actions(self, decision: DecisionResult) -> List[str]:
        """Plan follow-up actions"""
        return [
            "Schedule client update meeting",
            "Monitor court calendar for scheduling orders",
            "Prepare discovery plan",
            "Review and update case strategy monthly"
        ]

    def _save_phase_results(self):
        """Save current phase results to case file"""
        if not self.current_case_id:
            return

        case_file = self.case_database_path / f"{self.current_case_id}.json"

        if case_file.exists():
            with open(case_file, 'r') as f:
                case_data = json.load(f)
        else:
            case_data = {"case_id": self.current_case_id}

        # Convert dataclass results to dict for JSON serialization
        case_data["phase_results"] = {}
        for phase, result in self.phase_results.items():
            case_data["phase_results"][phase.value] = asdict(result)

        case_data["last_updated"] = datetime.now(timezone.utc).isoformat()

        with open(case_file, 'w') as f:
            json.dump(case_data, f, indent=2, default=str)

    def _log_reasoning_event(self, event_type: str, details: Dict[str, Any]):
        """Log reasoning event to legal reasoning log"""
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "case_id": self.current_case_id,
            "details": details
        }

        # Append to reasoning log
        log_entries = []
        if self.reasoning_log_path.exists():
            with open(self.reasoning_log_path, 'r') as f:
                try:
                    log_entries = json.load(f)
                except json.JSONDecodeError:
                    log_entries = []

        log_entries.append(event)

        with open(self.reasoning_log_path, 'w') as f:
            json.dump(log_entries, f, indent=2, default=str)

    def _display_observation_results(self, observation: ObservationResult):
        """Display observation phase results"""
        table = Table(title="Observation Phase Results")
        table.add_column("Category", style="cyan")
        table.add_column("Details", style="white")

        table.add_row("Case ID", observation.case_id)
        table.add_row("Jurisdiction", observation.jurisdiction)
        table.add_row("Case Type", observation.case_type)
        table.add_row("Fact Count", str(len(observation.facts)))
        table.add_row("Source Count", str(len(observation.sources)))
        table.add_row("Confidence Score", f"{observation.confidence_score:.2f}")

        console.print(table)

    def _display_orientation_results(self, orientation: OrientationResult):
        """Display orientation phase results"""
        console.print(Panel(
            f"Identified {len(orientation.legal_issues)} legal issues\n"
            f"Constitutional considerations: {len(orientation.constitutional_considerations)}\n"
            f"Procedural requirements: {len(orientation.procedural_requirements)}",
            title="Orientation Phase Results",
            border_style="yellow"
        ))

    def _display_decision_results(self, decision: DecisionResult):
        """Display decision phase results"""
        console.print(Panel(
            f"Recommended Strategy: {decision.recommended_strategy.name}\n"
            f"Success Probability: {decision.recommended_strategy.success_probability:.1%}\n"
            f"Confidence Level: {decision.confidence_assessment.name}",
            title="Decision Phase Results",
            border_style="red"
        ))

    def _display_action_results(self, action: ActionResult):
        """Display action phase results"""
        console.print(Panel(
            f"Documents Generated: {len(action.documents_generated)}\n"
            f"Tasks Created: {len(action.tasks_created)}\n"
            f"Deadlines Set: {len(action.deadlines_set)}\n"
            f"Status: {action.execution_status}",
            title="Action Phase Results",
            border_style="green"
        ))

    def _generate_phase_markdown(self, phase: OODAPhase, result) -> List[str]:
        """Generate markdown for a specific phase"""
        lines = [f"## {phase.value.upper()} Phase", ""]

        if phase == OODAPhase.OBSERVE:
            lines.extend([
                f"**Case ID:** {result.case_id}",
                f"**Jurisdiction:** {result.jurisdiction}",
                f"**Case Type:** {result.case_type}",
                f"**Confidence Score:** {result.confidence_score:.2f}",
                "",
                "### Key Facts",
                ""
            ])
            for key, value in result.facts.items():
                lines.append(f"- **{key}:** {value}")
            lines.append("")

        elif phase == OODAPhase.ORIENT:
            lines.extend([
                "### Legal Issues",
                ""
            ])
            for issue in result.legal_issues:
                lines.extend([
                    f"#### {issue.description}",
                    f"**Applicable Law:** {', '.join(issue.applicable_law)}",
                    f"**Complexity:** {issue.complexity.name}",
                    ""
                ])

        elif phase == OODAPhase.DECIDE:
            lines.extend([
                "### Recommended Strategy",
                f"**Name:** {result.recommended_strategy.name}",
                f"**Success Probability:** {result.recommended_strategy.success_probability:.1%}",
                f"**Confidence:** {result.confidence_assessment.name}",
                "",
                "### Arguments:",
                ""
            ])
            for arg in result.recommended_strategy.arguments:
                lines.append(f"- {arg}")
            lines.append("")

        elif phase == OODAPhase.ACT:
            lines.extend([
                "### Documents Generated",
                ""
            ])
            for doc in result.documents_generated:
                lines.append(f"- {doc}")
            lines.extend([
                "",
                "### Tasks Created",
                ""
            ])
            for task in result.tasks_created:
                lines.append(f"- {task['title']} (Due: {task['deadline']})")
            lines.append("")

        return lines
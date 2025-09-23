"""
Legal Document Templates and Structure Tools

This module provides comprehensive templates and structural guidance for creating
various types of legal documents following established best practices.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from .writing_principles import LegalDocumentType, AnalysisStructure


class TemplateSection(Enum):
    """Standard template sections"""
    HEADER = "header"
    CAPTION = "caption"
    INTRODUCTION = "introduction"
    STATEMENT_OF_FACTS = "statement_of_facts"
    LEGAL_ANALYSIS = "legal_analysis"
    ARGUMENT = "argument"
    CONCLUSION = "conclusion"
    SIGNATURE_BLOCK = "signature_block"
    CERTIFICATE_OF_SERVICE = "certificate_of_service"


@dataclass
class SectionTemplate:
    """Template for a document section"""
    name: str
    section_type: TemplateSection
    description: str
    required: bool
    template_text: str
    placeholder_instructions: Dict[str, str] = field(default_factory=dict)
    best_practices: List[str] = field(default_factory=list)
    common_mistakes: List[str] = field(default_factory=list)


@dataclass
class DocumentTemplate:
    """Complete template for a legal document type"""
    document_type: LegalDocumentType
    name: str
    description: str
    sections: List[SectionTemplate]
    formatting_requirements: Dict[str, str]
    page_limits: Optional[Dict[str, int]] = None
    court_specific_requirements: Dict[str, List[str]] = field(default_factory=dict)
    analysis_framework: Optional[AnalysisStructure] = None


class LegalDocumentTemplates:
    """Comprehensive legal document template system"""

    def __init__(self):
        self.templates = self._initialize_templates()

    def _initialize_templates(self) -> Dict[LegalDocumentType, DocumentTemplate]:
        """Initialize all document templates"""

        templates = {}

        # Legal Brief Template
        templates[LegalDocumentType.BRIEF] = self._create_brief_template()

        # Legal Memorandum Template
        templates[LegalDocumentType.MEMORANDUM] = self._create_memorandum_template()

        # Motion Template
        templates[LegalDocumentType.MOTION] = self._create_motion_template()

        # Client Letter Template
        templates[LegalDocumentType.CLIENT_LETTER] = self._create_client_letter_template()

        # Contract Template
        templates[LegalDocumentType.CONTRACT] = self._create_contract_template()

        return templates

    def _create_brief_template(self) -> DocumentTemplate:
        """Create appellate brief template"""

        sections = [
            SectionTemplate(
                name="Cover Page",
                section_type=TemplateSection.HEADER,
                description="Case caption and filing information",
                required=True,
                template_text="""[COURT NAME]
[CASE NUMBER]

[PLAINTIFF/APPELLANT NAME],
    Plaintiff-Appellant,

v.

[DEFENDANT/APPELLEE NAME],
    Defendant-Appellee.

[DOCUMENT TITLE]

[ATTORNEY NAME]
[BAR NUMBER]
[FIRM NAME]
[ADDRESS]
[PHONE/EMAIL]
Attorney for [CLIENT]""",
                placeholder_instructions={
                    "[COURT NAME]": "Full name of the court (e.g., 'UNITED STATES COURT OF APPEALS FOR THE ELEVENTH CIRCUIT')",
                    "[CASE NUMBER]": "Case docket number",
                    "[PLAINTIFF/APPELLANT NAME]": "Full legal name of plaintiff/appellant",
                    "[DEFENDANT/APPELLEE NAME]": "Full legal name of defendant/appellee",
                    "[DOCUMENT TITLE]": "Title of brief (e.g., 'BRIEF OF APPELLANT')",
                    "[ATTORNEY NAME]": "Attorney's full name",
                    "[BAR NUMBER]": "State bar admission number",
                    "[FIRM NAME]": "Law firm or organization name",
                    "[ADDRESS]": "Complete mailing address",
                    "[PHONE/EMAIL]": "Contact information",
                    "[CLIENT]": "Party being represented"
                },
                best_practices=[
                    "Use all caps for court name and case caption",
                    "Double-check case number accuracy",
                    "Include all required attorney information",
                    "Use proper party designations (Appellant/Appellee)"
                ],
                common_mistakes=[
                    "Incorrect court name or jurisdiction",
                    "Missing or incorrect case number",
                    "Incomplete attorney contact information",
                    "Wrong party designations"
                ]
            ),

            SectionTemplate(
                name="Table of Contents",
                section_type=TemplateSection.HEADER,
                description="Document outline with page references",
                required=True,
                template_text="""TABLE OF CONTENTS

STATEMENT OF ISSUES PRESENTED FOR REVIEW ............................ [page]

STATEMENT OF THE CASE ................................................ [page]

STATEMENT OF FACTS ................................................... [page]

SUMMARY OF ARGUMENT .................................................. [page]

ARGUMENT ............................................................. [page]

I. [FIRST MAJOR ARGUMENT HEADING] ................................... [page]
   A. [Sub-argument A] .............................................. [page]
   B. [Sub-argument B] .............................................. [page]

II. [SECOND MAJOR ARGUMENT HEADING] ................................. [page]
    A. [Sub-argument A] ............................................. [page]
    B. [Sub-argument B] ............................................. [page]

CONCLUSION ........................................................... [page]""",
                placeholder_instructions={
                    "[page]": "Actual page number where section begins",
                    "[FIRST MAJOR ARGUMENT HEADING]": "Main legal argument heading",
                    "[SECOND MAJOR ARGUMENT HEADING]": "Second main legal argument heading",
                    "[Sub-argument A/B]": "Supporting sub-arguments"
                },
                best_practices=[
                    "Update page numbers after final formatting",
                    "Use consistent formatting for all headings",
                    "Include all major sections and subsections",
                    "Use parallel structure in headings"
                ]
            ),

            SectionTemplate(
                name="Table of Authorities",
                section_type=TemplateSection.HEADER,
                description="List of all legal authorities cited",
                required=True,
                template_text="""TABLE OF AUTHORITIES

CASES
                                                                      Page
[Case Name], [Citation] .............................................. [page]
[Case Name], [Citation] .............................................. [page]

STATUTES

[Statute Citation] .................................................... [page]
[Statute Citation] .................................................... [page]

REGULATIONS

[Regulation Citation] ................................................. [page]

OTHER AUTHORITIES

[Secondary Authority] ................................................. [page]""",
                placeholder_instructions={
                    "[Case Name]": "Full case name as it appears in citation",
                    "[Citation]": "Complete legal citation including court and year",
                    "[Statute Citation]": "Complete statutory citation",
                    "[Regulation Citation]": "Complete regulatory citation",
                    "[Secondary Authority]": "Law review articles, treatises, etc.",
                    "[page]": "Page numbers where authority is cited"
                },
                best_practices=[
                    "Alphabetize entries within each category",
                    "Use proper citation format throughout",
                    "Include pinpoint page references",
                    "Update after completing document"
                ]
            ),

            SectionTemplate(
                name="Statement of Issues",
                section_type=TemplateSection.INTRODUCTION,
                description="Precise legal questions presented",
                required=True,
                template_text="""STATEMENT OF ISSUES PRESENTED FOR REVIEW

1. Whether [precise legal question in yes/no format]?

2. Whether [second legal question in yes/no format]?""",
                placeholder_instructions={
                    "[precise legal question in yes/no format]": "Frame issue to suggest answer favorable to client"
                },
                best_practices=[
                    "Frame issues favorably but accurately",
                    "Use specific facts in question formulation",
                    "Make issues answerable with yes/no",
                    "Order from strongest to weakest issue"
                ],
                common_mistakes=[
                    "Vague or overly broad issue statements",
                    "Issues not tied to specific legal standards",
                    "Neutral framing that doesn't favor client",
                    "Too many issues (generally limit to 2-3)"
                ]
            ),

            SectionTemplate(
                name="Statement of Facts",
                section_type=TemplateSection.STATEMENT_OF_FACTS,
                description="Objective recitation of relevant facts",
                required=True,
                template_text="""STATEMENT OF FACTS

[Provide chronological narrative of relevant facts. Include record citations for all factual assertions. Present facts objectively but emphasize those favorable to your client's position.]

[Paragraph 1: Background/context]

[Paragraph 2: Key events leading to dispute]

[Paragraph 3: Procedural history]

[Final paragraph: Current posture]""",
                placeholder_instructions={
                    "[Provide chronological narrative...]": "Tell compelling story while maintaining objectivity",
                    "[Paragraph 1: Background/context]": "Set stage with necessary background",
                    "[Paragraph 2: Key events...]": "Detail events that led to legal dispute",
                    "[Paragraph 3: Procedural history]": "Describe court proceedings to date",
                    "[Final paragraph: Current posture]": "Explain current status and what court must decide"
                },
                best_practices=[
                    "Include record citations for all facts",
                    "Present facts chronologically",
                    "Emphasize facts favorable to client",
                    "Remain objective and accurate",
                    "Include only legally relevant facts"
                ],
                common_mistakes=[
                    "Including legal conclusions in fact section",
                    "Missing record citations",
                    "Arguing rather than stating facts",
                    "Including irrelevant details"
                ]
            ),

            SectionTemplate(
                name="Argument",
                section_type=TemplateSection.ARGUMENT,
                description="Legal analysis using CRAC structure",
                required=True,
                template_text="""ARGUMENT

I. [FIRST MAJOR ARGUMENT HEADING STATING CONCLUSION]

[Opening paragraph stating conclusion and roadmap]

A. [Sub-argument A heading]

[Rule paragraph: State the applicable legal rule with supporting citations]

[Explanation paragraph: Explain how courts have applied this rule through case analysis]

[Application paragraph: Apply the rule to the facts of this case]

[Conclusion paragraph: Restate conclusion for this sub-argument]

B. [Sub-argument B heading]

[Follow same CRAC structure]

II. [SECOND MAJOR ARGUMENT HEADING]

[Continue with same structure for each major argument]""",
                placeholder_instructions={
                    "[FIRST MAJOR ARGUMENT HEADING]": "Conclusory heading stating your position",
                    "[Opening paragraph...]": "Preview the argument structure and conclusion",
                    "[Rule paragraph...]": "State governing law with proper citations",
                    "[Explanation paragraph...]": "Synthesize case law to explain rule application",
                    "[Application paragraph...]": "Apply law to specific facts of case",
                    "[Conclusion paragraph...]": "Restate conclusion based on analysis"
                },
                best_practices=[
                    "Use CRAC structure consistently",
                    "Lead with your strongest arguments",
                    "Address counterarguments",
                    "Use persuasive headings",
                    "Support all assertions with authority"
                ],
                common_mistakes=[
                    "Weak or incomplete rule statements",
                    "Insufficient case law analysis",
                    "Failure to apply law to facts",
                    "Ignoring adverse authority"
                ]
            ),

            SectionTemplate(
                name="Conclusion",
                section_type=TemplateSection.CONCLUSION,
                description="Request for relief and summary",
                required=True,
                template_text="""CONCLUSION

For the foregoing reasons, [Appellant/Appellee] respectfully requests that this Court [specific relief requested].

                                    Respectfully submitted,

                                    /s/ [Attorney Name]
                                    [Attorney Name]
                                    [Bar Number]
                                    [Firm Name]
                                    [Address]
                                    [Phone]
                                    [Email]
                                    Attorney for [Client]""",
                placeholder_instructions={
                    "[Appellant/Appellee]": "Your client's designation",
                    "[specific relief requested]": "Precise relief sought (reverse, affirm, remand, etc.)",
                    "[Attorney Name]": "Attorney's full name",
                    "[Bar Number]": "State bar number",
                    "[Firm Name]": "Law firm name",
                    "[Address]": "Complete address",
                    "[Phone]": "Phone number",
                    "[Email]": "Email address",
                    "[Client]": "Party represented"
                },
                best_practices=[
                    "Be specific about relief requested",
                    "Keep conclusion brief",
                    "Include complete signature block",
                    "Match tone to document formality"
                ]
            )
        ]

        return DocumentTemplate(
            document_type=LegalDocumentType.BRIEF,
            name="Appellate Brief",
            description="Template for appellate court briefs",
            sections=sections,
            formatting_requirements={
                "font": "Times New Roman 12pt",
                "spacing": "Double-spaced",
                "margins": "1 inch all sides",
                "page_numbering": "Bottom center",
                "headings": "Bold, same font as text"
            },
            page_limits={
                "main_brief": 50,
                "reply_brief": 25
            },
            court_specific_requirements={
                "federal_circuit": [
                    "Include statement of related cases",
                    "Provide jurisdictional statement",
                    "Include addendum with relevant statutory provisions"
                ],
                "state_appellate": [
                    "Check local rules for specific requirements",
                    "May require different caption format",
                    "Different page limits may apply"
                ]
            },
            analysis_framework=AnalysisStructure.CRAC
        )

    def _create_memorandum_template(self) -> DocumentTemplate:
        """Create legal memorandum template"""

        sections = [
            SectionTemplate(
                name="Header",
                section_type=TemplateSection.HEADER,
                description="Memorandum identifying information",
                required=True,
                template_text="""MEMORANDUM

TO:      [Recipient Name and Title]
FROM:    [Your Name and Title]
DATE:    [Date]
RE:      [Brief description of legal issue or case name]""",
                placeholder_instructions={
                    "[Recipient Name and Title]": "Person receiving memo and their position",
                    "[Your Name and Title]": "Your name and position",
                    "[Date]": "Date memo was prepared",
                    "[Brief description...]": "Concise description of legal matter"
                },
                best_practices=[
                    "Use clear, descriptive subject line",
                    "Include complete date",
                    "Be specific about the legal issue",
                    "Use professional formatting"
                ]
            ),

            SectionTemplate(
                name="Question Presented",
                section_type=TemplateSection.INTRODUCTION,
                description="Precise legal question being analyzed",
                required=True,
                template_text="""QUESTION PRESENTED

Whether [specific legal question incorporating key facts and applicable law]?""",
                placeholder_instructions={
                    "[specific legal question...]": "Frame question objectively, including key facts"
                },
                best_practices=[
                    "Include key facts in question formulation",
                    "Reference applicable legal standard",
                    "Make question specific and answerable",
                    "Remain objective in framing"
                ],
                common_mistakes=[
                    "Overly broad or vague questions",
                    "Questions not tied to specific facts",
                    "Multiple questions in single statement",
                    "Biased framing"
                ]
            ),

            SectionTemplate(
                name="Brief Answer",
                section_type=TemplateSection.INTRODUCTION,
                description="Concise answer to question presented",
                required=True,
                template_text="""BRIEF ANSWER

[Likely/Probably/Yes/No]. [One to two sentence explanation of conclusion and primary reasoning.]""",
                placeholder_instructions={
                    "[Likely/Probably/Yes/No]": "Direct answer with appropriate qualification",
                    "[One to two sentence explanation...]": "Brief reasoning for conclusion"
                },
                best_practices=[
                    "Give direct answer first",
                    "Qualify answer appropriately (likely, probably, etc.)",
                    "Provide brief reasoning",
                    "Keep to 1-2 sentences maximum"
                ]
            ),

            SectionTemplate(
                name="Statement of Facts",
                section_type=TemplateSection.STATEMENT_OF_FACTS,
                description="Objective recitation of relevant facts",
                required=True,
                template_text="""STATEMENT OF FACTS

[Provide chronological narrative of legally relevant facts. Remain objective and include all material facts, both favorable and unfavorable to the client's position.]""",
                placeholder_instructions={
                    "[Provide chronological narrative...]": "Tell complete story objectively"
                },
                best_practices=[
                    "Include all material facts",
                    "Remain objective",
                    "Organize chronologically",
                    "Focus on legally relevant details"
                ]
            ),

            SectionTemplate(
                name="Discussion",
                section_type=TemplateSection.LEGAL_ANALYSIS,
                description="Detailed legal analysis using IRAC structure",
                required=True,
                template_text="""DISCUSSION

I. [FIRST ISSUE HEADING]

[Issue: Restate the legal issue to be analyzed]

[Rule: State the applicable legal rule with supporting citations and explanation]

[Application: Apply the rule to the specific facts of the case]

[Conclusion: State conclusion for this issue]

II. [SECOND ISSUE HEADING]

[Continue IRAC analysis for additional issues]""",
                placeholder_instructions={
                    "[FIRST ISSUE HEADING]": "Specific legal issue being analyzed",
                    "[Issue: Restate...]": "Clear statement of legal question",
                    "[Rule: State...]": "Comprehensive rule statement with authorities",
                    "[Application: Apply...]": "Thorough application of law to facts",
                    "[Conclusion: State...]": "Clear conclusion based on analysis"
                },
                best_practices=[
                    "Use IRAC structure consistently",
                    "Provide complete rule statements",
                    "Apply law systematically to facts",
                    "Address counterarguments",
                    "Remain objective in analysis"
                ]
            ),

            SectionTemplate(
                name="Conclusion",
                section_type=TemplateSection.CONCLUSION,
                description="Summary of analysis and recommendations",
                required=True,
                template_text="""CONCLUSION

[Restate conclusion and provide any recommendations for action.]""",
                placeholder_instructions={
                    "[Restate conclusion...]": "Brief summary and any recommendations"
                },
                best_practices=[
                    "Restate main conclusion",
                    "Include practical recommendations",
                    "Keep brief and actionable",
                    "Address next steps if appropriate"
                ]
            )
        ]

        return DocumentTemplate(
            document_type=LegalDocumentType.MEMORANDUM,
            name="Legal Memorandum",
            description="Template for objective legal analysis memoranda",
            sections=sections,
            formatting_requirements={
                "font": "Times New Roman 12pt",
                "spacing": "Single or 1.5 spacing",
                "margins": "1 inch all sides",
                "page_numbering": "Bottom center or top right"
            },
            analysis_framework=AnalysisStructure.IRAC
        )

    def _create_motion_template(self) -> DocumentTemplate:
        """Create motion template"""

        sections = [
            SectionTemplate(
                name="Caption",
                section_type=TemplateSection.CAPTION,
                description="Case caption and motion title",
                required=True,
                template_text="""IN THE [COURT NAME]
[COUNTY/DISTRICT], [STATE]

[PLAINTIFF NAME],           )
                           )    Case No. [CASE NUMBER]
    Plaintiff,             )
                           )
v.                         )
                           )
[DEFENDANT NAME],          )
                           )
    Defendant.             )
___________________________)

[MOTION TITLE]""",
                placeholder_instructions={
                    "[COURT NAME]": "Full court name",
                    "[COUNTY/DISTRICT]": "Jurisdiction location",
                    "[STATE]": "State name",
                    "[PLAINTIFF NAME]": "Full plaintiff name",
                    "[CASE NUMBER]": "Case docket number",
                    "[DEFENDANT NAME]": "Full defendant name",
                    "[MOTION TITLE]": "Specific motion title (e.g., 'MOTION TO DISMISS')"
                }
            ),

            SectionTemplate(
                name="Introduction",
                section_type=TemplateSection.INTRODUCTION,
                description="Opening statement of motion and relief sought",
                required=True,
                template_text="""[Movant name] respectfully moves this Court for [specific relief requested] and states as follows:""",
                placeholder_instructions={
                    "[Movant name]": "Party filing the motion",
                    "[specific relief requested]": "Precise relief being sought"
                },
                best_practices=[
                    "State relief clearly and specifically",
                    "Use formal, respectful language",
                    "Be concise in introduction"
                ]
            ),

            SectionTemplate(
                name="Statement of Facts",
                section_type=TemplateSection.STATEMENT_OF_FACTS,
                description="Relevant factual background",
                required=True,
                template_text="""STATEMENT OF FACTS

[Provide factual background necessary to understand the motion. Present facts favorably but accurately.]""",
                best_practices=[
                    "Include only facts relevant to motion",
                    "Present facts favorably to movant",
                    "Remain accurate and verifiable",
                    "Use record citations when available"
                ]
            ),

            SectionTemplate(
                name="Argument",
                section_type=TemplateSection.ARGUMENT,
                description="Legal argument supporting motion",
                required=True,
                template_text="""ARGUMENT

I. [FIRST ARGUMENT HEADING SUPPORTING MOTION]

[Legal analysis using CRAC structure to support granting the motion]

II. [SECOND ARGUMENT HEADING]

[Continue with additional supporting arguments]""",
                best_practices=[
                    "Use persuasive CRAC structure",
                    "Lead with strongest arguments",
                    "Support with relevant authority",
                    "Address likely counterarguments"
                ]
            ),

            SectionTemplate(
                name="Conclusion",
                section_type=TemplateSection.CONCLUSION,
                description="Prayer for relief",
                required=True,
                template_text="""CONCLUSION

WHEREFORE, [Movant] respectfully requests that this Court [specific relief requested].

                                    Respectfully submitted,

                                    /s/ [Attorney Name]
                                    [Attorney Name]
                                    [Bar Number]
                                    [Firm Name]
                                    [Address]
                                    [Phone]
                                    [Email]
                                    Attorney for [Client]""",
                best_practices=[
                    "Use formal prayer language",
                    "Be specific about relief requested",
                    "Include complete signature block"
                ]
            )
        ]

        return DocumentTemplate(
            document_type=LegalDocumentType.MOTION,
            name="Motion",
            description="Template for court motions",
            sections=sections,
            formatting_requirements={
                "font": "Times New Roman 12pt",
                "spacing": "Double-spaced",
                "margins": "1 inch all sides",
                "page_numbering": "Bottom center"
            },
            analysis_framework=AnalysisStructure.CRAC
        )

    def _create_client_letter_template(self) -> DocumentTemplate:
        """Create client letter template"""

        sections = [
            SectionTemplate(
                name="Header",
                section_type=TemplateSection.HEADER,
                description="Letterhead and addressing",
                required=True,
                template_text="""[FIRM LETTERHEAD]

[Date]

[Client Name]
[Client Address]
[City, State ZIP]

Re: [Matter description]

Dear [Client Name]:""",
                placeholder_instructions={
                    "[FIRM LETTERHEAD]": "Law firm name and contact information",
                    "[Date]": "Date letter is written",
                    "[Client Name]": "Client's full name",
                    "[Client Address]": "Client's mailing address",
                    "[Matter description]": "Brief description of legal matter"
                }
            ),

            SectionTemplate(
                name="Opening",
                section_type=TemplateSection.INTRODUCTION,
                description="Opening paragraph with purpose",
                required=True,
                template_text="""I am writing to [state purpose of letter and provide brief summary of advice or information being conveyed].""",
                best_practices=[
                    "State purpose clearly in first sentence",
                    "Provide brief overview of advice",
                    "Use plain language appropriate for client"
                ]
            ),

            SectionTemplate(
                name="Background",
                section_type=TemplateSection.STATEMENT_OF_FACTS,
                description="Factual background relevant to advice",
                required=False,
                template_text="""BACKGROUND

[Summarize relevant facts and procedural history as necessary for client understanding.]""",
                best_practices=[
                    "Include only facts necessary for understanding",
                    "Use clear, non-technical language",
                    "Organize chronologically"
                ]
            ),

            SectionTemplate(
                name="Legal Analysis",
                section_type=TemplateSection.LEGAL_ANALYSIS,
                description="Legal advice and analysis",
                required=True,
                template_text="""LEGAL ANALYSIS

[Provide legal advice in clear, understandable terms. Explain relevant law and how it applies to client's situation. Include practical recommendations.]""",
                best_practices=[
                    "Use plain language explanations",
                    "Avoid unnecessary legal jargon",
                    "Provide practical advice",
                    "Include risks and benefits",
                    "Give specific recommendations"
                ]
            ),

            SectionTemplate(
                name="Conclusion",
                section_type=TemplateSection.CONCLUSION,
                description="Summary and next steps",
                required=True,
                template_text="""CONCLUSION

[Summarize key advice and outline next steps or recommended actions.]

Please feel free to contact me if you have any questions about this matter.

                                    Sincerely,


                                    [Attorney Name]
                                    [Title]""",
                best_practices=[
                    "Summarize key points clearly",
                    "Outline specific next steps",
                    "Invite follow-up questions",
                    "Use appropriate closing"
                ]
            )
        ]

        return DocumentTemplate(
            document_type=LegalDocumentType.CLIENT_LETTER,
            name="Client Letter",
            description="Template for client advice letters",
            sections=sections,
            formatting_requirements={
                "font": "Times New Roman 12pt",
                "spacing": "Single-spaced",
                "margins": "1 inch all sides"
            }
        )

    def _create_contract_template(self) -> DocumentTemplate:
        """Create basic contract template"""

        sections = [
            SectionTemplate(
                name="Title and Parties",
                section_type=TemplateSection.HEADER,
                description="Contract title and party identification",
                required=True,
                template_text="""[CONTRACT TITLE]

This [Contract Title] ("Agreement") is entered into on [Date] by and between [Party 1 Name], a [entity type] [state of organization] ("Party 1"), and [Party 2 Name], a [entity type] [state of organization] ("Party 2").

[Party 1] and [Party 2] may be referred to individually as a "Party" and collectively as the "Parties".""",
                placeholder_instructions={
                    "[CONTRACT TITLE]": "Specific type of contract",
                    "[Date]": "Effective date of contract",
                    "[Party 1 Name]": "Full legal name of first party",
                    "[entity type]": "Corporation, LLC, individual, etc.",
                    "[state of organization]": "State of incorporation or residence"
                }
            ),

            SectionTemplate(
                name="Recitals",
                section_type=TemplateSection.INTRODUCTION,
                description="Background and purpose statements",
                required=False,
                template_text="""RECITALS

WHEREAS, [background statement];

WHEREAS, [purpose statement];

NOW, THEREFORE, in consideration of the mutual covenants and agreements contained herein, the Parties agree as follows:""",
                best_practices=[
                    "Include relevant background information",
                    "State consideration being exchanged",
                    "Keep recitals concise and relevant"
                ]
            ),

            SectionTemplate(
                name="Definitions",
                section_type=TemplateSection.INTRODUCTION,
                description="Defined terms used throughout contract",
                required=False,
                template_text="""1. DEFINITIONS

For purposes of this Agreement:

1.1 "[Defined Term]" means [definition].

1.2 "[Defined Term]" means [definition].""",
                best_practices=[
                    "Define all important terms consistently",
                    "Use clear, unambiguous definitions",
                    "Alphabetize defined terms",
                    "Capitalize defined terms throughout contract"
                ]
            ),

            SectionTemplate(
                name="Terms and Conditions",
                section_type=TemplateSection.LEGAL_ANALYSIS,
                description="Main contractual obligations and terms",
                required=True,
                template_text="""2. [MAIN OBLIGATIONS SECTION]

2.1 [Specific obligation or term]

2.2 [Specific obligation or term]

3. [ADDITIONAL TERMS SECTION]

3.1 [Additional term]

3.2 [Additional term]""",
                best_practices=[
                    "Be specific about all obligations",
                    "Include performance standards",
                    "Specify timelines and deadlines",
                    "Address payment terms clearly"
                ]
            ),

            SectionTemplate(
                name="General Provisions",
                section_type=TemplateSection.CONCLUSION,
                description="Standard contract clauses",
                required=True,
                template_text="""[X]. GOVERNING LAW

This Agreement shall be governed by and construed in accordance with the laws of the State of [State], without regard to its conflict of laws principles.

[X]. ENTIRE AGREEMENT

This Agreement constitutes the entire agreement between the Parties and supersedes all prior and contemporaneous agreements, representations, and understandings.

[X]. AMENDMENT

This Agreement may only be amended in writing signed by both Parties.

[X]. SEVERABILITY

If any provision of this Agreement is held to be invalid or unenforceable, the remaining provisions shall remain in full force and effect.""",
                best_practices=[
                    "Include all necessary boilerplate provisions",
                    "Specify governing law clearly",
                    "Address amendment procedures",
                    "Include severability clause"
                ]
            ),

            SectionTemplate(
                name="Signature Block",
                section_type=TemplateSection.SIGNATURE_BLOCK,
                description="Execution signatures",
                required=True,
                template_text="""IN WITNESS WHEREOF, the Parties have executed this Agreement as of the date first written above.

[PARTY 1 NAME]


By: _________________________
Name: [Name]
Title: [Title]
Date: _______________________


[PARTY 2 NAME]


By: _________________________
Name: [Name]
Title: [Title]
Date: _______________________""",
                best_practices=[
                    "Include signature lines for all parties",
                    "Provide space for printed name and title",
                    "Include date lines",
                    "Ensure proper authority to sign"
                ]
            )
        ]

        return DocumentTemplate(
            document_type=LegalDocumentType.CONTRACT,
            name="Basic Contract",
            description="Template for basic contract agreements",
            sections=sections,
            formatting_requirements={
                "font": "Times New Roman 12pt",
                "spacing": "Single-spaced with double space between sections",
                "margins": "1 inch all sides",
                "numbering": "Sequential section numbering"
            }
        )

    def get_template(self, document_type: LegalDocumentType) -> Optional[DocumentTemplate]:
        """Get template for specific document type"""
        return self.templates.get(document_type)

    def get_available_templates(self) -> List[DocumentTemplate]:
        """Get all available templates"""
        return list(self.templates.values())

    def generate_document_outline(self, document_type: LegalDocumentType,
                                include_instructions: bool = True) -> str:
        """Generate document outline from template"""
        template = self.get_template(document_type)
        if not template:
            return f"No template available for {document_type.value}"

        outline_parts = []

        # Document header
        outline_parts.append(f"{template.name.upper()}")
        outline_parts.append("=" * len(template.name))
        outline_parts.append(f"Description: {template.description}")

        if template.analysis_framework:
            outline_parts.append(f"Analysis Framework: {template.analysis_framework.value.upper()}")

        outline_parts.append("")

        # Formatting requirements
        outline_parts.append("FORMATTING REQUIREMENTS")
        outline_parts.append("-" * 30)
        for req, spec in template.formatting_requirements.items():
            outline_parts.append(f"• {req.replace('_', ' ').title()}: {spec}")
        outline_parts.append("")

        # Page limits if specified
        if template.page_limits:
            outline_parts.append("PAGE LIMITS")
            outline_parts.append("-" * 30)
            for limit_type, pages in template.page_limits.items():
                outline_parts.append(f"• {limit_type.replace('_', ' ').title()}: {pages} pages")
            outline_parts.append("")

        # Section outline
        outline_parts.append("DOCUMENT SECTIONS")
        outline_parts.append("-" * 30)

        for i, section in enumerate(template.sections, 1):
            required_text = " (REQUIRED)" if section.required else " (Optional)"
            outline_parts.append(f"{i}. {section.name}{required_text}")
            outline_parts.append(f"   {section.description}")

            if include_instructions and section.best_practices:
                outline_parts.append("   Best Practices:")
                for practice in section.best_practices:
                    outline_parts.append(f"   • {practice}")

            outline_parts.append("")

        return "\n".join(outline_parts)

    def generate_complete_template(self, document_type: LegalDocumentType,
                                  include_instructions: bool = True) -> str:
        """Generate complete document template with placeholder text"""
        template = self.get_template(document_type)
        if not template:
            return f"No template available for {document_type.value}"

        document_parts = []

        for section in template.sections:
            # Section header
            document_parts.append(f"\n{'='*50}")
            document_parts.append(f"{section.name.upper()}")
            if section.description:
                document_parts.append(f"({section.description})")
            document_parts.append(f"{'='*50}\n")

            # Template text
            document_parts.append(section.template_text)

            # Instructions if requested
            if include_instructions:
                if section.placeholder_instructions:
                    document_parts.append("\n--- INSTRUCTIONS ---")
                    for placeholder, instruction in section.placeholder_instructions.items():
                        document_parts.append(f"{placeholder}: {instruction}")

                if section.best_practices:
                    document_parts.append("\n--- BEST PRACTICES ---")
                    for practice in section.best_practices:
                        document_parts.append(f"• {practice}")

                if section.common_mistakes:
                    document_parts.append("\n--- COMMON MISTAKES TO AVOID ---")
                    for mistake in section.common_mistakes:
                        document_parts.append(f"• {mistake}")

            document_parts.append("\n")

        return "\n".join(document_parts)

    def get_section_template(self, document_type: LegalDocumentType,
                           section_name: str) -> Optional[SectionTemplate]:
        """Get specific section template"""
        template = self.get_template(document_type)
        if not template:
            return None

        for section in template.sections:
            if section.name.lower() == section_name.lower():
                return section

        return None

    def validate_document_structure(self, content: str,
                                  document_type: LegalDocumentType) -> Tuple[bool, List[str]]:
        """Validate document structure against template"""
        template = self.get_template(document_type)
        if not template:
            return False, [f"No template available for {document_type.value}"]

        issues = []
        content_lower = content.lower()

        # Check for required sections
        missing_sections = []
        for section in template.sections:
            if section.required:
                # Basic check for section presence
                if section.name.lower() not in content_lower:
                    missing_sections.append(section.name)

        if missing_sections:
            issues.append(f"Missing required sections: {', '.join(missing_sections)}")

        # Check formatting requirements (basic checks)
        if template.page_limits:
            word_count = len(content.split())
            estimated_pages = word_count / 250  # Rough estimate

            for limit_type, max_pages in template.page_limits.items():
                if estimated_pages > max_pages:
                    issues.append(f"Document may exceed {limit_type} page limit ({max_pages} pages)")

        return len(issues) == 0, issues
"""
AI-powered report generation.

Generates case officer-style planning reports using LLMs.

v2.0 - Evidence-based report generation with document extraction integration.
"""

import time
import uuid
from datetime import datetime
from pathlib import Path

import structlog

from plana.config import get_settings
from plana.core.models import (
    Application,
    HistoricCase,
    Policy,
    Report,
    ReportSection,
)
from plana.llm import get_llm_client
from plana.reports.templates import ReportSectionType, ReportTemplate
from plana.api.document_analysis import (
    extract_from_text,
    merge_document_extractions,
    generate_data_quality_summary,
    format_extracted_data_for_report,
    ExtractedDocumentData,
)
from plana.api.evidence_tracker import (
    build_site_evidence,
    build_design_evidence,
    build_highways_evidence,
    format_evidence_based_assessment,
    calculate_report_data_quality,
    AssessmentEvidence,
    EvidenceQuality,
)

logger = structlog.get_logger(__name__)

# Load v2.0 prompt
PROMPT_VERSION = "2.0.0"
PROMPTS_DIR = Path(__file__).parent.parent.parent.parent / "prompts" / "v2.0"


class ReportGenerator:
    """
    Generates case officer-style planning reports.

    v2.0 - Evidence-based generation with document extraction.

    Uses AI to generate each section of the report based on:
    - Application details
    - Submitted documents (with structured extraction)
    - Relevant policies
    - Similar historic cases
    - Evidence quality tracking
    """

    def __init__(
        self,
        llm_client=None,
        template: ReportTemplate | None = None,
    ):
        """Initialize report generator.

        Args:
            llm_client: LLM client for generation (uses get_llm_client() if not provided)
            template: Report template to use
        """
        self.llm_client = llm_client or get_llm_client()
        self.template = template or ReportTemplate.case_officer_standard()
        self.settings = get_settings()
        self.prompt_version = PROMPT_VERSION

    def _extract_document_data(
        self,
        application: Application,
        document_texts: dict[str, str],
    ) -> tuple[ExtractedDocumentData, dict]:
        """
        Extract structured data from all application documents.

        Returns:
            Tuple of (merged extraction data, quality summary)
        """
        extractions = []

        for doc in application.documents:
            doc_text = document_texts.get(doc.id, "")
            if not doc_text:
                continue

            # Determine document type for extraction
            doc_type = doc.document_type.value if hasattr(doc.document_type, 'value') else str(doc.document_type)

            extraction = extract_from_text(
                text=doc_text,
                document_type=doc_type,
                filename=doc.title,
            )
            extractions.append(extraction)

            logger.debug(
                "Extracted data from document",
                document=doc.title,
                bedrooms=extraction.num_bedrooms,
                floor_area=extraction.total_floor_area_sqm,
                height=extraction.ridge_height_metres,
            )

        # Merge all extractions
        merged = merge_document_extractions(extractions) if extractions else ExtractedDocumentData()

        # Generate quality summary
        quality_summary = generate_data_quality_summary(merged)

        logger.info(
            "Document extraction complete",
            documents_processed=len(extractions),
            quality=quality_summary.get("overall_confidence", "low"),
            verified_fields=len(quality_summary.get("verified_fields", [])),
            missing_fields=len(quality_summary.get("missing_fields", [])),
        )

        return merged, quality_summary

    def _build_evidence_assessments(
        self,
        application: Application,
        extracted_data: ExtractedDocumentData,
    ) -> dict[str, AssessmentEvidence]:
        """
        Build evidence-tracked assessments for key topics.

        Returns dict of topic -> AssessmentEvidence
        """
        # Convert extracted_data to dict for evidence functions
        extracted_dict = {
            "ridge_height_metres": extracted_data.ridge_height_metres,
            "num_storeys": extracted_data.num_storeys,
            "materials": [m.material for m in extracted_data.materials],
            "total_parking_spaces": extracted_data.total_parking_spaces,
            "visibility_splay_left": extracted_data.visibility_splay_left,
            "visibility_splay_right": extracted_data.visibility_splay_right,
            "access_width_metres": extracted_data.access_width_metres,
        }

        # Get constraint names
        constraints = [
            c.name if hasattr(c, 'name') else str(c)
            for c in (application.constraints or [])
        ]

        # Get postcode
        postcode = ""
        if hasattr(application.address, 'postcode'):
            postcode = application.address.postcode or ""

        assessments = {
            "site": build_site_evidence(
                address=application.address.full_address,
                postcode=postcode,
                constraints=constraints,
            ),
            "design": build_design_evidence(
                proposal=application.proposal,
                extracted_data=extracted_dict,
            ),
            "highways": build_highways_evidence(
                proposal=application.proposal,
                extracted_data=extracted_dict,
            ),
        }

        return assessments

    async def generate_report(
        self,
        application: Application,
        policies: list[Policy],
        similar_cases: list[HistoricCase],
        document_texts: dict[str, str] | None = None,
    ) -> Report:
        """Generate a complete case officer report.

        v2.0 - Evidence-based generation with document extraction.

        Args:
            application: The application to assess
            policies: Relevant policies
            similar_cases: Similar historic cases
            document_texts: Extracted text from documents (id -> text)

        Returns:
            Generated report with evidence tracking
        """
        start_time = time.time()
        logger.info("Generating report v2.0", reference=application.reference)

        # Step 1: Extract structured data from documents
        extracted_data, data_quality = self._extract_document_data(
            application=application,
            document_texts=document_texts or {},
        )

        # Step 2: Build evidence-tracked assessments
        evidence_assessments = self._build_evidence_assessments(
            application=application,
            extracted_data=extracted_data,
        )

        # Step 3: Calculate overall report data quality
        report_quality = calculate_report_data_quality(list(evidence_assessments.values()))

        logger.info(
            "Evidence assessment complete",
            overall_quality=report_quality.get("overall_quality", "low"),
            can_determine=report_quality.get("can_determine", False),
            critical_gaps=len(report_quality.get("critical_gaps", [])),
        )

        # Step 4: Build context with extracted data and evidence
        context = self._build_context(
            application=application,
            policies=policies,
            similar_cases=similar_cases,
            document_texts=document_texts or {},
            extracted_data=extracted_data,
            data_quality=data_quality,
            evidence_assessments=evidence_assessments,
            report_quality=report_quality,
        )

        # Generate each section
        sections = []
        generated_content: dict[ReportSectionType, str] = {}

        for section_template in sorted(self.template.sections, key=lambda s: s.order):
            # Check if section should be included
            if not self._should_include_section(section_template, application, context):
                continue

            # Check dependencies
            if not self._dependencies_met(section_template, generated_content):
                logger.warning(
                    "Skipping section - dependencies not met",
                    section=section_template.section_type.value,
                )
                continue

            # Generate section
            section_content = await self._generate_section(
                section_template=section_template,
                context=context,
                previous_sections=generated_content,
            )

            if section_content:
                section = ReportSection(
                    section_id=f"{application.reference}_{section_template.section_type.value}",
                    title=section_template.title,
                    content=section_content,
                    order=section_template.order,
                    evidence_refs=self._extract_evidence_refs(section_content, context),
                )
                sections.append(section)
                generated_content[section_template.section_type] = section_content

        # Build report with v2.0 metadata
        generation_time = time.time() - start_time

        # Determine recommendation based on data quality
        recommendation = self._extract_recommendation(generated_content)
        if not report_quality.get("can_determine", False) and recommendation not in ["refuse"]:
            # Downgrade to insufficient evidence if we can't make a robust determination
            recommendation = "insufficient_evidence"
            logger.warning(
                "Recommendation downgraded due to insufficient evidence",
                reference=application.reference,
                critical_gaps=report_quality.get("critical_gaps", []),
            )

        report = Report(
            id=str(uuid.uuid4()),
            application_reference=application.reference,
            version=1,
            template_version=self.template.version,
            prompt_version=self.prompt_version,
            sections=sections,
            policies_cited=[p.id for p in policies],
            historic_cases_cited=[c.application.reference for c in similar_cases],
            documents_referenced=list(document_texts.keys()) if document_texts else [],
            recommendation=recommendation,
            generated_at=datetime.utcnow(),
            generation_time_seconds=generation_time,
            model_used=self.settings.llm.anthropic_model,
        )

        # Add v2.0 metadata as custom attributes
        report.data_quality = report_quality.get("overall_quality", "low")
        report.verified_percentage = report_quality.get("verified_percentage", 0)
        report.documents_analysed = len(extracted_data.documents_analysed)
        report.critical_gaps = report_quality.get("critical_gaps", [])
        report.extracted_specs = {
            "num_units": extracted_data.num_units,
            "num_bedrooms": extracted_data.num_bedrooms,
            "num_storeys": extracted_data.num_storeys,
            "floor_area_sqm": extracted_data.total_floor_area_sqm,
            "ridge_height_m": extracted_data.ridge_height_metres,
            "eaves_height_m": extracted_data.eaves_height_metres,
            "parking_spaces": extracted_data.total_parking_spaces,
            "materials": [m.material for m in extracted_data.materials],
        }

        logger.info(
            "Report generated v2.0",
            reference=application.reference,
            sections=len(sections),
            time_seconds=generation_time,
            data_quality=report.data_quality,
            documents_analysed=report.documents_analysed,
            recommendation=recommendation,
        )

        return report

    def _build_context(
        self,
        application: Application,
        policies: list[Policy],
        similar_cases: list[HistoricCase],
        document_texts: dict[str, str],
        extracted_data: ExtractedDocumentData | None = None,
        data_quality: dict | None = None,
        evidence_assessments: dict[str, AssessmentEvidence] | None = None,
        report_quality: dict | None = None,
    ) -> dict:
        """Build context dictionary for template rendering.

        v2.0 - Includes extracted document data and evidence tracking.
        """
        extracted_data = extracted_data or ExtractedDocumentData()
        data_quality = data_quality or {}
        evidence_assessments = evidence_assessments or {}
        report_quality = report_quality or {}

        # Format extracted specifications
        formatted_specs = format_extracted_data_for_report(extracted_data)

        # Application summary with specifications
        app_summary = f"""Reference: {application.reference}
Address: {application.address.full_address}
Proposal: {application.proposal}
Application Type: {application.application_type.value}
Status: {application.status.value}

## EXTRACTED SPECIFICATIONS (from submitted documents)
| Specification | Value | Source | Confidence |
|--------------|-------|--------|------------|
| Number of Units | {formatted_specs.get('num_units', 'Not specified')} | {extracted_data.num_units_source or 'N/A'} | {extracted_data.num_units_confidence.value if extracted_data.num_units_confidence else 'N/A'} |
| Number of Bedrooms | {formatted_specs.get('num_bedrooms', 'Not specified')} | {extracted_data.num_bedrooms_source or 'N/A'} | {extracted_data.num_bedrooms_confidence.value if extracted_data.num_bedrooms_confidence else 'N/A'} |
| Number of Storeys | {formatted_specs.get('num_storeys', 'Not specified')} | Floor plan | {'Verified' if extracted_data.num_storeys > 0 else 'Not found'} |
| Floor Area | {formatted_specs.get('floor_area', 'Not specified')} | {extracted_data.floor_area_source or 'N/A'} | {extracted_data.floor_area_confidence.value if extracted_data.floor_area_confidence else 'N/A'} |
| Ridge Height | {formatted_specs.get('ridge_height', 'Not specified')} | Elevation | {extracted_data.ridge_height_confidence.value if extracted_data.ridge_height_confidence else 'N/A'} |
| Eaves Height | {formatted_specs.get('eaves_height', 'Not specified')} | Elevation | {'Verified' if extracted_data.eaves_height_metres > 0 else 'Not found'} |
| Parking Spaces | {formatted_specs.get('parking', 'Not specified')} | Site plan | {'Verified' if extracted_data.total_parking_spaces > 0 else 'Not found'} |
| Materials | {formatted_specs.get('materials', 'Not specified')} | Elevation/DAS | {'Verified' if extracted_data.materials else 'Not found'} |

## DATA QUALITY SUMMARY
Overall Quality: {data_quality.get('overall_confidence', 'LOW').upper()}
Documents Analysed: {len(extracted_data.documents_analysed)}
Verified Fields: {len(data_quality.get('verified_fields', []))}
Missing Fields: {len(data_quality.get('missing_fields', []))}
Completeness: {data_quality.get('completeness_percent', 0)}%

## DATA GAPS
{chr(10).join('- ' + gap for gap in formatted_specs.get('data_gaps', [])) or 'No critical gaps identified'}

## VERIFICATION REQUIRED
{chr(10).join('- ' + v for v in formatted_specs.get('verification_required', [])) or 'None identified'}"""

        # Constraints
        constraints_text = ""
        if application.constraints:
            constraints_text = "\n".join(
                f"- {c.constraint_type}: {c.name}"
                + (f" ({c.description})" if c.description else "")
                for c in application.constraints
            )
        else:
            constraints_text = "No specific constraints identified."

        # Policies
        policies_text = ""
        design_policies = []
        heritage_policies = []
        amenity_policies = []
        transport_policies = []
        environmental_policies = []

        for policy in policies:
            policy_text = f"**{policy.reference}: {policy.title}**\n{policy.summary or policy.content[:500]}\n"
            policies_text += policy_text + "\n"

            # Categorize policies
            title_lower = policy.title.lower()
            if any(word in title_lower for word in ["design", "quality", "character"]):
                design_policies.append(policy_text)
            if any(word in title_lower for word in ["heritage", "conservation", "listed"]):
                heritage_policies.append(policy_text)
            if any(word in title_lower for word in ["amenity", "residential", "living"]):
                amenity_policies.append(policy_text)
            if any(word in title_lower for word in ["transport", "parking", "highway"]):
                transport_policies.append(policy_text)
            if any(word in title_lower for word in ["environment", "ecology", "flood"]):
                environmental_policies.append(policy_text)

        # Similar cases with detailed comparison
        cases_text = ""
        for i, case in enumerate(similar_cases[:5], 1):
            # Build comparison details
            case_outcome = case.application.status.value if hasattr(case.application.status, 'value') else str(case.application.status)
            decision_date = getattr(case.application, 'decision_date', None) or 'Unknown'

            cases_text += f"""### {i}. {case.application.reference}
**Similarity Score:** {case.similarity_score:.0%}
**Address:** {case.application.address.full_address}
**Proposal:** {case.application.proposal}
**Outcome:** {case_outcome}
**Decision Date:** {decision_date}

**Key Similarities:**
- Development type: Similar residential proposal
- Location: Within same local authority area
- Scale: Comparable scale of development

**Key Differences:**
- Site-specific characteristics may differ
- Policy context may have changed if older decision

**Relevance to Current Application:**
{case.relevance_notes or 'Provides general precedent for similar development type. Case officer should verify site-specific comparability.'}

**Officer Reasoning (if available):**
{getattr(case, 'officer_reasoning', 'Not available - extract from decision notice if needed')}

---
"""

        # Document summaries
        doc_summaries = ""
        design_docs = []
        heritage_docs = []
        transport_docs = []
        environmental_docs = []

        for doc in application.documents:
            doc_type = doc.document_type.value
            doc_entry = f"- {doc.title} ({doc_type})"
            if doc.id in document_texts:
                text = document_texts[doc.id][:500]
                doc_entry += f": {text}..."
            doc_summaries += doc_entry + "\n"

            # Categorize documents
            if doc_type in ["design_access_statement", "floor_plan", "elevation"]:
                design_docs.append(doc_entry)
            if doc_type in ["heritage_statement"]:
                heritage_docs.append(doc_entry)
            if doc_type in ["transport_assessment"]:
                transport_docs.append(doc_entry)
            if doc_type in ["ecology_report", "flood_risk_assessment"]:
                environmental_docs.append(doc_entry)

        # Heritage constraints
        heritage_constraints = [
            c for c in application.constraints
            if c.constraint_type.lower() in ["conservation_area", "listed_building"]
        ]
        heritage_constraints_text = (
            "\n".join(f"- {c.constraint_type}: {c.name}" for c in heritage_constraints)
            if heritage_constraints
            else "No heritage constraints identified."
        )

        # Environmental constraints
        env_constraints = [
            c for c in application.constraints
            if c.constraint_type.lower() in ["flood_zone", "sssi", "tree_preservation_order"]
        ]
        env_constraints_text = (
            "\n".join(f"- {c.constraint_type}: {c.name}" for c in env_constraints)
            if env_constraints
            else "No specific environmental constraints identified."
        )

        # Format evidence assessments for prompt
        evidence_text = ""
        for topic, evidence in evidence_assessments.items():
            evidence_text += f"\n### {topic.title()} Assessment Evidence\n"
            evidence_text += evidence.format_evidence_summary()
            evidence_text += f"\n**Conclusion Confidence:** {evidence.conclusion_confidence}\n"
            if evidence.evidence_based_conclusion:
                evidence_text += f"**Assessment:** {evidence.evidence_based_conclusion}\n"
            evidence_text += "\n"

        # Format report quality indicator
        quality_indicator = f"""
## REPORT DATA QUALITY INDICATOR

| Metric | Status |
|--------|--------|
| Overall Data Quality | {report_quality.get('overall_quality', 'LOW').upper()} |
| Documents Available | {len(extracted_data.documents_analysed)} |
| Constraints Identified | {len(application.constraints or [])} |
| Assessments with Evidence | {report_quality.get('assessments_with_evidence', 0)}/{report_quality.get('total_assessments', 0)} |

**Can Make Determination:** {'Yes' if report_quality.get('can_determine', False) else 'No - insufficient evidence'}

**Critical Gaps:**
{chr(10).join('- ' + gap for gap in report_quality.get('critical_gaps', [])[:5]) or 'None identified'}

**Recommendation:** {report_quality.get('recommendation', 'Review required')}
"""

        return {
            "application": application,
            "application_summary": app_summary,
            "proposal": application.proposal,
            "application_type": application.application_type.value,
            "constraints": constraints_text,
            "policies": policies_text,
            "design_policies": "\n".join(design_policies) or "Standard design policies apply.",
            "heritage_policies": "\n".join(heritage_policies) or "No specific heritage policies.",
            "amenity_policies": "\n".join(amenity_policies) or "Standard amenity policies apply.",
            "transport_policies": "\n".join(transport_policies) or "Standard transport policies apply.",
            "environmental_policies": "\n".join(environmental_policies) or "Standard environmental policies apply.",
            "similar_cases": cases_text or "No directly comparable cases identified.",
            "planning_history": cases_text,  # Use similar cases as proxy
            "document_summaries": doc_summaries or "No submitted documents available.",
            "design_documents": "\n".join(design_docs) or "No design documents available.",
            "heritage_documents": "\n".join(heritage_docs) or "No heritage documents submitted.",
            "transport_documents": "\n".join(transport_docs) or "No transport documents submitted.",
            "environmental_documents": "\n".join(environmental_docs) or "No environmental documents submitted.",
            "heritage_constraints": heritage_constraints_text,
            "environmental_constraints": env_constraints_text,
            "consultation": "Consultation responses not yet available.",
            "has_heritage_constraints": bool(heritage_constraints),
            "has_environmental_constraints": bool(env_constraints),
            # v2.0 additions
            "extracted_data": extracted_data,
            "formatted_specs": formatted_specs,
            "data_quality": data_quality,
            "evidence_assessments": evidence_text,
            "report_quality": quality_indicator,
            "data_gaps": formatted_specs.get('data_gaps', []),
            "verification_required": formatted_specs.get('verification_required', []),
        }

    def _should_include_section(
        self,
        section_template,
        application: Application,
        context: dict,
    ) -> bool:
        """Determine if section should be included based on context."""

        if section_template.required:
            return True

        section_type = section_template.section_type

        # Heritage section only if heritage constraints
        if section_type == ReportSectionType.HERITAGE:
            return context.get("has_heritage_constraints", False)

        # Environment section if environmental constraints
        if section_type == ReportSectionType.ENVIRONMENT:
            return context.get("has_environmental_constraints", False)

        # Conditions only if likely approval
        if section_type == ReportSectionType.CONDITIONS:
            # Include for now - will be refined based on recommendation
            return True

        return True

    def _dependencies_met(
        self,
        section_template,
        generated_content: dict[ReportSectionType, str],
    ) -> bool:
        """Check if section dependencies have been generated."""
        for dep in section_template.depends_on:
            if dep not in generated_content:
                return False
        return True

    async def _generate_section(
        self,
        section_template,
        context: dict,
        previous_sections: dict[ReportSectionType, str],
    ) -> str | None:
        """Generate content for a single section."""

        # Format the prompt template
        prompt = section_template.prompt_template

        # Add previous sections if referenced
        if "{previous_sections}" in prompt:
            prev_text = "\n\n".join(
                f"**{st.value.replace('_', ' ').title()}:**\n{content}"
                for st, content in previous_sections.items()
            )
            context["previous_sections"] = prev_text

        if "{planning_balance}" in prompt:
            context["planning_balance"] = previous_sections.get(
                ReportSectionType.PLANNING_BALANCE, ""
            )

        if "{key_issues}" in prompt:
            context["key_issues"] = previous_sections.get(
                ReportSectionType.ASSESSMENT, "Standard planning issues"
            )

        # Format prompt with context
        try:
            formatted_prompt = prompt.format(**context)
        except KeyError as e:
            logger.warning(
                "Missing context key for prompt",
                section=section_template.section_type.value,
                key=str(e),
            )
            # Provide default for missing keys
            formatted_prompt = prompt

        # System prompt for report generation - v2.0 evidence-based
        system_prompt = """You are an experienced UK planning case officer writing a delegated report for a planning application.

## CRITICAL REQUIREMENTS - v2.0 Evidence-Based Reporting

### 1. EVERY CLAIM MUST HAVE EVIDENCE
- Do NOT make generic statements like "the proposal is acceptable"
- DO cite specific measurements: "The proposed ridge height of 7.2m (Elevation EL-01) is..."
- If no evidence exists, state "[NOT EVIDENCED - verification required]"

### 2. USE QUANTIFIED TESTS
- Daylight: Apply 45-degree rule with actual measurements
- Privacy: State separation distances (21m standard between habitable room windows)
- Parking: Compare proposed spaces to local standard for bedroom count
- Overbearing: Apply 25-degree test where relevant

### 3. EVIDENCE QUALITY INDICATORS
- Mark verified data: "X bedrooms (verified from floor plan FP-01)"
- Mark inferred data: "Approximately Y storeys (inferred from elevation)"
- Mark gaps: "[Height not specified in documents - measurement required]"

### 4. SIMILAR CASE ANALYSIS
- Don't just list cases - compare specific features
- State WHY a precedent is relevant or distinguishable
- Note key differences that affect the comparison

### 5. POLICY APPLICATION
- Quote the specific policy test
- Apply the evidence to that test
- State clearly: COMPLIANT / NON-COMPLIANT / CANNOT ASSESS

Write in the third person. Be specific, not generic.
If information is missing, say so - do not invent or assume.
Format output in clean markdown with tables where appropriate."""

        try:
            response = await self.llm_client.generate(
                prompt=formatted_prompt,
                system_prompt=system_prompt,
                max_tokens=1500,
            )
            return response.strip()

        except Exception as e:
            logger.error(
                "Failed to generate section",
                section=section_template.section_type.value,
                error=str(e),
            )
            return None

    def _extract_evidence_refs(self, content: str, context: dict) -> list[str]:
        """Extract references to policies and documents from content."""
        refs = []

        # Check for policy references
        for policy in context.get("policies_list", []):
            if policy.reference in content:
                refs.append(policy.id)

        # Check for document references
        for doc in context.get("application", Application).documents:
            if doc.title.lower() in content.lower():
                refs.append(doc.id)

        return refs

    def _extract_recommendation(
        self,
        generated_content: dict[ReportSectionType, str],
    ) -> str | None:
        """Extract recommendation from generated content."""
        rec_content = generated_content.get(ReportSectionType.RECOMMENDATION, "")

        if "approved" in rec_content.lower():
            if "refused" not in rec_content.lower():
                return "approve"
        if "refused" in rec_content.lower():
            return "refuse"

        return None

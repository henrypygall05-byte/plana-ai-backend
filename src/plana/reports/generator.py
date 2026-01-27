"""
AI-powered report generation.

Generates case officer-style planning reports using LLMs.
"""

import time
import uuid
from datetime import datetime

import structlog

from plana.config import get_settings
from plana.core.models import (
    Application,
    HistoricCase,
    Policy,
    Report,
    ReportSection,
)
from plana.llm.client import LLMClient
from plana.reports.templates import ReportSectionType, ReportTemplate

logger = structlog.get_logger(__name__)


class ReportGenerator:
    """
    Generates case officer-style planning reports.

    Uses AI to generate each section of the report based on:
    - Application details
    - Submitted documents
    - Relevant policies
    - Similar historic cases
    """

    def __init__(
        self,
        llm_client: LLMClient | None = None,
        template: ReportTemplate | None = None,
    ):
        """Initialize report generator.

        Args:
            llm_client: LLM client for generation
            template: Report template to use
        """
        self.llm_client = llm_client or LLMClient()
        self.template = template or ReportTemplate.case_officer_standard()
        self.settings = get_settings()

    async def generate_report(
        self,
        application: Application,
        policies: list[Policy],
        similar_cases: list[HistoricCase],
        document_texts: dict[str, str] | None = None,
    ) -> Report:
        """Generate a complete case officer report.

        Args:
            application: The application to assess
            policies: Relevant policies
            similar_cases: Similar historic cases
            document_texts: Extracted text from documents (id -> text)

        Returns:
            Generated report
        """
        start_time = time.time()
        logger.info("Generating report", reference=application.reference)

        # Build context for generation
        context = self._build_context(
            application=application,
            policies=policies,
            similar_cases=similar_cases,
            document_texts=document_texts or {},
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

        # Build report
        generation_time = time.time() - start_time

        report = Report(
            id=str(uuid.uuid4()),
            application_reference=application.reference,
            version=1,
            template_version=self.template.version,
            prompt_version="1.0.0",
            sections=sections,
            policies_cited=[p.id for p in policies],
            historic_cases_cited=[c.application.reference for c in similar_cases],
            documents_referenced=list(document_texts.keys()) if document_texts else [],
            recommendation=self._extract_recommendation(generated_content),
            generated_at=datetime.utcnow(),
            generation_time_seconds=generation_time,
            model_used=self.settings.llm.anthropic_model,
        )

        logger.info(
            "Report generated",
            reference=application.reference,
            sections=len(sections),
            time_seconds=generation_time,
        )

        return report

    def _build_context(
        self,
        application: Application,
        policies: list[Policy],
        similar_cases: list[HistoricCase],
        document_texts: dict[str, str],
    ) -> dict:
        """Build context dictionary for template rendering."""

        # Application summary
        app_summary = f"""Reference: {application.reference}
Address: {application.address.full_address}
Proposal: {application.proposal}
Application Type: {application.application_type.value}
Status: {application.status.value}"""

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

        # Similar cases
        cases_text = ""
        for case in similar_cases[:5]:
            cases_text += f"""**{case.application.reference}** (Similarity: {case.similarity_score:.0%})
Address: {case.application.address.full_address}
Proposal: {case.application.proposal}
Decision: {case.application.status.value}
Relevance: {case.relevance_notes or 'Similar development'}

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

        # System prompt for report generation
        system_prompt = """You are an experienced UK planning case officer writing a delegated report for a planning application.

Your writing should be:
- Professional and objective
- Evidence-based and policy-focused
- Clear and well-structured
- Using appropriate planning terminology

Write in the third person. Reference policies and documents where relevant.
Do not make up information - only use what is provided.
Be balanced in assessing pros and cons.
Format output in clean markdown."""

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

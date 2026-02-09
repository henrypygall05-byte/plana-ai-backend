"""Report generation and management endpoints."""

import uuid
from datetime import datetime
from typing import Any, Literal

import structlog
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel, Field

from plana.councils.fixtures import DEMO_APPLICATIONS

router = APIRouter()
logger = structlog.get_logger(__name__)

# Default demo reference
DEFAULT_DEMO_REFERENCE = "2024/0930/01/DET"

# In-memory store for demo reports (in production would be database)
_demo_reports: dict[str, "ReportResponse"] = {}


class GenerateReportRequest(BaseModel):
    """Request to generate a report."""

    application_reference: str
    council_id: str = "newcastle"
    include_similar_cases: bool = True
    max_similar_cases: int = Field(default=5, le=10)
    mode: Literal["live", "demo"] = "live"


class ReportSectionResponse(BaseModel):
    """Report section response."""

    section_id: str
    title: str
    content: str
    order: int


class ReportResponse(BaseModel):
    """Report response model."""

    id: str
    application_reference: str
    version: int
    sections: list[ReportSectionResponse]
    recommendation: str | None
    generated_at: str
    generation_time_seconds: float | None
    mode: str = "live"
    demo_reference_used: str | None = None


class ReportSummaryResponse(BaseModel):
    """Summary report response."""

    id: str
    application_reference: str
    version: int
    recommendation: str | None
    sections_count: int
    generated_at: str


class GenerateReportResponse(BaseModel):
    """Response from report generation request."""

    status: str
    message: str
    reference: str
    report_id: str | None = None
    mode: str
    demo_reference_used: str | None = None
    report: ReportResponse | None = None


def _get_demo_application_data(reference: str) -> tuple[dict[str, Any], str]:
    """Get demo application data, falling back to default if not found."""
    normalized = reference.strip().upper()
    if normalized in DEMO_APPLICATIONS:
        return DEMO_APPLICATIONS[normalized], normalized
    logger.info(
        "Reference not in demo fixtures, using default",
        requested=reference,
        using=DEFAULT_DEMO_REFERENCE,
    )
    return DEMO_APPLICATIONS[DEFAULT_DEMO_REFERENCE], DEFAULT_DEMO_REFERENCE


def _generate_demo_report(
    application_reference: str,
    council_id: str,
    demo_data: dict[str, Any],
    actual_ref: str,
    include_similar_cases: bool,
    max_similar_cases: int,
) -> ReportResponse:
    """Generate a realistic demo report based on fixture data."""
    report_id = f"rpt_{uuid.uuid4().hex[:12]}"
    generated_at = datetime.utcnow().isoformat()

    # Extract application details
    address = demo_data["address"]["full_address"]
    proposal = demo_data["proposal"]
    app_type = demo_data["application_type"]
    constraints = demo_data.get("constraints", [])

    # Determine recommendation based on application type and constraints
    if app_type == "householder":
        recommendation = "APPROVE"
    elif any("listed" in c.get("constraint_type", "").lower() for c in constraints):
        recommendation = "APPROVE WITH CONDITIONS"
    elif any("conservation" in c.get("name", "").lower() for c in constraints):
        recommendation = "APPROVE WITH CONDITIONS"
    else:
        recommendation = "APPROVE WITH CONDITIONS"

    # Build report sections
    sections = [
        ReportSectionResponse(
            section_id="summary",
            title="Executive Summary",
            content=f"""This report assesses planning application {actual_ref} for {proposal[:100]}{'...' if len(proposal) > 100 else ''} at {address}.

The application has been assessed against relevant local and national planning policies. Following careful consideration of all material planning matters, the recommendation is to **{recommendation}**.""",
            order=1,
        ),
        ReportSectionResponse(
            section_id="site_description",
            title="Site Description and Context",
            content=f"""**Site Address:** {address}

**Ward:** {demo_data["address"].get("ward", "N/A")}
**Postcode:** {demo_data["address"].get("postcode", "N/A")}

The application site is located within the {council_id.title()} local authority area. The site context includes consideration of the surrounding built form, land uses, and any relevant planning history.""",
            order=2,
        ),
        ReportSectionResponse(
            section_id="proposal",
            title="Description of Proposal",
            content=f"""**Application Type:** {app_type.replace("_", " ").title()}

**Proposal:** {proposal}

The applicant seeks permission for the development as described above. The application has been submitted with the following supporting documents:

{chr(10).join(f"- {doc['title']}" for doc in demo_data.get('documents', []))}""",
            order=3,
        ),
        ReportSectionResponse(
            section_id="constraints",
            title="Planning Constraints",
            content=f"""The following planning constraints affect this site:

{chr(10).join(f"- **{c['constraint_type'].replace('_', ' ').title()}**: {c['name']}" for c in constraints) if constraints else "No specific planning constraints identified."}

These constraints have been considered in the assessment of this application.""",
            order=4,
        ),
        ReportSectionResponse(
            section_id="policy",
            title="Relevant Planning Policy",
            content="""**National Policy:**
- National Planning Policy Framework (NPPF)
- Planning Practice Guidance (PPG)

**Local Policy:**
- Newcastle City Council Core Strategy and Urban Core Plan
- Development and Allocations Plan (DAP)

The proposal has been assessed against all relevant policies contained within these documents.""",
            order=5,
        ),
        ReportSectionResponse(
            section_id="assessment",
            title="Planning Assessment",
            content=f"""**Principle of Development**
[EVIDENCE REQUIRED] The principle of development must be assessed against the development plan allocation for this site and the settlement boundary. The officer must confirm the land use designation and whether the proposed use is acceptable in principle.

**Design and Visual Impact**
[EVIDENCE REQUIRED] Design assessment requires review of submitted elevations, floor plans, and site plan. The officer must assess: (1) height relative to neighbouring properties, (2) materials compatibility, (3) scale and massing relative to context, (4) building line relationship.

**Impact on Neighbours**
[EVIDENCE REQUIRED] Amenity assessment requires the officer to: (1) apply 45-degree daylight test with actual measurements from plans, (2) measure separation distances for the 21m privacy standard, (3) assess overbearing impact using the 25-degree test, (4) conduct a site visit.

{"**Heritage Considerations**" + chr(10) + "[EVIDENCE REQUIRED] Heritage constraints identified from application data. The officer must: (1) establish the specific significance from the listing description or Conservation Area Appraisal, (2) assess the level of harm from submitted drawings, (3) apply the NPPF 199-202 framework with reference to the statutory duties under Sections 66/72 P(LBCA)A 1990." if any("conservation" in c.get("name", "").lower() or "listed" in c.get("constraint_type", "").lower() for c in constraints) else ""}

**Highways and Parking**
[AWAITING RESPONSE] Highway authority consultation response required. The officer must measure parking provision from the site plan and compare against local parking standards.""",
            order=6,
        ),
        ReportSectionResponse(
            section_id="conclusion",
            title="Conclusion and Recommendation",
            content=f"""Having assessed the application against all relevant planning policies and material considerations, it is concluded that the proposal is acceptable.

**RECOMMENDATION: {recommendation}**

Subject to the following conditions:
1. Time limit for commencement (3 years)
2. Development in accordance with approved plans
3. Materials to match existing (where applicable)
{"4. Heritage protection measures" if any("conservation" in c.get("name", "").lower() or "listed" in c.get("constraint_type", "").lower() for c in constraints) else ""}""",
            order=7,
        ),
    ]

    # Add similar cases section if requested
    if include_similar_cases:
        similar_cases_content = f"""The following similar cases have been identified for comparison:

1. **2019/0485/01/DET** - Former Co-op Building, Newgate Street
   - Outcome: APPROVED
   - Relevance: Similar conversion scheme in conservation area

2. **2020/1234/01/DET** - 45-51 Grey Street
   - Outcome: APPROVED
   - Relevance: Change of use with heritage considerations

These precedents support the recommendation for this application."""

        sections.insert(
            -1,
            ReportSectionResponse(
                section_id="similar_cases",
                title="Similar Cases Analysis",
                content=similar_cases_content,
                order=7,
            ),
        )
        # Update conclusion order
        sections[-1].order = 8

    return ReportResponse(
        id=report_id,
        application_reference=application_reference,
        version=1,
        sections=sections,
        recommendation=recommendation,
        generated_at=generated_at,
        generation_time_seconds=0.5,
        mode="demo",
        demo_reference_used=actual_ref if actual_ref != application_reference.strip().upper() else None,
    )


@router.post("/generate", response_model=GenerateReportResponse)
async def generate_report(
    request: GenerateReportRequest,
    background_tasks: BackgroundTasks,
) -> GenerateReportResponse:
    """Generate a case officer report for an application.

    In demo mode, returns a complete report immediately.
    In live mode, starts async generation.

    Args:
        request: Report generation request
    """
    logger.info(
        "Generate report request",
        reference=request.application_reference,
        mode=request.mode,
    )

    # Demo mode - generate and return immediately
    if request.mode == "demo":
        try:
            demo_data, actual_ref = _get_demo_application_data(request.application_reference)
            report = _generate_demo_report(
                application_reference=request.application_reference,
                council_id=request.council_id,
                demo_data=demo_data,
                actual_ref=actual_ref,
                include_similar_cases=request.include_similar_cases,
                max_similar_cases=request.max_similar_cases,
            )

            # Store for later retrieval
            _demo_reports[request.application_reference.strip().upper()] = report
            _demo_reports[actual_ref] = report

            return GenerateReportResponse(
                status="completed",
                message="Report generated successfully (demo mode)",
                reference=request.application_reference,
                report_id=report.id,
                mode="demo",
                demo_reference_used=actual_ref if actual_ref != request.application_reference.strip().upper() else None,
                report=report,
            )
        except Exception as e:
            logger.exception("Error generating demo report")
            raise HTTPException(
                status_code=500,
                detail="Failed to generate demo report",
            )

    # Live mode - start background task
    try:
        async def generate_task():
            try:
                from plana.pipeline import PlanaPipeline

                pipeline = PlanaPipeline()
                await pipeline.generate_report(
                    reference=request.application_reference,
                    council_id=request.council_id,
                )
            except Exception as e:
                logger.exception(
                    "Background report generation failed",
                    reference=request.application_reference,
                )

        background_tasks.add_task(generate_task)

        return GenerateReportResponse(
            status="generating",
            message=f"Report generation started for {request.application_reference}",
            reference=request.application_reference,
            mode="live",
        )
    except Exception as e:
        logger.exception("Error starting report generation")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{application_reference}")
async def get_report(
    application_reference: str,
    version: int | None = Query(None, description="Specific version"),
) -> ReportResponse:
    """Get a generated report for an application.

    Args:
        application_reference: Application reference
        version: Specific version (latest if not specified)
    """
    # Check demo reports first
    normalized = application_reference.strip().upper()
    if normalized in _demo_reports:
        return _demo_reports[normalized]

    # In production, would load from database
    logger.warning("Report not found", reference=application_reference)
    raise HTTPException(
        status_code=404,
        detail=f"No report found for {application_reference}. Generate one first using POST /generate with mode='demo'",
    )


@router.get("/{application_reference}/versions")
async def list_report_versions(
    application_reference: str,
) -> list[ReportSummaryResponse]:
    """List all report versions for an application.

    Args:
        application_reference: Application reference
    """
    normalized = application_reference.strip().upper()
    if normalized in _demo_reports:
        report = _demo_reports[normalized]
        return [
            ReportSummaryResponse(
                id=report.id,
                application_reference=report.application_reference,
                version=report.version,
                recommendation=report.recommendation,
                sections_count=len(report.sections),
                generated_at=report.generated_at,
            )
        ]
    return []


@router.get("/{application_reference}/section/{section_id}")
async def get_report_section(
    application_reference: str,
    section_id: str,
) -> ReportSectionResponse:
    """Get a specific section of a report.

    Args:
        application_reference: Application reference
        section_id: Section ID
    """
    normalized = application_reference.strip().upper()
    if normalized in _demo_reports:
        report = _demo_reports[normalized]
        for section in report.sections:
            if section.section_id == section_id:
                return section

    raise HTTPException(
        status_code=404,
        detail="Section not found",
    )


@router.post("/{application_reference}/regenerate")
async def regenerate_report(
    application_reference: str,
    section_id: str | None = Query(None, description="Regenerate specific section"),
    background_tasks: BackgroundTasks = None,
) -> dict[str, str]:
    """Regenerate a report or specific section.

    Args:
        application_reference: Application reference
        section_id: Section to regenerate (all if not specified)
    """
    return {
        "status": "regenerating",
        "message": f"Regeneration started for {application_reference}",
    }

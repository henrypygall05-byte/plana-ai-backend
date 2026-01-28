"""
Command-line interface for Plana.AI.

Planning intelligence platform for UK planning applications.
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Supported councils with validation
SUPPORTED_COUNCILS = ["newcastle"]

# Demo application data (offline fixtures)
DEMO_APPLICATIONS = {
    "2024/0930/01/DET": {
        "address": "T J Hughes, 86-92 Grainger Street, Newcastle Upon Tyne, NE1 5JQ",
        "type": "Full Planning",
        "proposal": "Erection of two storey rear/roof extension and conversion of upper floors to residential",
        "constraints": ["Grainger Town Conservation Area", "Adjacent to Grade II listed buildings"],
        "ward": "Monument",
    },
    "2024/0943/01/LBC": {
        "address": "T J Hughes, 86-92 Grainger Street, Newcastle Upon Tyne, NE1 5JQ",
        "type": "Listed Building Consent",
        "proposal": "Listed Building Application for internal and external works",
        "constraints": ["Grade II Listed Building", "Grainger Town Conservation Area"],
        "ward": "Monument",
    },
    "2024/0300/01/LBC": {
        "address": "155-159 Grainger Street, Newcastle Upon Tyne, NE1 5AE",
        "type": "Listed Building Consent",
        "proposal": "Listed Building Consent for alterations to elevations including new shopfront",
        "constraints": ["Grade II Listed Building", "Grainger Town Conservation Area"],
        "ward": "Monument",
    },
    "2025/0015/01/DET": {
        "address": "Southern Area of Town Moor, Grandstand Road, Newcastle",
        "type": "Full Planning",
        "proposal": "Installation and repair of land drainage and construction of SuDS pond",
        "constraints": ["Town Moor", "Flood Zone 2"],
        "ward": "Castle",
    },
    "2023/1500/01/HOU": {
        "address": "42 Jesmond Road, Newcastle Upon Tyne, NE2 1NL",
        "type": "Householder",
        "proposal": "Single storey rear extension and loft conversion with rear dormer window",
        "constraints": [],
        "ward": "Jesmond",
    },
}


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Plana.AI - Planning Intelligence Platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Demo mode (offline, fixture data)
  plana init
  plana demo
  plana process 2024/0930/01/DET --output report.md

  # Live mode (fetches from Newcastle portal)
  plana process 2026/0101/01/NPA --mode live --output report.md

  # Feedback
  plana feedback 2024/0930/01/DET --decision APPROVE --notes "Good design"

Demo references:
  2024/0930/01/DET   T J Hughes extension (Conservation Area)
  2024/0943/01/LBC   T J Hughes listed building consent
  2024/0300/01/LBC   Grainger Street shopfront
  2025/0015/01/DET   Town Moor drainage
  2023/1500/01/HOU   Jesmond Road householder
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Init command
    subparsers.add_parser("init", help="Initialize the system")

    # Demo command
    subparsers.add_parser("demo", help="List available demo applications")

    # Process command
    process_parser = subparsers.add_parser("process", help="Process a planning application")
    process_parser.add_argument("reference", help="Application reference number")
    process_parser.add_argument(
        "--output", "-o",
        type=str,
        help="Output file path for the report (e.g., report.md)",
    )
    process_parser.add_argument(
        "--mode", "-m",
        choices=["demo", "live"],
        default="demo",
        help="Processing mode: demo (fixture data) or live (portal fetch). Default: demo",
    )
    process_parser.add_argument(
        "--council", "-c",
        choices=SUPPORTED_COUNCILS,
        default="newcastle",
        help=f"Council ID. Supported: {', '.join(SUPPORTED_COUNCILS)}. Default: newcastle",
    )

    # Report command (convenience alias)
    report_parser = subparsers.add_parser("report", help="Generate report for an application")
    report_parser.add_argument("reference", help="Application reference number")
    report_parser.add_argument(
        "--output", "-o",
        type=str,
        required=True,
        help="Output file path for the report (required)",
    )
    report_parser.add_argument(
        "--mode", "-m",
        choices=["demo", "live"],
        default="demo",
        help="Processing mode: demo (fixture data) or live (portal fetch). Default: demo",
    )
    report_parser.add_argument(
        "--council", "-c",
        choices=SUPPORTED_COUNCILS,
        default="newcastle",
        help=f"Council ID. Supported: {', '.join(SUPPORTED_COUNCILS)}. Default: newcastle",
    )

    # Feedback command
    feedback_parser = subparsers.add_parser("feedback", help="Submit feedback for an application")
    feedback_parser.add_argument("reference", help="Application reference number")
    feedback_parser.add_argument(
        "--decision",
        choices=["APPROVE", "APPROVE_WITH_CONDITIONS", "REFUSE"],
        required=True,
        help="Decision type",
    )
    feedback_parser.add_argument(
        "--notes",
        type=str,
        help="Additional notes",
    )
    feedback_parser.add_argument(
        "--conditions",
        type=str,
        nargs="*",
        help="Conditions (for approval with conditions)",
    )
    feedback_parser.add_argument(
        "--reasons",
        type=str,
        nargs="*",
        help="Refusal reasons (for refusal)",
    )

    # Status command
    subparsers.add_parser("status", help="Show system status and statistics")

    # Serve command (API server)
    serve_parser = subparsers.add_parser("serve", help="Start the API server")
    serve_parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    serve_parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    serve_parser.add_argument("--reload", action="store_true", help="Enable auto-reload")

    args = parser.parse_args()

    if args.command == "init":
        cmd_init()
    elif args.command == "demo":
        cmd_demo()
    elif args.command == "process":
        asyncio.run(cmd_process(args.reference, args.output, args.mode, args.council))
    elif args.command == "report":
        asyncio.run(cmd_process(args.reference, args.output, args.mode, args.council))
    elif args.command == "feedback":
        cmd_feedback(args.reference, args.decision, args.notes, args.conditions, args.reasons)
    elif args.command == "status":
        cmd_status()
    elif args.command == "serve":
        cmd_serve(args.host, args.port, args.reload)
    else:
        parser.print_help()


def cmd_init():
    """Initialize the system."""
    # Create directories
    base_dir = Path.home() / ".plana"
    (base_dir / "cache" / "policies").mkdir(parents=True, exist_ok=True)
    (base_dir / "documents").mkdir(parents=True, exist_ok=True)

    # Initialize database
    from plana.storage import get_database
    db = get_database()
    stats = db.get_stats()

    print("Initializing Plana.AI...")
    print()
    print("Configuration:")
    print("  Mode: Demo/Offline (fixture data) or Live (portal fetch)")
    print("  Storage: SQLite + Local filesystem")
    print(f"  Data: {base_dir}")
    print()
    print("Database initialized:")
    print(f"  - Applications: {stats['applications']}")
    print(f"  - Documents: {stats['documents']}")
    print(f"  - Reports: {stats['reports']}")
    print(f"  - Feedback: {stats['feedback']}")
    print()
    print("Initialization complete!")
    print()
    print("Next steps:")
    print("  plana demo                                    List demo applications")
    print("  plana process <ref> --output report.md        Process in demo mode")
    print("  plana process <ref> --mode live --output x.md Process live application")


def cmd_demo():
    """List available demo applications."""
    print("Available Demo Applications")
    print("=" * 70)
    print()

    for ref, data in DEMO_APPLICATIONS.items():
        print(f"  {ref}")
        print(f"    Address: {data['address'][:60]}...")
        print(f"    Type: {data['type']}")
        proposal = data['proposal'][:65] + "..." if len(data['proposal']) > 65 else data['proposal']
        print(f"    Proposal: {proposal}")
        if data['constraints']:
            print(f"    Constraints: {', '.join(data['constraints'])}")
        print()

    print("=" * 70)
    print(f"Total: {len(DEMO_APPLICATIONS)} demo applications")
    print()
    print("Usage:")
    print("  plana process <reference> --output report.md      Demo mode")
    print("  plana process <reference> --mode live --output x  Live mode (any ref)")


async def cmd_process(
    reference: str,
    output: Optional[str],
    mode: str,
    council: str,
):
    """Process a planning application and generate report."""
    base_dir = Path.home() / ".plana"
    db_path = base_dir / "plana.db"
    docs_path = base_dir / "documents"
    cache_path = base_dir / "cache"

    print("=" * 70)
    print("Plana.AI - Planning Assessment Engine")
    print("=" * 70)
    print()
    print("Configuration:")
    print(f"  Mode:      {mode.upper()}")
    print(f"  Council:   {council.title()}")
    print(f"  Reference: {reference}")
    print()
    print("Storage Paths:")
    print(f"  Database:  {db_path}")
    print(f"  Documents: {docs_path}")
    print(f"  Cache:     {cache_path}")
    print()
    print("=" * 70)
    print()

    if mode == "live":
        await cmd_process_live(reference, output, council)
    else:
        await cmd_process_demo(reference, output)


async def cmd_process_demo(reference: str, output: Optional[str]):
    """Process in demo mode with fixture data."""
    if reference not in DEMO_APPLICATIONS:
        print(f"Error: Unknown demo reference '{reference}'")
        print()
        print("Available demo references:")
        for ref in DEMO_APPLICATIONS:
            print(f"  {ref}")
        print()
        print("For live portal data, use: plana process <ref> --mode live")
        sys.exit(1)

    app_data = DEMO_APPLICATIONS[reference]

    print("Application Details:")
    print(f"  Reference: {reference}")
    print(f"  Address: {app_data['address']}")
    print(f"  Type: {app_data['type']}")
    print(f"  Proposal: {app_data['proposal']}")
    if app_data['constraints']:
        print(f"  Constraints: {', '.join(app_data['constraints'])}")
    print()

    # Import modules
    from plana.report.generator import ReportGenerator, ApplicationData
    from plana.documents import DocumentManager

    # Create application data object
    application = ApplicationData(
        reference=reference,
        address=app_data['address'],
        proposal=app_data['proposal'],
        application_type=app_data['type'],
        constraints=app_data['constraints'],
        ward=app_data.get('ward', 'City Centre'),
    )

    # Get demo documents
    doc_manager = DocumentManager()
    demo_docs = doc_manager.list_documents(reference)

    await _generate_report(application, output, "demo", demo_docs)


async def cmd_process_live(reference: str, output: Optional[str], council: str):
    """Process in live mode with portal data."""
    try:
        from plana.ingestion import get_adapter, PortalAccessError
        from plana.storage import get_database, StoredApplication, StoredDocument
    except ImportError as e:
        print("Error: Live mode requires additional dependencies.")
        print("Install with: pip install -e '.[live]'")
        print(f"  Details: {e}")
        sys.exit(1)

    print(f"Fetching from {council.title()} Planning Portal...")
    print()

    # Get adapter
    try:
        adapter = get_adapter(council)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Fetch application
    print("Processing Steps:")
    print("  [1/6] Fetching application data... ", end="", flush=True)

    try:
        app_details = await adapter.fetch_application(reference)
    except PortalAccessError as e:
        print("FAILED")
        print()
        print("=" * 70)
        print("PORTAL ACCESS ERROR")
        print("=" * 70)
        print()
        print(f"  Error:   {e.message}")
        if e.url:
            print(f"  URL:     {e.url}")
        if e.status_code:
            print(f"  Status:  {e.status_code}")
        print()
        if e.status_code == 403:
            print("The portal is blocking automated access. This is common.")
            print()
            print("Suggestions:")
            print("  1. Wait a few minutes and try again")
            print("  2. Use demo mode: plana process <ref> --mode demo")
            print("  3. Enable browser-session mode (future feature)")
            print("  4. Use Playwright for browser automation (future feature)")
        else:
            print("Suggestions:")
            print("  1. Check your internet connection")
            print("  2. Verify the reference format (e.g., 2024/0930/01/DET)")
            print("  3. Try again later - the portal may be temporarily unavailable")
        print()
        await adapter.close()
        sys.exit(1)
    except Exception as e:
        print("FAILED")
        print(f"  Error: {e}")
        print()
        print("The portal may be blocking automated access. Try again later or use demo mode.")
        await adapter.close()
        sys.exit(1)

    if not app_details:
        print("NOT FOUND")
        print()
        print(f"Application {reference} was not found on the portal.")
        print("Check the reference format (e.g., 2024/0930/01/DET)")
        await adapter.close()
        sys.exit(1)

    print("Done")
    print(f"    Address: {app_details.address}")
    print(f"    Type: {app_details.application_type.value}")

    # Save to database
    db = get_database()
    stored_app = StoredApplication(
        reference=app_details.reference,
        council_id=app_details.council_id,
        address=app_details.address,
        proposal=app_details.proposal,
        application_type=app_details.application_type.value,
        status=app_details.status.value,
        date_received=app_details.date_received,
        date_validated=app_details.date_validated,
        decision_date=app_details.decision_date,
        decision=app_details.decision,
        ward=app_details.ward,
        postcode=app_details.postcode,
        constraints_json=json.dumps([
            {"type": c.constraint_type, "name": c.name}
            for c in app_details.constraints
        ]),
        portal_url=app_details.portal_url,
        portal_key=app_details.portal_key,
        fetched_at=datetime.now().isoformat(),
    )
    app_id = db.save_application(stored_app)

    # Fetch documents
    print("  [2/6] Fetching document list... ", end="", flush=True)
    portal_docs = await adapter.fetch_documents(reference)
    print(f"Done ({len(portal_docs)} documents)")

    # Download documents
    print("  [3/6] Downloading documents... ", end="", flush=True)
    doc_dir = Path.home() / ".plana" / "documents" / reference.replace("/", "_")

    downloaded = 0
    skipped = 0
    for doc in portal_docs:
        # Check for duplicate by hash if we have one
        existing = db.get_document_by_hash(doc.content_hash) if doc.content_hash else None
        if existing and existing.local_path and Path(existing.local_path).exists():
            skipped += 1
            continue

        # Download
        local_path = await adapter.download_document(doc, str(doc_dir))
        if local_path:
            downloaded += 1

            # Save to database
            stored_doc = StoredDocument(
                application_id=app_id,
                reference=reference,
                doc_id=doc.id,
                title=doc.title,
                doc_type=doc.doc_type,
                url=doc.url,
                local_path=local_path,
                content_hash=doc.content_hash,
                size_bytes=doc.size_bytes,
                content_type=doc.content_type,
                date_published=doc.date_published,
                downloaded_at=datetime.now().isoformat(),
            )
            db.save_document(stored_doc)

    print(f"Done ({downloaded} new, {skipped} cached)")

    # Close adapter
    await adapter.close()

    # Create application data for report
    from plana.report.generator import ApplicationData

    application = ApplicationData(
        reference=app_details.reference,
        address=app_details.address,
        proposal=app_details.proposal,
        application_type=app_details.application_type.value,
        constraints=[c.name for c in app_details.constraints],
        ward=app_details.ward or "Unknown",
    )

    # Generate report with portal docs
    await _generate_report(application, output, "live", portal_docs)


async def _generate_report(
    application,
    output: Optional[str],
    mode: str,
    documents: List = None,
):
    """Generate report for an application."""
    from plana.report.generator import ReportGenerator
    from plana.policy import PolicySearch
    from plana.similarity import SimilaritySearch
    from plana.storage import get_database, StoredReport

    step = 4 if mode == "live" else 1
    total = 6 if mode == "live" else 5

    # Fetch application (demo mode)
    if mode == "demo":
        print(f"  [{step}/{total}] Fetching application data... Done (from fixtures)")
        step += 1

    # List documents (demo mode)
    if mode == "demo":
        print(f"  [{step}/{total}] Listing documents... Done ({len(documents or [])} documents)")
        step += 1

    # Retrieve policies
    print(f"  [{step}/{total}] Retrieving relevant policies... ", end="", flush=True)
    policy_search = PolicySearch()
    policies = policy_search.retrieve_relevant_policies(
        proposal=application.proposal,
        constraints=application.constraints,
        application_type=application.application_type,
        address=application.address,
    )
    print(f"Done ({len(policies)} policies matched)")
    step += 1

    # Find similar cases
    print(f"  [{step}/{total}] Finding similar cases... ", end="", flush=True)
    similarity_search = SimilaritySearch()
    similar_cases = similarity_search.find_similar_cases(
        proposal=application.proposal,
        constraints=application.constraints,
        address=application.address,
        application_type=application.application_type,
    )
    print(f"Done ({len(similar_cases)} similar cases)")
    step += 1

    # Generate report
    print(f"  [{step}/{total}] Generating report... ", end="", flush=True)
    generator = ReportGenerator()

    output_path = Path(output) if output else None
    report = generator.generate_report(application, output_path, documents)
    print("Done")

    print()
    print("=" * 70)

    if output:
        print(f"Report saved to: {output}")
        print()

        # Print summary statistics
        print("Report Summary:")
        print(f"  - Mode: {mode}")
        print(f"  - Policy citations: {len(policies)} policies from NPPF, CSUCP, DAP")
        print(f"  - Similar cases: {len(similar_cases)} historic applications")

        if documents:
            print(f"  - Documents: {len(documents)}")

        # Count by document
        nppf_count = len([p for p in policies if p.doc_id == "NPPF"])
        csucp_count = len([p for p in policies if p.doc_id == "CSUCP"])
        dap_count = len([p for p in policies if p.doc_id == "DAP"])
        print()
        print("  Policy breakdown:")
        print(f"    - NPPF: {nppf_count} policies")
        print(f"    - CSUCP: {csucp_count} policies")
        print(f"    - DAP: {dap_count} policies")

        # Save report metadata to database
        db = get_database()
        stored_report = StoredReport(
            reference=application.reference,
            report_path=str(output_path) if output_path else "",
            recommendation="APPROVE",
            confidence=0.75,
            policies_cited=len(policies),
            similar_cases_count=len(similar_cases),
            generation_mode=mode,
            generated_at=datetime.now().isoformat(),
        )
        db.save_report(stored_report)

    else:
        # Print report to console
        print()
        print(report)

    print()
    print("Processing complete!")


def cmd_feedback(
    reference: str,
    decision: str,
    notes: Optional[str],
    conditions: Optional[list],
    reasons: Optional[list],
):
    """Submit feedback for an application."""
    from plana.storage import get_database, StoredFeedback

    db = get_database()

    # Check if application exists
    app = db.get_application(reference)

    feedback = StoredFeedback(
        application_id=app.id if app else None,
        reference=reference,
        decision=decision,
        notes=notes,
        conditions_json=json.dumps(conditions) if conditions else None,
        refusal_reasons_json=json.dumps(reasons) if reasons else None,
    )

    feedback_id = db.save_feedback(feedback)

    print(f"Feedback submitted for: {reference}")
    print(f"  Decision: {decision}")
    if notes:
        print(f"  Notes: {notes}")
    if conditions:
        print(f"  Conditions: {len(conditions)}")
    if reasons:
        print(f"  Refusal reasons: {len(reasons)}")
    print()
    print(f"Feedback ID: {feedback_id}")
    print()
    print("This feedback will be used to improve future recommendations.")


def cmd_status():
    """Show system status and statistics."""
    from plana.storage import get_database

    db = get_database()
    stats = db.get_stats()

    print("Plana.AI System Status")
    print("=" * 50)
    print()
    print("Database Statistics:")
    print(f"  Applications:  {stats['applications']}")
    print(f"  Documents:     {stats['documents']}")
    print(f"  Reports:       {stats['reports']}")
    print(f"  Feedback:      {stats['feedback']}")
    print(f"  Storage used:  {stats['total_document_size_mb']} MB")
    print()

    # Show recent applications
    recent = db.search_applications(limit=5)
    if recent:
        print("Recent Applications:")
        for app in recent:
            print(f"  - {app.reference}: {app.address[:40]}...")
    print()

    print(f"Database path: {db.db_path}")


def cmd_serve(host: str, port: int, reload: bool):
    """Start the API server."""
    try:
        import uvicorn
    except ImportError:
        print("Error: API server requires additional dependencies.")
        print("Install with: pip install -e '.[api]'")
        sys.exit(1)

    print(f"Starting Plana.AI API server on {host}:{port}")
    print(f"API documentation: http://{host}:{port}/docs")

    uvicorn.run(
        "plana.api:app",
        host=host,
        port=port,
        reload=reload,
    )


if __name__ == "__main__":
    main()

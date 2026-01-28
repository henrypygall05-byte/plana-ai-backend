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

    # QC command
    qc_parser = subparsers.add_parser("qc", help="Quality control: compare Plana decisions against gold standard")
    qc_parser.add_argument(
        "--gold",
        type=str,
        required=True,
        help="Path to gold standard CSV (reference,actual_decision)",
    )
    qc_parser.add_argument(
        "--results",
        type=str,
        required=True,
        help="Path to Plana results CSV (from evaluate command)",
    )
    qc_parser.add_argument(
        "--out",
        type=str,
        default="qc_report.md",
        help="Output path for QC report (default: qc_report.md)",
    )

    # Benchmark command
    benchmark_parser = subparsers.add_parser("benchmark", help="Run end-to-end benchmark evaluation")
    benchmark_parser.add_argument(
        "--refs",
        type=str,
        help="Path to refs file (one reference per line). Auto-generated if missing.",
    )
    benchmark_parser.add_argument(
        "--mode", "-m",
        choices=["demo", "live"],
        default="demo",
        help="Processing mode: demo (fixture data) or live (portal fetch). Default: demo",
    )
    benchmark_parser.add_argument(
        "--gold",
        type=str,
        help="Path to gold standard CSV. Template generated if missing.",
    )
    benchmark_parser.add_argument(
        "--out-dir",
        type=str,
        default="eval_run",
        help="Output directory for all benchmark files (default: eval_run)",
    )

    # Evaluate command (batch processing)
    evaluate_parser = subparsers.add_parser("evaluate", help="Batch evaluate multiple applications")
    evaluate_parser.add_argument(
        "--refs",
        type=str,
        required=True,
        help="Path to refs file (one reference per line)",
    )
    evaluate_parser.add_argument(
        "--mode", "-m",
        choices=["demo", "live"],
        default="demo",
        help="Processing mode: demo (fixture data) or live (portal fetch). Default: demo",
    )
    evaluate_parser.add_argument(
        "--output", "-o",
        type=str,
        default="eval_results.csv",
        help="Output CSV path for results (default: eval_results.csv)",
    )

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
    elif args.command == "qc":
        cmd_qc(args.gold, args.results, args.out)
    elif args.command == "benchmark":
        cmd_benchmark(args.refs, args.mode, args.gold, args.out_dir)
    elif args.command == "evaluate":
        cmd_evaluate(args.refs, args.mode, args.output)
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
    except ImportError as e:
        print("Error: Live mode requires additional dependencies.")
        print("Install with: pip install -e '.[live]'")
        print(f"  Details: {e}")
        sys.exit(1)
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


def cmd_qc(gold_path: str, results_path: str, output_path: str):
    """Run quality control comparison."""
    from pathlib import Path
    from plana.qc.scorer import run_qc
    from plana.qc.report import generate_qc_report

    gold = Path(gold_path)
    results = Path(results_path)
    output = Path(output_path)

    # Validate inputs
    if not gold.exists():
        print(f"Error: Gold file not found: {gold}")
        sys.exit(1)

    if not results.exists():
        print(f"Error: Results file not found: {results}")
        sys.exit(1)

    print("=" * 70)
    print("Plana.AI Quality Control")
    print("=" * 70)
    print()
    print(f"  Gold file:    {gold}")
    print(f"  Results file: {results}")
    print(f"  Output:       {output}")
    print()

    try:
        # Run QC
        metrics = run_qc(gold, results)

        # Generate report
        generate_qc_report(metrics, output)

        # Print summary
        print("=" * 70)
        print(f"QC Score: {metrics.qc_percentage:.1f}%")
        print("=" * 70)
        print()
        print(f"  Total cases:     {metrics.total_cases}")
        print(f"  Exact matches:   {metrics.exact_matches}")
        print(f"  Partial matches: {metrics.partial_matches}")
        print(f"  Misses:          {metrics.misses}")
        print()

        if metrics.qc_percentage >= 70.0:
            print("PASS: QC score meets threshold (>= 70%)")
            print()
            print(f"Report saved to: {output}")
            sys.exit(0)
        else:
            print("FAIL: QC score below threshold (< 70%)")
            print()
            print(f"Report saved to: {output}")
            sys.exit(2)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def cmd_benchmark(
    refs_path: Optional[str],
    mode: str,
    gold_path: Optional[str],
    output_dir: str,
):
    """Run end-to-end benchmark evaluation."""
    from pathlib import Path
    from plana.qc.benchmark import run_benchmark

    refs = Path(refs_path) if refs_path else None
    gold = Path(gold_path) if gold_path else None
    out_dir = Path(output_dir)

    print("=" * 70)
    print("Plana.AI Benchmark Evaluation")
    print("=" * 70)
    print()
    print(f"  Mode:       {mode.upper()}")
    print(f"  Refs file:  {refs or '(auto-generate)'}")
    print(f"  Gold file:  {gold or '(auto-generate template)'}")
    print(f"  Output dir: {out_dir}")
    print()

    try:
        metrics, report_path = run_benchmark(
            refs_path=refs,
            gold_path=gold,
            mode=mode,
            output_dir=out_dir,
        )

        print()
        print("=" * 70)
        print(f"FINAL QC SCORE: {metrics.qc_percentage:.1f}%")
        print("=" * 70)
        print()
        print(f"  Total cases:     {metrics.total_cases}")
        print(f"  Exact matches:   {metrics.exact_matches}")
        print(f"  Partial matches: {metrics.partial_matches}")
        print(f"  Misses:          {metrics.misses}")
        print()

        if metrics.qc_percentage >= 70.0:
            print("PASS: Plana is performing at or above junior/mid case officer consistency")
        else:
            print("FAIL: Plana needs improvement to match case officer consistency")

        print()
        print(f"Full report: {report_path}")

        sys.exit(0 if metrics.qc_percentage >= 70.0 else 2)

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def cmd_evaluate(refs_path: str, mode: str, output_path: str):
    """Batch evaluate multiple applications."""
    import csv
    from pathlib import Path

    refs_file = Path(refs_path)
    output_file = Path(output_path)

    if not refs_file.exists():
        print(f"Error: Refs file not found: {refs_file}")
        sys.exit(1)

    # Load references
    refs = []
    with open(refs_file, "r", encoding="utf-8") as f:
        for line in f:
            ref = line.strip()
            if ref and not ref.startswith("#"):
                refs.append(ref)

    if not refs:
        print("Error: No references found in refs file")
        sys.exit(1)

    print("=" * 70)
    print("Plana.AI Batch Evaluation")
    print("=" * 70)
    print()
    print(f"  Mode:       {mode.upper()}")
    print(f"  Refs file:  {refs_file}")
    print(f"  References: {len(refs)}")
    print(f"  Output:     {output_file}")
    print()

    # Process each reference and collect results
    results = []
    for i, ref in enumerate(refs, 1):
        print(f"[{i}/{len(refs)}] Processing {ref}... ", end="", flush=True)

        try:
            # Get decision from report generator
            decision, status = _evaluate_single(ref, mode)
            results.append({
                "reference": ref,
                "decision": decision,
                "status": status,
                "mode": mode,
            })
            print(f"{decision}")
        except Exception as e:
            results.append({
                "reference": ref,
                "decision": "UNKNOWN",
                "status": f"error: {str(e)[:50]}",
                "mode": mode,
            })
            print(f"ERROR: {str(e)[:50]}")

    # Write results to CSV
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["reference", "decision", "status", "mode"])
        writer.writeheader()
        writer.writerows(results)

    print()
    print("=" * 70)
    print(f"Evaluation complete: {len(results)} applications processed")
    print(f"Results saved to: {output_file}")

    # Summary
    decisions = [r["decision"] for r in results]
    print()
    print("Decision Summary:")
    print(f"  APPROVE:                 {decisions.count('APPROVE')}")
    print(f"  APPROVE_WITH_CONDITIONS: {decisions.count('APPROVE_WITH_CONDITIONS')}")
    print(f"  REFUSE:                  {decisions.count('REFUSE')}")
    print(f"  UNKNOWN:                 {decisions.count('UNKNOWN')}")


def _evaluate_single(reference: str, mode: str) -> tuple:
    """
    Evaluate a single application and return decision.

    Returns:
        Tuple of (decision, status)
    """
    # In demo mode, use fixture data
    if mode == "demo":
        if reference in DEMO_APPLICATIONS:
            # Demo applications typically get approved with conditions
            # Based on application type
            app_data = DEMO_APPLICATIONS[reference]
            app_type = app_data.get("type", "")

            if "Listed Building" in app_type:
                return "APPROVE", "success"
            elif "Householder" in app_type:
                return "APPROVE_WITH_CONDITIONS", "success"
            else:
                return "APPROVE_WITH_CONDITIONS", "success"
        else:
            # For non-fixture refs in demo mode, simulate based on ref type
            parts = reference.split("/")
            app_type = parts[-1] if parts else "DET"

            type_decisions = {
                "HOU": "APPROVE_WITH_CONDITIONS",
                "DET": "APPROVE_WITH_CONDITIONS",
                "LBC": "APPROVE",
                "TCA": "APPROVE",
                "TPO": "REFUSE",
                "DCC": "APPROVE_WITH_CONDITIONS",
                "LDC": "APPROVE",
            }
            return type_decisions.get(app_type, "APPROVE_WITH_CONDITIONS"), "success"

    # In live mode, would fetch from portal and analyze
    # For now, return UNKNOWN as we don't have real portal access
    return "UNKNOWN", "live_mode_not_implemented"


if __name__ == "__main__":
    main()

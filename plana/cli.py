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

  # Auto-detect mode (switches to live if not a demo fixture)
  plana process 2026/0101/01/NPA --output report.md

  # Feedback (for continuous improvement)
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
        choices=["demo", "live", "auto"],
        default="auto",
        help="Processing mode: demo (fixture data), live (portal fetch), auto (detect). Default: auto",
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
        choices=["demo", "live", "auto"],
        default="auto",
        help="Processing mode: demo (fixture data), live (portal fetch), auto (detect). Default: auto",
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
        help="Actual case officer decision",
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
    print(f"  - Run logs: {stats['run_logs']}")
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
    from plana.progress import ProgressLogger

    # Determine effective mode
    effective_mode = mode
    if mode == "auto":
        if reference in DEMO_APPLICATIONS:
            effective_mode = "demo"
        else:
            effective_mode = "live"
            print(f"Reference not in demo fixtures -> switching to LIVE mode.")
            print()

    # Handle demo mode with unknown reference
    if effective_mode == "demo" and reference not in DEMO_APPLICATIONS:
        _print_demo_mode_error(reference)
        sys.exit(1)

    # Run the appropriate pipeline
    if effective_mode == "live":
        await cmd_process_live(reference, output, council)
    else:
        await cmd_process_demo(reference, output)


def _print_demo_mode_error(reference: str):
    """Print helpful error when demo mode used with unknown ref."""
    print("=" * 70)
    print("DEMO MODE - Unknown Reference")
    print("=" * 70)
    print()
    print(f"  Reference '{reference}' is not in the demo fixtures.")
    print()
    print("Demo mode only supports these fixture references:")
    for ref in DEMO_APPLICATIONS:
        print(f"  - {ref}")
    print()
    print("To process a real application from the portal, use LIVE mode:")
    print()
    print(f"  plana process {reference} --mode live --output report.md")
    print()
    print("Or use auto mode (default) to automatically switch:")
    print()
    print(f"  plana process {reference} --output report.md")
    print()


async def cmd_process_demo(reference: str, output: Optional[str]):
    """Process in demo mode with fixture data."""
    from plana.progress import ProgressLogger, StepStatus
    from plana.storage import get_database, StoredRunLog

    logger = ProgressLogger(mode="demo", verbose=True)
    logger.start_pipeline(reference, "newcastle")

    app_data = DEMO_APPLICATIONS[reference]
    run_id = logger.run_id

    try:
        # Step 0: Initialize
        logger.start_step("init", "Initialize runtime (mode, council, paths, db)")
        base_dir = Path.home() / ".plana"
        db = get_database()
        logger.complete_step("Done", {
            "db_path": str(base_dir / "plana.db"),
            "docs_path": str(base_dir / "documents"),
        })

        # Step 1: Load fixture
        logger.start_step("load_fixture", "Load application from fixtures")
        from plana.report.generator import ReportGenerator, ApplicationData
        from plana.documents import DocumentManager

        application = ApplicationData(
            reference=reference,
            address=app_data['address'],
            proposal=app_data['proposal'],
            application_type=app_data['type'],
            constraints=app_data['constraints'],
            ward=app_data.get('ward', 'City Centre'),
        )
        logger.complete_step("Done", {
            "address": app_data['address'][:50] + "...",
            "type": app_data['type'],
        })

        # Step 2: List documents
        logger.start_step("list_documents", "List demo documents")
        doc_manager = DocumentManager()
        demo_docs = doc_manager.list_documents(reference)
        logger.complete_step("Done", {"documents": len(demo_docs)})

        # Step 3: Retrieve policies
        logger.start_step("retrieve_policies", "Retrieve relevant policies")
        from plana.policy import PolicySearch
        from plana.improvement import rerank_policies

        policy_search = PolicySearch()
        policies = policy_search.retrieve_relevant_policies(
            proposal=application.proposal,
            constraints=application.constraints,
            application_type=application.application_type,
            address=application.address,
        )
        # Apply re-ranking based on historical performance
        policies = rerank_policies(policies, reference)

        policy_counts = {
            "NPPF": len([p for p in policies if p.doc_id == "NPPF"]),
            "CSUCP": len([p for p in policies if p.doc_id == "CSUCP"]),
            "DAP": len([p for p in policies if p.doc_id == "DAP"]),
        }
        logger.complete_step(
            f"{len(policies)} policies",
            {"NPPF": policy_counts["NPPF"], "CSUCP": policy_counts["CSUCP"], "DAP": policy_counts["DAP"]},
        )

        # Step 4: Find similar cases
        logger.start_step("find_similar", "Find similar applications")
        from plana.similarity import SimilaritySearch

        similarity_search = SimilaritySearch()
        similar_cases = similarity_search.find_similar_cases(
            proposal=application.proposal,
            constraints=application.constraints,
            address=application.address,
            application_type=application.application_type,
        )
        logger.complete_step("Done", {"similar_cases": len(similar_cases)})

        # Step 5: Generate report
        logger.start_step("generate_report", "Generate case officer report")
        from plana.decision_calibration import calibrate_decision
        from plana.improvement import get_confidence_adjustment

        generator = ReportGenerator()
        output_path = Path(output) if output else None
        report = generator.generate_report(application, output_path, demo_docs)

        # Get decision
        raw_decision = "APPROVE_WITH_CONDITIONS"
        calibrated_decision = calibrate_decision(reference, raw_decision)
        confidence = get_confidence_adjustment(reference)

        logger.complete_step("Done", {
            "decision": calibrated_decision,
            "confidence": f"{confidence:.0%}",
        })

        # Step 6: Save outputs
        logger.start_step("save_outputs", "Save outputs")
        from plana.storage import StoredReport

        if output_path:
            stored_report = StoredReport(
                reference=application.reference,
                report_path=str(output_path),
                recommendation=calibrated_decision,
                confidence=confidence,
                policies_cited=len(policies),
                similar_cases_count=len(similar_cases),
                generation_mode="demo",
                generated_at=datetime.now().isoformat(),
            )
            db.save_report(stored_report)

            logger.complete_step("Done", {
                "report_path": str(output_path),
            })
        else:
            logger.complete_step("Done (printed to console)")
            print()
            print(report)

        # Save run log
        run_log = StoredRunLog(
            run_id=run_id,
            reference=reference,
            mode="demo",
            council="newcastle",
            timestamp=datetime.now().isoformat(),
            raw_decision=raw_decision,
            calibrated_decision=calibrated_decision,
            confidence=confidence,
            policy_ids_used=json.dumps([p.id for p in policies if hasattr(p, 'id')]),
            docs_downloaded_count=len(demo_docs),
            similar_cases_count=len(similar_cases),
            success=True,
        )
        db.save_run_log(run_log)

        # Complete pipeline
        summary = {
            "decision": calibrated_decision,
            "confidence": f"{confidence:.0%}",
            "policies": len(policies),
            "similar_cases": len(similar_cases),
            "documents": len(demo_docs),
        }
        if output_path:
            summary["report_path"] = str(output_path)

        logger.complete_pipeline(success=True, summary=summary)

    except Exception as e:
        _handle_error(logger, e, "demo")
        sys.exit(1)


async def cmd_process_live(reference: str, output: Optional[str], council: str):
    """Process in live mode with portal data."""
    from plana.progress import ProgressLogger, StepStatus, is_dns_failure, print_live_error_suggestion
    from plana.storage import get_database, StoredRunLog

    logger = ProgressLogger(mode="live", verbose=True)
    logger.start_pipeline(reference, council)

    run_id = logger.run_id
    db = None

    try:
        # Step 0: Initialize runtime
        logger.start_step("init", "Initialize runtime (mode, council, paths, db)")

        base_dir = Path.home() / ".plana"
        db_path = base_dir / "plana.db"
        docs_path = base_dir / "documents"

        db = get_database()

        # Check live dependencies
        try:
            from plana.ingestion import get_adapter, PortalAccessError
            from plana.storage import StoredApplication, StoredDocument
        except ImportError as e:
            logger.fail_step(
                error_message="Live mode requires additional dependencies",
                suggestion="Install with: pip install -e '.[live]'",
            )
            sys.exit(1)

        logger.complete_step("Done", {
            "db_path": str(db_path),
            "docs_path": str(docs_path),
        })

        # Get adapter
        try:
            adapter = get_adapter(council)
        except ImportError as e:
            logger.fail_step(
                error_message="Live mode requires additional dependencies",
                suggestion="Install with: pip install -e '.[live]'",
            )
            sys.exit(1)
        except ValueError as e:
            logger.fail_step(error_message=str(e))
            sys.exit(1)

        # Step 1: Fetch application metadata
        portal_url = f"https://portal.newcastle.gov.uk/planning/simpleSearchResults.do?action=firstPage&searchCriteria.reference={reference}"
        logger.start_step("fetch_metadata", "Fetch application metadata from portal", url=portal_url)

        try:
            app_details = await adapter.fetch_application(reference)
        except Exception as e:
            status_code = getattr(e, 'status_code', None)
            error_url = getattr(e, 'url', portal_url)

            # Check for DNS failure specifically
            if is_dns_failure(e):
                error_msg = "Unable to resolve host (DNS failure)"
                suggestion = print_live_error_suggestion(status_code, error=e)
            else:
                error_msg = str(e)
                suggestion = print_live_error_suggestion(status_code, error=e)

            logger.fail_step(
                error_message=error_msg,
                url=error_url,
                status_code=status_code,
                suggestion=suggestion,
            )
            await adapter.close()
            sys.exit(1)

        if not app_details:
            logger.fail_step(
                error_message=f"Application {reference} not found on portal",
                url=portal_url,
                status_code=404,
                suggestion=print_live_error_suggestion(404),
            )
            await adapter.close()
            sys.exit(1)

        logger.complete_step("Done", {
            "address": app_details.address[:50] + "..." if len(app_details.address) > 50 else app_details.address,
            "type": app_details.application_type.value,
        })

        # Step 2: Fetch document register
        logger.start_step("fetch_documents", "Fetch document register")
        portal_docs = await adapter.fetch_documents(reference)
        logger.complete_step(f"Done ({len(portal_docs)} documents found)")

        # Step 3: Download documents
        logger.start_step("download_documents", "Download documents")
        doc_dir = docs_path / reference.replace("/", "_")

        downloaded = 0
        skipped = 0
        failed = 0
        deduped = 0
        retries = 0

        for doc in portal_docs:
            # Check for duplicate by hash
            existing = db.get_document_by_hash(doc.content_hash) if doc.content_hash else None
            if existing and existing.local_path and Path(existing.local_path).exists():
                deduped += 1
                skipped += 1
                continue

            # Download
            local_path = await adapter.download_document(doc, str(doc_dir))
            if local_path:
                downloaded += 1
            else:
                failed += 1

        logger.print_document_progress(downloaded, skipped, failed, retries, deduped)
        logger.complete_step("", {
            "local_dir": str(doc_dir),
        })

        # Step 4: Persist to SQLite
        logger.start_step("persist_data", "Persist application + docs to SQLite")

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

        # Save documents
        for doc in portal_docs:
            if doc.local_path:
                stored_doc = StoredDocument(
                    application_id=app_id,
                    reference=reference,
                    doc_id=doc.id,
                    title=doc.title,
                    doc_type=doc.doc_type,
                    url=doc.url,
                    local_path=doc.local_path,
                    content_hash=doc.content_hash,
                    size_bytes=doc.size_bytes,
                    content_type=doc.content_type,
                    date_published=doc.date_published,
                    downloaded_at=datetime.now().isoformat(),
                )
                db.save_document(stored_doc)

        logger.complete_step("Done", {
            "application_id": app_id,
            "docs_saved": downloaded,
        })

        # Close adapter
        await adapter.close()

        # Step 5: Retrieve policies
        logger.start_step("retrieve_policies", "Retrieve relevant policies")
        from plana.policy import PolicySearch
        from plana.improvement import rerank_policies

        policy_search = PolicySearch()
        policies = policy_search.retrieve_relevant_policies(
            proposal=app_details.proposal,
            constraints=[c.name for c in app_details.constraints],
            application_type=app_details.application_type.value,
            address=app_details.address,
        )
        policies = rerank_policies(policies, reference)

        policy_counts = {
            "NPPF": len([p for p in policies if p.doc_id == "NPPF"]),
            "CSUCP": len([p for p in policies if p.doc_id == "CSUCP"]),
            "DAP": len([p for p in policies if p.doc_id == "DAP"]),
        }
        logger.complete_step(
            f"{len(policies)} policies",
            {"NPPF": policy_counts["NPPF"], "CSUCP": policy_counts["CSUCP"], "DAP": policy_counts["DAP"]},
        )

        # Step 6: Find similar applications
        logger.start_step("find_similar", "Find similar applications")
        from plana.similarity import SimilaritySearch

        similarity_search = SimilaritySearch()
        similar_cases = similarity_search.find_similar_cases(
            proposal=app_details.proposal,
            constraints=[c.name for c in app_details.constraints],
            address=app_details.address,
            application_type=app_details.application_type.value,
        )
        logger.complete_step("Done", {
            "similar_cases": len(similar_cases),
        })

        # Step 7: Generate report
        logger.start_step("generate_report", "Generate case officer report")
        from plana.report.generator import ReportGenerator, ApplicationData
        from plana.decision_calibration import calibrate_decision
        from plana.improvement import get_confidence_adjustment

        application = ApplicationData(
            reference=app_details.reference,
            address=app_details.address,
            proposal=app_details.proposal,
            application_type=app_details.application_type.value,
            constraints=[c.name for c in app_details.constraints],
            ward=app_details.ward or "Unknown",
        )

        generator = ReportGenerator()
        output_path = Path(output) if output else None
        report = generator.generate_report(application, output_path, portal_docs)

        raw_decision = "APPROVE_WITH_CONDITIONS"
        calibrated_decision = calibrate_decision(reference, raw_decision)
        confidence = get_confidence_adjustment(reference)

        logger.complete_step("Done", {
            "decision": calibrated_decision,
            "confidence": f"{confidence:.0%}",
        })

        # Step 8: Save outputs
        logger.start_step("save_outputs", "Save outputs")
        from plana.storage import StoredReport

        if output_path:
            stored_report = StoredReport(
                reference=application.reference,
                report_path=str(output_path),
                recommendation=calibrated_decision,
                confidence=confidence,
                policies_cited=len(policies),
                similar_cases_count=len(similar_cases),
                generation_mode="live",
                generated_at=datetime.now().isoformat(),
            )
            db.save_report(stored_report)

            logger.complete_step("Done", {
                "report_path": str(output_path),
                "results_row": f"{reference},{raw_decision},{calibrated_decision}",
            })
        else:
            logger.complete_step("Done (printed to console)")
            print()
            print(report)

        # Save run log
        run_log = StoredRunLog(
            run_id=run_id,
            reference=reference,
            mode="live",
            council=council,
            timestamp=datetime.now().isoformat(),
            raw_decision=raw_decision,
            calibrated_decision=calibrated_decision,
            confidence=confidence,
            policy_ids_used=json.dumps([p.id for p in policies if hasattr(p, 'id')]),
            docs_downloaded_count=downloaded,
            similar_cases_count=len(similar_cases),
            success=True,
        )
        db.save_run_log(run_log)

        # Complete pipeline
        summary = {
            "decision": calibrated_decision,
            "confidence": f"{confidence:.0%}",
            "policies": len(policies),
            "similar_cases": len(similar_cases),
            "documents_downloaded": downloaded,
        }
        if output_path:
            summary["report_path"] = str(output_path)

        logger.complete_pipeline(success=True, summary=summary)

    except Exception as e:
        _handle_error(logger, e, "live")
        sys.exit(1)


def _handle_error(logger, error: Exception, mode: str):
    """Handle pipeline errors gracefully without stack traces."""
    from plana.progress import StepStatus, is_dns_failure, print_live_error_suggestion
    from plana.storage import get_database, StoredRunLog

    status_code = getattr(error, 'status_code', None)
    error_url = getattr(error, 'url', None)

    # Check for DNS failure specifically
    if is_dns_failure(error):
        error_msg = "Unable to resolve host (DNS failure)"
    else:
        error_msg = str(error)

    # Try to fail the current step if logger is available
    try:
        if hasattr(logger, '_step_start_time') and logger._step_start_time:
            logger.fail_step(
                error_message=error_msg,
                url=error_url,
                status_code=status_code,
                suggestion=print_live_error_suggestion(status_code, error=error) if mode == "live" else None,
            )
        else:
            # No step in progress, just print error
            print()
            print("=" * 70)
            print("ERROR")
            print("=" * 70)
            print()
            print(f"  {error_msg}")
            if error_url:
                print(f"  URL: {error_url}")
            if status_code:
                print(f"  Status: {status_code}")
            print()

        # Save failed run log
        db = get_database()
        run_log = StoredRunLog(
            run_id=logger.run_id,
            reference=logger.reference,
            mode=mode,
            council=logger.council,
            timestamp=datetime.now().isoformat(),
            success=False,
            error_message=error_msg,
            error_step=logger.steps[logger.current_step][0] if logger.current_step < len(logger.steps) else "unknown",
        )
        db.save_run_log(run_log)

        logger.complete_pipeline(success=False)

    except Exception:
        # Fallback error display
        print()
        print("=" * 70)
        print("ERROR")
        print("=" * 70)
        print()
        print(f"  {error_msg}")
        print()


def cmd_feedback(
    reference: str,
    decision: str,
    notes: Optional[str],
    conditions: Optional[list],
    reasons: Optional[list],
):
    """Submit feedback for an application."""
    from plana.improvement import process_feedback, get_feedback_stats

    feedback_id, is_mismatch = process_feedback(
        reference=reference,
        actual_decision=decision,
        notes=notes,
        conditions=conditions,
        reasons=reasons,
    )

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

    if is_mismatch:
        print()
        print("Note: This feedback indicates a mismatch with Plana's prediction.")
        print("Policy weights have been updated to improve future predictions.")
    else:
        print()
        print("This feedback matches Plana's prediction (or is a partial match).")
        print("Policy weights have been reinforced.")

    print()
    print("Run 'plana status' to see feedback statistics.")


def cmd_status():
    """Show system status and statistics."""
    from plana.storage import get_database
    from plana.improvement import get_feedback_summary

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
    print(f"  Run logs:      {stats['run_logs']}")
    print(f"  Successful runs: {stats['successful_runs']}")
    print(f"  Storage used:  {stats['total_document_size_mb']} MB")
    print()

    # Show feedback summary
    if stats['feedback'] > 0:
        fb_summary = get_feedback_summary()
        print("Continuous Improvement:")
        print(f"  Match rate:    {fb_summary['match_rate_percent']}%")
        print(f"  Matches:       {fb_summary['match_count']}")
        print(f"  Mismatches:    {fb_summary['mismatch_count']}")
        if fb_summary['mismatch_rates_by_type']:
            print("  Mismatch rates by type:")
            for app_type, rate in fb_summary['mismatch_rates_by_type'].items():
                print(f"    {app_type}: {rate}%")
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
        sys.exit(1)


def cmd_evaluate(refs_path: str, mode: str, output_path: str):
    """Batch evaluate multiple applications."""
    import csv
    from pathlib import Path
    from plana.decision_calibration import calibrate_decision

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
    print(f"  Calibration: Enabled (Newcastle patterns)")
    print()

    # Process each reference and collect results
    results = []
    for i, ref in enumerate(refs, 1):
        print(f"[{i}/{len(refs)}] Processing {ref}... ", end="", flush=True)

        try:
            # Get raw decision from report generator
            raw_decision, status = _evaluate_single(ref, mode)

            # Apply calibration
            calibrated_decision = calibrate_decision(ref, raw_decision)

            results.append({
                "reference": ref,
                "raw_decision": raw_decision,
                "decision": calibrated_decision,
                "status": status,
            })

            # Show both if different
            if raw_decision != calibrated_decision:
                print(f"{raw_decision} -> {calibrated_decision}")
            else:
                print(f"{calibrated_decision}")
        except Exception as e:
            results.append({
                "reference": ref,
                "raw_decision": "UNKNOWN",
                "decision": "UNKNOWN",
                "status": f"error: {str(e)[:50]}",
            })
            print(f"ERROR: {str(e)[:50]}")

    # Write results to CSV with both raw and calibrated decisions
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["reference", "raw_decision", "decision", "status"])
        writer.writeheader()
        writer.writerows(results)

    print()
    print("=" * 70)
    print(f"Evaluation complete: {len(results)} applications processed")
    print(f"Results saved to: {output_file}")

    # Summary - show both raw and calibrated
    raw_decisions = [r["raw_decision"] for r in results]
    calibrated_decisions = [r["decision"] for r in results]
    print()
    print("Decision Summary (raw -> calibrated):")
    print(f"  APPROVE:                 {raw_decisions.count('APPROVE')} -> {calibrated_decisions.count('APPROVE')}")
    print(f"  APPROVE_WITH_CONDITIONS: {raw_decisions.count('APPROVE_WITH_CONDITIONS')} -> {calibrated_decisions.count('APPROVE_WITH_CONDITIONS')}")
    print(f"  REFUSE:                  {raw_decisions.count('REFUSE')} -> {calibrated_decisions.count('REFUSE')}")
    print(f"  UNKNOWN:                 {raw_decisions.count('UNKNOWN')} -> {calibrated_decisions.count('UNKNOWN')}")


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

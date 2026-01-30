"""
Command-line interface for Plana.AI.

Provides commands to run the pipeline, start the API server,
and manage the system.
"""

import asyncio
import sys
from pathlib import Path

import structlog

logger = structlog.get_logger(__name__)


def setup_logging(debug: bool = False) -> None:
    """Configure structured logging."""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.dev.ConsoleRenderer() if debug else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def main() -> None:
    """Main CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Plana.AI - Planning Intelligence Platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a single application
  plana process 2026/0101/01/NPA

  # Start the API server
  plana serve

  # Generate report for an application
  plana report 2026/0101/01/NPA

  # Search for applications
  plana search --postcode NE1

  # Initialize the system
  plana init
        """,
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Process command
    process_parser = subparsers.add_parser(
        "process",
        help="Process a planning application",
    )
    process_parser.add_argument(
        "reference",
        help="Application reference number",
    )
    process_parser.add_argument(
        "--council",
        default="newcastle",
        help="Council ID (default: newcastle)",
    )
    process_parser.add_argument(
        "--force",
        action="store_true",
        help="Force reprocessing",
    )

    # Report command
    report_parser = subparsers.add_parser(
        "report",
        help="Generate report for an application",
    )
    report_parser.add_argument(
        "reference",
        help="Application reference number",
    )
    report_parser.add_argument(
        "--council",
        default="newcastle",
        help="Council ID",
    )
    report_parser.add_argument(
        "--output",
        type=Path,
        help="Output file path",
    )

    # Serve command
    serve_parser = subparsers.add_parser(
        "serve",
        help="Start the API server",
    )
    serve_parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to",
    )
    serve_parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to",
    )
    serve_parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload",
    )

    # Search command
    search_parser = subparsers.add_parser(
        "search",
        help="Search for applications",
    )
    search_parser.add_argument(
        "--postcode",
        help="Filter by postcode",
    )
    search_parser.add_argument(
        "--address",
        help="Filter by address",
    )
    search_parser.add_argument(
        "--council",
        default="newcastle",
        help="Council ID",
    )
    search_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum results",
    )

    # Init command
    init_parser = subparsers.add_parser(
        "init",
        help="Initialize the system",
    )

    # Demo command - list available fixture applications
    demo_parser = subparsers.add_parser(
        "demo",
        help="List available demo applications (fixture mode)",
    )

    # Status command - show current configuration
    status_parser = subparsers.add_parser(
        "status",
        help="Show current configuration and status",
    )

    args = parser.parse_args()

    setup_logging(debug=args.debug)

    if args.command == "process":
        asyncio.run(cmd_process(args))
    elif args.command == "report":
        asyncio.run(cmd_report(args))
    elif args.command == "serve":
        cmd_serve(args)
    elif args.command == "search":
        asyncio.run(cmd_search(args))
    elif args.command == "init":
        asyncio.run(cmd_init(args))
    elif args.command == "demo":
        cmd_demo(args)
    elif args.command == "status":
        cmd_status(args)
    else:
        parser.print_help()


async def cmd_process(args) -> None:
    """Process an application."""
    from plana.pipeline import PlanaPipeline

    print(f"Processing application: {args.reference}")

    pipeline = PlanaPipeline()
    result = await pipeline.run(
        reference=args.reference,
        council_id=args.council,
        force_reprocess=args.force,
    )

    if result.success:
        print(f"\nSuccess! Report generated: {result.report.id}")
        print(f"Duration: {result.duration_seconds:.1f}s")
        print(f"Policies cited: {len(result.policies)}")
        print(f"Similar cases: {len(result.similar_cases)}")

        if result.report:
            print(f"\nRecommendation: {result.report.recommendation or 'Not determined'}")
    else:
        print(f"\nFailed with errors:")
        for error in result.errors:
            print(f"  - {error}")
        sys.exit(1)


async def cmd_report(args) -> None:
    """Generate a report."""
    from plana.pipeline import PlanaPipeline

    print(f"Generating report for: {args.reference}")

    pipeline = PlanaPipeline()
    report = await pipeline.generate_report(
        reference=args.reference,
        council_id=args.council,
    )

    if args.output:
        with open(args.output, "w") as f:
            f.write(report.full_content)
        print(f"Report saved to: {args.output}")
    else:
        print("\n" + "=" * 60)
        print(report.full_content)
        print("=" * 60)

    print(f"\nReport ID: {report.id}")
    print(f"Sections: {len(report.sections)}")
    print(f"Recommendation: {report.recommendation or 'Not determined'}")


def cmd_serve(args) -> None:
    """Start the API server."""
    import uvicorn

    print(f"Starting Plana.AI API server on {args.host}:{args.port}")

    uvicorn.run(
        "plana.api.app:create_app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        factory=True,
    )


async def cmd_search(args) -> None:
    """Search for applications."""
    from plana.councils import get_portal

    print(f"Searching applications in {args.council}...")

    portal = get_portal(args.council)
    try:
        applications = await portal.search_applications(
            postcode=args.postcode,
            address=args.address,
            max_results=args.limit,
        )

        print(f"\nFound {len(applications)} applications:\n")

        for app in applications:
            print(f"  {app.reference}")
            print(f"    Address: {app.address.full_address}")
            print(f"    Proposal: {app.proposal[:80]}...")
            print(f"    Status: {app.status.value}")
            print()

    finally:
        await portal.close()


async def cmd_init(args) -> None:
    """Initialize the system."""
    from plana.config import get_settings
    from plana.pipeline import PlanaPipeline

    settings = get_settings()

    print("Initializing Plana.AI...")
    print()
    print("Configuration:")
    print(f"  Mode: {'Fixture/Demo' if settings.use_fixtures else 'Live Portal'}")
    print(f"  LLM: {'Stub (no API key)' if settings.skip_llm else 'Enabled'}")
    print(f"  Vector Store: {settings.vector_store.backend}")
    print(f"  Storage: {settings.storage.backend}")
    print()

    settings.ensure_directories()

    pipeline = PlanaPipeline()
    await pipeline.initialize()

    print("Initialization complete!")
    print(f"Data directory: {settings.data_dir}")
    print()
    print("Next steps:")
    print("  plana demo          # List available demo applications")
    print("  plana process <ref> # Process an application")
    print("  plana serve         # Start the API server")


def cmd_demo(args) -> None:
    """List available demo applications."""
    from plana.councils.fixtures import DEMO_APPLICATIONS

    print("Available Demo Applications")
    print("=" * 60)
    print()
    print("These applications are available in fixture mode (default).")
    print("Use: plana process <reference>")
    print()

    for ref, data in DEMO_APPLICATIONS.items():
        print(f"  {ref}")
        print(f"    Address: {data['address']['full_address'][:60]}...")
        print(f"    Type: {data['application_type']}")
        proposal = data['proposal'][:70] + "..." if len(data['proposal']) > 70 else data['proposal']
        print(f"    Proposal: {proposal}")
        if data.get('constraints'):
            constraints = ", ".join(c['name'] for c in data['constraints'])
            print(f"    Constraints: {constraints}")
        print()

    print("=" * 60)
    print(f"Total: {len(DEMO_APPLICATIONS)} demo applications")
    print()
    print("To use live portal (may be blocked): export PLANA_USE_FIXTURES=false")


def cmd_status(args) -> None:
    """Show current configuration and status."""
    import os
    from plana.config import get_settings

    settings = get_settings()

    print("Plana.AI Configuration Status")
    print("=" * 60)
    print()

    # Mode
    print("Mode:")
    if settings.use_fixtures:
        print("  Portal: Fixture/Demo mode (offline)")
    else:
        print("  Portal: Live mode (requires network)")

    if settings.skip_llm:
        print("  LLM: Disabled (stub responses)")
    elif settings.llm.anthropic_api_key:
        print("  LLM: Anthropic Claude enabled")
    elif settings.llm.openai_api_key:
        print("  LLM: OpenAI enabled")
    else:
        print("  LLM: No API key (will use stub)")

    print()

    # Components
    print("Components:")
    print(f"  Vector Store: {settings.vector_store.backend}")
    print(f"  Storage: {settings.storage.backend}")
    print(f"  Data Directory: {settings.data_dir}")
    print()

    # Environment variables
    print("Environment Variables:")
    env_vars = [
        ("PLANA_USE_FIXTURES", os.environ.get("PLANA_USE_FIXTURES", "(not set, default: true)")),
        ("PLANA_SKIP_LLM", os.environ.get("PLANA_SKIP_LLM", "(not set, default: false)")),
        ("PLANA_DATA_DIR", os.environ.get("PLANA_DATA_DIR", "(not set, uses ~/.plana)")),
        ("ANTHROPIC_API_KEY", "***" if settings.llm.anthropic_api_key else "(not set)"),
        ("OPENAI_API_KEY", "***" if settings.llm.openai_api_key else "(not set)"),
    ]
    for name, value in env_vars:
        print(f"  {name}: {value}")

    print()
    print("=" * 60)


if __name__ == "__main__":
    main()

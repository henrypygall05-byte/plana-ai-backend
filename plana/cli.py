"""
Command-line interface for Plana.AI.

Planning intelligence platform for UK planning applications.
"""

import argparse
import sys
from pathlib import Path

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
  plana init                                    Initialize the system
  plana demo                                    List available demo applications
  plana process <ref>                           Process an application (console output)
  plana process <ref> --output report.md        Process and save report to file
  plana report <ref> --output report.md         Generate report only

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

    # Report command (convenience alias)
    report_parser = subparsers.add_parser("report", help="Generate report for an application")
    report_parser.add_argument("reference", help="Application reference number")
    report_parser.add_argument(
        "--output", "-o",
        type=str,
        required=True,
        help="Output file path for the report (required)",
    )

    args = parser.parse_args()

    if args.command == "init":
        cmd_init()
    elif args.command == "demo":
        cmd_demo()
    elif args.command == "process":
        cmd_process(args.reference, args.output)
    elif args.command == "report":
        cmd_process(args.reference, args.output)
    else:
        parser.print_help()


def cmd_init():
    """Initialize the system."""
    from pathlib import Path

    # Create cache directories
    cache_dir = Path.home() / ".plana"
    (cache_dir / "cache" / "policies").mkdir(parents=True, exist_ok=True)
    (cache_dir / "documents").mkdir(parents=True, exist_ok=True)

    print("Initializing Plana.AI...")
    print()
    print("Configuration:")
    print("  Mode: Demo/Offline (fixture data)")
    print("  Storage: Local filesystem")
    print(f"  Cache: {cache_dir}")
    print()
    print("Created directories:")
    print(f"  - {cache_dir / 'cache' / 'policies'}")
    print(f"  - {cache_dir / 'documents'}")
    print()
    print("Initialization complete!")
    print()
    print("Next steps:")
    print("  plana demo                          List available demo applications")
    print("  plana process <ref> --output x.md   Process and generate report")


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
    print("  plana process <reference>                   Process (console output)")
    print("  plana process <reference> --output x.md     Process and save report")


def cmd_process(reference: str, output: str = None):
    """Process a planning application and generate report."""
    if reference not in DEMO_APPLICATIONS:
        print(f"Error: Unknown reference '{reference}'")
        print()
        print("Available demo references:")
        for ref in DEMO_APPLICATIONS:
            print(f"  {ref}")
        sys.exit(1)

    app_data = DEMO_APPLICATIONS[reference]

    print(f"Processing application: {reference}")
    print("=" * 70)
    print()
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
    from plana.policy import PolicySearch
    from plana.similarity import SimilaritySearch
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

    print("Processing Steps:")

    # Step 1: Fetch application data
    print("  [1/5] Fetching application data... ", end="", flush=True)
    print("Done (from fixtures)")

    # Step 2: List documents
    print("  [2/5] Listing documents... ", end="", flush=True)
    doc_manager = DocumentManager()
    documents = doc_manager.list_documents(reference)
    print(f"Done ({len(documents)} documents)")

    # Step 3: Retrieve policies
    print("  [3/5] Retrieving relevant policies... ", end="", flush=True)
    policy_search = PolicySearch()
    policies = policy_search.retrieve_relevant_policies(
        proposal=application.proposal,
        constraints=application.constraints,
        application_type=application.application_type,
        address=application.address,
    )
    print(f"Done ({len(policies)} policies matched)")

    # Step 4: Find similar cases
    print("  [4/5] Finding similar cases... ", end="", flush=True)
    similarity_search = SimilaritySearch()
    similar_cases = similarity_search.find_similar_cases(
        proposal=application.proposal,
        constraints=application.constraints,
        address=application.address,
        application_type=application.application_type,
    )
    print(f"Done ({len(similar_cases)} similar cases)")

    # Step 5: Generate report
    print("  [5/5] Generating report... ", end="", flush=True)
    generator = ReportGenerator()

    output_path = Path(output) if output else None
    report = generator.generate_report(application, output_path)
    print("Done")

    print()
    print("=" * 70)

    if output:
        print(f"Report saved to: {output}")
        print()

        # Print summary statistics
        print("Report Summary:")
        print(f"  - Policy citations: {len(policies)} policies from NPPF, CSUCP, DAP")
        print(f"  - Similar cases: {len(similar_cases)} historic applications")
        print(f"  - Documents reviewed: {len(documents)}")

        # Count by document
        nppf_count = len([p for p in policies if p.doc_id == "NPPF"])
        csucp_count = len([p for p in policies if p.doc_id == "CSUCP"])
        dap_count = len([p for p in policies if p.doc_id == "DAP"])
        print()
        print("  Policy breakdown:")
        print(f"    - NPPF: {nppf_count} policies")
        print(f"    - CSUCP: {csucp_count} policies")
        print(f"    - DAP: {dap_count} policies")

    else:
        # Print report to console
        print()
        print(report)

    print()
    print("Processing complete!")


if __name__ == "__main__":
    main()

"""
Command-line interface for Plana.AI.

Simple demo-only CLI for local development.
"""

import argparse
import sys

# Demo application data (offline fixtures)
DEMO_APPLICATIONS = {
    "2024/0930/01/DET": {
        "address": "T J Hughes, 86-92 Grainger Street, Newcastle Upon Tyne, NE1 5JQ",
        "type": "Full Planning",
        "proposal": "Erection of two storey rear/roof extension and conversion of upper floors to residential",
        "constraints": ["Grainger Town Conservation Area", "Adjacent to Grade II listed buildings"],
    },
    "2024/0943/01/LBC": {
        "address": "T J Hughes, 86-92 Grainger Street, Newcastle Upon Tyne, NE1 5JQ",
        "type": "Listed Building Consent",
        "proposal": "Listed Building Application for internal and external works",
        "constraints": ["Grade II Listed Building", "Grainger Town Conservation Area"],
    },
    "2024/0300/01/LBC": {
        "address": "155-159 Grainger Street, Newcastle Upon Tyne, NE1 5AE",
        "type": "Listed Building Consent",
        "proposal": "Listed Building Consent for alterations to elevations including new shopfront",
        "constraints": ["Grade II Listed Building", "Grainger Town Conservation Area"],
    },
    "2025/0015/01/DET": {
        "address": "Southern Area of Town Moor, Grandstand Road, Newcastle",
        "type": "Full Planning",
        "proposal": "Installation and repair of land drainage and construction of SuDS pond",
        "constraints": ["Town Moor", "Flood Zone 2"],
    },
    "2023/1500/01/HOU": {
        "address": "42 Jesmond Road, Newcastle Upon Tyne, NE2 1NL",
        "type": "Householder",
        "proposal": "Single storey rear extension and loft conversion with rear dormer window",
        "constraints": [],
    },
}


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Plana.AI - Planning Intelligence Platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  plana init              Initialize the system
  plana demo              List available demo applications
  plana process <ref>     Process a planning application

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

    args = parser.parse_args()

    if args.command == "init":
        cmd_init()
    elif args.command == "demo":
        cmd_demo()
    elif args.command == "process":
        cmd_process(args.reference)
    else:
        parser.print_help()


def cmd_init():
    """Initialize the system."""
    print("Initializing Plana.AI...")
    print()
    print("Configuration:")
    print("  Mode: Demo/Offline (fixture data)")
    print("  Storage: Local filesystem")
    print()
    print("Initialization complete!")
    print()
    print("Next steps:")
    print("  plana demo              List available demo applications")
    print("  plana process <ref>     Process an application")


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
    print("Usage: plana process <reference>")


def cmd_process(reference: str):
    """Process a planning application."""
    if reference not in DEMO_APPLICATIONS:
        print(f"Error: Unknown reference '{reference}'")
        print()
        print("Available demo references:")
        for ref in DEMO_APPLICATIONS:
            print(f"  {ref}")
        sys.exit(1)

    app = DEMO_APPLICATIONS[reference]

    print(f"Processing application: {reference}")
    print("=" * 70)
    print()
    print("Application Details:")
    print(f"  Reference: {reference}")
    print(f"  Address: {app['address']}")
    print(f"  Type: {app['type']}")
    print(f"  Proposal: {app['proposal']}")
    if app['constraints']:
        print(f"  Constraints: {', '.join(app['constraints'])}")
    print()
    print("Processing Steps:")
    print("  [1/4] Fetching application data... Done (from fixtures)")
    print("  [2/4] Analyzing documents... Done (demo mode)")
    print("  [3/4] Retrieving relevant policies... Done")
    print("  [4/4] Generating report... Done")
    print()
    print("=" * 70)
    print("Processing complete!")
    print()
    print(f"Application {reference} has been processed successfully.")
    print("Report generated using demo/template mode.")


if __name__ == "__main__":
    main()

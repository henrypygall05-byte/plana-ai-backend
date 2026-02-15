#!/usr/bin/env python3
"""
Smoke-test script: monitors document processing queue for a reference.

Usage:
    python scripts/check_queue.py 2024/0930/01/DET
    python scripts/check_queue.py 2024/0930/01/DET --duration 60 --interval 3

Prints counts every --interval seconds for --duration seconds.
Confirms that queued decreases and processed increases.
Exit code 0 = queue drained, 1 = stuck.
"""

import argparse
import sys
import time

# Ensure the project root is on sys.path
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from plana.storage.database import Database


def main() -> int:
    parser = argparse.ArgumentParser(description="Monitor document processing queue")
    parser.add_argument("reference", help="Application reference (e.g. 2024/0930/01/DET)")
    parser.add_argument("--duration", type=int, default=30, help="Total monitoring duration in seconds (default: 30)")
    parser.add_argument("--interval", type=float, default=2.0, help="Poll interval in seconds (default: 2)")
    args = parser.parse_args()

    db = Database()
    reference = args.reference

    print(f"Monitoring queue for: {reference}")
    print(f"Duration: {args.duration}s | Interval: {args.interval}s")
    print("-" * 65)
    print(f"{'Time':>6}  {'Total':>5}  {'Queued':>6}  {'Processing':>10}  {'Processed':>9}  {'Failed':>6}")
    print("-" * 65)

    start = time.time()
    initial_queued = None
    final_queued = None
    initial_processed = None
    final_processed = None

    while True:
        elapsed = time.time() - start
        if elapsed > args.duration:
            break

        counts = db.get_processing_counts(reference)
        total = counts["total"]
        queued = counts["queued"]
        processing = counts["processing"]
        processed = counts["processed"]
        failed = counts["failed"]

        if initial_queued is None:
            initial_queued = queued
            initial_processed = processed

        final_queued = queued
        final_processed = processed

        print(f"{elapsed:5.1f}s  {total:>5}  {queued:>6}  {processing:>10}  {processed:>9}  {failed:>6}")

        if queued == 0 and processing == 0:
            print("\nQueue fully drained.")
            break

        time.sleep(args.interval)

    print("-" * 65)

    if initial_queued == 0 and final_queued == 0:
        print("No queued documents found for this reference.")
        return 0

    queued_delta = initial_queued - final_queued
    processed_delta = final_processed - initial_processed

    print(f"Queued:    {initial_queued} -> {final_queued}  (delta: -{queued_delta})")
    print(f"Processed: {initial_processed} -> {final_processed}  (delta: +{processed_delta})")

    if queued_delta > 0 and processed_delta > 0:
        print("\nVERDICT: PASS - Queue is being consumed. Worker is running.")
        return 0
    elif final_queued == 0:
        print("\nVERDICT: PASS - Queue is empty (all documents processed/failed).")
        return 0
    else:
        print("\nVERDICT: FAIL - Queue is STUCK. Queued count did not decrease.")
        print("Possible causes:")
        print("  1. Worker process is not running")
        print("  2. Worker crashed (check logs)")
        print("  3. No local_path set on documents (nothing to extract)")
        print()
        print("To start the worker:")
        print("  python -m plana.documents.worker --loop")
        return 1


if __name__ == "__main__":
    sys.exit(main())

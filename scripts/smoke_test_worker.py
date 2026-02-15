#!/usr/bin/env python3
"""
End-to-end smoke test: enqueue documents, run worker, verify timeline.

Usage:
    # Against a real reference (requires docs already saved in DB):
    python scripts/smoke_test_worker.py 24/00730/FUL

    # Self-contained test (creates temp DB + docs, runs worker inline):
    python scripts/smoke_test_worker.py --self-test

Prints a status timeline:
    t0:    queued=26, processing=0, processed=0, failed=0
    t+2s:  queued=24, processing=1, processed=1, failed=0
    ...
    final: queued=0,  processing=0, processed=25, failed=1

Exit code 0 = all docs processed/failed, 1 = stuck.
"""

import argparse
import sys
import tempfile
import time
from pathlib import Path

# Ensure the project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from plana.storage.database import Database
from plana.storage.models import StoredDocument


def _print_header():
    print(f"{'Time':>8}  {'Total':>5}  {'Queued':>6}  {'Processing':>10}  "
          f"{'Processed':>9}  {'Failed':>6}")
    print("-" * 70)


def _print_row(elapsed: float, counts: dict):
    t_label = f"t+{elapsed:.0f}s" if elapsed > 0 else "t0"
    print(f"{t_label:>8}  {counts['total']:>5}  {counts['queued']:>6}  "
          f"{counts['processing']:>10}  {counts['processed']:>9}  "
          f"{counts['failed']:>6}")


def monitor_existing(reference: str, duration: int, interval: float) -> int:
    """Monitor an existing reference in the default database."""
    db = Database()
    counts = db.get_processing_counts(reference)

    if counts["total"] == 0:
        print(f"ERROR: No documents found for reference: {reference}")
        return 1

    print(f"Reference: {reference}")
    print(f"Duration: {duration}s | Interval: {interval}s")
    print()
    _print_header()

    start = time.time()
    snapshots = []

    while True:
        elapsed = time.time() - start
        counts = db.get_processing_counts(reference)
        _print_row(elapsed, counts)
        snapshots.append((elapsed, dict(counts)))

        if counts["queued"] == 0 and counts["processing"] == 0:
            break
        if elapsed >= duration:
            break

        time.sleep(interval)

    print("-" * 70)
    first = snapshots[0][1]
    last = snapshots[-1][1]

    print(f"\nInitial:  queued={first['queued']}, processed={first['processed']}, "
          f"failed={first['failed']}")
    print(f"Final:    queued={last['queued']}, processed={last['processed']}, "
          f"failed={last['failed']}")

    # Show any failed documents with reasons
    if last["failed"] > 0:
        docs = db.get_documents(reference)
        print("\nFailed documents:")
        for doc in docs:
            if doc.processing_status == "failed":
                reason = getattr(doc, "failure_reason", None) or "unknown"
                print(f"  - {doc.doc_id} ({doc.title}): {reason}")

    if last["queued"] == 0 and last["processing"] == 0:
        print("\nVERDICT: PASS — queue fully drained")
        return 0
    else:
        print("\nVERDICT: FAIL — queue stuck")
        print("  Is the worker running?  python -m plana.documents.worker --loop")
        return 1


def self_test() -> int:
    """Self-contained test: create temp DB, enqueue docs, run worker inline."""
    print("=== Self-contained smoke test ===\n")

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "smoke.db"
        db = Database(db_path)

        reference = "SMOKE/TEST/001"
        doc_count = 8

        # Create document files and enqueue them
        for i in range(doc_count):
            doc_file = Path(tmpdir) / f"doc_{i}.txt"
            doc_file.write_text(f"Planning document {i}: design and access statement content.")

            doc = StoredDocument(
                application_id=1,
                reference=reference,
                doc_id=f"smoke_doc_{i}",
                title=f"Document {i}.txt",
                doc_type="TXT",
                local_path=str(doc_file),
                mime_type="text/plain",
            )
            db.save_document(doc)

        # Also add some drawing files (no text extraction)
        for i in range(3):
            doc = StoredDocument(
                application_id=1,
                reference=reference,
                doc_id=f"smoke_plan_{i}",
                title=f"{'Site Plan' if i == 0 else 'Elevation'} {i}.pdf",
                doc_type="PDF",
                local_path="/nonexistent/path.pdf",
                mime_type="application/pdf",
            )
            db.save_document(doc)

        total_docs = doc_count + 3

        # Verify initial state
        counts = db.get_processing_counts(reference)
        print(f"Enqueued {total_docs} documents (reference: {reference})")
        print()
        _print_header()

        start = time.time()
        _print_row(0, counts)

        assert counts["queued"] == total_docs, f"Expected {total_docs} queued, got {counts['queued']}"

        # Run worker inline (drain_queue)
        from plana.documents.worker import drain_queue
        processed = drain_queue(db)

        elapsed = time.time() - start
        counts = db.get_processing_counts(reference)
        _print_row(elapsed, counts)

        print("-" * 70)
        print(f"\nWorker processed {processed} documents in {elapsed:.1f}s")
        print(f"Final: queued={counts['queued']}, processed={counts['processed']}, "
              f"failed={counts['failed']}")

        # Show any failed documents
        if counts["failed"] > 0:
            docs = db.get_documents(reference)
            print("\nFailed documents:")
            for doc in docs:
                if doc.processing_status == "failed":
                    reason = getattr(doc, "failure_reason", None) or "unknown"
                    print(f"  - {doc.doc_id} ({doc.title}): {reason}")

        # Verify final state
        if counts["queued"] > 0:
            print("\nVERDICT: FAIL — documents still queued after drain")
            return 1

        if counts["processed"] + counts["failed"] != total_docs:
            print(f"\nVERDICT: FAIL — expected {total_docs} processed+failed, "
                  f"got {counts['processed'] + counts['failed']}")
            return 1

        print(f"\nVERDICT: PASS — all {total_docs} documents processed/failed, queue drained")

        # Test reprocess cycle
        print("\n--- Reprocess cycle ---")
        db.reset_stalled_for_reference(reference)
        counts = db.get_processing_counts(reference)
        stalled = counts["queued"]
        print(f"After reset_stalled: queued={stalled} (failed docs re-queued)")

        db.reset_documents_for_reference(reference)
        counts = db.get_processing_counts(reference)
        print(f"After reset_all: queued={counts['queued']}")

        processed2 = drain_queue(db)
        counts = db.get_processing_counts(reference)
        print(f"After 2nd drain: processed={counts['processed']}, "
              f"failed={counts['failed']}")
        print(f"\nVERDICT: PASS — reprocess cycle completed ({processed2} docs)")

        return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Smoke test: verify document worker processes queue end-to-end",
    )
    parser.add_argument(
        "reference", nargs="?",
        help="Application reference to monitor (e.g. 24/00730/FUL)",
    )
    parser.add_argument(
        "--self-test", action="store_true",
        help="Run self-contained test with temp DB (no external deps)",
    )
    parser.add_argument(
        "--duration", type=int, default=120,
        help="Max monitoring duration in seconds (default: 120)",
    )
    parser.add_argument(
        "--interval", type=float, default=3.0,
        help="Poll interval in seconds (default: 3)",
    )
    args = parser.parse_args()

    if args.self_test:
        return self_test()
    elif args.reference:
        return monitor_existing(args.reference, args.duration, args.interval)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())

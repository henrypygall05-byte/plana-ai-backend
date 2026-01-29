"""
Progress logger for Plana.AI pipeline execution.

Provides structured step-by-step output with timing, URLs, counts, and error handling.
"""

import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class StepStatus(Enum):
    """Status of a pipeline step."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    WARNING = "warning"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StepResult:
    """Result of a pipeline step."""
    step_name: str
    status: StepStatus
    message: str = ""
    duration_ms: int = 0
    details: Dict[str, Any] = field(default_factory=dict)
    error_url: Optional[str] = None
    error_status_code: Optional[int] = None
    error_suggestion: Optional[str] = None


# Pipeline step definitions
LIVE_PIPELINE_STEPS = [
    ("init", "Initialize runtime"),
    ("fetch_metadata", "Fetch application metadata from portal"),
    ("fetch_documents", "Fetch document register"),
    ("download_documents", "Download documents"),
    ("persist_data", "Persist application + docs to SQLite"),
    ("retrieve_policies", "Retrieve relevant policies"),
    ("find_similar", "Find similar applications"),
    ("generate_report", "Generate case officer report"),
    ("save_outputs", "Save outputs"),
]

DEMO_PIPELINE_STEPS = [
    ("init", "Initialize runtime"),
    ("load_fixture", "Load application from fixtures"),
    ("list_documents", "List demo documents"),
    ("retrieve_policies", "Retrieve relevant policies"),
    ("find_similar", "Find similar applications"),
    ("generate_report", "Generate case officer report"),
    ("save_outputs", "Save outputs"),
]


class ProgressLogger:
    """
    Progress logger for the Plana.AI pipeline.

    Outputs step-by-step progress with timing information.

    Example output:
    [0/8] Initialize runtime (mode, council, paths, db) ... 12ms
    [1/8] Fetch application metadata from Newcastle portal
          URL: https://publicaccess.newcastle.gov.uk/online-applications/...
          ... Done (245ms)
    """

    def __init__(
        self,
        mode: str = "live",
        verbose: bool = True,
        output_stream=None,
    ):
        """Initialize the progress logger.

        Args:
            mode: Pipeline mode ('live' or 'demo')
            verbose: Whether to print detailed output
            output_stream: Stream to write output (default: sys.stdout)
        """
        self.mode = mode
        self.verbose = verbose
        self.output = output_stream or sys.stdout

        # Select steps based on mode
        self.steps = LIVE_PIPELINE_STEPS if mode == "live" else DEMO_PIPELINE_STEPS
        self.total_steps = len(self.steps)

        # Step tracking
        self.current_step = 0
        self.step_results: List[StepResult] = []
        self._step_start_time: Optional[float] = None
        self._pipeline_start_time: Optional[float] = None

        # Run metadata
        self.reference: Optional[str] = None
        self.council: Optional[str] = None
        self.run_id: Optional[str] = None

    def start_pipeline(
        self,
        reference: str,
        council: str = "newcastle",
        run_id: Optional[str] = None,
    ) -> None:
        """Start the pipeline and print header.

        Args:
            reference: Application reference
            council: Council ID
            run_id: Optional run ID for logging
        """
        self.reference = reference
        self.council = council
        self.run_id = run_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self._pipeline_start_time = time.time()

        if self.verbose:
            self._print("=" * 70)
            self._print("Plana.AI - Planning Assessment Engine")
            self._print("=" * 70)
            self._print()
            self._print(f"Mode:      {self.mode.upper()}")
            self._print(f"Council:   {council.title()}")
            self._print(f"Reference: {reference}")
            self._print(f"Run ID:    {self.run_id}")
            self._print()
            self._print("-" * 70)
            self._print("Pipeline Progress:")
            self._print("-" * 70)
            self._print()

    def start_step(
        self,
        step_name: str,
        message: Optional[str] = None,
        url: Optional[str] = None,
    ) -> None:
        """Start a new step.

        Args:
            step_name: Name/ID of the step
            message: Optional custom message
            url: Optional URL being accessed
        """
        self._step_start_time = time.time()

        # Find step index
        step_idx = next(
            (i for i, (name, _) in enumerate(self.steps) if name == step_name),
            self.current_step
        )
        self.current_step = step_idx

        # Get step description
        step_desc = message
        if not step_desc:
            for name, desc in self.steps:
                if name == step_name:
                    step_desc = desc
                    break
            step_desc = step_desc or step_name

        if self.verbose:
            self._print(f"[{step_idx}/{self.total_steps - 1}] {step_desc}")
            if url:
                self._print(f"      URL: {url}")
            self._print("      ... ", end="", flush=True)

    def update_step(self, message: str) -> None:
        """Update current step with additional info.

        Args:
            message: Status message
        """
        if self.verbose:
            self._print(message, end="", flush=True)

    def complete_step(
        self,
        message: str = "Done",
        details: Optional[Dict[str, Any]] = None,
        status: StepStatus = StepStatus.SUCCESS,
    ) -> StepResult:
        """Complete the current step.

        Args:
            message: Completion message
            details: Additional details to store
            status: Step status

        Returns:
            StepResult with timing and details
        """
        duration_ms = self._get_step_duration_ms()

        result = StepResult(
            step_name=self.steps[self.current_step][0],
            status=status,
            message=message,
            duration_ms=duration_ms,
            details=details or {},
        )
        self.step_results.append(result)

        if self.verbose:
            status_str = self._format_status(status)
            self._print(f"{status_str} ({duration_ms}ms)")
            if details:
                for key, value in details.items():
                    self._print(f"      {key}: {value}")

        self.current_step += 1
        return result

    def fail_step(
        self,
        error_message: str,
        url: Optional[str] = None,
        status_code: Optional[int] = None,
        suggestion: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> StepResult:
        """Fail the current step with error details.

        Args:
            error_message: Error description
            url: Failing URL (if applicable)
            status_code: HTTP status code (if applicable)
            suggestion: Suggested fix
            details: Additional details

        Returns:
            StepResult with error info
        """
        duration_ms = self._get_step_duration_ms()

        result = StepResult(
            step_name=self.steps[self.current_step][0],
            status=StepStatus.FAILED,
            message=error_message,
            duration_ms=duration_ms,
            details=details or {},
            error_url=url,
            error_status_code=status_code,
            error_suggestion=suggestion,
        )
        self.step_results.append(result)

        if self.verbose:
            self._print("FAILED")
            self._print()
            self._print("=" * 70)
            self._print("PIPELINE ERROR")
            self._print("=" * 70)
            self._print()
            self._print(f"  Step:    {self.steps[self.current_step][1]}")
            self._print(f"  Error:   {error_message}")
            if url:
                self._print(f"  URL:     {url}")
            if status_code:
                self._print(f"  Status:  {status_code}")
            self._print(f"  Duration: {duration_ms}ms")
            self._print()
            if suggestion:
                self._print("Suggestion:")
                self._print(f"  {suggestion}")
                self._print()

        return result

    def skip_step(self, reason: str = "Skipped") -> StepResult:
        """Skip the current step.

        Args:
            reason: Reason for skipping

        Returns:
            StepResult marking step as skipped
        """
        duration_ms = self._get_step_duration_ms()

        result = StepResult(
            step_name=self.steps[self.current_step][0],
            status=StepStatus.SKIPPED,
            message=reason,
            duration_ms=duration_ms,
        )
        self.step_results.append(result)

        if self.verbose:
            self._print(f"Skipped ({reason})")

        self.current_step += 1
        return result

    def complete_pipeline(
        self,
        success: bool = True,
        summary: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Complete the pipeline and print summary.

        Args:
            success: Whether pipeline succeeded
            summary: Summary data to display

        Returns:
            Pipeline results dictionary
        """
        total_duration_ms = int((time.time() - self._pipeline_start_time) * 1000)

        # Collect results
        results = {
            "run_id": self.run_id,
            "reference": self.reference,
            "council": self.council,
            "mode": self.mode,
            "success": success,
            "total_duration_ms": total_duration_ms,
            "steps": [
                {
                    "name": r.step_name,
                    "status": r.status.value,
                    "duration_ms": r.duration_ms,
                    "message": r.message,
                }
                for r in self.step_results
            ],
            "timestamp": datetime.now().isoformat(),
        }

        if summary:
            results.update(summary)

        if self.verbose:
            self._print()
            self._print("=" * 70)
            if success:
                self._print("Pipeline completed successfully!")
            else:
                self._print("Pipeline completed with errors.")
            self._print("=" * 70)
            self._print()
            self._print(f"  Total duration: {total_duration_ms}ms")
            self._print(f"  Steps completed: {len([r for r in self.step_results if r.status == StepStatus.SUCCESS])}/{len(self.steps)}")

            if summary:
                self._print()
                self._print("Summary:")
                for key, value in summary.items():
                    if key not in ("run_id", "reference", "council", "mode"):
                        self._print(f"  {key}: {value}")

            self._print()

        return results

    def print_document_progress(
        self,
        succeeded: int,
        skipped: int,
        failed: int,
        retries: int = 0,
        deduped: int = 0,
    ) -> None:
        """Print document download progress.

        Args:
            succeeded: Number of successful downloads
            skipped: Number of skipped documents
            failed: Number of failed downloads
            retries: Number of retries performed
            deduped: Number of documents deduplicated by hash
        """
        if self.verbose:
            parts = [f"{succeeded} succeeded"]
            if skipped > 0:
                parts.append(f"{skipped} skipped")
            if failed > 0:
                parts.append(f"{failed} failed")
            if retries > 0:
                parts.append(f"{retries} retries")
            if deduped > 0:
                parts.append(f"{deduped} deduplicated")
            self._print(", ".join(parts), end="", flush=True)

    def print_policy_counts(self, counts: Dict[str, int]) -> None:
        """Print policy retrieval counts by source.

        Args:
            counts: Dictionary of source -> count
        """
        if self.verbose:
            total = sum(counts.values())
            parts = [f"{total} policies"]
            breakdown = [f"{source}: {count}" for source, count in counts.items() if count > 0]
            if breakdown:
                parts.append(f"({', '.join(breakdown)})")
            self._print(" ".join(parts), end="", flush=True)

    def _get_step_duration_ms(self) -> int:
        """Get duration of current step in milliseconds."""
        if self._step_start_time is None:
            return 0
        return int((time.time() - self._step_start_time) * 1000)

    def _format_status(self, status: StepStatus) -> str:
        """Format status for display."""
        status_map = {
            StepStatus.SUCCESS: "Done",
            StepStatus.WARNING: "Warning",
            StepStatus.FAILED: "FAILED",
            StepStatus.SKIPPED: "Skipped",
        }
        return status_map.get(status, str(status.value))

    def _print(self, *args, **kwargs) -> None:
        """Print to output stream."""
        print(*args, file=self.output, **kwargs)


def print_live_error_suggestion(status_code: Optional[int] = None) -> str:
    """Get a suggestion for common live mode errors.

    Args:
        status_code: HTTP status code (if applicable)

    Returns:
        Suggestion string
    """
    if status_code == 403:
        return (
            "The portal is blocking automated access (403 Forbidden).\n"
            "Suggestions:\n"
            "  1. Wait a few minutes and try again\n"
            "  2. Check if the portal requires authentication\n"
            "  3. Consider using Playwright/browser-session mode (future feature)\n"
            "  4. Use demo mode for testing: plana process <ref> --mode demo"
        )
    elif status_code == 404:
        return (
            "Application not found on the portal (404).\n"
            "Suggestions:\n"
            "  1. Verify the reference format (e.g., 2024/0930/01/DET)\n"
            "  2. Check if the application exists on the portal website\n"
            "  3. The application may have been removed or archived"
        )
    elif status_code == 429:
        return (
            "Rate limited by the portal (429 Too Many Requests).\n"
            "Suggestions:\n"
            "  1. Wait 5-10 minutes before trying again\n"
            "  2. Reduce the number of concurrent requests"
        )
    elif status_code and status_code >= 500:
        return (
            f"Portal server error ({status_code}).\n"
            "Suggestions:\n"
            "  1. The portal may be experiencing issues\n"
            "  2. Try again later\n"
            "  3. Check portal status page if available"
        )
    else:
        return (
            "Connection failed.\n"
            "Suggestions:\n"
            "  1. Check your internet connection\n"
            "  2. Verify the portal is accessible\n"
            "  3. Try again later"
        )

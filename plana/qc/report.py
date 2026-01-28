"""
QC report generation for Plana.AI.

Generates markdown reports with QC metrics, confusion matrix, and analysis.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

from plana.qc.scorer import (
    Decision,
    MatchType,
    QCMetrics,
)


def generate_qc_report(
    metrics: QCMetrics,
    output_path: Optional[Path] = None,
) -> str:
    """
    Generate a QC report in markdown format.

    Args:
        metrics: QCMetrics object with all scores
        output_path: Optional path to write the report

    Returns:
        Report content as string
    """
    sections = [
        _generate_header(metrics),
        _generate_summary(metrics),
        _generate_confusion_matrix(metrics),
        _generate_case_breakdown(metrics),
        _generate_mismatch_analysis(metrics),
        _generate_footer(),
    ]

    report = "\n\n".join(sections)

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report, encoding="utf-8")

    return report


def _generate_header(metrics: QCMetrics) -> str:
    """Generate report header with headline QC percentage."""
    pass_fail = "PASS" if metrics.qc_percentage >= 70.0 else "FAIL"
    emoji = "" if metrics.qc_percentage >= 70.0 else ""

    return f"""# Plana.AI Quality Control Report

## Overall QC Score: {metrics.qc_percentage:.1f}% {emoji} {pass_fail}

This report compares Plana's planning decisions against actual Newcastle case officer outcomes.

- **Threshold for PASS**: 70%
- **Current Score**: {metrics.qc_percentage:.1f}%
- **Interpretation**: {"Plana is performing at or above junior/mid case officer consistency" if metrics.qc_percentage >= 70 else "Plana needs improvement to match case officer consistency"}"""


def _generate_summary(metrics: QCMetrics) -> str:
    """Generate summary counts section."""
    return f"""## Summary

| Metric | Count | Percentage |
|--------|-------|------------|
| Total Cases | {metrics.total_cases} | 100% |
| Exact Matches | {metrics.exact_matches} | {(metrics.exact_matches / metrics.total_cases * 100) if metrics.total_cases > 0 else 0:.1f}% |
| Partial Matches | {metrics.partial_matches} | {(metrics.partial_matches / metrics.total_cases * 100) if metrics.total_cases > 0 else 0:.1f}% |
| Misses | {metrics.misses} | {(metrics.misses / metrics.total_cases * 100) if metrics.total_cases > 0 else 0:.1f}% |

**Scoring Rules:**
- **Exact Match (1.0 points)**: Plana and officer made the same decision
- **Partial Match (0.5 points)**: Both approved, but one with conditions and one without
- **Miss (0.0 points)**: Fundamental disagreement (approve vs refuse) or unknown decision"""


def _generate_confusion_matrix(metrics: QCMetrics) -> str:
    """Generate confusion matrix table."""
    if not metrics.confusion_matrix:
        return "## Confusion Matrix\n\n*No data available*"

    # Decision labels in display order
    decisions = ["APPROVE", "APPROVE_WITH_CONDITIONS", "REFUSE", "UNKNOWN"]
    short_labels = {
        "APPROVE": "Approve",
        "APPROVE_WITH_CONDITIONS": "Approve+Cond",
        "REFUSE": "Refuse",
        "UNKNOWN": "Unknown",
    }

    # Build header
    header = "| Actual \\\\ Plana | " + " | ".join(short_labels[d] for d in decisions) + " | Total |"
    separator = "|" + "|".join(["---"] * (len(decisions) + 2)) + "|"

    # Build rows
    rows = []
    for actual in decisions:
        if actual not in metrics.confusion_matrix:
            continue
        row_data = metrics.confusion_matrix[actual]
        row_total = sum(row_data.get(d, 0) for d in decisions)
        if row_total == 0:
            continue
        cells = [str(row_data.get(d, 0)) for d in decisions]
        rows.append(f"| **{short_labels[actual]}** | " + " | ".join(cells) + f" | {row_total} |")

    if not rows:
        return "## Confusion Matrix\n\n*No data available*"

    return f"""## Confusion Matrix

Rows = Actual case officer decision, Columns = Plana's decision

{header}
{separator}
{chr(10).join(rows)}"""


def _generate_case_breakdown(metrics: QCMetrics) -> str:
    """Generate per-case breakdown table."""
    if not metrics.case_scores:
        return "## Per-Case Breakdown\n\n*No cases evaluated*"

    header = "| Reference | Plana Decision | Actual Decision | Match Type | Score |"
    separator = "|-----------|----------------|-----------------|------------|-------|"

    rows = []
    for cs in metrics.case_scores:
        match_icon = {
            MatchType.EXACT: "Exact",
            MatchType.PARTIAL: "Partial",
            MatchType.MISS: "Miss",
        }.get(cs.match_type, "Unknown")

        rows.append(
            f"| {cs.reference} | {cs.plana_decision.value} | {cs.actual_decision.value} | {match_icon} | {cs.score:.1f} |"
        )

    return f"""## Per-Case Breakdown

{header}
{separator}
{chr(10).join(rows)}

**Total Score**: {metrics.total_score:.1f} / {metrics.total_cases:.0f} = {metrics.qc_percentage:.1f}%"""


def _generate_mismatch_analysis(metrics: QCMetrics) -> str:
    """Generate mismatch analysis section with plain-English explanations."""
    misses = [cs for cs in metrics.case_scores if cs.match_type == MatchType.MISS]

    if not misses:
        return """## Mismatch Analysis

No mismatches found. Plana's decisions aligned with case officer outcomes for all evaluated cases."""

    analysis_lines = []
    for cs in misses:
        explanation = _explain_mismatch(cs)
        analysis_lines.append(f"### {cs.reference}\n\n{explanation}")

    return f"""## Mismatch Analysis

The following cases had fundamental disagreements between Plana and the case officer:

{chr(10).join(analysis_lines)}"""


def _explain_mismatch(case_score) -> str:
    """Generate plain-English explanation for a mismatch."""
    plana = case_score.plana_decision
    actual = case_score.actual_decision

    if plana == Decision.UNKNOWN:
        return (
            f"- **Plana**: Could not determine a decision (UNKNOWN)\n"
            f"- **Officer**: {actual.value}\n"
            f"- **Analysis**: Plana failed to process this application or produce a clear recommendation. "
            f"This may indicate a processing error, unsupported application type, or missing data."
        )

    if actual == Decision.UNKNOWN:
        return (
            f"- **Plana**: {plana.value}\n"
            f"- **Officer**: Decision not recorded (UNKNOWN)\n"
            f"- **Analysis**: The actual case officer decision was not provided in the gold standard file. "
            f"Update the gold file with the correct decision."
        )

    approval_types = {Decision.APPROVE, Decision.APPROVE_WITH_CONDITIONS}

    if plana in approval_types and actual == Decision.REFUSE:
        plana_str = "approved" if plana == Decision.APPROVE else "approved with conditions"
        return (
            f"- **Plana**: {plana.value} (recommended approval)\n"
            f"- **Officer**: REFUSE (refused the application)\n"
            f"- **Analysis**: Plana {plana_str} this application, but the case officer refused it. "
            f"This suggests Plana may have underweighted negative planning considerations such as:\n"
            f"  - Heritage or conservation impact\n"
            f"  - Neighbour amenity concerns\n"
            f"  - Design quality issues\n"
            f"  - Policy non-compliance\n"
            f"  - Cumulative harm\n\n"
            f"  **Action**: Review the officer's refusal reasons and update policy weighting."
        )

    if plana == Decision.REFUSE and actual in approval_types:
        actual_str = "approved" if actual == Decision.APPROVE else "approved with conditions"
        return (
            f"- **Plana**: REFUSE (recommended refusal)\n"
            f"- **Officer**: {actual.value} ({actual_str})\n"
            f"- **Analysis**: Plana recommended refusal, but the case officer approved. "
            f"This suggests Plana may have overweighted concerns or missed mitigating factors such as:\n"
            f"  - Design improvements during negotiation\n"
            f"  - Conditions that address concerns\n"
            f"  - Planning balance favouring approval\n"
            f"  - Site-specific considerations\n"
            f"  - Policy flexibility or exceptions\n\n"
            f"  **Action**: Review the approval reasoning and adjust Plana's sensitivity."
        )

    return (
        f"- **Plana**: {plana.value}\n"
        f"- **Officer**: {actual.value}\n"
        f"- **Analysis**: Decision mismatch. Review the specific circumstances of this case."
    )


def _generate_footer() -> str:
    """Generate report footer."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"""---

## Methodology

**QC Score Calculation:**
```
QC % = (Sum of scores / Total cases) x 100
```

**Scoring:**
- Exact match: 1.0 point
- Partial match (APPROVE vs APPROVE_WITH_CONDITIONS): 0.5 points
- Miss (APPROVE vs REFUSE, UNKNOWN): 0.0 points

**Threshold:**
- QC >= 70%: PASS (comparable to junior/mid case officer consistency)
- QC < 70%: FAIL (needs improvement)

---

*Report generated by Plana.AI QC on {timestamp}*"""

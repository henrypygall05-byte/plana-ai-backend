"""
Test data factories for Plana.AI.

Provides factory functions to create test data with sensible defaults.
Uses a factory pattern similar to factory_boy but without the dependency.
"""

import random
import string
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional


def random_string(length: int = 10) -> str:
    """Generate a random string."""
    return "".join(random.choices(string.ascii_lowercase, k=length))


def random_reference() -> str:
    """Generate a random application reference."""
    year = random.randint(2020, 2026)
    num = random.randint(1, 9999)
    seq = random.randint(1, 99)
    type_code = random.choice(["DET", "HOU", "LBC", "TCA", "TPO"])
    return f"{year}/{num:04d}/{seq:02d}/{type_code}"


def random_address() -> str:
    """Generate a random address."""
    number = random.randint(1, 200)
    street = random.choice([
        "High Street", "Church Road", "Station Road", "Main Street",
        "Victoria Road", "Park Avenue", "Queen Street", "King Street",
    ])
    return f"{number} {street}, Newcastle Upon Tyne, NE{random.randint(1,6)} {random.randint(1,9)}{random.choice(string.ascii_uppercase)}{random.choice(string.ascii_uppercase)}"


def random_proposal() -> str:
    """Generate a random proposal description."""
    proposals = [
        "Erection of single storey rear extension",
        "Conversion of garage to habitable room",
        "Installation of replacement windows",
        "Construction of front porch",
        "Erection of two storey side extension",
        "Change of use from retail to residential",
        "Installation of new shopfront",
        "Loft conversion with rear dormer",
    ]
    return random.choice(proposals)


# =============================================================================
# Storage Model Factories
# =============================================================================


class ApplicationFactory:
    """Factory for creating StoredApplication instances."""

    @staticmethod
    def create(
        reference: Optional[str] = None,
        council_id: str = "newcastle",
        address: Optional[str] = None,
        proposal: Optional[str] = None,
        application_type: str = "householder",
        status: str = "pending",
        **kwargs,
    ):
        """Create a StoredApplication with defaults."""
        from plana.storage.models import StoredApplication

        return StoredApplication(
            reference=reference or random_reference(),
            council_id=council_id,
            address=address or random_address(),
            proposal=proposal or random_proposal(),
            application_type=application_type,
            status=status,
            date_received=kwargs.get("date_received", datetime.now().isoformat()),
            ward=kwargs.get("ward", "Monument"),
            postcode=kwargs.get("postcode", "NE1 1AA"),
            constraints_json=kwargs.get("constraints_json", "[]"),
            fetched_at=kwargs.get("fetched_at", datetime.now().isoformat()),
        )

    @staticmethod
    def create_batch(count: int, **kwargs) -> list:
        """Create multiple StoredApplication instances."""
        return [ApplicationFactory.create(**kwargs) for _ in range(count)]


class DocumentFactory:
    """Factory for creating StoredDocument instances."""

    @staticmethod
    def create(
        reference: Optional[str] = None,
        doc_id: Optional[str] = None,
        title: Optional[str] = None,
        doc_type: str = "plans",
        **kwargs,
    ):
        """Create a StoredDocument with defaults."""
        from plana.storage.models import StoredDocument

        titles = [
            "Application Form", "Site Location Plan", "Block Plan",
            "Proposed Floor Plans", "Proposed Elevations", "Design Statement",
        ]

        return StoredDocument(
            reference=reference or random_reference(),
            doc_id=doc_id or f"DOC_{random_string(8).upper()}",
            title=title or random.choice(titles),
            doc_type=doc_type,
            url=kwargs.get("url", f"https://portal.example.com/docs/{random_string(10)}.pdf"),
            local_path=kwargs.get("local_path"),
            content_hash=kwargs.get("content_hash", random_string(32)),
            size_bytes=kwargs.get("size_bytes", random.randint(10000, 5000000)),
            content_type=kwargs.get("content_type", "application/pdf"),
            downloaded_at=kwargs.get("downloaded_at", datetime.now().isoformat()),
        )

    @staticmethod
    def create_batch(count: int, **kwargs) -> list:
        """Create multiple StoredDocument instances."""
        return [DocumentFactory.create(**kwargs) for _ in range(count)]


class ReportFactory:
    """Factory for creating StoredReport instances."""

    @staticmethod
    def create(
        reference: Optional[str] = None,
        report_path: Optional[str] = None,
        recommendation: str = "APPROVE_WITH_CONDITIONS",
        confidence: float = 0.75,
        **kwargs,
    ):
        """Create a StoredReport with defaults."""
        from plana.storage.models import StoredReport

        ref = reference or random_reference()

        return StoredReport(
            reference=ref,
            report_path=report_path or f"/tmp/reports/{ref.replace('/', '_')}.md",
            recommendation=recommendation,
            confidence=confidence,
            policies_cited=kwargs.get("policies_cited", random.randint(5, 15)),
            similar_cases_count=kwargs.get("similar_cases_count", random.randint(2, 8)),
            generation_mode=kwargs.get("generation_mode", "demo"),
            prompt_version=kwargs.get("prompt_version", "1.0.0"),
            schema_version=kwargs.get("schema_version", "1.0.0"),
            generated_at=kwargs.get("generated_at", datetime.now().isoformat()),
        )


class FeedbackFactory:
    """Factory for creating StoredFeedback instances."""

    @staticmethod
    def create(
        reference: Optional[str] = None,
        decision: str = "APPROVE_WITH_CONDITIONS",
        notes: Optional[str] = None,
        **kwargs,
    ):
        """Create a StoredFeedback with defaults."""
        from plana.storage.models import StoredFeedback

        return StoredFeedback(
            reference=reference or random_reference(),
            decision=decision,
            notes=notes or "Test feedback note",
            conditions_json=kwargs.get("conditions_json"),
            refusal_reasons_json=kwargs.get("refusal_reasons_json"),
            actual_decision=kwargs.get("actual_decision"),
            submitted_by=kwargs.get("submitted_by", "test_user"),
        )


class RunLogFactory:
    """Factory for creating StoredRunLog instances."""

    @staticmethod
    def create(
        reference: Optional[str] = None,
        run_id: Optional[str] = None,
        mode: str = "demo",
        success: bool = True,
        **kwargs,
    ):
        """Create a StoredRunLog with defaults."""
        from plana.storage.models import StoredRunLog

        return StoredRunLog(
            run_id=run_id or f"run_{random_string(12)}",
            reference=reference or random_reference(),
            mode=mode,
            council=kwargs.get("council", "newcastle"),
            timestamp=kwargs.get("timestamp", datetime.now().isoformat()),
            raw_decision=kwargs.get("raw_decision", "APPROVE_WITH_CONDITIONS"),
            calibrated_decision=kwargs.get("calibrated_decision", "APPROVE_WITH_CONDITIONS"),
            confidence=kwargs.get("confidence", 0.75),
            docs_downloaded_count=kwargs.get("docs_downloaded_count", 5),
            similar_cases_count=kwargs.get("similar_cases_count", 3),
            success=success,
            error_message=kwargs.get("error_message"),
        )


# =============================================================================
# Core Model Factories
# =============================================================================


class PolicyExcerptFactory:
    """Factory for creating PolicyExcerpt instances."""

    @staticmethod
    def create(
        policy_id: Optional[str] = None,
        doc_id: str = "NPPF",
        score: float = 0.8,
        **kwargs,
    ):
        """Create a PolicyExcerpt with defaults."""
        from plana.policy.search import PolicyExcerpt

        pid = policy_id or f"{doc_id}-{random.randint(1, 200)}"

        return PolicyExcerpt(
            doc_id=doc_id,
            doc_title=kwargs.get("doc_title", "National Planning Policy Framework"),
            policy_id=pid,
            policy_title=kwargs.get("policy_title", "Test Policy"),
            text=kwargs.get("text", "This is a test policy excerpt for testing purposes."),
            page=kwargs.get("page", random.randint(1, 300)),
            score=score,
            match_reason=kwargs.get("match_reason", "Test match"),
        )

    @staticmethod
    def create_batch(count: int, **kwargs) -> list:
        """Create multiple PolicyExcerpt instances."""
        return [PolicyExcerptFactory.create(**kwargs) for _ in range(count)]


# =============================================================================
# API Request Factories
# =============================================================================


class ProcessRequestFactory:
    """Factory for creating API process request data."""

    @staticmethod
    def create(
        reference: Optional[str] = None,
        council_id: str = "newcastle",
        mode: str = "demo",
    ) -> dict:
        """Create a process request payload."""
        return {
            "reference": reference or random_reference(),
            "council_id": council_id,
            "mode": mode,
        }


class ImportRequestFactory:
    """Factory for creating API import request data."""

    @staticmethod
    def create(
        reference: Optional[str] = None,
        address: Optional[str] = None,
        proposal: Optional[str] = None,
        **kwargs,
    ) -> dict:
        """Create an import request payload."""
        return {
            "reference": reference or random_reference(),
            "council_id": kwargs.get("council_id", "newcastle"),
            "address": address or random_address(),
            "proposal": proposal or random_proposal(),
            "application_type": kwargs.get("application_type", "householder"),
            "constraints": kwargs.get("constraints", []),
            "ward": kwargs.get("ward", "Monument"),
        }


class FeedbackRequestFactory:
    """Factory for creating API feedback request data."""

    @staticmethod
    def create(
        reference: Optional[str] = None,
        decision: str = "APPROVE_WITH_CONDITIONS",
        notes: Optional[str] = None,
    ) -> dict:
        """Create a feedback request payload."""
        return {
            "reference": reference or random_reference(),
            "decision": decision,
            "notes": notes or "Test feedback",
        }

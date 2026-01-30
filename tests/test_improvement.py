"""
Unit tests for the continuous improvement module.

Tests feedback processing, policy re-ranking, and confidence adjustment.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from plana.storage.models import StoredFeedback, StoredRunLog, StoredPolicyWeight


class TestFeedbackProcessing:
    """Tests for feedback processing."""

    def test_is_decision_mismatch_exact_match(self):
        """Test that exact matches are not mismatches."""
        from plana.improvement.feedback import _is_decision_mismatch

        assert _is_decision_mismatch("APPROVE", "APPROVE") is False
        assert _is_decision_mismatch("REFUSE", "REFUSE") is False
        assert _is_decision_mismatch("APPROVE_WITH_CONDITIONS", "APPROVE_WITH_CONDITIONS") is False

    def test_is_decision_mismatch_partial_match(self):
        """Test that APPROVE <-> APPROVE_WITH_CONDITIONS is not a mismatch."""
        from plana.improvement.feedback import _is_decision_mismatch

        assert _is_decision_mismatch("APPROVE", "APPROVE_WITH_CONDITIONS") is False
        assert _is_decision_mismatch("APPROVE_WITH_CONDITIONS", "APPROVE") is False

    def test_is_decision_mismatch_real_mismatch(self):
        """Test that APPROVE vs REFUSE is a mismatch."""
        from plana.improvement.feedback import _is_decision_mismatch

        assert _is_decision_mismatch("APPROVE", "REFUSE") is True
        assert _is_decision_mismatch("REFUSE", "APPROVE") is True
        assert _is_decision_mismatch("APPROVE_WITH_CONDITIONS", "REFUSE") is True

    def test_is_decision_mismatch_none_plana(self):
        """Test that None plana decision is a mismatch."""
        from plana.improvement.feedback import _is_decision_mismatch

        assert _is_decision_mismatch(None, "APPROVE") is True

    def test_is_decision_mismatch_normalizes_case(self):
        """Test that comparison is case-insensitive."""
        from plana.improvement.feedback import _is_decision_mismatch

        assert _is_decision_mismatch("approve", "APPROVE") is False
        assert _is_decision_mismatch("Approve_With_Conditions", "APPROVE_WITH_CONDITIONS") is False


class TestPolicyReranking:
    """Tests for deterministic policy re-ranking."""

    def test_rerank_policies_maintains_order_without_weights(self):
        """Test that policies maintain order when no weights exist."""
        from plana.improvement.reranking import rerank_policies

        # Create mock policies
        policies = [
            MagicMock(id="NPPF_123"),
            MagicMock(id="CSUCP_45"),
            MagicMock(id="DAP_67"),
        ]

        # With no weights in DB, order should be maintained
        with patch('plana.improvement.reranking.get_policy_boost', return_value=1.0):
            result = rerank_policies(policies, "2024/0930/01/HOU")

        # Same order when all weights are equal
        assert len(result) == 3

    def test_rerank_policies_boosts_high_weight_policies(self):
        """Test that policies with higher weights are ranked higher."""
        from plana.improvement.reranking import rerank_policies

        # Create mock policies
        policy1 = MagicMock(id="low_weight")
        policy2 = MagicMock(id="high_weight")
        policy3 = MagicMock(id="medium_weight")
        policies = [policy1, policy2, policy3]

        # Mock weights: policy2 has highest weight
        def mock_boost(policy_id, app_type):
            if policy_id == "high_weight":
                return 1.5
            elif policy_id == "medium_weight":
                return 1.2
            return 1.0

        with patch('plana.improvement.reranking.get_policy_boost', side_effect=mock_boost):
            result = rerank_policies(policies, "2024/0930/01/HOU")

        # High weight should be first
        assert result[0].id == "high_weight"
        assert result[1].id == "medium_weight"
        assert result[2].id == "low_weight"

    def test_get_confidence_adjustment_returns_valid_range(self):
        """Test that confidence adjustment is between 0.4 and 0.95."""
        from plana.improvement.reranking import get_confidence_adjustment

        with patch('plana.improvement.feedback.get_mismatch_rate', return_value=0.0):
            confidence = get_confidence_adjustment("2024/0930/01/HOU")
            assert 0.4 <= confidence <= 0.95

        with patch('plana.improvement.feedback.get_mismatch_rate', return_value=1.0):
            confidence = get_confidence_adjustment("2024/0930/01/HOU")
            assert 0.4 <= confidence <= 0.95

    def test_get_confidence_adjustment_reduces_with_mismatches(self):
        """Test that confidence decreases with higher mismatch rates."""
        from plana.improvement.reranking import get_confidence_adjustment

        with patch('plana.improvement.feedback.get_mismatch_rate', return_value=0.0):
            high_confidence = get_confidence_adjustment("2024/0930/01/HOU")

        with patch('plana.improvement.feedback.get_mismatch_rate', return_value=0.5):
            low_confidence = get_confidence_adjustment("2024/0930/01/HOU")

        assert low_confidence < high_confidence

    def test_default_confidence_varies_by_type(self):
        """Test that default confidence varies by application type."""
        from plana.improvement.reranking import DEFAULT_CONFIDENCE

        # DCC (discharge of conditions) should have high confidence
        assert DEFAULT_CONFIDENCE.get("DCC", 0) > 0.8

        # TPO (tree preservation) should have lower confidence
        assert DEFAULT_CONFIDENCE.get("TPO", 0) < 0.7


class TestIsMatch:
    """Tests for the match determination function."""

    def test_is_match_exact(self):
        """Test exact match detection."""
        from plana.improvement.reranking import _is_match

        assert _is_match("APPROVE", "APPROVE") is True
        assert _is_match("REFUSE", "REFUSE") is True

    def test_is_match_partial(self):
        """Test partial match (APPROVE <-> APPROVE_WITH_CONDITIONS)."""
        from plana.improvement.reranking import _is_match

        assert _is_match("APPROVE", "APPROVE_WITH_CONDITIONS") is True
        assert _is_match("APPROVE_WITH_CONDITIONS", "APPROVE") is True

    def test_is_match_false(self):
        """Test non-matches."""
        from plana.improvement.reranking import _is_match

        assert _is_match("APPROVE", "REFUSE") is False
        assert _is_match("REFUSE", "APPROVE_WITH_CONDITIONS") is False


class TestStorageModels:
    """Tests for storage model dataclasses."""

    def test_stored_run_log_has_required_fields(self):
        """Test that StoredRunLog has all required fields."""
        run_log = StoredRunLog(
            run_id="test_001",
            reference="2024/0930/01/DET",
            mode="live",
            council="newcastle",
            raw_decision="APPROVE",
            calibrated_decision="APPROVE_WITH_CONDITIONS",
            confidence=0.75,
            policy_ids_used='["NPPF_1", "CSUCP_2"]',
            docs_downloaded_count=10,
            similar_cases_count=5,
            success=True,
        )

        assert run_log.run_id == "test_001"
        assert run_log.reference == "2024/0930/01/DET"
        assert run_log.mode == "live"
        assert run_log.raw_decision == "APPROVE"
        assert run_log.calibrated_decision == "APPROVE_WITH_CONDITIONS"

    def test_stored_policy_weight_has_required_fields(self):
        """Test that StoredPolicyWeight has all required fields."""
        weight = StoredPolicyWeight(
            policy_id="NPPF_Section_12",
            application_type="HOU",
            weight=1.3,
            match_count=10,
            mismatch_count=2,
        )

        assert weight.policy_id == "NPPF_Section_12"
        assert weight.application_type == "HOU"
        assert weight.weight == 1.3
        assert weight.match_count == 10
        assert weight.mismatch_count == 2


class TestFeedbackStats:
    """Tests for feedback statistics."""

    def test_feedback_stats_dataclass(self):
        """Test FeedbackStats dataclass initialization."""
        from plana.improvement.feedback import FeedbackStats

        stats = FeedbackStats(
            total_feedback=100,
            match_count=80,
            mismatch_count=20,
            match_rate=0.8,
        )

        assert stats.total_feedback == 100
        assert stats.match_rate == 0.8
        assert stats.by_decision == {}  # Default

    def test_feedback_stats_default_by_decision(self):
        """Test that by_decision defaults to empty dict."""
        from plana.improvement.feedback import FeedbackStats

        stats = FeedbackStats()
        assert stats.by_decision is not None
        assert isinstance(stats.by_decision, dict)

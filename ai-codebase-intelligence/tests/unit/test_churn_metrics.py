"""Tests for churn metrics — Nagappan & Ball 2005."""

from __future__ import annotations

from unittest.mock import patch

from ai_codebase_intelligence.core.analysis.churn_metrics import (
    calculate_churn_metrics,
    _count_lines,
)


class TestCalculateChurnMetrics:
    """Test churn metric computation."""

    @patch("ai_codebase_intelligence.core.analysis.churn_metrics.git_file_churn")
    @patch("ai_codebase_intelligence.core.analysis.churn_metrics._count_lines")
    def test_computes_relative_churn(self, mock_loc, mock_churn):
        mock_churn.return_value = {
            "churn_count": 10, "lines_added": 200, "lines_deleted": 50,
        }
        mock_loc.return_value = 500

        result = calculate_churn_metrics("/repo", ["src/main.py"])

        assert len(result["files"]) == 1
        f = result["files"][0]
        assert f["churnCount"] == 10
        assert f["linesAdded"] == 200
        assert f["linesDeleted"] == 50
        assert f["relativeChurn"] == 0.4  # 200/500
        assert f["relativeDeleted"] == 0.1  # 50/500

    @patch("ai_codebase_intelligence.core.analysis.churn_metrics.git_file_churn")
    @patch("ai_codebase_intelligence.core.analysis.churn_metrics._count_lines")
    def test_handles_zero_loc(self, mock_loc, mock_churn):
        mock_churn.return_value = {
            "churn_count": 5, "lines_added": 100, "lines_deleted": 0,
        }
        mock_loc.return_value = 0

        result = calculate_churn_metrics("/repo", ["deleted.py"])

        f = result["files"][0]
        assert f["relativeChurn"] == 0.0
        assert f["relativeDeleted"] == 0.0

    @patch("ai_codebase_intelligence.core.analysis.churn_metrics.git_file_churn")
    @patch("ai_codebase_intelligence.core.analysis.churn_metrics._count_lines")
    def test_repo_level_ratio(self, mock_loc, mock_churn):
        mock_loc.return_value = 100
        # First file has churn, second doesn't
        mock_churn.side_effect = [
            {"churn_count": 5, "lines_added": 50, "lines_deleted": 10},
            {"churn_count": 0, "lines_added": 0, "lines_deleted": 0},
        ]

        result = calculate_churn_metrics("/repo", ["a.py", "b.py"])

        assert result["repoLevel"]["totalFiles"] == 2
        assert result["repoLevel"]["filesWithChurn"] == 1
        assert result["repoLevel"]["filesChurnedRatio"] == 0.5

    @patch("ai_codebase_intelligence.core.analysis.churn_metrics.git_file_churn")
    @patch("ai_codebase_intelligence.core.analysis.churn_metrics._count_lines")
    def test_sorts_by_churn_count_descending(self, mock_loc, mock_churn):
        mock_loc.return_value = 100
        mock_churn.side_effect = [
            {"churn_count": 2, "lines_added": 10, "lines_deleted": 5},
            {"churn_count": 10, "lines_added": 100, "lines_deleted": 50},
        ]

        result = calculate_churn_metrics("/repo", ["low.py", "high.py"])

        assert result["files"][0]["filePath"] == "high.py"
        assert result["files"][1]["filePath"] == "low.py"

    def test_citation_present(self):
        with patch("ai_codebase_intelligence.core.analysis.churn_metrics.git_file_churn") as m:
            m.return_value = {"churn_count": 0, "lines_added": 0, "lines_deleted": 0}
            with patch("ai_codebase_intelligence.core.analysis.churn_metrics._count_lines", return_value=0):
                result = calculate_churn_metrics("/repo", [])
        assert "Nagappan" in result["citation"]

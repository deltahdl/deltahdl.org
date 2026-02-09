"""Unit tests for compute_descendants.py."""

import json
import os
import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Generator
from unittest.mock import patch, MagicMock


SAMPLE_GRAPH = {
    "bootstrap": {"name": "Bootstrap", "depends_on": []},
    "www_redirect": {"name": "WWW Redirect", "depends_on": ["bootstrap"]},
}

SAMPLE_WAITING: dict[str, Any] = {}

FIXED_SINCE = datetime(2026, 1, 11, 2, 0, 0, tzinfo=timezone.utc)


def get_api_url_from_check_workflow(compute_descendants: Any, workflow_key: str) -> str:
    """Helper to capture the API URL from check_workflow_completed."""
    mock_result = MagicMock()
    mock_result.stdout = ""
    with patch("compute_descendants.subprocess.run", return_value=mock_result) as mock_run:
        compute_descendants.check_workflow_completed(workflow_key, "owner/repo", FIXED_SINCE)
    return mock_run.call_args[0][0][2]


class TestParseArgs:
    """Tests for parse_args function."""

    def test_parses_workflow_argument(self, compute_descendants) -> None:
        """Test that --workflow argument is parsed correctly."""
        argv = ["prog", "--workflow", "bootstrap", "--repo", "o/r"]
        with patch.object(sys, "argv", argv):
            args = compute_descendants.parse_args()
        assert args.workflow == "bootstrap"

    def test_parses_repo_argument(self, compute_descendants) -> None:
        """Test that --repo argument is parsed correctly."""
        argv = ["prog", "--workflow", "test", "--repo", "owner/repo"]
        with patch.object(sys, "argv", argv):
            args = compute_descendants.parse_args()
        assert args.repo == "owner/repo"

    def test_graph_defaults_to_standard_path(self, compute_descendants) -> None:
        """Test that --graph defaults to etc/workflow_dependencies.json."""
        argv = ["prog", "--workflow", "test", "--repo", "o/r"]
        with patch.object(sys, "argv", argv):
            args = compute_descendants.parse_args()
        assert args.graph == "etc/workflow_dependencies.json"

    def test_parses_custom_graph_path(self, compute_descendants) -> None:
        """Test that --graph argument is parsed correctly."""
        argv = ["prog", "--workflow", "test", "--repo", "o/r", "--graph", "custom.json"]
        with patch.object(sys, "argv", argv):
            args = compute_descendants.parse_args()
        assert args.graph == "custom.json"

    def test_lookback_hours_defaults_to_24(self, compute_descendants) -> None:
        """Test that --lookback-hours defaults to 24."""
        argv = ["prog", "--workflow", "test", "--repo", "o/r"]
        with patch.object(sys, "argv", argv):
            args = compute_descendants.parse_args()
        assert args.lookback_hours == 24

    def test_parses_lookback_hours(self, compute_descendants) -> None:
        """Test that --lookback-hours argument is parsed correctly."""
        argv = ["prog", "--workflow", "test", "--repo", "o/r", "--lookback-hours", "48"]
        with patch.object(sys, "argv", argv):
            args = compute_descendants.parse_args()
        assert args.lookback_hours == 48


class TestFindDescendants:
    """Tests for find_descendants function."""

    def test_returns_empty_for_leaf_workflow(self, compute_descendants) -> None:
        """Test that a leaf workflow has no descendants."""
        result = compute_descendants.find_descendants(SAMPLE_GRAPH, "www_redirect")
        assert result == []

    def test_returns_direct_descendants(self, compute_descendants) -> None:
        """Test that direct descendants are returned."""
        result = compute_descendants.find_descendants(SAMPLE_GRAPH, "bootstrap")
        assert result == ["www_redirect"]

    def test_returns_empty_for_unknown_workflow(self, compute_descendants) -> None:
        """Test that unknown workflow has no descendants."""
        result = compute_descendants.find_descendants(SAMPLE_GRAPH, "unknown")
        assert result == []


class TestCheckWorkflowCompleted:
    """Tests for check_workflow_completed function."""

    def test_returns_true_when_successful_run_exists(
        self, compute_descendants
    ) -> None:
        """Test returns True when a successful run exists."""
        mock_result = MagicMock()
        mock_result.stdout = "12345\n"
        since = datetime.now(timezone.utc)

        with patch("compute_descendants.subprocess.run", return_value=mock_result):
            result = compute_descendants.check_workflow_completed(
                "Bootstrap", "owner/repo", since
            )
        assert result is True

    def test_returns_false_when_no_successful_run(self, compute_descendants) -> None:
        """Test returns False when no successful run exists."""
        mock_result = MagicMock()
        mock_result.stdout = ""
        since = datetime.now(timezone.utc)

        with patch("compute_descendants.subprocess.run", return_value=mock_result):
            result = compute_descendants.check_workflow_completed(
                "Bootstrap", "owner/repo", since
            )
        assert result is False

    def test_returns_false_when_only_whitespace(self, compute_descendants) -> None:
        """Test returns False when output is only whitespace."""
        mock_result = MagicMock()
        mock_result.stdout = "   \n"
        since = datetime.now(timezone.utc)

        with patch("compute_descendants.subprocess.run", return_value=mock_result):
            result = compute_descendants.check_workflow_completed(
                "Bootstrap", "owner/repo", since
            )
        assert result is False

    def test_uses_workflow_specific_api_endpoint(self, compute_descendants) -> None:
        """Test that API call uses workflow-specific endpoint."""
        api_url = get_api_url_from_check_workflow(compute_descendants, "www_redirect")
        assert "actions/workflows/www_redirect.yml/runs" in api_url

    def test_api_url_includes_status_filter(self, compute_descendants) -> None:
        """Test that API URL includes status=success filter."""
        api_url = get_api_url_from_check_workflow(compute_descendants, "bootstrap")
        assert "status=success" in api_url

    def test_api_url_includes_created_filter(self, compute_descendants) -> None:
        """Test that API URL includes created date filter."""
        api_url = get_api_url_from_check_workflow(compute_descendants, "bootstrap")
        assert "created=%3E%3D2026-01-11T02:00:00Z" in api_url


class TestGetDependencyStatus:
    """Tests for get_dependency_status function."""

    def test_single_dependency_returns_all_met(self, compute_descendants) -> None:
        """Test returns all_met=True when only current workflow is dependency."""
        graph: dict[str, Any] = {"child": {"depends_on": ["parent"]}}
        result = compute_descendants.get_dependency_status(
            graph, "child", "parent", "owner/repo", 24
        )
        assert result["all_met"] is True

    def test_single_dependency_has_satisfied_list(self, compute_descendants) -> None:
        """Test that current workflow is in satisfied list."""
        graph: dict[str, Any] = {"child": {"depends_on": ["parent"]}}
        result = compute_descendants.get_dependency_status(
            graph, "child", "parent", "owner/repo", 24
        )
        assert "parent" in result["satisfied"]

    def test_single_dependency_has_empty_missing(self, compute_descendants) -> None:
        """Test returns empty missing list for single dependency."""
        graph: dict[str, Any] = {"child": {"depends_on": ["parent"]}}
        result = compute_descendants.get_dependency_status(
            graph, "child", "parent", "owner/repo", 24
        )
        assert result["missing"] == []


class TestComputeDescendantsStatus:
    """Tests for compute_descendants_status function."""

    def test_returns_empty_ready_for_leaf_workflow(self, compute_descendants) -> None:
        """Test returns empty ready for leaf workflow."""
        ready, _ = compute_descendants.compute_descendants_status(
            SAMPLE_GRAPH, "www_redirect", "owner/repo", 24
        )
        assert ready == []

    def test_returns_empty_waiting_for_leaf_workflow(self, compute_descendants) -> None:
        """Test returns empty waiting for leaf workflow."""
        _, waiting = compute_descendants.compute_descendants_status(
            SAMPLE_GRAPH, "www_redirect", "owner/repo", 24
        )
        assert waiting == {}

    def test_single_dep_descendants_are_in_ready(self, compute_descendants) -> None:
        """Test that single-dependency descendants are in ready list."""
        ready, _ = compute_descendants.compute_descendants_status(
            SAMPLE_GRAPH, "bootstrap", "owner/repo", 24
        )
        assert ready == ["www_redirect"]


class TestWriteGithubOutput:
    """Tests for write_github_output function."""

    def test_writes_nothing_without_github_output_env(
        self, compute_descendants
    ) -> None:
        """Test that nothing is written when GITHUB_OUTPUT is not set."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("GITHUB_OUTPUT", None)
            compute_descendants.write_github_output(["a"], {"b": {"missing": ["c"]}})
        assert True  # No exception means success

    def test_writes_ready_to_output_file(
        self, compute_descendants, tmp_path
    ) -> None:
        """Test that ready list is written to GITHUB_OUTPUT."""
        output_file = tmp_path / "output"
        output_file.touch()

        with patch.dict(os.environ, {"GITHUB_OUTPUT": str(output_file)}):
            compute_descendants.write_github_output(["www_redirect"], {})

        assert 'ready=["www_redirect"]' in output_file.read_text()

    def test_writes_waiting_to_output_file(
        self, compute_descendants, tmp_path
    ) -> None:
        """Test that waiting dict is written to GITHUB_OUTPUT."""
        output_file = tmp_path / "output"
        output_file.touch()

        waiting = {"www_redirect": {"missing": ["bootstrap"], "satisfied": []}}
        with patch.dict(os.environ, {"GITHUB_OUTPUT": str(output_file)}):
            compute_descendants.write_github_output([], waiting)

        assert "www_redirect" in output_file.read_text()


class TestWriteStepSummary:
    """Tests for write_step_summary function."""

    def test_writes_nothing_without_github_step_summary_env(
        self, compute_descendants
    ) -> None:
        """Test that nothing is written when GITHUB_STEP_SUMMARY is not set."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("GITHUB_STEP_SUMMARY", None)
            compute_descendants.write_step_summary("bootstrap", ["a"], {})
        assert True  # No exception means success

    def test_writes_workflow_name_to_summary(
        self, compute_descendants, tmp_path
    ) -> None:
        """Test that completed workflow name is written to summary."""
        summary_file = tmp_path / "summary"
        summary_file.touch()

        with patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": str(summary_file)}):
            compute_descendants.write_step_summary("bootstrap", [], {})

        assert "bootstrap" in summary_file.read_text()

    def test_writes_ready_workflow_to_summary(
        self, compute_descendants, tmp_path
    ) -> None:
        """Test that ready descendant workflow is shown in summary."""
        summary_file = tmp_path / "summary"
        summary_file.touch()

        with patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": str(summary_file)}):
            compute_descendants.write_step_summary("bootstrap", ["www_redirect"], {})

        assert "www_redirect" in summary_file.read_text()

    def test_shows_no_descendants_message(
        self, compute_descendants, tmp_path
    ) -> None:
        """Test that message is shown when no descendants."""
        summary_file = tmp_path / "summary"
        summary_file.touch()

        with patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": str(summary_file)}):
            compute_descendants.write_step_summary("leaf", [], {})

        assert "No descendants found" in summary_file.read_text()


class TestMain:
    """Tests for main function."""

    @contextmanager
    def _run_main_with_graph(
        self, _compute_descendants: Any, workflow: str = "bootstrap"
    ) -> Generator[None, None, None]:
        """Context manager for running main with mocked graph."""
        argv = ["prog", "--workflow", workflow, "--repo", "o/r"]
        with patch.object(sys, "argv", argv):
            with patch(
                "compute_descendants.load_dependency_graph", return_value=SAMPLE_GRAPH
            ):
                with patch.dict(os.environ, {}, clear=True):
                    os.environ.pop("GITHUB_OUTPUT", None)
                    os.environ.pop("GITHUB_STEP_SUMMARY", None)
                    yield

    def test_returns_0_on_success(self, compute_descendants) -> None:
        """Test returns 0 on success."""
        with self._run_main_with_graph(compute_descendants):
            result = compute_descendants.main()
        assert result == 0

    def test_stdout_contains_completed_workflow(
        self, compute_descendants, capsys
    ) -> None:
        """Test that stdout contains completed_workflow field."""
        with self._run_main_with_graph(compute_descendants):
            compute_descendants.main()

        output = json.loads(capsys.readouterr().out)
        assert output["completed_workflow"] == "bootstrap"

    def test_stdout_contains_ready_descendants(
        self, compute_descendants, capsys
    ) -> None:
        """Test that stdout contains ready descendants."""
        with self._run_main_with_graph(compute_descendants):
            compute_descendants.main()

        output = json.loads(capsys.readouterr().out)
        assert output["ready"] == ["www_redirect"]

"""Unit tests for get_running.py and utils.py."""

import json
import sys
from unittest.mock import MagicMock, patch


# Sample dependency graph for testing
SAMPLE_GRAPH = {
    "bootstrap": {
        "name": "Bootstrap",
        "depends_on": [],
        "paths": ["src/bootstrap/**"],
    },
    "www_redirect": {
        "name": "WWW Redirect",
        "depends_on": ["bootstrap"],
        "paths": ["src/www/redirect/**"],
    },
}


class TestBuildNameToKeyMap:
    """Tests for build_name_to_key_map function."""

    def test_empty_graph(self, utils) -> None:
        """Test with empty graph."""
        name_to_key = utils.build_name_to_key_map({})
        assert not name_to_key

    def test_workflow_without_name(self, utils) -> None:
        """Test workflow config without name field is skipped."""
        graph = {
            "no_name": {"depends_on": [], "paths": ["src/**"]},
            "with_name": {"name": "Named Workflow", "depends_on": []},
        }
        name_to_key = utils.build_name_to_key_map(graph)
        assert name_to_key == {"Named Workflow": "with_name"}


class TestGetWorkflowRuns:
    """Tests for get_workflow_runs function."""

    @patch("utils.subprocess.run")
    def test_returns_runs_on_success(self, mock_run: MagicMock, utils) -> None:
        """Test successful API response parsing."""
        runs = [
            {"id": 123, "name": "Bootstrap", "status": "in_progress"},
            {"id": 456, "name": "WWW Redirect", "status": "in_progress"},
        ]
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps(runs),
            stderr=""
        )
        result = utils.get_workflow_runs("owner/repo", "in_progress")
        assert result == runs

    @patch("utils.subprocess.run")
    def test_returns_empty_on_api_error(self, mock_run: MagicMock, utils) -> None:
        """Test API error returns empty list."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="API error"
        )
        result = utils.get_workflow_runs("owner/repo", "in_progress")
        assert result == []

    @patch("utils.subprocess.run")
    def test_returns_empty_on_invalid_json(self, mock_run: MagicMock, utils) -> None:
        """Test invalid JSON returns empty list."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="not valid json",
            stderr=""
        )
        result = utils.get_workflow_runs("owner/repo", "in_progress")
        assert result == []

    @patch("utils.subprocess.run")
    def test_returns_empty_on_empty_response(self, mock_run: MagicMock, utils) -> None:
        """Test empty response returns empty list."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="",
            stderr=""
        )
        result = utils.get_workflow_runs("owner/repo", "in_progress")
        assert result == []


def _run_main_with_exclude_flag(get_running, capsys):
    """Helper to run main with --exclude-workflowctl flag."""
    graph = {
        "bootstrap": {"name": "Bootstrap", "depends_on": []},
        "workflowctl": {"name": "Workflow Controller", "depends_on": []},
    }
    runs = [
        {"name": "Bootstrap", "status": "in_progress"},
        {"name": "Workflow Controller", "status": "in_progress"},
    ]
    argv = [
        "prog", "--graph", "g.json", "--repo", "o/r", "--exclude-workflowctl"
    ]
    with patch.object(sys, "argv", argv):
        with patch("get_running.load_graph_with_error", return_value=(graph, "")):
            with patch("get_running.get_workflow_runs", return_value=runs):
                get_running.main()
    out = capsys.readouterr().out
    return json.loads(out)


class TestMainExcludeWorkflowctl:
    """Tests for workflowctl exclusion in main."""

    def test_excludes_workflowctl_when_flag_set(self, get_running, capsys) -> None:
        """Test workflowctl workflow is excluded when flag is set."""
        result = _run_main_with_exclude_flag(get_running, capsys)
        assert "workflowctl" not in result["workflows"]

    def test_includes_bootstrap_when_exclude_flag_set(self, get_running, capsys) -> None:
        """Test bootstrap workflow is still included when exclude flag is set."""
        result = _run_main_with_exclude_flag(get_running, capsys)
        assert "bootstrap" in result["workflows"]

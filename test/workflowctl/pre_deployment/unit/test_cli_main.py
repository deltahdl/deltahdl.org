"""Unit tests for workflowctl CLI main() functions.

These tests verify the main() flow of each CLI command with all external
dependencies mocked (gh CLI calls, file system). Per the test tenets,
these are unit tests because they test single components (main functions)
with dependencies mocked, not cross-file compatibility.
"""

import json
import sys
from unittest.mock import patch


class TestCancelMain:
    """Unit tests for cancel.py main()."""

    def test_no_running_workflows_exits_zero(
        self, cancel, sample_graph_file
    ) -> None:
        """Main returns 0 when no workflows are running."""
        test_args = [
            "cancel", "--repo", "owner/repo",
            "--changed-files", "src/bootstrap/main.py",
            "--running", "[]", "--graph", sample_graph_file,
        ]
        with patch.object(sys, "argv", test_args):
            assert cancel.main() == 0

    def test_invalid_running_json_exits_one(
        self, cancel, sample_graph_file
    ) -> None:
        """Main returns 1 for invalid --running JSON."""
        test_args = [
            "cancel", "--repo", "owner/repo",
            "--changed-files", "src/bootstrap/main.py",
            "--running", "not-valid-json", "--graph", sample_graph_file,
        ]
        with patch.object(sys, "argv", test_args):
            assert cancel.main() == 1

    def test_missing_graph_exits_one(self, cancel) -> None:
        """Main returns 1 when graph file is missing."""
        test_args = [
            "cancel", "--repo", "owner/repo",
            "--changed-files", "src/bootstrap/main.py",
            "--running", '["www_redirect"]',
            "--graph", "/nonexistent/graph.json",
        ]
        with patch.object(sys, "argv", test_args):
            assert cancel.main() == 1

    @patch("cancel.get_cancelable_runs")
    def test_no_matching_runs_exits_zero(
        self, mock_get_runs, cancel, sample_graph_file
    ) -> None:
        """Main returns 0 when no runs match workflows to cancel."""
        mock_get_runs.return_value = []
        test_args = [
            "cancel", "--repo", "owner/repo",
            "--changed-files", "src/bootstrap/main.py",
            "--running", '["www_redirect"]',
            "--graph", sample_graph_file,
        ]
        with patch.object(sys, "argv", test_args):
            assert cancel.main() == 0

    @patch("cancel.cancel_run")
    @patch("cancel.get_cancelable_runs")
    def test_successful_cancel_exits_zero(
        self, mock_get_runs, mock_cancel, cancel, sample_graph_file
    ) -> None:
        """Main returns 0 when all cancellations succeed."""
        mock_get_runs.side_effect = [
            [{"id": 123, "name": "WWW Redirect", "run_number": 1}],
            [],
        ]
        mock_cancel.return_value = True
        test_args = [
            "cancel", "--repo", "owner/repo",
            "--changed-files", "src/www/redirect/test.py",
            "--running", '["www_redirect"]',
            "--graph", sample_graph_file,
        ]
        with patch.object(sys, "argv", test_args):
            assert cancel.main() == 0

    @patch("cancel.cancel_run")
    @patch("cancel.get_cancelable_runs")
    def test_failed_cancel_exits_one(
        self, mock_get_runs, mock_cancel, cancel, sample_graph_file
    ) -> None:
        """Main returns 1 when a cancellation fails."""
        mock_get_runs.side_effect = [
            [{"id": 123, "name": "WWW Redirect", "run_number": 1}],
            [],
        ]
        mock_cancel.return_value = False
        test_args = [
            "cancel", "--repo", "owner/repo",
            "--changed-files", "src/www/redirect/test.py",
            "--running", '["www_redirect"]',
            "--graph", sample_graph_file,
        ]
        with patch.object(sys, "argv", test_args):
            assert cancel.main() == 1


class TestDispatchRootsMain:
    """Unit tests for dispatch_roots.py main()."""

    def test_missing_graph_exits_one(self, dispatch_roots) -> None:
        """Main returns 1 when graph file is missing."""
        test_args = [
            "dispatch_roots", "--repo", "owner/repo",
            "--changed-files", "src/bootstrap/main.py",
            "--graph", "/nonexistent/graph.json",
        ]
        with patch.object(sys, "argv", test_args):
            assert dispatch_roots.main() == 1

    def test_invalid_running_json_exits_one(
        self, dispatch_roots, sample_graph_file
    ) -> None:
        """Main returns 1 for invalid --running JSON."""
        test_args = [
            "dispatch_roots", "--repo", "owner/repo",
            "--changed-files", "src/bootstrap/main.py",
            "--running", "not-valid-json",
            "--graph", sample_graph_file,
        ]
        with patch.object(sys, "argv", test_args):
            assert dispatch_roots.main() == 1

    def test_no_roots_exits_zero(
        self, dispatch_roots, sample_graph_file
    ) -> None:
        """Main returns 0 when no roots need dispatching."""
        test_args = [
            "dispatch_roots", "--repo", "owner/repo",
            "--changed-files", "unrelated/file.txt",
            "--graph", sample_graph_file,
        ]
        with patch.object(sys, "argv", test_args):
            assert dispatch_roots.main() == 0

    @patch("dispatch_roots.workflow_file_exists")
    @patch("dispatch_roots.dispatch_workflow")
    def test_successful_dispatch_exits_zero(
        self, mock_dispatch, mock_exists,
        dispatch_roots, sample_graph_file
    ) -> None:
        """Main returns 0 when dispatch succeeds."""
        mock_exists.return_value = True
        mock_dispatch.return_value = True
        test_args = [
            "dispatch_roots", "--repo", "owner/repo",
            "--changed-files", "src/bootstrap/main.py",
            "--graph", sample_graph_file,
        ]
        with patch.object(sys, "argv", test_args):
            assert dispatch_roots.main() == 0

    @patch("dispatch_roots.workflow_file_exists")
    @patch("dispatch_roots.dispatch_workflow")
    def test_failed_dispatch_exits_one(
        self, mock_dispatch, mock_exists,
        dispatch_roots, sample_graph_file
    ) -> None:
        """Main returns 1 when dispatch fails."""
        mock_exists.return_value = True
        mock_dispatch.return_value = False
        test_args = [
            "dispatch_roots", "--repo", "owner/repo",
            "--changed-files", "src/bootstrap/main.py",
            "--graph", sample_graph_file,
        ]
        with patch.object(sys, "argv", test_args):
            assert dispatch_roots.main() == 1

    @patch("dispatch_roots.workflow_file_exists")
    def test_skips_nonexistent_workflow_file(
        self, mock_exists, dispatch_roots, sample_graph_file
    ) -> None:
        """Main skips workflows whose files don't exist."""
        mock_exists.return_value = False
        test_args = [
            "dispatch_roots", "--repo", "owner/repo",
            "--changed-files", "src/bootstrap/main.py",
            "--graph", sample_graph_file,
        ]
        with patch.object(sys, "argv", test_args):
            assert dispatch_roots.main() == 0

    @patch("dispatch_roots.workflow_file_exists")
    @patch("dispatch_roots.dispatch_workflow")
    def test_trigger_descendants_flag_passes_true(
        self, mock_dispatch, mock_exists,
        dispatch_roots, sample_graph_file
    ) -> None:
        """Main passes trigger_descendants=True when flag is set."""
        mock_exists.return_value = True
        mock_dispatch.return_value = True
        test_args = [
            "dispatch_roots", "--repo", "owner/repo",
            "--changed-files", "src/bootstrap/main.py",
            "--trigger-descendants",
            "--graph", sample_graph_file,
        ]
        with patch.object(sys, "argv", test_args):
            dispatch_roots.main()
        mock_dispatch.assert_called_with(
            "bootstrap", "owner/repo", True, False
        )
        assert True  # Explicit pass

    @patch("dispatch_roots.workflow_file_exists")
    @patch("dispatch_roots.dispatch_workflow")
    def test_commit_message_triggers_descendants(
        self, mock_dispatch, mock_exists,
        dispatch_roots, sample_graph_file
    ) -> None:
        """Main triggers descendants when commit message has directive."""
        mock_exists.return_value = True
        mock_dispatch.return_value = True
        test_args = [
            "dispatch_roots", "--repo", "owner/repo",
            "--changed-files", "src/bootstrap/main.py",
            "--commit-message", "Fix bug [trigger descendants]",
            "--graph", sample_graph_file,
        ]
        with patch.object(sys, "argv", test_args):
            dispatch_roots.main()
        mock_dispatch.assert_called_with(
            "bootstrap", "owner/repo", True, False
        )
        assert True  # Explicit pass


class TestGetRunningMain:
    """Unit tests for get_running.py main()."""

    @staticmethod
    def _run_and_parse(get_running, graph_file: str, capsys) -> dict:
        """Run get_running.main() and return parsed JSON output."""
        test_args = [
            "get_running", "--repo", "owner/repo",
            "--graph", graph_file,
        ]
        with patch.object(sys, "argv", test_args):
            get_running.main()
        return json.loads(capsys.readouterr().out)

    def test_missing_graph_exits_one(self, get_running) -> None:
        """Main returns 1 when graph file is missing."""
        test_args = [
            "get_running", "--repo", "owner/repo",
            "--graph", "/nonexistent/graph.json",
        ]
        with patch.object(sys, "argv", test_args):
            assert get_running.main() == 1

    @patch("get_running.get_workflow_runs")
    def test_no_running_workflows_outputs_empty(
        self, mock_get_runs, get_running, sample_graph_file, capsys
    ) -> None:
        """Main outputs empty workflows list when none running."""
        mock_get_runs.return_value = []
        output = self._run_and_parse(
            get_running, sample_graph_file, capsys
        )
        assert output == {"workflows": []}

    @patch("get_running.get_workflow_runs")
    def test_returns_running_workflow_keys(
        self, mock_get_runs, get_running, sample_graph_file, capsys
    ) -> None:
        """Main returns workflow keys for running workflows."""
        mock_get_runs.side_effect = [
            [{"name": "WWW Redirect"}, {"name": "Bootstrap"}],
            [],
        ]
        output = self._run_and_parse(
            get_running, sample_graph_file, capsys
        )
        assert set(output["workflows"]) == {"bootstrap", "www_redirect"}

    @patch("get_running.get_workflow_runs")
    def test_excludes_unknown_workflows(
        self, mock_get_runs, get_running, sample_graph_file, capsys
    ) -> None:
        """Main excludes workflows not in graph."""
        mock_get_runs.side_effect = [
            [{"name": "Unknown Workflow"}, {"name": "Bootstrap"}],
            [],
        ]
        output = self._run_and_parse(
            get_running, sample_graph_file, capsys
        )
        assert output["workflows"] == ["bootstrap"]


class TestComputeRootsMain:
    """Unit tests for compute_roots.py main()."""

    @staticmethod
    def _run_and_parse(compute_roots, args: list, capsys) -> dict:
        """Run compute_roots.main() and return parsed JSON output."""
        with patch.object(sys, "argv", ["compute_roots"] + args):
            compute_roots.main()
        return json.loads(capsys.readouterr().out)

    def test_missing_graph_exits_one(self, compute_roots) -> None:
        """Main exits 1 when graph file is missing."""
        test_args = [
            "compute_roots", "--changed-files", "src/bootstrap/main.py",
            "--graph", "/nonexistent/graph.json",
        ]
        with patch.object(sys, "argv", test_args):
            try:
                compute_roots.main()
            except SystemExit as e:
                assert e.code == 1

    def test_no_affected_files_outputs_empty(
        self, compute_roots, sample_graph_file, capsys
    ) -> None:
        """Main outputs empty workflows when no files match."""
        args = [
            "--changed-files", "unrelated/file.txt",
            "--graph", sample_graph_file,
        ]
        output = self._run_and_parse(compute_roots, args, capsys)
        assert output == {"workflows": []}

    def test_outputs_root_workflow(
        self, compute_roots, sample_graph_file, capsys
    ) -> None:
        """Main outputs root workflow for changed files."""
        args = [
            "--changed-files", "src/bootstrap/main.py",
            "--graph", sample_graph_file,
        ]
        output = self._run_and_parse(compute_roots, args, capsys)
        assert output == {"workflows": ["bootstrap"]}

    def test_start_from_overrides_file_detection(
        self, compute_roots, sample_graph_file, capsys
    ) -> None:
        """Main uses --start-from instead of file detection."""
        args = [
            "--changed-files", "src/bootstrap/main.py",
            "--start-from", "www_redirect",
            "--graph", sample_graph_file,
        ]
        output = self._run_and_parse(compute_roots, args, capsys)
        assert output == {"workflows": ["www_redirect"]}

    def test_invalid_start_from_exits_one(
        self, compute_roots, sample_graph_file
    ) -> None:
        """Main exits 1 for unknown --start-from workflow."""
        test_args = [
            "compute_roots", "--changed-files", "src/bootstrap/main.py",
            "--start-from", "nonexistent_workflow",
            "--graph", sample_graph_file,
        ]
        with patch.object(sys, "argv", test_args):
            try:
                compute_roots.main()
            except SystemExit as e:
                assert e.code == 1

    def test_execution_plan_includes_all_descendants(
        self, compute_roots, sample_graph_file, capsys
    ) -> None:
        """Main with --execution-plan includes all descendants."""
        args = [
            "--changed-files", "src/bootstrap/main.py",
            "--execution-plan", "--graph", sample_graph_file,
        ]
        output = self._run_and_parse(compute_roots, args, capsys)
        assert set(output["workflows"]) == {"bootstrap", "www_redirect"}

    def test_levels_output_structure(
        self, compute_roots, sample_graph_file, capsys
    ) -> None:
        """Main with --levels outputs correct level structure."""
        args = [
            "--changed-files", "src/bootstrap/main.py",
            "--levels", "--graph", sample_graph_file,
        ]
        output = self._run_and_parse(compute_roots, args, capsys)
        assert "levels" in output and isinstance(output["levels"], list)

    def test_levels_first_level_has_bootstrap(
        self, compute_roots, sample_graph_file, capsys
    ) -> None:
        """Main with --levels has bootstrap in first level."""
        args = [
            "--changed-files", "src/bootstrap/main.py",
            "--levels", "--graph", sample_graph_file,
        ]
        output = self._run_and_parse(compute_roots, args, capsys)
        assert "bootstrap" in output["levels"][0]

    def test_indexed_output_structure(
        self, compute_roots, sample_graph_file, capsys
    ) -> None:
        """Main with --indexed outputs correct structure."""
        args = [
            "--changed-files", "src/bootstrap/main.py",
            "--indexed", "--graph", sample_graph_file,
        ]
        output = self._run_and_parse(compute_roots, args, capsys)
        assert "workflows" in output and isinstance(
            output["workflows"], list
        )

    def test_indexed_workflow_has_required_fields(
        self, compute_roots, sample_graph_file, capsys
    ) -> None:
        """Main with --indexed has idx and name fields."""
        args = [
            "--changed-files", "src/bootstrap/main.py",
            "--indexed", "--graph", sample_graph_file,
        ]
        output = self._run_and_parse(compute_roots, args, capsys)
        assert (
            "idx" in output["workflows"][0]
            and "name" in output["workflows"][0]
        )

    def test_slots_output_has_count_and_keys(
        self, compute_roots, sample_graph_file, capsys
    ) -> None:
        """Main with --slots outputs count and key variables."""
        args = [
            "--changed-files", "src/bootstrap/main.py",
            "--execution-plan", "--slots", "5",
            "--graph", sample_graph_file,
        ]
        with patch.object(sys, "argv", ["compute_roots"] + args):
            compute_roots.main()
        lines = capsys.readouterr().out.strip().split("\n")
        has_count = any(line.startswith("count=") for line in lines)
        has_key = any(line.startswith("key_01=") for line in lines)
        assert has_count and has_key

    def test_running_merges_with_roots(
        self, compute_roots, sample_graph_file, capsys
    ) -> None:
        """Main with --running merges running workflows with roots."""
        args = [
            "--changed-files", "src/www/redirect/main.py",
            "--running", '["bootstrap"]',
            "--graph", sample_graph_file,
        ]
        output = self._run_and_parse(compute_roots, args, capsys)
        assert "bootstrap" in output["workflows"]

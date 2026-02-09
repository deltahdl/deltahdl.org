"""Unit tests for utils.py."""

import argparse
import sys
from unittest.mock import patch, MagicMock, mock_open

import pytest


class TestCreateBaseParser:
    """Tests for create_base_parser function."""

    def test_creates_parser_with_description(self, utils) -> None:
        """Test that parser is created with the given description."""
        parser = utils.create_base_parser("Test description")
        assert "Test description" in parser.description

    def test_adds_repo_argument(self, utils) -> None:
        """Test that --repo argument is added and required."""
        parser = utils.create_base_parser("Test")
        with patch.object(sys, "argv", ["prog", "--repo", "owner/repo"]):
            args = parser.parse_args()
        assert args.repo == "owner/repo"

    def test_adds_graph_argument_with_default(self, utils) -> None:
        """Test that --graph argument has correct default."""
        parser = utils.create_base_parser("Test")
        with patch.object(sys, "argv", ["prog", "--repo", "o/r"]):
            args = parser.parse_args()
        assert args.graph == "etc/workflow_dependencies.json"

    def test_graph_argument_can_be_overridden(self, utils) -> None:
        """Test that --graph argument can be overridden."""
        parser = utils.create_base_parser("Test")
        with patch.object(sys, "argv", ["prog", "--repo", "o/r", "--graph", "custom.json"]):
            args = parser.parse_args()
        assert args.graph == "custom.json"


class TestAddChangedFilesArg:
    """Tests for add_changed_files_arg function."""

    def test_adds_changed_files_argument(self, utils) -> None:
        """Test that --changed-files argument is added."""
        parser = argparse.ArgumentParser()
        utils.add_changed_files_arg(parser)
        with patch.object(sys, "argv", ["prog", "--changed-files", "file1.py,file2.py"]):
            args = parser.parse_args()
        assert args.changed_files == "file1.py,file2.py"

    def test_changed_files_is_required(self, utils) -> None:
        """Test that --changed-files argument is required and errors without it."""
        parser = argparse.ArgumentParser()
        utils.add_changed_files_arg(parser)
        with patch.object(sys, "argv", ["prog"]):
            with pytest.raises(SystemExit):
                parser.parse_args()


class TestAddRunningArg:
    """Tests for add_running_arg function."""

    def test_adds_running_argument_with_default(self, utils) -> None:
        """Test that --running argument has correct default."""
        parser = argparse.ArgumentParser()
        utils.add_running_arg(parser)
        with patch.object(sys, "argv", ["prog"]):
            args = parser.parse_args()
        assert args.running == "[]"

    def test_running_argument_can_be_overridden(self, utils) -> None:
        """Test that --running argument can be overridden."""
        parser = argparse.ArgumentParser()
        utils.add_running_arg(parser)
        with patch.object(sys, "argv", ["prog", "--running", '["workflow1"]']):
            args = parser.parse_args()
        assert args.running == '["workflow1"]'


class TestParseChangedFiles:
    """Tests for parse_changed_files function."""

    @pytest.mark.parametrize(
        "input_str,expected",
        [
            ("file.py", ["file.py"]),
            ("file1.py,file2.py,file3.py", ["file1.py", "file2.py", "file3.py"]),
            ("file1.py, file2.py , file3.py", ["file1.py", "file2.py", "file3.py"]),
            ("file1.py,,file2.py,", ["file1.py", "file2.py"]),
            ("", []),
            (",,,", []),
        ],
        ids=[
            "single_file",
            "multiple_files",
            "strips_whitespace",
            "filters_empty_strings",
            "empty_string",
            "only_commas",
        ],
    )
    def test_parse_changed_files(self, utils, input_str: str, expected: list) -> None:
        """Test parse_changed_files with various inputs."""
        result = utils.parse_changed_files(input_str)
        assert result == expected


class TestParseRunningWorkflows:
    """Tests for parse_running_workflows function."""

    def test_parses_valid_json_array_returns_workflows(self, utils) -> None:
        """Test parsing valid JSON array returns correct workflows."""
        workflows, _ = utils.parse_running_workflows('["workflow1", "workflow2"]')
        assert workflows == ["workflow1", "workflow2"]

    def test_parses_valid_json_array_returns_no_error(self, utils) -> None:
        """Test parsing valid JSON array returns no error."""
        _, error = utils.parse_running_workflows('["workflow1", "workflow2"]')
        assert error is None

    def test_parses_empty_array_returns_empty_list(self, utils) -> None:
        """Test parsing empty JSON array returns empty list."""
        workflows, _ = utils.parse_running_workflows("[]")
        assert workflows == []

    def test_parses_empty_array_returns_no_error(self, utils) -> None:
        """Test parsing empty JSON array returns no error."""
        _, error = utils.parse_running_workflows("[]")
        assert error is None

    def test_invalid_json_returns_empty_workflows(self, utils) -> None:
        """Test that invalid JSON returns empty workflows list."""
        workflows, _ = utils.parse_running_workflows("not valid json")
        assert workflows == []

    def test_invalid_json_returns_error_message(self, utils) -> None:
        """Test that invalid JSON returns error message containing Invalid JSON."""
        _, error = utils.parse_running_workflows("not valid json")
        assert "Invalid JSON" in error


class TestLoadDependencyGraph:
    """Tests for load_dependency_graph function."""

    def test_loads_json_file(self, utils) -> None:
        """Test that JSON file is loaded correctly."""
        mock_data = '{"workflow1": {"name": "Test"}}'
        with patch("builtins.open", mock_open(read_data=mock_data)):
            result = utils.load_dependency_graph("test.json")
        assert result == {"workflow1": {"name": "Test"}}

    def test_raises_on_file_not_found(self, utils) -> None:
        """Test that FileNotFoundError is raised for missing file."""
        with patch("builtins.open", side_effect=FileNotFoundError()):
            with pytest.raises(FileNotFoundError):
                utils.load_dependency_graph("missing.json")


class TestLoadGraphWithError:
    """Tests for load_graph_with_error function."""

    def test_returns_graph_on_success(self, utils) -> None:
        """Test that graph is returned on success."""
        mock_data = '{"workflow1": {"name": "Test"}}'
        with patch("builtins.open", mock_open(read_data=mock_data)):
            graph, _ = utils.load_graph_with_error("test.json")
        assert graph == {"workflow1": {"name": "Test"}}

    def test_returns_empty_error_on_success(self, utils) -> None:
        """Test that empty error string is returned on success."""
        mock_data = '{"workflow1": {"name": "Test"}}'
        with patch("builtins.open", mock_open(read_data=mock_data)):
            _, error = utils.load_graph_with_error("test.json")
        assert error == ""

    def test_returns_none_graph_for_missing_file(self, utils) -> None:
        """Test that None graph is returned for missing file."""
        with patch("builtins.open", side_effect=FileNotFoundError()):
            graph, _ = utils.load_graph_with_error("missing.json")
        assert graph is None

    def test_returns_error_message_for_missing_file(self, utils) -> None:
        """Test that error message is returned for missing file."""
        with patch("builtins.open", side_effect=FileNotFoundError()):
            _, error = utils.load_graph_with_error("missing.json")
        assert "not found" in error


class TestLoadGraphOrExit:
    """Tests for load_graph_or_exit function."""

    def test_returns_graph_on_success(self, utils) -> None:
        """Test that graph is returned on success."""
        mock_data = '{"workflow1": {"name": "Test"}}'
        with patch("builtins.open", mock_open(read_data=mock_data)):
            graph, _ = utils.load_graph_or_exit("test.json")
        assert graph == {"workflow1": {"name": "Test"}}

    def test_returns_none_error_on_success(self, utils) -> None:
        """Test that None error is returned on success."""
        mock_data = '{"workflow1": {"name": "Test"}}'
        with patch("builtins.open", mock_open(read_data=mock_data)):
            _, error = utils.load_graph_or_exit("test.json")
        assert error is None

    def test_returns_none_graph_for_missing_file(self, utils) -> None:
        """Test that None graph is returned for missing file."""
        with patch("builtins.open", side_effect=FileNotFoundError()):
            graph, _ = utils.load_graph_or_exit("missing.json")
        assert graph is None

    def test_returns_error_for_missing_file(self, utils) -> None:
        """Test that error is returned for missing file."""
        with patch("builtins.open", side_effect=FileNotFoundError()):
            _, error = utils.load_graph_or_exit("missing.json")
        assert error is not None


class TestRunSubprocess:
    """Tests for run_subprocess function."""

    def test_returns_subprocess_result(self, utils) -> None:
        """Test that subprocess result is returned."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        with patch("utils.subprocess.run", return_value=mock_result):
            result = utils.run_subprocess(["echo", "test"])
        assert result == mock_result

    def test_passes_capture_output_true(self, utils) -> None:
        """Test that capture_output=True is passed to subprocess.run."""
        with patch("utils.subprocess.run") as mock_run:
            utils.run_subprocess(["echo", "test"])
        _, kwargs = mock_run.call_args
        assert kwargs["capture_output"] is True

    def test_passes_text_true(self, utils) -> None:
        """Test that text=True is passed to subprocess.run."""
        with patch("utils.subprocess.run") as mock_run:
            utils.run_subprocess(["echo", "test"])
        _, kwargs = mock_run.call_args
        assert kwargs["text"] is True

    def test_passes_check_false(self, utils) -> None:
        """Test that check=False is passed to subprocess.run."""
        with patch("utils.subprocess.run") as mock_run:
            utils.run_subprocess(["echo", "test"])
        _, kwargs = mock_run.call_args
        assert kwargs["check"] is False


class TestDispatchGhWorkflow:
    """Tests for dispatch_gh_workflow function."""

    def test_returns_true_on_success(self, utils) -> None:
        """Test returns True when command succeeds."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        with patch("utils.run_subprocess", return_value=mock_result):
            result = utils.dispatch_gh_workflow("workflow.yml", "owner/repo")
        assert result is True

    def test_returns_false_on_failure(self, utils) -> None:
        """Test returns False when command fails."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "error message"
        with patch("utils.run_subprocess", return_value=mock_result):
            result = utils.dispatch_gh_workflow("workflow.yml", "owner/repo")
        assert result is False

    def test_builds_correct_command(self, utils) -> None:
        """Test that correct command is built."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        with patch("utils.run_subprocess", return_value=mock_result) as mock_run:
            utils.dispatch_gh_workflow("workflow.yml", "owner/repo")
        cmd = mock_run.call_args[0][0]
        assert cmd == ["gh", "workflow", "run", "workflow.yml", "--repo", "owner/repo"]

    def test_appends_extra_args_flag(self, utils) -> None:
        """Test that -f flag is appended to command."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        with patch("utils.run_subprocess", return_value=mock_result) as mock_run:
            utils.dispatch_gh_workflow("workflow.yml", "owner/repo", ["-f", "key=value"])
        cmd = mock_run.call_args[0][0]
        assert "-f" in cmd

    def test_appends_extra_args_value(self, utils) -> None:
        """Test that key=value is appended to command."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        with patch("utils.run_subprocess", return_value=mock_result) as mock_run:
            utils.dispatch_gh_workflow("workflow.yml", "owner/repo", ["-f", "key=value"])
        cmd = mock_run.call_args[0][0]
        assert "key=value" in cmd


class TestFileMatchesPatternDoublestar:
    """Tests for ** pattern matching via directory prefix."""

    def test_matches_via_startswith_when_fnmatch_fails(self, utils) -> None:
        """Test ** pattern matches via startswith when fnmatch fails."""
        # Pattern src/api/**/*.py with file src/api/v1/test (no .py)
        # fnmatch(src/api/v1/test, src/api/*/*.py) = False
        # but startswith(src/api/) = True, so line 174 is hit
        result = utils.file_matches_pattern("src/api/v1/test", "src/api/**/*.py")
        assert result is True

    def test_doublestar_requires_prefix_match(self, utils) -> None:
        """Test ** pattern requires correct directory prefix."""
        result = utils.file_matches_pattern("srcapi/file.py", "src/api/**")
        assert result is False

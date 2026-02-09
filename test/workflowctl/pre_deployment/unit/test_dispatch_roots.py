"""Unit tests for dispatch_roots.py."""
import sys

from unittest.mock import MagicMock, mock_open, patch


class TestShouldTriggerDescendants:
    """Tests for should_trigger_descendants function."""

    def test_returns_true_when_flag_is_true(self, dispatch_roots) -> None:
        """Test returns True when trigger_flag is True."""
        assert dispatch_roots.should_trigger_descendants(True, "") is True

    def test_returns_true_when_commit_has_tag(self, dispatch_roots) -> None:
        """Test returns True when commit message has [trigger descendants]."""
        assert dispatch_roots.should_trigger_descendants(
            False, "feat: add feature [trigger descendants]"
        ) is True

    def test_returns_true_when_commit_has_tag_case_insensitive(self, dispatch_roots) -> None:
        """Test [Trigger Descendants] tag is case insensitive."""
        assert dispatch_roots.should_trigger_descendants(
            False, "feat: add feature [Trigger Descendants]"
        ) is True

    def test_returns_false_when_no_conditions_met(self, dispatch_roots) -> None:
        """Test returns False when no conditions are met."""
        assert dispatch_roots.should_trigger_descendants(
            False, "feat: normal commit"
        ) is False


class TestWorkflowFileExists:
    """Tests for workflow_file_exists function."""

    @patch("os.path.isfile")
    def test_returns_true_when_file_exists(self, mock_isfile: MagicMock, dispatch_roots) -> None:
        """Test returns True when workflow file exists."""
        mock_isfile.return_value = True
        assert dispatch_roots.workflow_file_exists("bootstrap") is True

    @patch("os.path.isfile")
    def test_checks_correct_path(self, mock_isfile: MagicMock, dispatch_roots) -> None:
        """Test checks correct workflow file path."""
        mock_isfile.return_value = True
        dispatch_roots.workflow_file_exists("bootstrap")
        mock_isfile.assert_called_once_with(".github/workflows/bootstrap.yml")
        assert True  # Explicit pass

    @patch("os.path.isfile")
    def test_returns_false_when_file_missing(self, mock_isfile: MagicMock, dispatch_roots) -> None:
        """Test returns False when workflow file is missing."""
        mock_isfile.return_value = False
        assert dispatch_roots.workflow_file_exists("missing") is False


class TestWorkflowAcceptsInput:
    """Tests for workflow_accepts_input function."""

    def test_returns_true_when_input_present(self, dispatch_roots) -> None:
        """Test returns True when specified input is defined."""
        content = """
name: Test Workflow
on:
  workflow_dispatch:
    inputs:
      trigger_descendants:
        default: false
        type: boolean
"""
        with patch("builtins.open", mock_open(read_data=content)):
            assert dispatch_roots.workflow_accepts_input("test", "trigger_descendants") is True

    def test_returns_false_when_input_missing(self, dispatch_roots) -> None:
        """Test returns False when specified input is not defined."""
        content = """
name: Test Workflow
on:
  workflow_dispatch:
    inputs:
      other_input:
        default: false
        type: boolean
"""
        with patch("builtins.open", mock_open(read_data=content)):
            assert dispatch_roots.workflow_accepts_input("test", "trigger_descendants") is False

    def test_returns_false_on_file_error(self, dispatch_roots) -> None:
        """Test returns False when file cannot be read."""
        with patch("builtins.open", side_effect=IOError("File not found")):
            assert dispatch_roots.workflow_accepts_input("missing", "trigger_descendants") is False


class TestDispatchWorkflow:
    """Tests for dispatch_workflow function."""

    @patch("dispatch_roots.workflow_accepts_input")
    @patch("dispatch_roots.dispatch_gh_workflow")
    def test_dispatches_returns_true_on_success(
        self,
        mock_dispatch: MagicMock,
        _mock_accepts: MagicMock,
        dispatch_roots
    ) -> None:
        """Test dispatch returns True on success."""
        mock_dispatch.return_value = True
        result = dispatch_roots.dispatch_workflow("test", "owner/repo", False, False)
        assert result is True

    @patch("dispatch_roots.workflow_accepts_input")
    @patch("dispatch_roots.dispatch_gh_workflow")
    def test_dispatches_without_flag_when_trigger_false(
        self,
        mock_dispatch: MagicMock,
        _mock_accepts: MagicMock,
        dispatch_roots
    ) -> None:
        """Test dispatch passes None extra_args when trigger_descendants False."""
        mock_dispatch.return_value = True
        dispatch_roots.dispatch_workflow("test", "owner/repo", False, False)
        call_args = mock_dispatch.call_args
        assert call_args[0][2] is None

    @patch("dispatch_roots.workflow_accepts_input")
    @patch("dispatch_roots.dispatch_gh_workflow")
    def test_dispatches_with_flag_when_workflow_accepts(
        self,
        mock_dispatch: MagicMock,
        mock_accepts: MagicMock,
        dispatch_roots
    ) -> None:
        """Test dispatch passes trigger_descendants flag when accepted."""
        mock_accepts.return_value = True
        mock_dispatch.return_value = True
        dispatch_roots.dispatch_workflow("test", "owner/repo", True, False)
        call_args = mock_dispatch.call_args
        assert call_args[0][2] == ["-f", "trigger_descendants=true"]

    @patch("dispatch_roots.workflow_accepts_input")
    @patch("dispatch_roots.dispatch_gh_workflow")
    def test_dispatches_without_flag_when_workflow_rejects(
        self,
        mock_dispatch: MagicMock,
        mock_accepts: MagicMock,
        dispatch_roots
    ) -> None:
        """Test dispatch passes None when workflow rejects trigger_descendants."""
        mock_accepts.return_value = False
        mock_dispatch.return_value = True
        dispatch_roots.dispatch_workflow("test", "owner/repo", True, False)
        call_args = mock_dispatch.call_args
        assert call_args[0][2] is None

    @patch("dispatch_roots.workflow_accepts_input")
    @patch("dispatch_roots.dispatch_gh_workflow")
    def test_returns_false_on_dispatch_failure(
        self,
        mock_dispatch: MagicMock,
        _mock_accepts: MagicMock,
        dispatch_roots
    ) -> None:
        """Test returns False when dispatch fails."""
        mock_dispatch.return_value = False
        result = dispatch_roots.dispatch_workflow("test", "owner/repo", False, False)
        assert result is False

    @patch("dispatch_roots.workflow_accepts_input")
    @patch("dispatch_roots.dispatch_gh_workflow")
    def test_includes_invalidate_cloudfront_flag(
        self,
        mock_dispatch: MagicMock,
        mock_accepts: MagicMock,
        dispatch_roots
    ) -> None:
        """Test dispatch includes invalidate_cloudfront flag when True and accepted."""
        mock_accepts.return_value = True
        mock_dispatch.return_value = True
        dispatch_roots.dispatch_workflow("test", "owner/repo", False, True)
        call_args = mock_dispatch.call_args
        assert call_args[0][2] == ["-f", "invalidate_cloudfront=true"]


class TestShouldInvalidateCloudfront:
    """Tests for should_invalidate_cloudfront function."""

    def test_returns_true_when_flag_is_true(self, dispatch_roots) -> None:
        """Test returns True when invalidate_flag is True."""
        result = dispatch_roots.should_invalidate_cloudfront(True, "any message")
        assert result is True

    def test_returns_true_when_commit_has_tag(self, dispatch_roots) -> None:
        """Test returns True when commit has [invalidate cloudfront] tag."""
        result = dispatch_roots.should_invalidate_cloudfront(
            False, "fix: update [invalidate cloudfront]"
        )
        assert result is True

    def test_returns_true_case_insensitive(self, dispatch_roots) -> None:
        """Test tag matching is case insensitive."""
        result = dispatch_roots.should_invalidate_cloudfront(
            False, "[INVALIDATE CLOUDFRONT]"
        )
        assert result is True

    def test_returns_false_when_no_conditions_met(self, dispatch_roots) -> None:
        """Test returns False when no conditions are met."""
        result = dispatch_roots.should_invalidate_cloudfront(False, "normal commit")
        assert result is False


def test_main_calls_compute_merge_roots_with_running(
    dispatch_roots,
) -> None:
    """Test compute_merge_roots is called when running_workflows provided."""
    graph: dict = {"a": {"depends_on": []}, "b": {"depends_on": []}}
    argv = [
        "prog", "--running", '["b"]',
        "--graph", "g.json", "--repo", "o/r",
        "--changed-files", "", "--commit-message", ""
    ]
    with patch.object(sys, "argv", argv):
        with patch(
            "dispatch_roots.load_graph_and_compute_roots",
            return_value=(graph, ["a"], None)
        ):
            with patch(
                "dispatch_roots.parse_running_workflows",
                return_value=(["b"], None)
            ):
                with patch(
                    "dispatch_roots.compute_merge_roots",
                    return_value=["a"]
                ) as mock_merge:
                    with patch(
                        "dispatch_roots.workflow_file_exists",
                        return_value=True
                    ):
                        with patch(
                            "dispatch_roots.dispatch_workflow",
                            return_value=True
                        ):
                            dispatch_roots.main()
    mock_merge.assert_called_once_with(["b"], ["a"], graph)
    assert True  # Explicit pass

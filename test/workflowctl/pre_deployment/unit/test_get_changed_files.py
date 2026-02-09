"""Unit tests for get_changed_files.py."""
import json
import sys

from unittest.mock import MagicMock, patch


class TestCommitExists:
    """Tests for commit_exists function."""

    @patch("get_changed_files.run_subprocess")
    def test_returns_true_when_commit_exists(
        self, mock_run: MagicMock, get_changed_files
    ) -> None:
        """Test that commit_exists returns True when commit exists."""
        mock_run.return_value = MagicMock(returncode=0)
        assert get_changed_files.commit_exists("abc123") is True

    @patch("get_changed_files.run_subprocess")
    def test_returns_false_when_commit_missing(
        self, mock_run: MagicMock, get_changed_files
    ) -> None:
        """Test that commit_exists returns False when commit is missing."""
        mock_run.return_value = MagicMock(returncode=1)
        assert get_changed_files.commit_exists("abc123") is False


class TestGetChangedFilesDiff:
    """Tests for get_changed_files_diff function."""

    @patch("get_changed_files.run_subprocess")
    def test_returns_files_on_success(
        self, mock_run: MagicMock, get_changed_files
    ) -> None:
        """Test successful git diff returns file list."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="file1.py\nfile2.py\nfile3.py\n"
        )
        result = get_changed_files.get_changed_files_diff("base", "head")
        assert result == ["file1.py", "file2.py", "file3.py"]

    @patch("get_changed_files.run_subprocess")
    def test_returns_empty_on_failure(
        self, mock_run: MagicMock, get_changed_files
    ) -> None:
        """Test failed git diff returns empty list."""
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        result = get_changed_files.get_changed_files_diff("base", "head")
        assert result == []

    @patch("get_changed_files.run_subprocess")
    def test_filters_empty_lines(self, mock_run: MagicMock, get_changed_files) -> None:
        """Test that empty lines are filtered out."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="file1.py\n\nfile2.py\n"
        )
        result = get_changed_files.get_changed_files_diff("base", "head")
        assert result == ["file1.py", "file2.py"]


class TestGetChangedFilesShow:
    """Tests for get_changed_files_show function."""

    @patch("get_changed_files.run_subprocess")
    def test_returns_files_on_success(
        self, mock_run: MagicMock, get_changed_files
    ) -> None:
        """Test successful git show returns file list."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="file1.py\nfile2.py\n"
        )
        result = get_changed_files.get_changed_files_show("head")
        assert result == ["file1.py", "file2.py"]

    @patch("get_changed_files.run_subprocess")
    def test_returns_empty_on_failure(
        self, mock_run: MagicMock, get_changed_files
    ) -> None:
        """Test failed git show returns empty list."""
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        result = get_changed_files.get_changed_files_show("head")
        assert result == []


class TestGetChangedFiles:
    """Tests for get_changed_files function."""

    @patch("get_changed_files.get_changed_files_diff")
    @patch("get_changed_files.commit_exists")
    def test_uses_head_minus_one_for_zero_sha(
        self,
        _mock_exists: MagicMock,
        mock_diff: MagicMock,
        get_changed_files
    ) -> None:
        """Test that ZERO_SHA triggers HEAD~1 fallback."""
        mock_diff.return_value = ["file.py"]
        get_changed_files.get_changed_files(get_changed_files.ZERO_SHA, "head123")
        mock_diff.assert_called_once_with("HEAD~1", "head123")
        assert True  # Explicit pass

    @patch("get_changed_files.get_changed_files_diff")
    @patch("get_changed_files.commit_exists")
    def test_uses_base_when_commit_exists(
        self,
        mock_exists: MagicMock,
        mock_diff: MagicMock,
        get_changed_files
    ) -> None:
        """Test that existing base commit is used directly."""
        mock_exists.return_value = True
        mock_diff.return_value = ["file.py"]
        get_changed_files.get_changed_files("base123", "head123")
        mock_diff.assert_called_once_with("base123", "head123")
        assert True  # Explicit pass

    @patch("get_changed_files.get_changed_files_diff")
    @patch("get_changed_files.commit_exists")
    def test_uses_head_minus_one_when_base_missing(
        self,
        mock_exists: MagicMock,
        mock_diff: MagicMock,
        get_changed_files
    ) -> None:
        """Test shallow clone fallback to HEAD~1."""
        mock_exists.return_value = False
        mock_diff.return_value = ["file.py"]
        get_changed_files.get_changed_files("missing123", "head123")
        mock_diff.assert_called_once_with("HEAD~1", "head123")
        assert True  # Explicit pass

    @patch("get_changed_files.get_changed_files_show")
    @patch("get_changed_files.get_changed_files_diff")
    @patch("get_changed_files.commit_exists")
    def test_falls_back_to_show_when_diff_empty(
        self,
        mock_exists: MagicMock,
        mock_diff: MagicMock,
        mock_show: MagicMock,
        get_changed_files
    ) -> None:
        """Test fallback to git show when diff returns empty."""
        mock_exists.return_value = True
        mock_diff.return_value = []
        mock_show.return_value = ["file.py"]
        result = get_changed_files.get_changed_files("base123", "head123")
        assert result == ["file.py"]

    @patch("get_changed_files.get_changed_files_show")
    @patch("get_changed_files.get_changed_files_diff")
    @patch("get_changed_files.commit_exists")
    def test_fallback_calls_show_with_head(
        self,
        mock_exists: MagicMock,
        mock_diff: MagicMock,
        mock_show: MagicMock,
        get_changed_files
    ) -> None:
        """Test fallback calls git show with head commit."""
        mock_exists.return_value = True
        mock_diff.return_value = []
        mock_show.return_value = ["file.py"]
        get_changed_files.get_changed_files("base123", "head123")
        mock_show.assert_called_once_with("head123")
        assert True  # Explicit pass


class TestHasSkipCi:
    """Tests for has_skip_ci function."""

    def test_detects_skip_ci_lowercase(self, get_changed_files) -> None:
        """Test detection of [skip ci] marker."""
        assert get_changed_files.has_skip_ci("Fix bug [skip ci]") is True

    def test_detects_skip_ci_uppercase(self, get_changed_files) -> None:
        """Test detection of [SKIP CI] marker (case insensitive)."""
        assert get_changed_files.has_skip_ci("Fix bug [SKIP CI]") is True

    def test_detects_ci_skip(self, get_changed_files) -> None:
        """Test detection of [ci skip] marker."""
        assert get_changed_files.has_skip_ci("Fix bug [ci skip]") is True

    def test_detects_no_ci(self, get_changed_files) -> None:
        """Test detection of [no ci] marker."""
        assert get_changed_files.has_skip_ci("Update docs [no ci]") is True

    def test_detects_skip_actions(self, get_changed_files) -> None:
        """Test detection of [skip actions] marker."""
        assert get_changed_files.has_skip_ci("Minor change [skip actions]") is True

    def test_returns_false_for_normal_message(self, get_changed_files) -> None:
        """Test that normal messages return False."""
        assert get_changed_files.has_skip_ci("Fix critical bug in API") is False

    def test_returns_false_for_empty_message(self, get_changed_files) -> None:
        """Test that empty messages return False."""
        assert get_changed_files.has_skip_ci("") is False


class TestGetFilesForCommit:
    """Tests for get_files_for_commit function."""

    @patch("get_changed_files.run_subprocess")
    def test_returns_files_on_success(
        self, mock_run: MagicMock, get_changed_files
    ) -> None:
        """Test successful git show returns file list."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="file1.py\nfile2.py\n"
        )
        result = get_changed_files.get_files_for_commit("abc123")
        assert result == ["file1.py", "file2.py"]

    @patch("get_changed_files.run_subprocess")
    def test_returns_empty_on_failure(
        self, mock_run: MagicMock, get_changed_files
    ) -> None:
        """Test failed git show returns empty list."""
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        result = get_changed_files.get_files_for_commit("abc123")
        assert result == []


class TestFilterFilesByCommits:
    """Tests for filter_files_by_commits function."""

    def test_returns_empty_for_empty_json(self, get_changed_files) -> None:
        """Test that empty JSON returns empty set."""
        assert get_changed_files.filter_files_by_commits("") == set()

    def test_returns_empty_for_invalid_json(self, get_changed_files) -> None:
        """Test that invalid JSON returns empty set."""
        assert get_changed_files.filter_files_by_commits("not valid json") == set()

    def test_returns_empty_for_null_json(self, get_changed_files) -> None:
        """Test that JSON null returns empty set."""
        assert get_changed_files.filter_files_by_commits("null") == set()

    def test_returns_empty_for_object_json(self, get_changed_files) -> None:
        """Test that JSON object returns empty set."""
        assert get_changed_files.filter_files_by_commits("{}") == set()

    def test_returns_empty_for_string_json(self, get_changed_files) -> None:
        """Test that JSON string returns empty set."""
        assert get_changed_files.filter_files_by_commits('"hello"') == set()

    def test_returns_empty_for_number_json(self, get_changed_files) -> None:
        """Test that JSON number returns empty set."""
        assert get_changed_files.filter_files_by_commits("123") == set()

    def test_returns_empty_for_boolean_json(self, get_changed_files) -> None:
        """Test that JSON boolean returns empty set."""
        assert get_changed_files.filter_files_by_commits("true") == set()

    @patch("get_changed_files.get_files_for_commit")
    def test_excludes_files_from_skip_ci_commits(
        self,
        mock_get_files: MagicMock,
        get_changed_files
    ) -> None:
        """Test that files from [skip ci] commits are excluded."""
        mock_get_files.return_value = ["docs/readme.md"]
        commits = [
            {"id": "abc123", "message": "Update docs [skip ci]"}
        ]
        result = get_changed_files.filter_files_by_commits(json.dumps(commits))
        assert result == {"docs/readme.md"}

    @patch("get_changed_files.get_files_for_commit")
    def test_does_not_exclude_files_from_normal_commits(
        self,
        mock_get_files: MagicMock,
        get_changed_files
    ) -> None:
        """Test that files from normal commits are not excluded."""
        commits = [
            {"id": "abc123", "message": "Fix important bug"}
        ]
        result = get_changed_files.filter_files_by_commits(json.dumps(commits))
        assert result == set()
        mock_get_files.assert_not_called()

    @patch("get_changed_files.get_files_for_commit")
    def test_handles_mixed_commits(
        self, mock_get_files: MagicMock, get_changed_files
    ) -> None:
        """Test handling of mixed [skip ci] and normal commits."""
        def get_files_side_effect(sha: str) -> list[str]:
            if sha == "skip1":
                return ["docs/a.md"]
            if sha == "skip2":
                return ["docs/b.md"]
            return []

        mock_get_files.side_effect = get_files_side_effect
        commits = [
            {"id": "skip1", "message": "Update docs [skip ci]"},
            {"id": "normal", "message": "Fix bug"},
            {"id": "skip2", "message": "More docs [ci skip]"},
        ]
        result = get_changed_files.filter_files_by_commits(json.dumps(commits))
        assert result == {"docs/a.md", "docs/b.md"}

    def test_handles_commits_without_id(self, get_changed_files) -> None:
        """Test that commits without id are handled gracefully."""
        commits = [
            {"message": "No id commit [skip ci]"}
        ]
        result = get_changed_files.filter_files_by_commits(json.dumps(commits))
        assert result == set()


class TestParseArgs:
    """Tests for parse_args function."""

    def test_parses_base_argument(self, get_changed_files) -> None:
        """Test parsing required --base argument."""
        argv = ["prog", "--base", "abc123", "--head", "def456"]
        with patch.object(sys, "argv", argv):
            args = get_changed_files.parse_args()
        assert args.base == "abc123"

    def test_parses_head_argument(self, get_changed_files) -> None:
        """Test parsing required --head argument."""
        argv = ["prog", "--base", "abc123", "--head", "def456"]
        with patch.object(sys, "argv", argv):
            args = get_changed_files.parse_args()
        assert args.head == "def456"

    def test_parses_commits_json(self, get_changed_files) -> None:
        """Test parsing optional --commits JSON argument."""
        commits = '[{"message": "test"}]'
        argv = ["prog", "--base", "a", "--head", "b", "--commits", commits]
        with patch.object(sys, "argv", argv):
            args = get_changed_files.parse_args()
        assert args.commits == commits

    def test_commits_defaults_to_empty(self, get_changed_files) -> None:
        """Test --commits defaults to empty string."""
        argv = ["prog", "--base", "a", "--head", "b"]
        with patch.object(sys, "argv", argv):
            args = get_changed_files.parse_args()
        assert args.commits == ""


class TestMain:
    """Tests for main function."""

    def test_returns_0_on_success(self, get_changed_files, capsys) -> None:
        """Test main returns 0 on success."""
        argv = ["prog", "--base", "a", "--head", "b"]
        with patch.object(sys, "argv", argv):
            with patch.object(
                get_changed_files, "get_changed_files", return_value=["file.py"]
            ):
                result = get_changed_files.main()
        # Consume stdout for cleanup
        capsys.readouterr()
        assert result == 0

    def test_outputs_json_with_files(self, get_changed_files, capsys) -> None:
        """Test main outputs JSON with files key."""
        argv = ["prog", "--base", "a", "--head", "b"]
        with patch.object(sys, "argv", argv):
            with patch.object(
                get_changed_files, "get_changed_files", return_value=["file.py"]
            ):
                get_changed_files.main()
        out = capsys.readouterr().out
        assert '"files"' in out

    def test_filters_files_when_commits_provided(self, get_changed_files, capsys) -> None:
        """Test main filters files based on commits."""
        commits = '[{"id": "abc", "message": "[skip ci] test"}]'
        argv = ["prog", "--base", "a", "--head", "b", "--commits", commits]
        with patch.object(sys, "argv", argv):
            with patch.object(
                get_changed_files, "get_changed_files", return_value=["a.py", "b.py"]
            ):
                with patch.object(
                    get_changed_files, "filter_files_by_commits", return_value={"a.py"}
                ):
                    get_changed_files.main()
        out = capsys.readouterr().out
        # a.py should be filtered out, b.py should remain
        assert "b.py" in out

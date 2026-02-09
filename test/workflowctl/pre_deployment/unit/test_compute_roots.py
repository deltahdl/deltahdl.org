"""Unit tests for compute_roots.py."""

import io
import sys
from test.workflowctl.conftest import SAMPLE_GRAPH
from unittest.mock import patch

import pytest


class TestFileMatchesPatterns:
    """Tests for file_matches_patterns function."""

    def test_exact_match_returns_true(self, compute_roots) -> None:
        """Test exact file path matching returns true."""
        patterns = [".github/workflows/bootstrap.yml"]
        assert compute_roots.file_matches_patterns(".github/workflows/bootstrap.yml", patterns)

    def test_exact_match_returns_false_for_different_file(self, compute_roots) -> None:
        """Test exact file path matching returns false for different file."""
        patterns = [".github/workflows/bootstrap.yml"]
        assert not compute_roots.file_matches_patterns(
            ".github/workflows/www_redirect.yml", patterns
        )

    def test_glob_star_match_direct_child(self, compute_roots) -> None:
        """Test single * glob pattern matches direct child."""
        patterns = ["src/*.tf"]
        assert compute_roots.file_matches_patterns("src/main.tf", patterns)

    def test_glob_star_match_nested_child(self, compute_roots) -> None:
        """Test single * glob pattern matches nested child.

        Note: fnmatch treats * as matching any characters including /,
        so src/*.tf matches src/sub/main.tf. This is acceptable since
        we primarily use ** patterns in workflow_dependencies.json.
        """
        patterns = ["src/*.tf"]
        assert compute_roots.file_matches_patterns("src/sub/main.tf", patterns)

    def test_double_star_match_direct_child(self, compute_roots) -> None:
        """Test ** glob pattern matches direct child."""
        patterns = ["src/bootstrap/**"]
        assert compute_roots.file_matches_patterns("src/bootstrap/main.tf", patterns)

    def test_double_star_match_nested_child(self, compute_roots) -> None:
        """Test ** glob pattern matches nested child."""
        patterns = ["src/bootstrap/**"]
        assert compute_roots.file_matches_patterns("src/bootstrap/sub/file.tf", patterns)

    def test_double_star_match_returns_false_for_different_path(self, compute_roots) -> None:
        """Test ** glob pattern returns false for different path."""
        patterns = ["src/bootstrap/**"]
        assert not compute_roots.file_matches_patterns("src/www/main.tf", patterns)

    def test_multiple_patterns_matches_first(self, compute_roots) -> None:
        """Test matching first of multiple patterns."""
        patterns = [".github/workflows/bootstrap.yml", "src/bootstrap/**"]
        assert compute_roots.file_matches_patterns(".github/workflows/bootstrap.yml", patterns)

    def test_multiple_patterns_matches_second(self, compute_roots) -> None:
        """Test matching second of multiple patterns."""
        patterns = [".github/workflows/bootstrap.yml", "src/bootstrap/**"]
        assert compute_roots.file_matches_patterns("src/bootstrap/main.tf", patterns)

    def test_multiple_patterns_returns_false_for_no_match(self, compute_roots) -> None:
        """Test multiple patterns returns false when none match."""
        patterns = [".github/workflows/bootstrap.yml", "src/bootstrap/**"]
        assert not compute_roots.file_matches_patterns("src/www/main.tf", patterns)

    def test_empty_patterns(self, compute_roots) -> None:
        """Test with empty pattern list."""
        assert not compute_roots.file_matches_patterns("any/file.txt", [])


class TestGetAllAncestors:
    """Tests for get_all_ancestors function."""

    def test_no_ancestors(self, compute_roots) -> None:
        """Test workflow with no dependencies."""
        ancestors = compute_roots.get_all_ancestors("bootstrap", SAMPLE_GRAPH)
        assert ancestors == set()

    def test_single_ancestor(self, compute_roots) -> None:
        """Test workflow with one direct dependency."""
        ancestors = compute_roots.get_all_ancestors("www_redirect", SAMPLE_GRAPH)
        assert ancestors == {"bootstrap"}

    def test_caching_stores_target_workflow(self, compute_roots) -> None:
        """Test that ancestor computation caches target workflow."""
        cache: dict[str, set[str]] = {}
        compute_roots.get_all_ancestors("www_redirect", SAMPLE_GRAPH, cache)
        assert "www_redirect" in cache

    def test_caching_stores_direct_ancestor(self, compute_roots) -> None:
        """Test that ancestor computation caches direct ancestor."""
        cache: dict[str, set[str]] = {}
        compute_roots.get_all_ancestors("www_redirect", SAMPLE_GRAPH, cache)
        assert "bootstrap" in cache


class TestGetAffectedWorkflows:
    """Tests for get_affected_workflows function."""

    def test_single_file_single_workflow(self, compute_roots) -> None:
        """Test single file affecting single workflow."""
        changed = ["src/bootstrap/main.tf"]
        affected = compute_roots.get_affected_workflows(changed, SAMPLE_GRAPH)
        assert affected == {"bootstrap"}

    def test_single_file_workflow_file(self, compute_roots) -> None:
        """Test changing a workflow file itself."""
        changed = [".github/workflows/www_redirect.yml"]
        affected = compute_roots.get_affected_workflows(changed, SAMPLE_GRAPH)
        assert affected == {"www_redirect"}

    def test_multiple_files_single_workflow(self, compute_roots) -> None:
        """Test multiple files affecting single workflow."""
        changed = ["src/bootstrap/main.tf", "src/bootstrap/variables.tf"]
        affected = compute_roots.get_affected_workflows(changed, SAMPLE_GRAPH)
        assert affected == {"bootstrap"}

    def test_multiple_files_multiple_workflows(self, compute_roots) -> None:
        """Test files affecting multiple workflows."""
        changed = ["src/bootstrap/main.tf", "src/www/redirect/main.tf"]
        affected = compute_roots.get_affected_workflows(changed, SAMPLE_GRAPH)
        assert affected == {"bootstrap", "www_redirect"}

    def test_no_matching_files(self, compute_roots) -> None:
        """Test with files that don't match any workflow."""
        changed = ["README.md", "docs/guide.md"]
        affected = compute_roots.get_affected_workflows(changed, SAMPLE_GRAPH)
        assert affected == set()


class TestComputeRootWorkflows:
    """Tests for compute_root_workflows function."""

    def test_single_root_workflow(self, compute_roots) -> None:
        """Test single workflow change returns that workflow as root."""
        changed = ["src/bootstrap/main.tf"]
        roots = compute_roots.compute_root_workflows(changed, SAMPLE_GRAPH)
        assert roots == ["bootstrap"]

    def test_ancestor_and_descendant_changed(self, compute_roots) -> None:
        """Test that only ancestor is returned when both are changed."""
        changed = ["src/bootstrap/main.tf", "src/www/redirect/main.tf"]
        roots = compute_roots.compute_root_workflows(changed, SAMPLE_GRAPH)
        # Only bootstrap should be root; www_redirect will cascade
        assert roots == ["bootstrap"]

    def test_independent_workflows(self, compute_roots) -> None:
        """Test multiple independent workflow changes."""
        # Create a graph with two independent branches
        graph = {
            "a": {"depends_on": [], "paths": ["src/a/**"]},
            "b": {"depends_on": [], "paths": ["src/b/**"]},
            "c": {"depends_on": ["a"], "paths": ["src/c/**"]},
            "d": {"depends_on": ["b"], "paths": ["src/d/**"]},
        }
        changed = ["src/a/file.tf", "src/b/file.tf"]
        roots = compute_roots.compute_root_workflows(changed, graph)
        assert sorted(roots) == ["a", "b"]

    def test_leaf_workflow_only(self, compute_roots) -> None:
        """Test changing only a leaf workflow returns it as root."""
        changed = ["src/www/redirect/main.tf"]
        roots = compute_roots.compute_root_workflows(changed, SAMPLE_GRAPH)
        assert roots == ["www_redirect"]

    def test_no_changes(self, compute_roots) -> None:
        """Test empty file list returns empty roots."""
        roots = compute_roots.compute_root_workflows([], SAMPLE_GRAPH)
        assert roots == []

    def test_unrelated_files(self, compute_roots) -> None:
        """Test files not matching any workflow return empty roots."""
        changed = ["README.md"]
        roots = compute_roots.compute_root_workflows(changed, SAMPLE_GRAPH)
        assert roots == []


class TestDiamondDependency:
    """Tests for diamond dependency patterns (multiple paths to same node)."""

    @pytest.fixture
    def diamond_graph(self) -> dict:
        """Create a diamond-shaped dependency graph."""
        return {
            "root": {"depends_on": [], "paths": ["src/root/**"]},
            "left": {"depends_on": ["root"], "paths": ["src/left/**"]},
            "right": {"depends_on": ["root"], "paths": ["src/right/**"]},
            "bottom": {"depends_on": ["left", "right"], "paths": ["src/bottom/**"]},
        }

    def test_diamond_root_change(self, diamond_graph: dict, compute_roots) -> None:
        """Test changing root in diamond returns only root."""
        changed = ["src/root/file.tf"]
        roots = compute_roots.compute_root_workflows(changed, diamond_graph)
        assert roots == ["root"]

    def test_diamond_both_middle(self, diamond_graph: dict, compute_roots) -> None:
        """Test changing both middle nodes returns both as roots."""
        changed = ["src/left/file.tf", "src/right/file.tf"]
        roots = compute_roots.compute_root_workflows(changed, diamond_graph)
        assert sorted(roots) == ["left", "right"]

    def test_diamond_one_middle_and_bottom(self, diamond_graph: dict, compute_roots) -> None:
        """Test changing one middle and bottom returns only middle."""
        changed = ["src/left/file.tf", "src/bottom/file.tf"]
        roots = compute_roots.compute_root_workflows(changed, diamond_graph)
        # Only left is root; bottom has left as ancestor
        assert roots == ["left"]

    def test_diamond_all_nodes(self, diamond_graph: dict, compute_roots) -> None:
        """Test changing all nodes returns only root."""
        changed = [
            "src/root/file.tf",
            "src/left/file.tf",
            "src/right/file.tf",
            "src/bottom/file.tf",
        ]
        roots = compute_roots.compute_root_workflows(changed, diamond_graph)
        assert roots == ["root"]


class TestGetAllDescendants:
    """Tests for get_all_descendants function."""

    def test_no_descendants(self, utils) -> None:
        """Test leaf workflow with no dependents."""
        descendants = utils.get_all_descendants("www_redirect", SAMPLE_GRAPH)
        assert descendants == set()

    def test_root_descendants(self, utils) -> None:
        """Test root workflow has all others as descendants."""
        descendants = utils.get_all_descendants("bootstrap", SAMPLE_GRAPH)
        assert descendants == {"www_redirect"}

    def test_caching_stores_target_workflow(self, utils) -> None:
        """Test that descendant computation caches target workflow."""
        cache: dict[str, set[str]] = {}
        utils.get_all_descendants("bootstrap", SAMPLE_GRAPH, cache)
        assert "bootstrap" in cache

    def test_caching_stores_direct_descendant(self, utils) -> None:
        """Test that descendant computation caches direct descendant."""
        cache: dict[str, set[str]] = {}
        utils.get_all_descendants("bootstrap", SAMPLE_GRAPH, cache)
        assert "www_redirect" in cache


class TestInsertSorted:
    """Tests for insert_sorted function."""

    def test_insert_into_empty_list(self, compute_roots) -> None:
        """Test inserting into empty list."""
        queue: list[str] = []
        compute_roots.insert_sorted(queue, "b")
        assert queue == ["b"]

    def test_insert_at_beginning(self, compute_roots) -> None:
        """Test inserting at beginning of list."""
        queue = ["c", "d", "e"]
        compute_roots.insert_sorted(queue, "a")
        assert queue == ["a", "c", "d", "e"]

    def test_insert_at_end(self, compute_roots) -> None:
        """Test inserting at end of list."""
        queue = ["a", "b", "c"]
        compute_roots.insert_sorted(queue, "z")
        assert queue == ["a", "b", "c", "z"]

    def test_insert_in_middle(self, compute_roots) -> None:
        """Test inserting in middle of list."""
        queue = ["a", "c", "e"]
        compute_roots.insert_sorted(queue, "b")
        assert queue == ["a", "b", "c", "e"]

    def test_insert_duplicate(self, compute_roots) -> None:
        """Test inserting duplicate value."""
        queue = ["a", "c", "e"]
        compute_roots.insert_sorted(queue, "c")
        assert queue == ["a", "c", "c", "e"]


class TestTopologicalSort:
    """Tests for topological_sort function."""

    def test_single_workflow(self, compute_roots) -> None:
        """Test sorting single workflow."""
        workflows = {"bootstrap"}
        result = compute_roots.topological_sort(workflows, SAMPLE_GRAPH)
        assert result == ["bootstrap"]

    def test_linear_chain(self, compute_roots) -> None:
        """Test sorting linear dependency chain."""
        workflows = {"bootstrap", "www_redirect"}
        result = compute_roots.topological_sort(workflows, SAMPLE_GRAPH)
        assert result == ["bootstrap", "www_redirect"]

    def test_respects_dependencies_bootstrap_before_www_redirect(self, compute_roots) -> None:
        """Test that bootstrap comes before www_redirect."""
        workflows = {"www_redirect", "bootstrap"}
        result = compute_roots.topological_sort(workflows, SAMPLE_GRAPH)
        assert result.index("bootstrap") < result.index("www_redirect")

    def test_diamond_pattern_ordering(self, compute_roots) -> None:
        """Test diamond-shaped graph maintains correct ordering."""
        graph = {"root": {"depends_on": []}, "left": {"depends_on": ["root"]},
                 "right": {"depends_on": ["root"]},
                 "bottom": {"depends_on": ["left", "right"]}}
        result = compute_roots.topological_sort({"root", "left", "right", "bottom"}, graph)
        assert (result[0], result[-1],
                result.index("left") < result.index("bottom"),
                result.index("right") < result.index("bottom")) == (
                    "root", "bottom", True, True)

    def test_partial_graph(self, compute_roots) -> None:
        """Test sorting subset of graph."""
        workflows = {"www_redirect"}
        result = compute_roots.topological_sort(workflows, SAMPLE_GRAPH)
        assert result == ["www_redirect"]


class TestTopologicalSortLevels:
    """Tests for topological_sort_levels function."""

    def test_single_workflow(self, compute_roots) -> None:
        """Test single workflow returns single level."""
        levels = compute_roots.topological_sort_levels({"bootstrap"}, SAMPLE_GRAPH)
        assert levels == [["bootstrap"]]

    def test_linear_chain(self, compute_roots) -> None:
        """Test linear chain returns one workflow per level."""
        levels = compute_roots.topological_sort_levels({"bootstrap", "www_redirect"},
                                         SAMPLE_GRAPH)
        assert levels == [["bootstrap"], ["www_redirect"]]

    def test_parallel_workflows_structure(self, compute_roots) -> None:
        """Test parallel workflows are grouped correctly by level."""
        graph = {"root": {"depends_on": []}, "left": {"depends_on": ["root"]},
                 "right": {"depends_on": ["root"]},
                 "bottom": {"depends_on": ["left", "right"]}}
        levels = compute_roots.topological_sort_levels({"root", "left", "right", "bottom"},
                                         graph)
        assert (len(levels), levels[0], sorted(levels[1]), levels[2]) == (
            3, ["root"], ["left", "right"], ["bottom"])

    def test_complex_parallel_structure(self, compute_roots) -> None:
        """Test complex parallel graph levels are correct."""
        graph = {"a": {"depends_on": []}, "b": {"depends_on": ["a"]},
                 "c": {"depends_on": ["a"]}, "d": {"depends_on": ["b"]},
                 "e": {"depends_on": ["c"]}, "f": {"depends_on": ["d", "e"]}}
        levels = compute_roots.topological_sort_levels({"a", "b", "c", "d", "e", "f"}, graph)
        assert (len(levels), levels[0], sorted(levels[1]), sorted(levels[2]),
                levels[3]) == (4, ["a"], ["b", "c"], ["d", "e"], ["f"])


class TestComputeExecutionPlan:
    """Tests for compute_execution_plan function."""

    def test_single_root_no_descendants(self, compute_roots) -> None:
        """Test single root with no descendants."""
        graph: dict[str, dict[str, list[str]]] = {"a": {"depends_on": []}}
        plan = compute_roots.compute_execution_plan(["a"], graph)
        assert plan == ["a"]

    def test_single_root_with_descendants(self, compute_roots) -> None:
        """Test single root includes all descendants."""
        plan = compute_roots.compute_execution_plan(["bootstrap"], SAMPLE_GRAPH)
        expected = ["bootstrap", "www_redirect"]
        assert plan == expected

    def test_leaf_root(self, compute_roots) -> None:
        """Test starting from leaf of chain."""
        plan = compute_roots.compute_execution_plan(["www_redirect"], SAMPLE_GRAPH)
        expected = ["www_redirect"]
        assert plan == expected

    def test_multiple_roots_execution_order(self, compute_roots) -> None:
        """Test multiple roots include all descendants in correct order."""
        graph = {"a": {"depends_on": []}, "b": {"depends_on": []},
                 "c": {"depends_on": ["a"]}, "d": {"depends_on": ["b"]}}
        plan = compute_roots.compute_execution_plan(["a", "b"], graph)
        assert (set(plan), plan.index("a") < plan.index("c"),
                plan.index("b") < plan.index("d")) == (
                    {"a", "b", "c", "d"}, True, True)


class TestComputeExecutionPlanLevels:
    """Tests for compute_execution_plan_levels function."""

    def test_single_root_no_descendants(self, compute_roots) -> None:
        """Test single root with no descendants."""
        graph: dict[str, dict[str, list[str]]] = {"a": {"depends_on": []}}
        levels = compute_roots.compute_execution_plan_levels(["a"], graph)
        assert levels == [["a"]]

    def test_single_root_with_descendants_has_two_levels(self, compute_roots) -> None:
        """Test single root with descendants has 2 levels."""
        levels = compute_roots.compute_execution_plan_levels(["bootstrap"], SAMPLE_GRAPH)
        assert len(levels) == 2

    def test_single_root_with_descendants_bootstrap_first(self, compute_roots) -> None:
        """Test single root with descendants has bootstrap first."""
        levels = compute_roots.compute_execution_plan_levels(["bootstrap"], SAMPLE_GRAPH)
        assert levels[0] == ["bootstrap"]

    def test_single_root_with_descendants_www_redirect_last(self, compute_roots) -> None:
        """Test single root with descendants has www_redirect last."""
        levels = compute_roots.compute_execution_plan_levels(["bootstrap"], SAMPLE_GRAPH)
        assert levels[-1] == ["www_redirect"]

    def test_parallel_branches_level_structure(self, compute_roots) -> None:
        """Test parallel branches graph has correct level structure."""
        graph = {"root": {"depends_on": []}, "left": {"depends_on": ["root"]},
                 "right": {"depends_on": ["root"]},
                 "bottom": {"depends_on": ["left", "right"]}}
        levels = compute_roots.compute_execution_plan_levels(["root"], graph)
        assert (len(levels), levels[0], sorted(levels[1]), levels[2]) == (
            3, ["root"], ["left", "right"], ["bottom"])

    def test_multiple_roots_same_level_structure(self, compute_roots) -> None:
        """Test multiple independent roots level structure."""
        graph = {"a": {"depends_on": []}, "b": {"depends_on": []},
                 "c": {"depends_on": ["a", "b"]}}
        levels = compute_roots.compute_execution_plan_levels(["a", "b"], graph)
        assert (len(levels), sorted(levels[0]), levels[1]) == (
            2, ["a", "b"], ["c"])


class TestOutputSlots:
    """Tests for output_slots function."""

    def test_exact_slots_outputs_count(self, compute_roots) -> None:
        """Test outputting exact number of slots shows correct count."""
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            compute_roots.output_slots(["a", "b"], 2)
            output = mock_stdout.getvalue()
        assert "count=2" in output

    def test_exact_slots_outputs_first_key(self, compute_roots) -> None:
        """Test outputting exact number of slots shows first key."""
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            compute_roots.output_slots(["a", "b"], 2)
            output = mock_stdout.getvalue()
        assert "key_01=a" in output

    def test_exact_slots_outputs_second_key(self, compute_roots) -> None:
        """Test outputting exact number of slots shows second key."""
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            compute_roots.output_slots(["a", "b"], 2)
            output = mock_stdout.getvalue()
        assert "key_02=b" in output

    def test_more_slots_outputs_count(self, compute_roots) -> None:
        """Test more slots than items shows correct count."""
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            compute_roots.output_slots(["a"], 4)
            output = mock_stdout.getvalue()
        assert "count=1" in output

    def test_more_slots_outputs_first_key(self, compute_roots) -> None:
        """Test more slots than items shows first key."""
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            compute_roots.output_slots(["a"], 4)
            output = mock_stdout.getvalue()
        assert "key_01=a" in output

    def test_more_slots_outputs_empty_second_key(self, compute_roots) -> None:
        """Test more slots than items shows empty second key."""
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            compute_roots.output_slots(["a"], 4)
            output = mock_stdout.getvalue()
        assert "key_02=" in output

    def test_more_slots_outputs_empty_third_key(self, compute_roots) -> None:
        """Test more slots than items shows empty third key."""
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            compute_roots.output_slots(["a"], 4)
            output = mock_stdout.getvalue()
        assert "key_03=" in output

    def test_more_slots_outputs_empty_fourth_key(self, compute_roots) -> None:
        """Test more slots than items shows empty fourth key."""
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            compute_roots.output_slots(["a"], 4)
            output = mock_stdout.getvalue()
        assert "key_04=" in output

    def test_empty_list_outputs_count_zero(self, compute_roots) -> None:
        """Test outputting with no items shows count zero."""
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            compute_roots.output_slots([], 2)
            output = mock_stdout.getvalue()
        assert "count=0" in output

    def test_empty_list_outputs_empty_first_key(self, compute_roots) -> None:
        """Test outputting with no items shows empty first key."""
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            compute_roots.output_slots([], 2)
            output = mock_stdout.getvalue()
        assert "key_01=" in output

    def test_empty_list_outputs_empty_second_key(self, compute_roots) -> None:
        """Test outputting with no items shows empty second key."""
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            compute_roots.output_slots([], 2)
            output = mock_stdout.getvalue()
        assert "key_02=" in output


class TestOutputResults:
    """Tests for output_results function."""

    def test_output_json_object(self, compute_roots) -> None:
        """Test JSON object output format."""
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            compute_roots.output_results(["a", "b"])
            output = mock_stdout.getvalue().strip()
        assert output == '{"workflows": ["a", "b"]}'

    def test_output_indexed(self, compute_roots) -> None:
        """Test indexed JSON output format."""
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            compute_roots.output_results(["a", "b"], indexed=True)
            output = mock_stdout.getvalue().strip()
        expected = '{"workflows": [{"idx": "01", "name": "a"}, {"idx": "02", "name": "b"}]}'
        assert output == expected

    def test_output_empty(self, compute_roots) -> None:
        """Test output with empty list."""
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            compute_roots.output_results([])
            output = mock_stdout.getvalue().strip()
        assert output == '{"workflows": []}'


class TestOutputLevelsIndexed:
    """Tests for output_levels_indexed function."""

    def test_single_level(self, compute_roots) -> None:
        """Test output with single level."""
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            compute_roots.output_levels_indexed([["a", "b"]])
            output = mock_stdout.getvalue().strip()
        expected = (
            '{"workflows": [{"idx": "01", "level": 1, "name": "a"}, '
            '{"idx": "02", "level": 1, "name": "b"}]}'
        )
        assert output == expected

    def test_multiple_levels(self, compute_roots) -> None:
        """Test output with multiple levels."""
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            compute_roots.output_levels_indexed([["a"], ["b", "c"], ["d"]])
            output = mock_stdout.getvalue().strip()
        expected = (
            '{"workflows": [{"idx": "01", "level": 1, "name": "a"}, '
            '{"idx": "02", "level": 2, "name": "b"}, '
            '{"idx": "03", "level": 2, "name": "c"}, '
            '{"idx": "04", "level": 3, "name": "d"}]}'
        )
        assert output == expected

    def test_empty_levels(self, compute_roots) -> None:
        """Test output with empty levels list."""
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            compute_roots.output_levels_indexed([])
            output = mock_stdout.getvalue().strip()
        assert output == '{"workflows": []}'


class TestComputeMergeRoots:
    """Tests for compute_merge_roots function.

    This function merges running workflows with new root workflows to find
    the optimal restart point when a new workflowctl run starts while
    workflows from a previous run are still executing.
    """

    def test_no_running_workflows(self, compute_roots) -> None:
        """Test with no running workflows returns new roots unchanged."""
        new_roots = ["www_redirect"]
        running: list[str] = []
        result = compute_roots.compute_merge_roots(running, new_roots, SAMPLE_GRAPH)
        assert result == ["www_redirect"]

    def test_no_new_roots(self, compute_roots) -> None:
        """Test with no new roots returns empty (let running workflows finish)."""
        new_roots: list[str] = []
        running = ["www_redirect"]
        result = compute_roots.compute_merge_roots(running, new_roots, SAMPLE_GRAPH)
        assert result == []

    def test_both_empty(self, compute_roots) -> None:
        """Test with both empty returns empty."""
        result = compute_roots.compute_merge_roots([], [], SAMPLE_GRAPH)
        assert result == []

    def test_running_downstream_of_new_root(self, compute_roots) -> None:
        """Test when running workflow is downstream of new changes.

        Scenario: Chain at www_redirect, new changes affect bootstrap
        bootstrap is upstream of www_redirect, so merge root is bootstrap.
        """
        running = ["www_redirect"]
        new_roots = ["bootstrap"]
        result = compute_roots.compute_merge_roots(running, new_roots, SAMPLE_GRAPH)
        # bootstrap is ancestor of www_redirect, so bootstrap is the merge root
        assert result == ["bootstrap"]

    def test_running_upstream_of_new_root(self, compute_roots) -> None:
        """Test when running workflow is upstream of new changes.

        Scenario: Chain at bootstrap, new changes affect www_redirect
        bootstrap is upstream of www_redirect, so merge root is bootstrap.
        """
        running = ["bootstrap"]
        new_roots = ["www_redirect"]
        result = compute_roots.compute_merge_roots(running, new_roots, SAMPLE_GRAPH)
        # bootstrap is ancestor of www_redirect, so bootstrap is the merge root
        assert result == ["bootstrap"]

    def test_running_and_new_same_level(self, compute_roots) -> None:
        """Test when running and new are at the same workflow.

        Scenario: Chain at bootstrap, new changes also affect bootstrap
        Merge root should be bootstrap.
        """
        running = ["bootstrap"]
        new_roots = ["bootstrap"]
        result = compute_roots.compute_merge_roots(running, new_roots, SAMPLE_GRAPH)
        assert result == ["bootstrap"]

    def test_unrelated_branches(self, compute_roots) -> None:
        """Test when running and new are in unrelated branches.

        Using diamond graph where left and right are independent.
        """
        graph = {
            "root": {"depends_on": [], "name": "Root"},
            "left": {"depends_on": ["root"], "name": "Left"},
            "right": {"depends_on": ["root"], "name": "Right"},
            "bottom": {"depends_on": ["left", "right"], "name": "Bottom"},
        }
        running = ["left"]
        new_roots = ["right"]
        result = compute_roots.compute_merge_roots(running, new_roots, graph)
        # Both are independent branches, both should be roots
        assert sorted(result) == ["left", "right"]

    def test_running_at_common_ancestor(self, compute_roots) -> None:
        """Test when running workflow is ancestor of new changes.

        Scenario: Running at bootstrap, new changes affect www_redirect
        bootstrap is ancestor of www_redirect, so bootstrap is the merge root.
        """
        running = ["bootstrap"]
        new_roots = ["www_redirect"]
        result = compute_roots.compute_merge_roots(running, new_roots, SAMPLE_GRAPH)
        assert result == ["bootstrap"]

    def test_multiple_running_workflows(self, compute_roots) -> None:
        """Test with multiple running workflows from parallel branches."""
        graph = {
            "root": {"depends_on": [], "name": "Root"},
            "left": {"depends_on": ["root"], "name": "Left"},
            "right": {"depends_on": ["root"], "name": "Right"},
            "left_child": {"depends_on": ["left"], "name": "Left Child"},
            "right_child": {"depends_on": ["right"], "name": "Right Child"},
        }
        running = ["left_child", "right_child"]
        new_roots = ["root"]
        result = compute_roots.compute_merge_roots(running, new_roots, graph)
        # root is ancestor of both, so root is the only merge root
        assert result == ["root"]

    def test_multiple_new_roots(self, compute_roots) -> None:
        """Test with multiple new root workflows."""
        graph = {
            "a": {"depends_on": [], "name": "A"},
            "b": {"depends_on": [], "name": "B"},
            "c": {"depends_on": ["a"], "name": "C"},
            "d": {"depends_on": ["b"], "name": "D"},
        }
        running = ["c"]
        new_roots = ["a", "b"]
        result = compute_roots.compute_merge_roots(running, new_roots, graph)
        # a is ancestor of c, so only a and b are roots
        assert sorted(result) == ["a", "b"]

    def test_unknown_running_workflow_filtered(self, compute_roots) -> None:
        """Test that unknown workflow keys are filtered out."""
        running = ["unknown_workflow"]
        new_roots = ["bootstrap"]
        result = compute_roots.compute_merge_roots(running, new_roots, SAMPLE_GRAPH)
        # Unknown workflow is filtered, only bootstrap remains
        assert result == ["bootstrap"]

    def test_mix_of_known_and_unknown(self, compute_roots) -> None:
        """Test with mix of known and unknown workflows."""
        running = ["www_redirect", "unknown_workflow"]
        new_roots = ["bootstrap"]
        result = compute_roots.compute_merge_roots(running, new_roots, SAMPLE_GRAPH)
        # bootstrap is ancestor of www_redirect, unknown is filtered
        assert result == ["bootstrap"]

    def test_returns_empty_when_both_inputs_empty(self, compute_roots) -> None:
        """Test returns [] when running and new_roots are both empty."""
        result = compute_roots.compute_merge_roots([], [], SAMPLE_GRAPH)
        assert result == []

    def test_returns_empty_when_workflows_not_in_graph(self, compute_roots) -> None:
        """Test returns [] when workflows don't exist in graph."""
        result = compute_roots.compute_merge_roots(
            ["nonexistent"], ["also_nonexistent"], SAMPLE_GRAPH
        )
        assert result == []


def test_topological_sort_levels_handles_cyclic_graph(compute_roots) -> None:
    """Test gracefully handles cyclic dependencies."""
    cyclic_graph = {
        "a": {"depends_on": ["c"]},
        "b": {"depends_on": ["a"]},
        "c": {"depends_on": ["b"]},  # cycle: a -> b -> c -> a
    }
    result = compute_roots.topological_sort_levels(
        {"a", "b", "c"}, cyclic_graph
    )
    # Should return partial result (empty), not infinite loop
    assert isinstance(result, list)


def test_main_levels_indexed_outputs_format(
    compute_roots, capsys
) -> None:
    """Test main with --levels --indexed outputs indexed format."""
    graph = {"a": {"depends_on": [], "paths": ["a.py"]}}
    argv = [
        "prog", "--changed-files", "a.py",
        "--levels", "--indexed",
    ]
    with patch.object(sys, "argv", argv):
        with patch(
            "compute_roots.load_dependency_graph",
            return_value=graph,
        ):
            compute_roots.main()
    out = capsys.readouterr().out
    assert '"idx":' in out

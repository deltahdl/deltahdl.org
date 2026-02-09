#!/usr/bin/env python3
"""
Compute root workflows and execution plans based on changed files.

This script reads the workflow dependency graph from etc/workflow_dependencies.json
and determines which workflows should be triggered for a given set of changed files.

A "root" workflow is one whose files were modified but has no ancestors that were
also modified. The execution plan includes the root workflow(s) and all their
descendants in topological order (dependencies before dependents).

Usage:
    python3 src/workflowctl/workflowctl.py compute-root-workflows \
        --changed-files "file1.py,file2.py"

Output:
    Default: {"workflows": ["bootstrap", "www_redirect"]}
    With --levels: {"levels": [["bootstrap"], ["www_redirect"]]}
    With --levels --indexed: {"workflows": [{"idx": "01", "level": 1, "name": "bootstrap"}]}
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from utils import file_matches_pattern, get_all_descendants


def load_dependency_graph(graph_path: Path) -> dict[str, Any]:
    """Load the workflow dependency graph from JSON file."""
    with open(graph_path, encoding="utf-8") as file:
        return json.load(file)


def load_and_validate_graph(graph_arg: str) -> dict[str, Any]:
    """Load dependency graph from path, exiting with error if not found."""
    graph_path = Path(graph_arg)
    if not graph_path.exists():
        print(f"Error: Dependency graph not found at {graph_path}", file=sys.stderr)
        sys.exit(1)
    return load_dependency_graph(graph_path)


def load_graph_and_compute_roots(
    graph_path: str,
    changed_files: list[str]
) -> tuple[dict[str, Any] | None, list[str], str | None]:
    """Load graph and compute root workflows.

    Returns (graph, roots, error). On success error is None.
    """
    try:
        graph = load_dependency_graph(Path(graph_path))
    except FileNotFoundError:
        return None, [], f"Error: Graph file not found: {graph_path}"
    roots = compute_root_workflows(changed_files, graph)
    return graph, roots, None


def get_all_ancestors(
    workflow: str, graph: dict[str, Any], cache: dict[str, set[str]] | None = None
) -> set[str]:
    """
    Get all ancestors (transitive dependencies) of a workflow.

    Returns a set of workflow keys that this workflow depends on,
    including indirect dependencies.
    """
    if cache is None:
        cache = {}

    if workflow in cache:
        return cache[workflow]

    ancestors: set[str] = set()
    direct_deps = graph.get(workflow, {}).get("depends_on", [])

    for dep in direct_deps:
        ancestors.add(dep)
        ancestors.update(get_all_ancestors(dep, graph, cache))

    cache[workflow] = ancestors
    return ancestors


def insert_sorted(queue: list[str], item: str) -> None:
    """Insert an item into a sorted list maintaining sort order."""
    for i, existing in enumerate(queue):
        if item < existing:
            queue.insert(i, item)
            return
    queue.append(item)


def _build_in_degree_map(
    workflows: set[str], graph: dict[str, Any]
) -> dict[str, int]:
    """Build in-degree map counting dependencies within the workflow set."""
    in_degree: dict[str, int] = {wf: 0 for wf in workflows}
    for wf in workflows:
        for dep in graph.get(wf, {}).get("depends_on", []):
            if dep in workflows:
                in_degree[wf] += 1
    return in_degree


def topological_sort(workflows: set[str], graph: dict[str, Any]) -> list[str]:
    """
    Sort workflows in topological order (dependencies before dependents).

    Uses Kahn's algorithm to ensure workflows are ordered such that
    all dependencies come before their dependents.
    """
    in_degree = _build_in_degree_map(workflows, graph)
    queue = sorted([wf for wf, degree in in_degree.items() if degree == 0])
    result: list[str] = []

    while queue:
        current = queue.pop(0)
        result.append(current)

        # Find workflows that depend on current and add ready ones to queue
        for wf in workflows:
            if current in graph.get(wf, {}).get("depends_on", []):
                in_degree[wf] -= 1
                if in_degree[wf] == 0:
                    insert_sorted(queue, wf)

    return result


def _sort_key(workflow: str, graph: dict[str, Any]) -> tuple[int, str]:
    """Return sort key for a workflow: (display_order, name)."""
    display_order = graph.get(workflow, {}).get("display_order", 999)
    return (display_order, workflow)


def topological_sort_levels(
    workflows: set[str], graph: dict[str, Any]
) -> list[list[str]]:
    """
    Sort workflows into execution levels for parallel execution.

    Returns a list of levels, where each level contains workflows that
    can run in parallel (all their dependencies are in earlier levels).
    Workflows within each level are sorted by display_order, then alphabetically.
    """
    in_degree = _build_in_degree_map(workflows, graph)
    levels: list[list[str]] = []
    remaining = set(workflows)

    while remaining:
        # Find all workflows with no remaining dependencies
        # Sort by display_order first, then alphabetically
        current_level = sorted(
            [wf for wf in remaining if in_degree[wf] == 0],
            key=lambda wf: _sort_key(wf, graph)
        )

        if not current_level:
            # Cycle detected or error
            break

        levels.append(current_level)

        # Remove current level from remaining and update in-degrees
        for wf in current_level:
            remaining.remove(wf)
            for other in remaining:
                if wf in graph.get(other, {}).get("depends_on", []):
                    in_degree[other] -= 1

    return levels


def compute_execution_plan(roots: list[str], graph: dict[str, Any]) -> list[str]:
    """
    Compute the full execution plan starting from root workflows.

    Returns all workflows that need to run (roots + all descendants)
    in topological order.
    """
    # Collect all workflows to run (roots + their descendants)
    all_workflows: set[str] = set(roots)
    descendant_cache: dict[str, set[str]] = {}

    for root in roots:
        all_workflows.update(get_all_descendants(root, graph, descendant_cache))

    # Sort in topological order
    return topological_sort(all_workflows, graph)


def compute_execution_plan_levels(
    roots: list[str], graph: dict[str, Any]
) -> list[list[str]]:
    """
    Compute the full execution plan as levels for parallel execution.

    Returns levels of workflows where each level can run in parallel,
    and all levels must complete before the next level starts.
    """
    # Collect all workflows to run (roots + their descendants)
    all_workflows: set[str] = set(roots)
    descendant_cache: dict[str, set[str]] = {}

    for root in roots:
        all_workflows.update(get_all_descendants(root, graph, descendant_cache))

    # Sort into levels
    return topological_sort_levels(all_workflows, graph)


def file_matches_patterns(filepath: str, patterns: list[str]) -> bool:
    """Check if a file path matches any of the given glob patterns."""
    return any(file_matches_pattern(filepath, pattern) for pattern in patterns)


def get_affected_workflows(
    changed_files: list[str], graph: dict[str, Any]
) -> set[str]:
    """
    Determine which workflows are affected by the changed files.

    Returns a set of workflow keys whose path patterns match any changed file.
    """
    affected: set[str] = set()

    for workflow_key, workflow_config in graph.items():
        patterns = workflow_config.get("paths", [])
        for filepath in changed_files:
            if file_matches_patterns(filepath, patterns):
                affected.add(workflow_key)
                break

    return affected


def compute_root_workflows(
    changed_files: list[str], graph: dict[str, Any]
) -> list[str]:
    """
    Compute the root workflows to trigger.

    A root workflow is one that:
    1. Has files that were modified (affected)
    2. Has NO ancestors that were also affected

    Root workflows should be triggered directly. Their descendants will be
    triggered via workflow_run cascading when the roots complete.
    """
    affected = get_affected_workflows(changed_files, graph)

    if not affected:
        return []

    # Build ancestor cache
    ancestor_cache: dict[str, set[str]] = {}
    for workflow in affected:
        get_all_ancestors(workflow, graph, ancestor_cache)

    # Find roots: affected workflows with no affected ancestors
    roots: list[str] = []
    for workflow in affected:
        ancestors = ancestor_cache.get(workflow, set())
        # If none of this workflow's ancestors are affected, it's a root
        if not ancestors.intersection(affected):
            roots.append(workflow)

    # Sort for deterministic output
    return sorted(roots)


def compute_merge_roots(
    running_workflows: list[str],
    new_roots: list[str],
    graph: dict[str, Any]
) -> list[str]:
    """
    Compute the minimal set of root workflows that covers both
    running workflows and new roots.

    This is used when a new workflowctl run starts while workflows from
    a previous run are still executing. The merge roots are the oldest
    ancestors that need to be (re)started to cover both the running
    workflows and the new changes.
    """
    # If no new roots, nothing to merge - let running workflows finish
    if not new_roots:
        return []

    # Combine all workflows that need to be covered
    affected = set(running_workflows) | set(new_roots)

    # Filter to only workflows that exist in the graph
    affected = {wf for wf in affected if wf in graph}

    if not affected:
        return []

    # Build ancestor cache
    ancestor_cache: dict[str, set[str]] = {}
    for workflow in affected:
        get_all_ancestors(workflow, graph, ancestor_cache)

    # Find merge roots: workflows with no affected ancestors
    roots: list[str] = []
    for workflow in affected:
        ancestors = ancestor_cache.get(workflow, set())
        # If none of this workflow's ancestors are in affected set, it's a root
        if not ancestors.intersection(affected):
            roots.append(workflow)

    # Sort for deterministic output
    return sorted(roots)


def _parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Compute root workflows to trigger based on changed files."
    )
    parser.add_argument(
        "--changed-files",
        required=True,
        help="Comma-separated list of changed files",
    )
    parser.add_argument(
        "--graph",
        default="etc/workflow_dependencies.json",
        help="Path to workflow dependency graph JSON file",
    )
    parser.add_argument(
        "--execution-plan",
        action="store_true",
        help="Output full execution plan (roots + descendants) in topological order",
    )
    parser.add_argument(
        "--start-from",
        help="Specify a workflow to start from (bypasses file detection)",
    )
    parser.add_argument(
        "--slots",
        type=int,
        default=0,
        help="Output slot variables for GitHub Actions (key_01, key_02, ... up to N)",
    )
    parser.add_argument(
        "--indexed",
        action="store_true",
        help="Output as indexed objects [{idx, name}, ...] for GitHub Actions matrix",
    )
    parser.add_argument(
        "--levels",
        action="store_true",
        help="Output execution plan as levels for parallel execution",
    )
    parser.add_argument(
        "--running",
        help="JSON array of currently running workflow keys to merge with",
    )
    return parser.parse_args()


def output_slots(output: list[str], num_slots: int) -> None:
    """Output slot variables for GitHub Actions."""
    print(f"count={len(output)}")
    for i in range(1, num_slots + 1):
        key = output[i - 1] if i <= len(output) else ""
        print(f"key_{i:02d}={key}")


def output_results(output: list[str], indexed: bool = False) -> None:
    """Output results as JSON object."""
    if indexed:
        # Output as objects with idx and name for proper ordering in GitHub Actions UI
        indexed_output = [
            {"idx": f"{i:02d}", "name": name} for i, name in enumerate(output, 1)
        ]
        print(json.dumps({"workflows": indexed_output}))
    else:
        print(json.dumps({"workflows": output}))


def output_levels_indexed(levels: list[list[str]]) -> None:
    """Output levels as indexed objects for GitHub Actions matrix visualization."""
    indexed_output = []
    idx = 1
    for level_num, level_workflows in enumerate(levels, 1):
        for name in level_workflows:
            indexed_output.append({
                "idx": f"{idx:02d}",
                "level": level_num,
                "name": name
            })
            idx += 1
    print(json.dumps({"workflows": indexed_output}))


def main() -> None:
    """Main entry point."""
    args = _parse_args()

    # Parse comma-separated changed files
    changed_files = [
        f.strip() for f in args.changed_files.split(",") if f.strip()
    ]

    # Load dependency graph
    graph = load_and_validate_graph(args.graph)

    # Determine roots: either from --start-from or from changed files
    if args.start_from:
        if args.start_from not in graph:
            print(f"Error: Unknown workflow '{args.start_from}'", file=sys.stderr)
            print(
                f"Available workflows: {', '.join(sorted(graph.keys()))}",
                file=sys.stderr,
            )
            sys.exit(1)
        roots = [args.start_from]
    else:
        roots = compute_root_workflows(changed_files, graph)

    # Merge with running workflows if provided
    if args.running:
        running_workflows = json.loads(args.running)
        if running_workflows:
            roots = compute_merge_roots(running_workflows, roots, graph)

    # Compute execution plan if requested
    if args.levels:
        levels = compute_execution_plan_levels(roots, graph)
        if args.indexed:
            # Output as indexed objects for matrix visualization
            output_levels_indexed(levels)
        else:
            # Output as JSON object with levels array
            print(json.dumps({"levels": levels}))
    elif args.slots > 0:
        output = compute_execution_plan(roots, graph)
        output_slots(output, args.slots)
    elif args.execution_plan:
        output = compute_execution_plan(roots, graph)
        output_results(output, args.indexed)
    else:
        output_results(roots, args.indexed)


if __name__ == "__main__":
    main()

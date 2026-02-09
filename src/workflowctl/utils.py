#!/usr/bin/env python3
"""Shared utilities for workflow orchestration scripts.

This module provides common functions used across multiple orchestration scripts
to avoid code duplication.
"""
import argparse
import fnmatch
import json
import os
import subprocess
import sys
from typing import Any


def create_base_parser(description: str) -> argparse.ArgumentParser:
    """Create a base argument parser with common --repo and --graph args."""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--repo",
        required=True,
        help="The GitHub repository (e.g., 'owner/repo')"
    )
    parser.add_argument(
        "--graph",
        default="etc/workflow_dependencies.json",
        help="Path to the workflow dependency graph file"
    )
    return parser


def add_changed_files_arg(parser: argparse.ArgumentParser) -> None:
    """Add --changed-files argument to parser."""
    parser.add_argument(
        "--changed-files",
        required=True,
        help="Comma-separated list of changed files"
    )


def add_running_arg(parser: argparse.ArgumentParser) -> None:
    """Add --running argument to parser."""
    parser.add_argument(
        "--running",
        default="[]",
        help="JSON array of currently running workflow keys"
    )


def parse_changed_files(changed_files_str: str) -> list[str]:
    """Parse comma-separated changed files string into list."""
    return [f.strip() for f in changed_files_str.split(",") if f.strip()]


def parse_running_workflows(running_str: str) -> tuple[list[str], str | None]:
    """Parse JSON array of running workflows.

    Returns (workflows, error_message). On success error is None.
    """
    try:
        return json.loads(running_str), None
    except json.JSONDecodeError:
        return [], f"Error: Invalid JSON for --running: {running_str}"


def load_graph_or_exit(graph_path: str) -> tuple[dict[str, Any] | None, str | None]:
    """Load graph from path, returning (graph, error).

    On success returns (graph, None). On failure returns (None, error_message).
    """
    graph, error = load_graph_with_error(graph_path)
    if graph is None:
        return None, error
    return graph, None


def load_graph_with_error(graph_path: str) -> tuple[dict[str, Any] | None, str]:
    """Load dependency graph, returning (graph, error_message).

    Returns (graph, "") on success, (None, error_message) on failure.
    """
    try:
        return load_dependency_graph(graph_path), ""
    except FileNotFoundError:
        return None, f"Error: Graph file not found: {graph_path}"


def load_dependency_graph(graph_path: str) -> dict[str, Any]:
    """Load the workflow dependency graph from JSON file."""
    with open(graph_path, encoding="utf-8") as f:
        return json.load(f)


def build_name_to_key_map(graph: dict[str, Any]) -> dict[str, str]:
    """Build a mapping from workflow display names to workflow keys.

    This is used to map the workflow names returned by GitHub API
    to the workflow keys used in the dependency graph.
    """
    name_to_key: dict[str, str] = {}
    for key, config in graph.items():
        name = config.get("name", "")
        if name:
            name_to_key[name] = key
    return name_to_key


def get_all_descendants(
    workflow: str, graph: dict[str, Any], cache: dict[str, set[str]] | None = None
) -> set[str]:
    """Get all descendants (workflows that depend on this one) of a workflow.

    Returns a set of workflow keys that depend on this workflow,
    including indirect dependents.
    """
    if cache is None:
        cache = {}

    if workflow in cache:
        return cache[workflow]

    descendants: set[str] = set()

    # Find all workflows that directly depend on this one
    for wf_key, wf_config in graph.items():
        if workflow in wf_config.get("depends_on", []):
            descendants.add(wf_key)
            descendants.update(get_all_descendants(wf_key, graph, cache))

    cache[workflow] = descendants
    return descendants


def get_workflow_runs(repo: str, status: str) -> list[dict[str, Any]]:
    """Query GitHub API for workflow runs with the given status.

    Args:
        repo: The GitHub repository (e.g., 'owner/repo')
        status: The workflow run status to filter by (e.g., 'in_progress', 'queued')

    Returns:
        List of workflow run objects from the API
    """
    result = subprocess.run(
        [
            "gh", "api",
            f"repos/{repo}/actions/runs",
            "-q", f".workflow_runs | map(select(.status == \"{status}\"))"
        ],
        capture_output=True,
        text=True,
        check=False
    )
    if result.returncode != 0:
        return []

    try:
        return json.loads(result.stdout) if result.stdout.strip() else []
    except json.JSONDecodeError:
        return []


def file_matches_pattern(filepath: str, pattern: str) -> bool:
    """Check if a file path matches a glob pattern.

    Supports ** for recursive directory matching.
    """
    if "**" in pattern:
        base_pattern = pattern.replace("**", "*")
        if fnmatch.fnmatch(filepath, base_pattern):
            return True
        dir_prefix = pattern.split("**")[0]
        if filepath.startswith(dir_prefix):
            return True
    return fnmatch.fnmatch(filepath, pattern)


def run_subprocess(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    """Run a subprocess with standard options."""
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False
    )


def dispatch_gh_workflow(
    workflow_file: str,
    repo: str,
    extra_args: list[str] | None = None
) -> bool:
    """Dispatch a GitHub workflow using gh CLI.

    Returns True on success, False on failure.
    """
    cmd = ["gh", "workflow", "run", workflow_file, "--repo", repo]
    if extra_args:
        cmd.extend(extra_args)

    result = run_subprocess(cmd)
    if result.returncode != 0:
        print(f"    Error: {result.stderr.strip()}", file=sys.stderr)
        return False
    return True


def workflow_file_exists(workflow: str) -> bool:
    """Check if the workflow file exists."""
    workflow_file = f".github/workflows/{workflow}.yml"
    return os.path.isfile(workflow_file)


def workflow_accepts_input(workflow: str, input_name: str) -> bool:
    """Check if a workflow accepts a specific input."""
    workflow_file = f".github/workflows/{workflow}.yml"
    try:
        with open(workflow_file, encoding="utf-8") as f:
            content = f.read()
            return f"{input_name}:" in content
    except (OSError, IOError):
        return False

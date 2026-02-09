#!/usr/bin/env python3
"""Get currently running workflows from GitHub Actions.

This script queries the GitHub API for workflow runs that are in_progress or queued,
maps them to workflow keys using the dependency graph, and outputs a JSON object.

Usage:
    python3 src/workflowctl/workflowctl.py get-running-workflows --repo owner/repo

Output:
    {"workflows": ["bootstrap", "www_redirect"]}
"""
import argparse
import json
import sys

from utils import (
    build_name_to_key_map,
    create_base_parser,
    get_workflow_runs,
    load_graph_with_error,
)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = create_base_parser(
        "Get currently running workflows from GitHub Actions"
    )
    parser.add_argument(
        "--exclude-workflowctl",
        action="store_true",
        default=True,
        help="Exclude the workflowctl workflow from results (default: true)"
    )
    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    args = parse_args()

    # Load dependency graph
    graph, error = load_graph_with_error(args.graph)
    if graph is None:
        print(error, file=sys.stderr)
        return 1

    # Build name-to-key mapping
    name_to_key = build_name_to_key_map(graph)

    # Get in_progress and queued workflow runs
    in_progress = get_workflow_runs(args.repo, "in_progress")
    queued = get_workflow_runs(args.repo, "queued")

    # Combine and extract unique workflow names
    all_runs = in_progress + queued
    workflow_names = set()
    for run in all_runs:
        name = run.get("name", "")
        if name:
            workflow_names.add(name)

    # Map names to keys
    workflow_keys: list[str] = []
    for name in workflow_names:
        if name in name_to_key:
            key = name_to_key[name]
            # Optionally exclude workflowctl
            if args.exclude_workflowctl and key == "workflowctl":
                continue
            workflow_keys.append(key)

    # Sort for deterministic output
    workflow_keys.sort()

    # Output as JSON object
    print(json.dumps({"workflows": workflow_keys}))
    return 0


if __name__ == "__main__":
    sys.exit(main())

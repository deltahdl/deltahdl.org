#!/usr/bin/env python3
"""Compute which descendant workflows are ready to dispatch.

This script reads the workflow dependency graph and identifies all workflows
that depend on the completed workflow. For each descendant, it determines
whether all dependencies have been satisfied (ready) or if some are still
missing (waiting).

Outputs:
    - GITHUB_OUTPUT: Sets 'ready' and 'waiting' variables
    - GITHUB_STEP_SUMMARY: Writes a markdown summary of descendants

Usage:
    python3 src/workflowctl/workflowctl.py compute-descendants \
        --workflow bootstrap --repo owner/repo

Exit codes:
    0: Success
    1: Failure (e.g., graph file not found)
"""
import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from typing import Any

from utils import create_base_parser, load_dependency_graph


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = create_base_parser(
        "Compute which descendant workflows are ready to dispatch"
    )
    parser.add_argument(
        "--workflow",
        required=True,
        help="The workflow key that just completed (e.g., 'bootstrap')"
    )
    parser.add_argument(
        "--lookback-hours",
        type=int,
        default=24,
        help="Hours to look back for successful dependency runs (default: 24)"
    )
    return parser.parse_args()


def find_descendants(graph: dict[str, Any], workflow: str) -> list[str]:
    """Find all workflows that directly depend on the specified workflow."""
    return [
        name for name, config in graph.items()
        if workflow in config.get("depends_on", [])
    ]


def check_workflow_completed(
    workflow_key: str,
    repo: str,
    since: datetime
) -> bool:
    """Check if a workflow has completed successfully since the given time."""
    since_str = since.strftime("%Y-%m-%dT%H:%M:%SZ")
    result = subprocess.run(
        [
            "gh", "api",
            f"repos/{repo}/actions/workflows/{workflow_key}.yml/runs"
            f"?status=success&created=%3E%3D{since_str}",
            "-q", ".workflow_runs[0].id",
        ],
        capture_output=True,
        text=True,
        check=False
    )
    # If we got any output, there's at least one successful run
    return bool(result.stdout.strip())


def get_dependency_status(
    graph: dict[str, Any],
    descendant: str,
    current_workflow: str,
    repo: str,
    lookback_hours: int
) -> dict[str, Any]:
    """Get detailed dependency status for a descendant workflow.

    Returns a dict with:
        - all_met: bool - whether all dependencies are satisfied
        - satisfied: list[str] - dependencies that have been met
        - missing: list[str] - dependencies that are still missing
    """
    dependencies = graph.get(descendant, {}).get("depends_on", [])
    other_deps = [d for d in dependencies if d != current_workflow]

    # Current workflow is always satisfied (it just completed)
    satisfied = [current_workflow]
    missing: list[str] = []

    if other_deps:
        since = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
        for dep in other_deps:
            if check_workflow_completed(dep, repo, since):
                satisfied.append(dep)
            else:
                missing.append(dep)

    return {
        "all_met": len(missing) == 0,
        "satisfied": satisfied,
        "missing": missing
    }


def compute_descendants_status(
    graph: dict[str, Any],
    workflow: str,
    repo: str,
    lookback_hours: int
) -> tuple[list[str], dict[str, dict[str, Any]]]:
    """Compute which descendants are ready vs waiting.

    Returns:
        ready: List of workflow keys ready to dispatch
        waiting: Dict mapping workflow keys to their missing dependency info
    """
    descendants = find_descendants(graph, workflow)

    ready: list[str] = []
    waiting: dict[str, dict[str, Any]] = {}

    for descendant in descendants:
        status = get_dependency_status(
            graph, descendant, workflow, repo, lookback_hours
        )

        if status["all_met"]:
            ready.append(descendant)
        else:
            waiting[descendant] = {
                "missing": status["missing"],
                "satisfied": status["satisfied"]
            }

    return ready, waiting


def write_github_output(ready: list[str], waiting: dict[str, Any]) -> None:
    """Write outputs to GITHUB_OUTPUT file."""
    output_file = os.environ.get("GITHUB_OUTPUT")
    if not output_file:
        return

    with open(output_file, "a", encoding="utf-8") as f:
        f.write(f"ready={json.dumps(ready)}\n")
        f.write(f"waiting={json.dumps(waiting)}\n")


def write_step_summary(
    workflow: str,
    ready: list[str],
    waiting: dict[str, dict[str, Any]]
) -> None:
    """Write a GitHub Step Summary with descendant status."""
    summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_file:
        return

    lines = [
        "## Descendant Dispatch Summary",
        "",
        f"**Completed:** `{workflow}`",
        "",
    ]

    descendants = ready + list(waiting.keys())
    if not descendants:
        lines.append("*No descendants found.*")
    else:
        lines.extend([
            "| Descendant | Status | Details |",
            "|------------|--------|---------|",
        ])

        for desc in ready:
            lines.append(f"| `{desc}` | Ready | All dependencies satisfied |")

        for desc, info in waiting.items():
            missing_str = ", ".join(f"`{m}`" for m in info["missing"])
            lines.append(f"| `{desc}` | Waiting | Missing: {missing_str} |")

        if waiting:
            lines.extend(["", "### Waiting Workflows"])
            for desc, info in waiting.items():
                lines.append(f"**{desc}** requires:")
                for dep in info["satisfied"]:
                    lines.append(f"- `{dep}` - Satisfied")
                for dep in info["missing"]:
                    lines.append(f"- `{dep}` - Missing (no successful run)")

    lines.append("")

    with open(summary_file, "a", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main() -> int:
    """Main entry point."""
    args = parse_args()

    graph = load_dependency_graph(args.graph)
    ready, waiting = compute_descendants_status(
        graph, args.workflow, args.repo, args.lookback_hours
    )

    # Write outputs
    write_github_output(ready, waiting)
    write_step_summary(args.workflow, ready, waiting)

    # Print JSON to stdout for debugging/local use
    result = {
        "completed_workflow": args.workflow,
        "ready": ready,
        "waiting": waiting
    }
    print(json.dumps(result, indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())

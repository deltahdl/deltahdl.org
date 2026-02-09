#!/usr/bin/env python3
"""Dispatch root workflows to GitHub Actions.

This module handles dispatching root workflows with proper trigger_descendants
and invalidate_cloudfront logic based on inputs, commit messages, and changed files.

Usage:
    python3 src/workflowctl/workflowctl.py dispatch-root-workflows \
        --repo owner/repo \
        --changed-files "file1.py,file2.py" \
        --running '["www_redirect"]' \
        --trigger-descendants \
        --invalidate-cloudfront

Exit codes:
    0: Success (all dispatches succeeded or nothing to dispatch)
    1: Failure (at least one dispatch failed)

No stdout output. Errors go to stderr.
"""
import argparse
import os
import re
import sys

from compute_roots import compute_merge_roots, load_graph_and_compute_roots
from utils import (
    add_changed_files_arg,
    add_running_arg,
    dispatch_gh_workflow,
    parse_changed_files,
    parse_running_workflows,
    workflow_accepts_input,
    workflow_file_exists,
)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Dispatch root workflows to GitHub Actions"
    )
    parser.add_argument(
        "--repo",
        required=True,
        help="GitHub repository (owner/repo)"
    )
    add_changed_files_arg(parser)
    add_running_arg(parser)
    parser.add_argument(
        "--commit-message",
        default=os.environ.get("COMMIT_MESSAGE", ""),
        help="The commit message to check for [trigger descendants] or [invalidate cloudfront]"
    )
    parser.add_argument(
        "--trigger-descendants",
        action="store_true",
        help="Trigger descendant workflows after root workflows complete"
    )
    parser.add_argument(
        "--invalidate-cloudfront",
        action="store_true",
        help="Force CloudFront cache invalidation in descendant workflows"
    )
    parser.add_argument(
        "--graph",
        default="etc/workflow_dependencies.json",
        help="Path to workflow dependency graph JSON file"
    )
    return parser.parse_args()


def should_trigger_descendants(
    trigger_flag: bool,
    commit_message: str
) -> bool:
    """Determine if descendants should be triggered.

    Returns True if:
    1. trigger_flag is True (--trigger-descendants passed), OR
    2. Commit message contains [trigger descendants]
    """
    if trigger_flag:
        return True

    if re.search(r"\[trigger descendants\]", commit_message, re.IGNORECASE):
        return True

    return False


def should_invalidate_cloudfront(
    invalidate_flag: bool,
    commit_message: str
) -> bool:
    """Determine if CloudFront cache should be invalidated.

    Returns True if:
    1. invalidate_flag is True (--invalidate-cloudfront passed), OR
    2. Commit message contains [invalidate cloudfront]
    """
    if invalidate_flag:
        return True

    if re.search(r"\[invalidate cloudfront\]", commit_message, re.IGNORECASE):
        return True

    return False


def dispatch_workflow(
    workflow: str,
    repo: str,
    trigger_descendants: bool,
    invalidate_cloudfront: bool
) -> bool:
    """Dispatch a single workflow. Returns True on success."""
    workflow_file = f".github/workflows/{workflow}.yml"

    # Build list of flags to pass
    flags: list[str] = []
    if trigger_descendants and workflow_accepts_input(workflow, "trigger_descendants"):
        flags.extend(["-f", "trigger_descendants=true"])
    if invalidate_cloudfront and workflow_accepts_input(workflow, "invalidate_cloudfront"):
        flags.extend(["-f", "invalidate_cloudfront=true"])

    extra_args = flags if flags else None
    return dispatch_gh_workflow(workflow_file, repo, extra_args)


def main() -> int:
    """Main entry point."""
    args = parse_args()
    changed_files = parse_changed_files(args.changed_files)

    graph, roots, error = load_graph_and_compute_roots(args.graph, changed_files)
    if error or graph is None:
        print(error, file=sys.stderr)
        return 1

    running_workflows, error = parse_running_workflows(args.running)
    if error:
        print(error, file=sys.stderr)
        return 1

    if running_workflows:
        roots = compute_merge_roots(running_workflows, roots, graph)

    if not roots:
        return 0

    # Determine if we should trigger descendants
    trigger = should_trigger_descendants(
        args.trigger_descendants,
        args.commit_message
    )

    # Determine if we should invalidate CloudFront
    invalidate = should_invalidate_cloudfront(
        args.invalidate_cloudfront,
        args.commit_message
    )

    # Dispatch each root
    failed = 0
    for workflow in roots:
        if not workflow_file_exists(workflow):
            continue
        if not dispatch_workflow(workflow, args.repo, trigger, invalidate):
            failed += 1

    return 1 if failed > 0 else 0


if __name__ == "__main__":
    sys.exit(main())

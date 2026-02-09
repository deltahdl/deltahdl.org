#!/usr/bin/env python3
"""Dispatch a single workflow to GitHub Actions.

Usage:
    python3 src/workflowctl/workflowctl.py dispatch-workflow \
        --workflow bootstrap \
        --repo owner/repo \
        --trigger-descendants \
        --invalidate-cloudfront

Exit codes:
    0: Success
    1: Failure
"""
import argparse
import sys

from utils import (
    dispatch_gh_workflow,
    workflow_accepts_input,
    workflow_file_exists,
)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Dispatch a single workflow to GitHub Actions"
    )
    parser.add_argument(
        "--workflow",
        required=True,
        help="Workflow name (without .yml extension)"
    )
    parser.add_argument(
        "--repo",
        required=True,
        help="GitHub repository (owner/repo)"
    )
    parser.add_argument(
        "--trigger-descendants",
        action="store_true",
        help="Pass trigger_descendants=true to the workflow"
    )
    parser.add_argument(
        "--invalidate-cloudfront",
        action="store_true",
        help="Pass invalidate_cloudfront=true to the workflow"
    )
    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    args = parse_args()

    if not workflow_file_exists(args.workflow):
        print(f"Workflow file not found: {args.workflow}.yml", file=sys.stderr)
        return 1

    workflow_file = f".github/workflows/{args.workflow}.yml"

    flags: list[str] = []
    if args.trigger_descendants:
        if workflow_accepts_input(args.workflow, "trigger_descendants"):
            flags.extend(["-f", "trigger_descendants=true"])
    if args.invalidate_cloudfront:
        if workflow_accepts_input(args.workflow, "invalidate_cloudfront"):
            flags.extend(["-f", "invalidate_cloudfront=true"])

    extra_args = flags if flags else None
    success = dispatch_gh_workflow(workflow_file, args.repo, extra_args)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Get changed files between two git commits.

This module handles edge cases like force pushes, shallow clones, and
initial commits to reliably determine which files changed.

Supports per-commit skip-CI filtering: files from commits with skip markers
(e.g., [skip ci], [ci skip]) in the message are excluded from the output.

Usage:
    python3 src/workflowctl/workflowctl.py get-changed-files \
        --base <base_sha> --head <head_sha> [--commits <json>]

Output:
    {"files": ["file1.py", "file2.py", ...]}
"""
import argparse
import json
import sys

from utils import run_subprocess


ZERO_SHA = "0000000000000000000000000000000000000000"
SKIP_CI_MARKERS = ["[skip ci]", "[ci skip]", "[no ci]", "[skip actions]"]


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Get changed files between two git commits"
    )
    parser.add_argument(
        "--base",
        required=True,
        help="Base commit SHA (before)"
    )
    parser.add_argument(
        "--head",
        required=True,
        help="Head commit SHA (current)"
    )
    parser.add_argument(
        "--commits",
        required=False,
        default="",
        help="JSON array of commits from github.event.commits"
    )
    return parser.parse_args()


def commit_exists(sha: str) -> bool:
    """Check if a commit exists in the repository."""
    result = run_subprocess(["git", "cat-file", "-e", sha])
    return result.returncode == 0


def get_changed_files_diff(base: str, head: str) -> list[str]:
    """Get changed files using git diff."""
    result = run_subprocess(["git", "diff", "--name-only", base, head])
    if result.returncode != 0:
        return []
    return [f for f in result.stdout.strip().split("\n") if f]


def get_changed_files_show(head: str) -> list[str]:
    """Get changed files using git show (fallback for single commit)."""
    result = run_subprocess(["git", "show", "--name-only", "--format=", head])
    if result.returncode != 0:
        return []
    return [f for f in result.stdout.strip().split("\n") if f]


def get_changed_files(base: str, head: str) -> list[str]:
    """Get list of changed files between base and head commits.

    Handles edge cases:
    - Zero SHA (initial commit or force push): uses HEAD~1
    - Missing base commit (shallow clone): uses HEAD~1
    - Both fallback to git show if git diff fails
    """
    # Determine effective base commit
    if base == ZERO_SHA:
        # Initial commit or force push
        effective_base = "HEAD~1"
    elif commit_exists(base):
        effective_base = base
    else:
        # Shallow clone - base commit not available
        effective_base = "HEAD~1"

    # Try git diff first
    files = get_changed_files_diff(effective_base, head)
    if files:
        return files

    # Fallback to git show for current commit
    return get_changed_files_show(head)


def has_skip_ci(message: str) -> bool:
    """Check if a commit message contains a skip CI marker."""
    message_lower = message.lower()
    return any(marker.lower() in message_lower for marker in SKIP_CI_MARKERS)


def get_files_for_commit(sha: str) -> list[str]:
    """Get files changed by a specific commit."""
    result = run_subprocess(["git", "show", "--name-only", "--format=", sha])
    if result.returncode != 0:
        return []
    return [f for f in result.stdout.strip().split("\n") if f]


def filter_files_by_commits(commits_json: str) -> set[str]:
    """Filter files based on per-commit [skip ci] markers.

    Returns set of files that should be EXCLUDED (from [skip ci] commits).
    """
    if not commits_json:
        return set()

    try:
        commits = json.loads(commits_json)
    except json.JSONDecodeError:
        return set()

    if not isinstance(commits, list):
        return set()

    excluded_files: set[str] = set()
    for commit in commits:
        message = commit.get("message", "")
        if has_skip_ci(message):
            commit_id = commit.get("id", "")
            if commit_id:
                files = get_files_for_commit(commit_id)
                excluded_files.update(files)

    return excluded_files


def main() -> int:
    """Main entry point."""
    args = parse_args()
    files = get_changed_files(args.base, args.head)

    # Filter out files from commits with [skip ci]
    if args.commits:
        excluded = filter_files_by_commits(args.commits)
        files = [f for f in files if f not in excluded]

    # Output as JSON object
    print(json.dumps({"files": files}))

    return 0


if __name__ == "__main__":
    sys.exit(main())

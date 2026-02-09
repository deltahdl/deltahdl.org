"""Pytest fixtures for workflowctl pre-deployment integration tests."""

import json

import pytest

from repo_utils import REPO_ROOT


GRAPH_PATH = REPO_ROOT / "etc" / "workflow_dependencies.json"
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"


@pytest.fixture(scope="module")
def dependency_graph() -> dict:
    """Load the workflow dependency graph."""
    with open(GRAPH_PATH, encoding="utf-8") as graph_file:
        return json.load(graph_file)


@pytest.fixture(scope="module")
def workflow_files() -> set:
    """Get set of workflow file stems (without .yml extension)."""
    return {
        f.stem for f in WORKFLOWS_DIR.glob("*.yml")
        if not f.stem.startswith(".")
    }

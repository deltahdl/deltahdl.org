"""Pytest configuration for workflowctl tests.

This module provides fixtures for testing workflowctl scripts. It uses dynamic
module loading because src/workflowctl/*.py are standalone scripts without
__init__.py (they're executed directly, not imported as packages).

Note: workflowctl tests mock subprocess calls, not AWS SDK calls. For AWS-related
tests, use pytest_plugins = ['test_fixtures.unit'] or ['test_fixtures.aws'].
"""

import importlib.util
import sys
from typing import Any, Dict

import pytest

from repo_utils import REPO_ROOT


# Standard dependency graph for testing workflowctl functionality.
# This graph represents a linear dependency chain with paths for file matching.
# Use this fixture when testing functions that need a realistic workflow graph.
SAMPLE_GRAPH: Dict[str, Dict[str, Any]] = {
    "bootstrap": {
        "name": "Bootstrap",
        "depends_on": [],
        "paths": [".github/workflows/bootstrap.yml", "src/bootstrap/**"],
    },
    "www_redirect": {
        "name": "WWW Redirect",
        "depends_on": ["bootstrap"],
        "paths": [".github/workflows/www_redirect.yml", "src/www/redirect/**"],
    },
}

WORKFLOWCTL_DIR = REPO_ROOT / "src" / "workflowctl"
sys.path.insert(0, str(WORKFLOWCTL_DIR))


def _load_module(name: str):
    """Load a module from the workflowctl directory."""
    module_path = WORKFLOWCTL_DIR / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load {name} module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# Load all workflowctl modules
_workflowctl_module = _load_module("workflowctl")
_utils_module = _load_module("utils")
_cancel_module = _load_module("cancel")
_compute_descendants_module = _load_module("compute_descendants")
_dispatch_roots_module = _load_module("dispatch_roots")
_get_changed_files_module = _load_module("get_changed_files")
_get_running_module = _load_module("get_running")
_compute_roots_module = _load_module("compute_roots")
_dispatch_workflow_module = _load_module("dispatch_workflow")


@pytest.fixture
def workflowctl():
    """Provide access to the workflowctl module."""
    return _workflowctl_module


@pytest.fixture
def utils():
    """Provide access to the utils module."""
    return _utils_module


@pytest.fixture
def cancel():
    """Provide access to the cancel module."""
    return _cancel_module


@pytest.fixture
def compute_descendants():
    """Provide access to the compute_descendants module."""
    return _compute_descendants_module


@pytest.fixture
def dispatch_roots():
    """Provide access to the dispatch_roots module."""
    return _dispatch_roots_module


@pytest.fixture
def get_changed_files():
    """Provide access to the get_changed_files module."""
    return _get_changed_files_module


@pytest.fixture
def get_running():
    """Provide access to the get_running module."""
    return _get_running_module


@pytest.fixture
def compute_roots():
    """Provide access to the compute_roots module."""
    return _compute_roots_module


@pytest.fixture
def dispatch_workflow():
    """Provide access to the dispatch_workflow module."""
    return _dispatch_workflow_module


@pytest.fixture
def sample_graph() -> Dict[str, Dict[str, Any]]:
    """Provide a standard dependency graph for testing.

    This graph represents a linear chain:
    bootstrap -> www_redirect

    Each workflow has name, depends_on, and paths fields.
    """
    return SAMPLE_GRAPH.copy()

"""Pytest fixtures for pre-deployment unit tests."""

import pytest
from repo_utils import REPO_ROOT


SRC_DIR = REPO_ROOT / "src" / "www" / "redirect"


@pytest.fixture
def src_dir():
    """Provide the source directory path."""
    return SRC_DIR

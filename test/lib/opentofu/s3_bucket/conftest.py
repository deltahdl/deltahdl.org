"""Pytest fixtures for s3_bucket module tests."""
import pytest


@pytest.fixture(name="module_path")
def fixture_module_path(modules_dir):
    """Provide path to s3_bucket module directory."""
    return modules_dir / "s3_bucket"

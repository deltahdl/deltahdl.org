"""Pytest fixtures for common module tests."""
import pytest


@pytest.fixture(name="module_path")
def fixture_module_path(modules_dir):
    """Provide path to common module directory."""
    return modules_dir / "common"


@pytest.fixture(name="locals_tf_content")
def fixture_locals_tf_content(module_path):
    """Provide locals.tf file content."""
    with open(module_path / "locals.tf", encoding="utf-8") as f:
        return f.read()

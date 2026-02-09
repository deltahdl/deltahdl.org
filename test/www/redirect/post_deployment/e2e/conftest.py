"""Pytest fixtures for www redirect E2E tests."""
import pytest


@pytest.fixture
def apex_domain():
    """Apex domain under test."""
    return "deltahdl.org"


@pytest.fixture
def www_domain():
    """WWW domain under test."""
    return "www.deltahdl.org"


@pytest.fixture
def redirect_target():
    """Expected redirect target."""
    return "https://github.com/deltahdl/deltahdl"

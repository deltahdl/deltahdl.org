"""Shared test helpers for naming convention tests."""
import pytest

from naming_conventions import validate_name


def create_iam_role_tests(roles: list):
    """Create test class for IAM role naming conventions.

    Args:
        roles: List of (resource_name, role_name) tuples

    Returns:
        Test class with parametrized tests for the given roles.
    """
    class TestIAMRoleNamingConventions:
        """Tests for IAM role naming conventions."""

        @staticmethod
        def get_role_count():
            """Return the number of roles being tested."""
            return len(roles)

        @pytest.mark.parametrize(
            "resource_name,role_name",
            roles,
            ids=[f"iam_role_{r[0]}" for r in roles],
        )
        def test_iam_role_name_is_pascalcase(self, resource_name, role_name):
            """Verify IAM role name uses PascalCase (no dashes or underscores)."""
            error = validate_name(role_name)
            assert error is None, (
                f"IAM role '{resource_name}' has invalid name '{role_name}': {error}"
            )

    return TestIAMRoleNamingConventions

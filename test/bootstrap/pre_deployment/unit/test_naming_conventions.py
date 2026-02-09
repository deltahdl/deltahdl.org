"""Unit tests to verify IAM role names use PascalCase in bootstrap.

These tests parse OpenTofu files to validate naming conventions before deployment.
Names must use PascalCase (no dashes, underscores, or other separators).
"""
import re

import pytest

from naming_conventions import validate_name
from repo_utils import REPO_ROOT
from opentofu_config import get_resource_prefix

BOOTSTRAP_SRC = REPO_ROOT / "src" / "bootstrap"


def extract_iam_role_names_from_bootstrap_locals() -> list:
    """Extract IAM role names from bootstrap locals.tf.

    Bootstrap passes role names to modules via variables, so we extract
    the actual names from locals.tf where they're defined.
    """
    locals_file = BOOTSTRAP_SRC / "locals.tf"
    if not locals_file.exists():
        return []

    with open(locals_file, encoding="utf-8") as f:
        content = f.read()

    prefix = get_resource_prefix()
    roles = []

    # Match locals that define IAM role names (contain "role" in the name)
    for match in re.finditer(r'(name_for_\w*role\w*)\s*=\s*"([^"]*)"', content, re.I):
        local_name, value = match.groups()
        # Resolve ${local.resource_prefix} references
        resolved = value.replace("${local.resource_prefix}", prefix)
        roles.append((local_name, resolved, "locals.tf"))

    return roles


IAM_ROLES = extract_iam_role_names_from_bootstrap_locals()


class TestIAMRoleNamingConventions:
    """Tests for IAM role naming conventions in bootstrap."""

    @pytest.mark.parametrize(
        "resource_name,role_name,source_file",
        IAM_ROLES if IAM_ROLES else [("NONE", "NONE", "NONE")],
        ids=([f"{r[2]}::{r[0]}" for r in IAM_ROLES]
             if IAM_ROLES else ["no_roles_found"]),
    )
    def test_iam_role_name_is_pascalcase(self, resource_name, role_name, source_file):
        """Verify IAM role name uses PascalCase (no dashes or underscores)."""
        if resource_name == "NONE":
            pytest.fail("No IAM roles found in bootstrap - check OpenTofu files")
        error = validate_name(role_name)
        assert error is None, (
            f"IAM role '{resource_name}' in {source_file} has invalid name "
            f"'{role_name}': {error}"
        )

    def test_no_iam_role_names_contain_dashes(self):
        """Verify no IAM role names contain dashes."""
        violations = [(r, n, f) for r, n, f in IAM_ROLES if '-' in n]
        assert len(violations) == 0, (
            f"Found {len(violations)} IAM roles with dashes:\n"
            + "\n".join(f"  - {f}::{r}: '{n}'" for r, n, f in violations)
        )

    def test_no_iam_role_names_contain_underscores(self):
        """Verify no IAM role names contain underscores."""
        violations = [(r, n, f) for r, n, f in IAM_ROLES if '_' in n]
        assert len(violations) == 0, (
            f"Found {len(violations)} IAM roles with underscores:\n"
            + "\n".join(f"  - {f}::{r}: '{n}'" for r, n, f in violations)
        )

    def test_all_iam_role_names_start_with_uppercase(self):
        """Verify all IAM role names start with an uppercase letter."""
        violations = [(r, n, f) for r, n, f in IAM_ROLES if n and not n[0].isupper()]
        assert len(violations) == 0, (
            f"Found {len(violations)} IAM roles not starting with uppercase:\n"
            + "\n".join(f"  - {f}::{r}: '{n}'" for r, n, f in violations)
        )


class TestExpectedRoles:
    """Tests for specific expected IAM roles in DeltaHDL bootstrap."""

    def test_github_actions_role_exists_in_locals(self):
        """Verify DeltaHDLGitHubActionsRole is defined in locals."""
        role_names = [n for _, n, _ in IAM_ROLES]
        assert any("GitHubActionsRole" in n for n in role_names), (
            "Expected DeltaHDLGitHubActionsRole not found in locals.tf"
        )

    def test_cloudtrail_logs_role_exists_in_locals(self):
        """Verify DeltaHDLCloudTrailLogsRole is defined in locals."""
        role_names = [n for _, n, _ in IAM_ROLES]
        assert any("CloudTrailLogsRole" in n for n in role_names), (
            "Expected DeltaHDLCloudTrailLogsRole not found in locals.tf"
        )

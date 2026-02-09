"""
Naming convention validation module.

This module provides functions to validate AWS resource naming conventions,
specifically for ensuring IAM roles use PascalCase.

Example usage:
    from naming_conventions import is_pascalcase, validate_name, find_violations

    is_pascalcase("DeltaHDLMyRole")  # True
    is_pascalcase("DeltaHDL-MyRole")  # False (contains dash)

    validate_name("DeltaHDL-MyRole")  # Returns error string
    find_violations(["DeltaHDLGood", "Bad-Name"])
"""

import re
from typing import List, Optional, Tuple

from repo_utils import extract_brace_block


def is_pascalcase(name: str) -> bool:
    """Check if a name follows PascalCase naming convention.

    Args:
        name: The name to validate.

    Returns:
        True if the name is valid PascalCase, False otherwise.
    """
    if not name:
        return False
    if not name[0].isupper():
        return False
    if not name.isalnum():
        return False
    return True


def validate_name(name: str) -> Optional[str]:
    """Validate a resource name and return an error message if invalid.

    Args:
        name: The name to validate.

    Returns:
        None if valid, or an error message string describing the issue.
    """
    if not name:
        return "Name is empty"

    violations = [
        (not name[0].isupper(), f"Name '{name}' must start with uppercase letter"),
        ('-' in name, f"Name '{name}' contains dash (-), use PascalCase instead"),
        ('_' in name, f"Name '{name}' contains underscore (_), use PascalCase instead"),
        (' ' in name, f"Name '{name}' contains space, use PascalCase instead"),
        (not name.isalnum(), f"Name '{name}' contains non-alphanumeric characters"),
    ]

    for condition, error_msg in violations:
        if condition:
            return error_msg

    return None


def find_violations(names: List[str]) -> List[Tuple[str, str]]:
    """Find all naming convention violations in a list of names.

    Args:
        names: List of names to check.

    Returns:
        List of tuples (name, error_message) for each violation.
    """
    violations = []
    for name in names:
        error = validate_name(name)
        if error:
            violations.append((name, error))
    return violations


def extract_iam_role_names_from_opentofu(content: str) -> List[Tuple[str, str]]:
    """Extract IAM role names from OpenTofu file content.

    Args:
        content: Raw content of an OpenTofu .tf file.

    Returns:
        List of tuples (resource_name, role_name) found in the file.
    """
    roles = []
    role_block_pattern = r'resource\s+"aws_iam_role"\s+"([^"]+)"\s*\{'

    for match in re.finditer(role_block_pattern, content):
        resource_name = match.group(1)
        block_content = extract_brace_block(content, match.end() - 1)

        name_pattern = r'name\s*=\s*"([^"]+)"'
        name_match = re.search(name_pattern, block_content)
        if name_match:
            roles.append((resource_name, name_match.group(1)))

    return roles

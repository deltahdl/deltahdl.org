"""
OpenTofu configuration parsing module.

This module provides functions to parse values from the shared OpenTofu module,
providing a single source of truth for configuration values across tests and tools.

Example usage:
    from opentofu_config import get_shared_config, TEST_AWS_REGION

    config = get_shared_config()
    region = config['aws_region']
    bucket = config['name_for_opentofu_state_bucket']

    # For unit test mock data (fake ARNs, URLs, etc.):
    mock_arn = f'arn:aws:s3:::{TEST_AWS_REGION}:123456789012:test-bucket'
"""

import re
from typing import Any, Dict

from repo_utils import REPO_ROOT as _REPO_ROOT

COMMON_MODULE_DIR = _REPO_ROOT / "lib" / "opentofu" / "common"


def parse_locals() -> Dict[str, str]:
    """Parse locals from the shared OpenTofu module's locals.tf file.

    Returns:
        Dict mapping local variable names to their string values.
        Only simple string assignments are parsed (key = "value").
    """
    locals_path = COMMON_MODULE_DIR / "locals.tf"
    with open(locals_path, encoding="utf-8") as f:
        content = f.read()

    values = {}
    pattern = r'(\w+)\s*=\s*"([^"]+)"'
    for match in re.finditer(pattern, content):
        key, value = match.groups()
        values[key] = value
    return values


def parse_outputs() -> Dict[str, str]:
    """Parse outputs from the shared OpenTofu module's outputs.tf file.

    Resolves local.* references using values from locals.tf.

    Returns:
        Dict mapping output names to their resolved string values.
    """
    outputs_path = COMMON_MODULE_DIR / "outputs.tf"
    with open(outputs_path, encoding="utf-8") as f:
        content = f.read()

    locals_dict = parse_locals()
    values = {}

    literal_pattern = r'output\s+"([^"]+)"\s*\{\s*value\s*=\s*"([^"]+)"'
    for match in re.findall(literal_pattern, content):
        output_name, value = match
        values[output_name] = value

    local_pattern = r'output\s+"([^"]+)"\s*\{\s*value\s*=\s*local\.(\w+)'
    for match in re.findall(local_pattern, content):
        output_name, local_name = match
        if local_name in locals_dict:
            values[output_name] = locals_dict[local_name]

    return values


def get_shared_config() -> Dict[str, Any]:
    """Get all configuration values from the shared OpenTofu module.

    Combines locals and outputs into a single dict. Output values take
    precedence over locals if there are naming conflicts.

    Returns:
        Dict with all configuration values from the shared module.
    """
    config: Dict[str, Any] = parse_locals()
    config.update(parse_outputs())
    return config


# Single source of truth for AWS region - derived from OpenTofu shared module.
# Use this constant in unit tests for mock data (fake ARNs, URLs, etc.)
# instead of hardcoding region strings.
TEST_AWS_REGION = parse_locals().get("aws_region", "us-east-2")


def get_resource_prefix() -> str:
    """Get the resource prefix from shared OpenTofu module."""
    return parse_locals().get("resource_prefix", "DeltaHDL")


def get_tfvars_values(tf_dir: Any) -> Dict[str, Any]:
    """Parse opentofu.tfvars file in the given directory.

    Args:
        tf_dir: Path to the OpenTofu directory

    Returns:
        Dict mapping variable names to their values (strings or lists).
    """
    tfvars_file = tf_dir / "opentofu.tfvars"
    if not tfvars_file.exists():
        return {}

    values: Dict[str, Any] = {}
    with open(tfvars_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                match = re.match(r'(\w+)\s*=\s*"([^"]+)"', line)
                if match:
                    values[match.group(1)] = match.group(2)
                    continue
                list_match = re.match(r'(\w+)\s*=\s*\[([^\]]*)\]', line)
                if list_match:
                    key = list_match.group(1)
                    list_content = list_match.group(2)
                    items = re.findall(r'"([^"]+)"', list_content)
                    values[key] = items
    return values

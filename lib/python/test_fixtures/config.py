"""Shared configuration fixture factories for pytest tests."""
import re
from pathlib import Path
from typing import Dict, Optional


def parse_tfvars_file(tfvars_path: Path) -> Dict[str, str]:
    """Parse an opentofu.tfvars file and return key-value pairs.

    Args:
        tfvars_path: Path to the opentofu.tfvars file

    Returns:
        Dictionary of key-value pairs from the file
    """
    config: Dict[str, str] = {}
    with open(tfvars_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                match = re.match(r'(\w+)\s*=\s*"?([^"]+)"?', line)
                if match:
                    key, value = match.groups()
                    config[key] = value.strip('"')
    return config


def parse_locals_file(
    locals_path: Path,
    shared_config: Optional[Dict[str, str]] = None
) -> Dict[str, str]:
    """Parse an OpenTofu locals.tf file and return key-value pairs.

    Handles both quoted string values and module.common.* references.

    Args:
        locals_path: Path to the locals.tf file
        shared_config: Optional shared_config for resolving module.common.* refs

    Returns:
        Dictionary of parsed values
    """
    config: Dict[str, str] = {}
    with open(locals_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if '=' in line and not line.startswith('#') and not line.startswith('locals'):
                match = re.match(r'(\w+)\s*=\s*(.+)', line)
                if match:
                    key, value = match.groups()
                    value = value.strip()
                    if value.startswith('"') and value.endswith('"'):
                        config[key] = value[1:-1]
                    elif shared_config and 'module.common.' in value:
                        ref = value.replace('module.common.', '').strip()
                        config[key] = shared_config.get(ref, '')
    return config

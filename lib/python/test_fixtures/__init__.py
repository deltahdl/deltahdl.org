"""Test fixtures package for shared pytest fixtures.

Re-exports commonly used opentofu_config functions for convenience.
"""
from opentofu_config import (
    get_shared_config,
    get_tfvars_values,
)

__all__ = [
    'get_shared_config',
    'get_tfvars_values',
]

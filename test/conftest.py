"""Path setup for all tests.

This conftest.py sets up lib/python in sys.path so tests can import
modules like repo_utils, opentofu_config, and test_fixtures.

Shared fixtures are loaded via pytest_plugins.
"""
import sys
from pathlib import Path

pytest_plugins = ['test_fixtures.aws']

_REPO_ROOT = Path(__file__).parent.parent
_LIB_DIR = _REPO_ROOT / "lib" / "python"
if str(_LIB_DIR) not in sys.path:
    sys.path.insert(0, str(_LIB_DIR))

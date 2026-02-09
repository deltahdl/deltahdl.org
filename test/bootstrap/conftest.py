"""Pytest fixtures for bootstrap tests."""
import re

import pytest
from repo_utils import REPO_ROOT

pytest_plugins = ['test_fixtures.aws']

BOOTSTRAP_DIR = REPO_ROOT / "src" / "bootstrap"
LOCALS_TF_PATH = BOOTSTRAP_DIR / "locals.tf"


def _extract_role_suffix(local_name: str) -> str:
    """Extract role name suffix from locals.tf file."""
    with open(LOCALS_TF_PATH, encoding='utf-8') as f:
        content = f.read()
    pattern = rf'{local_name}\s*=\s*"\${{local\.resource_prefix}}([^"]+)"'
    match = re.search(pattern, content)
    return match.group(1) if match else ''


def _get_locals_derived_values(shared: dict) -> dict:
    """Compute derived values from shared config and locals.tf."""
    prefix = shared['resource_prefix']
    logs = shared['name_for_central_logs_bucket']
    ct_suffix = _extract_role_suffix('name_for_cloudtrail_iam_role')
    gh_suffix = _extract_role_suffix('name_for_github_actions_role')
    return {
        'name_for_cloudtrail': f"{prefix}-cloudtrail",
        'name_for_cloudtrail_bucket': logs,
        'name_for_cloudtrail_iam_role': f"{prefix}{ct_suffix}",
        'name_for_cloudtrail_log_group': f"/aws/cloudtrail/{prefix}",
        'name_for_github_actions_role': f"{prefix}{gh_suffix}",
    }


@pytest.fixture(scope="module", name='bootstrap_dir')
def bootstrap_dir_fixture():
    """Provide path to bootstrap directory."""
    return BOOTSTRAP_DIR


@pytest.fixture(scope="module")
def config(shared_config, bootstrap_dir):
    """Provide combined configuration from shared module and tfvars."""
    tfvars_path = bootstrap_dir / "opentofu.tfvars"
    config_dict = dict(shared_config)
    config_dict.update(_get_locals_derived_values(shared_config))
    if tfvars_path.exists():
        with open(tfvars_path, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"')
                    config_dict[key] = value
    return config_dict

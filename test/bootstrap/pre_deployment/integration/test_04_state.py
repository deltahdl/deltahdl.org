"""Layer 4: State validation tests for bootstrap pre-deployment.

Verifies OpenTofu state matches AWS reality. Skips in cold state (no prior state).
"""
import subprocess

import pytest

from repo_utils import REPO_ROOT
from opentofu_config import TEST_AWS_REGION
from opentofu_drift import check_resource_exists, get_planned_creates


BOOTSTRAP_DIR = REPO_ROOT / "src" / "bootstrap"


def _has_existing_state() -> bool:
    """Check if bootstrap OpenTofu has existing state."""
    result = subprocess.run(
        ["tofu", "state", "list"],
        cwd=BOOTSTRAP_DIR,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    return result.returncode == 0 and len(result.stdout.strip()) > 0


def _is_opentofu_initialized() -> bool:
    """Check if OpenTofu is initialized."""
    return (BOOTSTRAP_DIR / ".terraform.lock.hcl").exists()


@pytest.mark.skipif(
    not _is_opentofu_initialized(),
    reason="OpenTofu not initialized"
)
@pytest.mark.skipif(
    not _has_existing_state(),
    reason="Cold state - no prior OpenTofu state to validate against"
)
def test_no_orphaned_resources():
    """Verify no resources to be created already exist in AWS.

    This test runs tofu plan to find resources that will be created,
    then checks if any of them already exist in AWS. If they do, it means
    the resource was created outside of OpenTofu and needs to be imported.
    """
    creates = get_planned_creates(BOOTSTRAP_DIR)

    if not creates:
        return  # Nothing to check

    orphaned = []
    for resource in creates:
        if check_resource_exists(resource["type"], resource["name"], TEST_AWS_REGION):
            orphaned.append(resource)

    if orphaned:
        msg = "\nOrphaned resources detected:\n"
        for r in orphaned:
            msg += f"  - {r['type']}: {r['name']}\n"
            msg += f"    Fix: tofu import {r['address']} {r['name']}\n"
        pytest.fail(msg)
    assert True  # Explicit pass

"""Shared test helpers for OpenTofu drift detection tests."""

from pathlib import Path

import pytest

from opentofu_drift import (
    check_resource_exists,
    get_planned_creates,
)


def create_orphaned_resource_tests(
    opentofu_dir: Path,
    region: str = "us-east-2",
):
    """Create test class for detecting orphaned resources using tofu plan.

    Args:
        opentofu_dir: Path to the OpenTofu directory for this stack
        region: AWS region to check in

    Returns:
        Test class that checks for orphaned resources.
    """
    class TestOrphanedResources:
        """Tests to detect resources that exist in AWS but not in OpenTofu state."""

        def test_opentofu_initialized(self):
            """Verify OpenTofu is initialized in the directory."""
            lock_file = opentofu_dir / ".terraform.lock.hcl"
            print(f"\nChecking OpenTofu initialization: {opentofu_dir}")
            assert lock_file.exists(), (
                f"OpenTofu not initialized in {opentofu_dir}. "
                f"Run 'tofu init' first."
            )
            print("  OpenTofu is initialized")

        def test_no_orphaned_resources(self):
            """Verify no resources to be created already exist in AWS.

            This test runs tofu plan to find resources that will be created,
            then checks if any of them already exist in AWS. If they do, it means
            the resource was created outside of OpenTofu and needs to be imported.
            """
            print("\n" + "=" * 60)
            print("Running tofu plan to detect resources to create...")
            print(f"  Directory: {opentofu_dir}")
            print(f"  Region: {region}")

            creates = get_planned_creates(opentofu_dir)

            print(f"\nFound {len(creates)} resources to create:")
            for resource in creates:
                print(f"  - {resource['type']}: {resource['name']} ({resource['address']})")

            if not creates:
                print("\nNo resources to create - nothing to check for orphans")
                print("=" * 60)
                return

            orphaned = []
            for resource in creates:
                resource_type = resource["type"]
                name = resource["name"]
                tf_address = resource["address"]
                print(f"\nChecking {resource_type}: {name}")
                exists = check_resource_exists(resource_type, name, region)
                print(f"  Exists in AWS: {exists}")
                if exists:
                    orphaned.append((resource_type, name, tf_address))

            print("=" * 60)

            if orphaned:
                msg = f"\n\n{'!'*60}\n"
                msg += f"ORPHANED RESOURCES DETECTED ({len(orphaned)})\n"
                msg += f"{'!'*60}\n\n"
                msg += "The following resources exist in AWS but NOT in OpenTofu state.\n"
                msg += "This will cause 'tofu apply' to fail or hang.\n\n"
                msg += "FIX: Run these commands before applying:\n\n"
                for resource_type, name, tf_address in orphaned:
                    msg += f"    tofu import {tf_address} {name}\n"
                msg += f"\n{'!'*60}"
                pytest.fail(msg)

    return TestOrphanedResources

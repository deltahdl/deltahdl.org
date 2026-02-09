"""Layer 1: Contract tests for bootstrap pre-deployment validation.

Verify cross-file compatibility between OpenTofu configuration files. No AWS calls.
"""
import re
from pathlib import Path




def _extract_module_common_refs(content: str) -> set:
    """Extract all module.common.* references from OpenTofu content."""
    pattern = r"module\.common\.([a-zA-Z_][a-zA-Z0-9_]*)"
    return set(re.findall(pattern, content))


def _extract_module_refs(content: str, module_name: str) -> set:
    """Extract module.<name>.* references from OpenTofu content."""
    pattern = rf"module\.{module_name}\.([a-zA-Z_][a-zA-Z0-9_]*)"
    return set(re.findall(pattern, content))


def test_locals_tf_exists(bootstrap_dir: Path):
    """Verify locals.tf file exists."""
    path = bootstrap_dir / "locals.tf"
    assert path.exists(), f"locals.tf not found at {path}"


def test_outputs_tf_exists(bootstrap_dir: Path):
    """Verify outputs.tf file exists."""
    path = bootstrap_dir / "outputs.tf"
    assert path.exists(), f"outputs.tf not found at {path}"


def test_common_module_outputs_tf_exists(common_module_dir: Path):
    """Verify common module outputs.tf file exists."""
    path = common_module_dir / "outputs.tf"
    assert path.exists(), f"common module outputs.tf not found at {path}"


def test_locals_common_refs_exist_in_common_module(
    locals_content: str, common_outputs: set
):
    """Verify all module.common.* references in locals.tf exist in common module."""
    common_refs = _extract_module_common_refs(locals_content)

    missing = common_refs - common_outputs
    assert not missing, (
        f"module.common.* references in locals.tf are missing from common module:\n"
        f"  Missing: {sorted(missing)}\n"
        f"  locals.tf references: {sorted(common_refs)}\n"
        f"  common module provides: {sorted(common_outputs)}"
    )


def test_outputs_github_oidc_refs_exist_in_module(
    outputs_content: str, github_oidc_outputs: set
):
    """Verify all module.github_oidc.* references in outputs.tf exist in module."""
    refs = _extract_module_refs(outputs_content, "github_oidc")

    missing = refs - github_oidc_outputs
    assert not missing, (
        f"module.github_oidc.* references in outputs.tf missing from module:\n"
        f"  Missing: {sorted(missing)}\n"
        f"  outputs.tf references: {sorted(refs)}\n"
        f"  github_oidc module provides: {sorted(github_oidc_outputs)}"
    )


def test_outputs_domain_refs_exist_in_module(
    outputs_content: str, domain_outputs: set
):
    """Verify all module.domain.* references in outputs.tf exist in module."""
    refs = _extract_module_refs(outputs_content, "domain")

    missing = refs - domain_outputs
    assert not missing, (
        f"module.domain.* references in outputs.tf missing from module:\n"
        f"  Missing: {sorted(missing)}\n"
        f"  outputs.tf references: {sorted(refs)}\n"
        f"  domain module provides: {sorted(domain_outputs)}"
    )


def test_outputs_central_logs_refs_exist_in_module(
    outputs_content: str, central_logs_outputs: set
):
    """Verify all module.central_logs.* references in outputs.tf exist in module."""
    refs = _extract_module_refs(outputs_content, "central_logs")

    missing = refs - central_logs_outputs
    assert not missing, (
        f"module.central_logs.* references in outputs.tf missing from module:\n"
        f"  Missing: {sorted(missing)}\n"
        f"  outputs.tf references: {sorted(refs)}\n"
        f"  central_logs module provides: {sorted(central_logs_outputs)}"
    )


def test_outputs_cloudtrail_refs_exist_in_module(
    outputs_content: str, cloudtrail_outputs: set
):
    """Verify all module.cloudtrail.* references in outputs.tf exist in module."""
    refs = _extract_module_refs(outputs_content, "cloudtrail")

    missing = refs - cloudtrail_outputs
    assert not missing, (
        f"module.cloudtrail.* references in outputs.tf missing from module:\n"
        f"  Missing: {sorted(missing)}\n"
        f"  outputs.tf references: {sorted(refs)}\n"
        f"  cloudtrail module provides: {sorted(cloudtrail_outputs)}"
    )


def test_variables_tf_exists(bootstrap_dir: Path):
    """Verify variables.tf file exists."""
    path = bootstrap_dir / "variables.tf"
    assert path.exists(), f"variables.tf not found at {path}"


def test_opentofu_tfvars_exists(bootstrap_dir: Path):
    """Verify opentofu.tfvars file exists."""
    path = bootstrap_dir / "opentofu.tfvars"
    assert path.exists(), f"opentofu.tfvars not found at {path}"

"""Unit tests for www redirect locals.tf configuration."""


def test_locals_file_exists(src_dir):
    """Verify locals.tf file exists."""
    assert (src_dir / "locals.tf").exists()


def test_locals_block_exists(src_dir):
    """Verify locals block is defined."""
    content = (src_dir / "locals.tf").read_text()
    assert "locals {" in content


def test_locals_apex_fqdn_defined(src_dir):
    """Verify apex_fqdn is defined."""
    content = (src_dir / "locals.tf").read_text()
    assert "apex_fqdn" in content


def test_locals_apex_fqdn_uses_module_common(src_dir):
    """Verify apex_fqdn references module.common.domain_name."""
    content = (src_dir / "locals.tf").read_text()
    assert "apex_fqdn             = module.common.domain_name" in content


def test_locals_www_fqdn_defined(src_dir):
    """Verify www_fqdn is defined."""
    content = (src_dir / "locals.tf").read_text()
    assert "www_fqdn" in content


def test_locals_www_fqdn_has_www_prefix(src_dir):
    """Verify www_fqdn has www. prefix."""
    content = (src_dir / "locals.tf").read_text()
    assert 'www_fqdn              = "www.${module.common.domain_name}"' in content


def test_locals_redirect_target_defined(src_dir):
    """Verify redirect_target is defined."""
    content = (src_dir / "locals.tf").read_text()
    assert "redirect_target" in content


def test_locals_redirect_target_is_github(src_dir):
    """Verify redirect_target points to GitHub repository."""
    content = (src_dir / "locals.tf").read_text()
    assert '"https://github.com/deltahdl/deltahdl"' in content


def test_locals_resource_prefix_defined(src_dir):
    """Verify resource_prefix is defined."""
    content = (src_dir / "locals.tf").read_text()
    assert "resource_prefix" in content


def test_locals_resource_prefix_includes_redirect(src_dir):
    """Verify resource_prefix includes Redirect suffix."""
    content = (src_dir / "locals.tf").read_text()
    assert '"${module.common.resource_prefix}Redirect"' in content


def test_locals_aws_region_references_module_common(src_dir):
    """Verify aws_region uses module.common."""
    content = (src_dir / "locals.tf").read_text()
    assert "aws_region            = module.common.aws_region" in content


def test_locals_domain_name_references_module_common(src_dir):
    """Verify domain_name uses module.common."""
    content = (src_dir / "locals.tf").read_text()
    assert "domain_name           = module.common.domain_name" in content


def test_locals_name_for_central_logs_defined(src_dir):
    """Verify name_for_central_logs is defined."""
    content = (src_dir / "locals.tf").read_text()
    assert "name_for_central_logs" in content


def test_locals_name_for_central_logs_uses_module_common(src_dir):
    """Verify name_for_central_logs uses module.common."""
    content = (src_dir / "locals.tf").read_text()
    assert "module.common.name_for_central_logs_bucket" in content

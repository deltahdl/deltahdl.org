"""Unit tests for www redirect providers.tf configuration."""


def test_providers_file_exists(src_dir):
    """Verify providers.tf file exists."""
    assert (src_dir / "providers.tf").exists()


def test_providers_aws_provider_defined(src_dir):
    """Verify AWS provider is defined."""
    content = (src_dir / "providers.tf").read_text()
    assert 'provider "aws"' in content


def test_providers_region_uses_local(src_dir):
    """Verify AWS provider region uses local.aws_region."""
    content = (src_dir / "providers.tf").read_text()
    assert "region = local.aws_region" in content


def test_providers_has_default_tags(src_dir):
    """Verify AWS provider has default_tags block."""
    content = (src_dir / "providers.tf").read_text()
    assert "default_tags {" in content


def test_providers_default_tags_managed_by_opentofu(src_dir):
    """Verify default tags include ManagedBy = OpenTofu."""
    content = (src_dir / "providers.tf").read_text()
    assert 'ManagedBy = "OpenTofu"' in content


def test_providers_default_tags_project_deltahdl(src_dir):
    """Verify default tags include Project = DeltaHDL."""
    content = (src_dir / "providers.tf").read_text()
    assert 'Project   = "DeltaHDL"' in content


def test_providers_default_tags_stack_redirect(src_dir):
    """Verify default tags include Stack = redirect."""
    content = (src_dir / "providers.tf").read_text()
    assert 'Stack     = "redirect"' in content


def test_providers_us_east_1_alias_defined(src_dir):
    """Verify us-east-1 provider alias is defined."""
    content = (src_dir / "providers.tf").read_text()
    assert 'alias  = "us-east-1"' in content


def test_providers_us_east_1_region_hardcoded(src_dir):
    """Verify us-east-1 provider region is hardcoded."""
    content = (src_dir / "providers.tf").read_text()
    assert 'region = "us-east-1"' in content


def test_providers_required_version(src_dir):
    """Verify required OpenTofu version is specified."""
    content = (src_dir / "providers.tf").read_text()
    assert 'required_version = ">= 1.14.0"' in content


def test_providers_required_providers_aws(src_dir):
    """Verify AWS provider is in required_providers."""
    content = (src_dir / "providers.tf").read_text()
    assert "aws = {" in content


def test_providers_aws_provider_source(src_dir):
    """Verify AWS provider source is hashicorp/aws."""
    content = (src_dir / "providers.tf").read_text()
    assert 'source  = "hashicorp/aws"' in content


def test_providers_aws_provider_version(src_dir):
    """Verify AWS provider version constraint."""
    content = (src_dir / "providers.tf").read_text()
    assert 'version = "~> 5.0"' in content

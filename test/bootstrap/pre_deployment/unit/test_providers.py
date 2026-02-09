"""Pre-deployment unit tests for bootstrap providers.tf configuration."""


def test_opentofu_version_constraint(bootstrap_dir):
    """Test that OpenTofu version constraint is >= 1.11.0."""
    content = (bootstrap_dir / "providers.tf").read_text()
    assert 'required_version = ">= 1.11.0"' in content


def test_aws_provider_source(bootstrap_dir):
    """Test that AWS provider uses hashicorp/aws source."""
    content = (bootstrap_dir / "providers.tf").read_text()
    assert 'source  = "hashicorp/aws"' in content


def test_aws_provider_version_constraint(bootstrap_dir):
    """Test that AWS provider version constraint is ~> 5.0."""
    content = (bootstrap_dir / "providers.tf").read_text()
    assert 'version = "~> 5.0"' in content


def test_aws_provider_uses_local_region(bootstrap_dir):
    """Test that AWS provider uses local.aws_region for region."""
    content = (bootstrap_dir / "providers.tf").read_text()
    assert "region = local.aws_region" in content

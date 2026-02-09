"""Pre-deployment unit tests for bootstrap shared.tf configuration."""


def test_shared_module_exists(bootstrap_dir):
    """Test that shared.tf file exists."""
    assert (bootstrap_dir / "shared.tf").exists()


def test_shared_module_uses_common_source(bootstrap_dir):
    """Test that shared module references the correct source path."""
    content = (bootstrap_dir / "shared.tf").read_text()
    assert 'source = "../../lib/opentofu/common"' in content


def test_shared_module_name_is_common(bootstrap_dir):
    """Test that shared module is named 'common'."""
    content = (bootstrap_dir / "shared.tf").read_text()
    assert 'module "common"' in content

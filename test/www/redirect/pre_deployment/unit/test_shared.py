"""Unit tests for www redirect shared.tf configuration."""


def test_shared_file_exists(src_dir):
    """Verify shared.tf file exists."""
    assert (src_dir / "shared.tf").exists()


def test_shared_common_module_defined(src_dir):
    """Verify common module is defined."""
    content = (src_dir / "shared.tf").read_text()
    assert 'module "common"' in content


def test_shared_module_source_path(src_dir):
    """Verify common module source path uses opentofu/common."""
    content = (src_dir / "shared.tf").read_text()
    assert 'source = "../../../lib/opentofu/common"' in content

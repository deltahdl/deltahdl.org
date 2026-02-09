"""Unit tests for www redirect backend.tf configuration."""


def test_backend_file_exists(src_dir):
    """Verify backend.tf file exists."""
    assert (src_dir / "backend.tf").exists()


def test_backend_type_is_s3(src_dir):
    """Verify backend type is S3."""
    content = (src_dir / "backend.tf").read_text()
    assert 'backend "s3"' in content


def test_backend_bucket_name(src_dir):
    """Verify backend uses the correct S3 bucket."""
    content = (src_dir / "backend.tf").read_text()
    assert "deltahdl-opentofu-state-us-east-2" in content


def test_backend_has_key_setting(src_dir):
    """Verify backend has a key setting."""
    content = (src_dir / "backend.tf").read_text()
    assert "key" in content


def test_backend_key_references_www_redirect(src_dir):
    """Verify backend state key references www-redirect."""
    content = (src_dir / "backend.tf").read_text()
    assert "www-redirect" in content


def test_backend_region(src_dir):
    """Verify backend region is us-east-2."""
    content = (src_dir / "backend.tf").read_text()
    assert 'region       = "us-east-2"' in content


def test_backend_has_encrypt_setting(src_dir):
    """Verify backend has encrypt setting."""
    content = (src_dir / "backend.tf").read_text()
    assert "encrypt" in content


def test_backend_encrypt_is_true(src_dir):
    """Verify backend encryption is enabled."""
    content = (src_dir / "backend.tf").read_text()
    assert "encrypt" in content and "= true" in content


def test_backend_uses_lockfile(src_dir):
    """Verify backend uses lockfile for state locking."""
    content = (src_dir / "backend.tf").read_text()
    assert "use_lockfile = true" in content


def test_backend_terraform_block_exists(src_dir):
    """Verify terraform block exists."""
    content = (src_dir / "backend.tf").read_text()
    assert "terraform {" in content

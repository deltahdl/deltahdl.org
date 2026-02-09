"""Pre-deployment unit tests for bootstrap backend.tf configuration."""


def test_backend_uses_s3_backend(bootstrap_dir):
    """Test that backend.tf uses S3 backend."""
    content = (bootstrap_dir / "backend.tf").read_text()
    assert 'backend "s3"' in content


def test_backend_bucket_name(bootstrap_dir):
    """Test that backend uses the correct S3 bucket."""
    content = (bootstrap_dir / "backend.tf").read_text()
    assert 'bucket       = "deltahdl-opentofu-state-us-east-2"' in content


def test_backend_key_path(bootstrap_dir):
    """Test that backend uses the correct state file key path."""
    content = (bootstrap_dir / "backend.tf").read_text()
    assert 'key          = "bootstrap/terraform.tfstate"' in content


def test_backend_region(bootstrap_dir):
    """Test that backend uses the correct AWS region."""
    content = (bootstrap_dir / "backend.tf").read_text()
    assert 'region       = "us-east-2"' in content


def test_backend_encryption_enabled(bootstrap_dir):
    """Test that backend has encryption enabled."""
    content = (bootstrap_dir / "backend.tf").read_text()
    assert "encrypt      = true" in content


def test_backend_uses_lockfile(bootstrap_dir):
    """Test that backend uses lockfile for state locking."""
    content = (bootstrap_dir / "backend.tf").read_text()
    assert "use_lockfile = true" in content

"""Pre-deployment unit tests for bootstrap locals.tf configuration."""


def test_opentofu_tfvars_file_exists(bootstrap_dir):
    """Test that opentofu.tfvars file exists."""
    assert (bootstrap_dir / "opentofu.tfvars").exists()


def test_config_has_name_for_cloudtrail(config):
    """Test that config has name_for_cloudtrail."""
    assert 'name_for_cloudtrail' in config


def test_config_has_name_for_cloudtrail_iam_role(config):
    """Test that config has name_for_cloudtrail_iam_role."""
    assert 'name_for_cloudtrail_iam_role' in config


def test_config_has_name_for_cloudtrail_log_group(config):
    """Test that config has name_for_cloudtrail_log_group."""
    assert 'name_for_cloudtrail_log_group' in config


def test_config_has_hosted_zone_id(config):
    """Test that config has hosted_zone_id."""
    assert 'hosted_zone_id' in config


def test_config_has_name_for_github_actions_role(config):
    """Test that config has name_for_github_actions_role."""
    assert 'name_for_github_actions_role' in config


def test_hosted_zone_id_starts_with_z(config):
    """Test that hosted_zone_id starts with Z."""
    assert config['hosted_zone_id'].startswith('Z')


def test_locals_has_name_for_opentofu_state_bucket(bootstrap_dir):
    """Test that locals.tf references name_for_opentofu_state_bucket."""
    content = (bootstrap_dir / "locals.tf").read_text()
    assert 'name_for_opentofu_state_bucket' in content


def test_locals_has_resource_prefix(bootstrap_dir):
    """Test that locals.tf defines resource_prefix from common module."""
    content = (bootstrap_dir / "locals.tf").read_text()
    assert 'resource_prefix' in content


def test_locals_github_actions_role_uses_prefix(bootstrap_dir):
    """Test that GitHub Actions role name uses resource_prefix."""
    content = (bootstrap_dir / "locals.tf").read_text()
    assert '${local.resource_prefix}GitHubActionsRole' in content


def test_locals_cloudtrail_iam_role_uses_prefix(bootstrap_dir):
    """Test that CloudTrail IAM role name uses resource_prefix."""
    content = (bootstrap_dir / "locals.tf").read_text()
    assert '${local.resource_prefix}CloudTrailLogsRole' in content

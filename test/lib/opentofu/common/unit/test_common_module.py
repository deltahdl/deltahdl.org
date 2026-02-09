"""Tests for common OpenTofu module."""


def test_locals_file_exists(module_path):
    """Test that locals.tf file exists."""
    assert (module_path / "locals.tf").exists()


def test_outputs_file_exists(module_path):
    """Test that outputs.tf file exists."""
    assert (module_path / "outputs.tf").exists()


def test_aws_region_local_exists(locals_tf_content):
    """Test that aws_region local exists."""
    assert "aws_region" in locals_tf_content


def test_aws_account_id_local_exists(locals_tf_content):
    """Test that aws_account_id local exists."""
    assert "aws_account_id" in locals_tf_content


def test_resource_prefix_local_exists(locals_tf_content):
    """Test that resource_prefix local exists."""
    assert "resource_prefix" in locals_tf_content


def test_admin_iam_user_output_exists(outputs_tf_content):
    """Test that admin_iam_user output exists."""
    assert 'output "admin_iam_user"' in outputs_tf_content


def test_aws_account_id_output_exists(outputs_tf_content):
    """Test that aws_account_id output exists."""
    assert 'output "aws_account_id"' in outputs_tf_content


def test_aws_region_output_exists(outputs_tf_content):
    """Test that aws_region output exists."""
    assert 'output "aws_region"' in outputs_tf_content


def test_domain_name_output_exists(outputs_tf_content):
    """Test that domain_name output exists."""
    assert 'output "domain_name"' in outputs_tf_content


def test_github_org_output_exists(outputs_tf_content):
    """Test that github_org output exists."""
    assert 'output "github_org"' in outputs_tf_content


def test_name_for_central_logs_bucket_output_exists(outputs_tf_content):
    """Test that name_for_central_logs_bucket output exists."""
    assert 'output "name_for_central_logs_bucket"' in outputs_tf_content


def test_name_for_github_repo_output_exists(outputs_tf_content):
    """Test that name_for_github_repo output exists."""
    assert 'output "name_for_github_repo"' in outputs_tf_content


def test_name_for_opentofu_state_bucket_output_exists(outputs_tf_content):
    """Test that name_for_opentofu_state_bucket output exists."""
    assert 'output "name_for_opentofu_state_bucket"' in outputs_tf_content


def test_resource_prefix_output_exists(outputs_tf_content):
    """Test that resource_prefix output exists."""
    assert 'output "resource_prefix"' in outputs_tf_content

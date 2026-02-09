"""Tests for s3_bucket OpenTofu module."""


def test_module_files_exist(module_path):
    """Test that required module files exist."""
    main = (module_path / "main.tf").exists()
    variables = (module_path / "variables.tf").exists()
    outputs = (module_path / "outputs.tf").exists()
    assert main and variables and outputs


def test_s3_bucket_resource_exists(main_tf_content):
    """Test that S3 bucket resource exists."""
    assert 'resource "aws_s3_bucket"' in main_tf_content


def test_s3_bucket_versioning_resource_exists(main_tf_content):
    """Test that S3 bucket versioning resource exists."""
    assert 'resource "aws_s3_bucket_versioning"' in main_tf_content


def test_s3_bucket_versioning_configurable(main_tf_content):
    """Test that S3 bucket versioning status is configurable."""
    has_var = 'var.versioning_enabled' in main_tf_content
    has_enabled = '"Enabled"' in main_tf_content
    has_disabled = '"Disabled"' in main_tf_content
    assert has_var and has_enabled and has_disabled


def test_s3_bucket_public_access_block_exists(main_tf_content):
    """Test that S3 bucket public access block exists."""
    assert 'resource "aws_s3_bucket_public_access_block"' in main_tf_content


def test_s3_bucket_public_access_block_all_enabled(main_tf_content):
    """Test that all public access block settings are enabled."""
    acls = 'block_public_acls       = true' in main_tf_content
    policy = 'block_public_policy     = true' in main_tf_content
    ignore = 'ignore_public_acls      = true' in main_tf_content
    restrict = 'restrict_public_buckets = true' in main_tf_content
    assert acls and policy and ignore and restrict


def test_s3_bucket_encryption_exists(main_tf_content):
    """Test that S3 bucket encryption configuration exists."""
    resource = 'resource "aws_s3_bucket_server_side_encryption_configuration"'
    assert resource in main_tf_content


def test_s3_bucket_encryption_uses_aes256(main_tf_content):
    """Test that S3 bucket encryption uses AES256."""
    assert 'sse_algorithm = "AES256"' in main_tf_content


def test_s3_bucket_logging_resource_exists(main_tf_content):
    """Test that S3 bucket logging resource exists."""
    assert 'resource "aws_s3_bucket_logging"' in main_tf_content


def test_s3_bucket_logging_is_optional(main_tf_content):
    """Test that S3 bucket logging is optional via count."""
    assert 'count = var.central_logs_bucket != null' in main_tf_content


def test_versioning_enabled_variable_exists(variables_tf_content):
    """Test that versioning_enabled variable exists."""
    assert 'variable "versioning_enabled"' in variables_tf_content


def test_bucket_name_variable_exists(variables_tf_content):
    """Test that bucket_name variable exists."""
    assert 'variable "bucket_name"' in variables_tf_content


def test_central_logs_bucket_variable_exists(variables_tf_content):
    """Test that central_logs_bucket variable exists."""
    assert 'variable "central_logs_bucket"' in variables_tf_content


def test_bucket_id_output_exists(outputs_tf_content):
    """Test that bucket_id output exists."""
    assert 'output "bucket_id"' in outputs_tf_content


def test_bucket_arn_output_exists(outputs_tf_content):
    """Test that bucket_arn output exists."""
    assert 'output "bucket_arn"' in outputs_tf_content

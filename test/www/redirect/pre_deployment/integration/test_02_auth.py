"""Layer 2: Authentication tests for www redirect pre-deployment validation.

Verify AWS credentials are valid before testing authorization, existence, or capability.
"""
import pytest


def test_aws_credentials_return_account(sts_client):
    """Verify AWS credentials return an account ID."""
    response = sts_client.get_caller_identity()
    assert "Account" in response


def test_aws_credentials_return_arn(sts_client):
    """Verify AWS credentials return a caller ARN."""
    response = sts_client.get_caller_identity()
    assert "Arn" in response


def test_aws_account_id_present(sts_client):
    """Verify AWS account ID is present in caller identity."""
    response = sts_client.get_caller_identity()
    account_id = response.get("Account", "")
    assert len(account_id) == 12, f"Expected 12-digit account ID, got: {account_id}"


def test_backend_uses_oidc_via_s3(src_dir):
    """Verify backend uses S3 backend compatible with OIDC authentication."""
    content = (src_dir / "backend.tf").read_text()
    assert 'backend "s3"' in content, (
        "Backend must use S3 for OIDC-compatible state storage"
    )

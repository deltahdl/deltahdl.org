"""Layer 2: Authentication tests for bootstrap pre-deployment validation.

Verify AWS credentials are valid before testing authorization or state.
"""
import boto3


class TestAWSAuthentication:
    """Layer 2: Authentication tests - Verify AWS credentials."""

    def test_aws_credentials_valid(self, sts_client):
        """Verify AWS credentials are valid."""
        response = sts_client.get_caller_identity()
        assert response["Account"] is not None

    def test_aws_credentials_not_expired(self, sts_client):
        """Verify AWS credentials are not expired."""
        response = sts_client.get_caller_identity()
        assert "Arn" in response

"""Layer 3: Authorization tests for bootstrap pre-deployment validation.

Verify permission to inspect the state bucket (not existence, not capability).
"""
import pytest
from botocore.exceptions import ClientError


class TestS3Authorization:
    """Layer 3: Verify S3 authorization."""

    def test_can_call_s3_head_bucket(self, s3_client, state_bucket_name):
        """Verify permission to call s3:HeadBucket on state bucket."""
        try:
            s3_client.head_bucket(Bucket=state_bucket_name)
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code in ("403", "AccessDenied"):
                pytest.fail(
                    f"No permission to call s3:HeadBucket on '{state_bucket_name}'"
                )
            # 404/NoSuchBucket means bucket doesn't exist but we have permission
            if error_code not in ("404", "NoSuchBucket"):
                raise
        assert True  # Explicit pass

    def test_bucket_name_is_configured(self, state_bucket_name):
        """Verify state bucket name is configured."""
        assert state_bucket_name, "State bucket name is not configured"


def test_can_call_s3_get_object(s3_client, state_bucket_name):
    """Verify permission to call s3:GetObject on state bucket."""
    try:
        s3_client.get_object(Bucket=state_bucket_name, Key="bootstrap/terraform.tfstate")
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code in ("403", "AccessDenied"):
            pytest.fail(f"No permission to call s3:GetObject on '{state_bucket_name}'")
        # NoSuchKey/NoSuchBucket means object/bucket doesn't exist but we have permission
        if error_code not in ("NoSuchKey", "NoSuchBucket", "404"):
            raise
    assert True  # Explicit pass

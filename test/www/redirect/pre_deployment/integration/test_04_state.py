"""Layer 4: State tests for www redirect pre-deployment validation.

Verify that the OpenTofu state bucket exists and is accessible. If resources
OpenTofu plans to create already exist in AWS, it indicates the resource was
created outside of OpenTofu or the state was lost.
"""
from test.www.redirect.pre_deployment.integration.conftest import (
    head_bucket_status_code,
)

import pytest
from botocore.exceptions import ClientError


def test_state_bucket_exists(s3_client, state_bucket_name):
    """Verify OpenTofu state bucket exists."""
    assert head_bucket_status_code(s3_client, state_bucket_name) == 200


def test_state_bucket_is_accessible(s3_client, state_bucket_name):
    """Verify OpenTofu state bucket is accessible for listing."""
    try:
        response = s3_client.list_objects_v2(
            Bucket=state_bucket_name, MaxKeys=1
        )
        assert "KeyCount" in response or "Contents" in response
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "AccessDenied":
            pytest.fail(
                f"No permission to list objects in "
                f"'{state_bucket_name}'"
            )
        raise

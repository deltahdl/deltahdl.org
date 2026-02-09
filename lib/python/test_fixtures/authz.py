"""Shared authorization test helpers.

Provides reusable helpers for authorization tests that verify
AWS API permissions without checking resource existence or capability.
"""
import pytest
from botocore.exceptions import ClientError


def check_s3_head_bucket_authorized(
    s3_client_instance, bucket_name
):
    """Check that the caller has permission to call s3:HeadBucket.

    Returns True if permission exists. Calls pytest.fail if a
    403/AccessDenied error occurs. Re-raises other unexpected errors.
    A 404/NoSuchBucket error means we have permission but the bucket
    doesn't exist, which still counts as authorized.
    """
    try:
        s3_client_instance.head_bucket(Bucket=bucket_name)
    except ClientError as exc:
        error_code = exc.response["Error"]["Code"]
        if error_code in ("403", "AccessDenied"):
            pytest.fail(
                f"No permission to call s3:HeadBucket "
                f"on '{bucket_name}'"
            )
        # 404/NoSuchBucket means bucket doesn't exist but we have permission
        if error_code not in ("404", "NoSuchBucket"):
            raise
    return True

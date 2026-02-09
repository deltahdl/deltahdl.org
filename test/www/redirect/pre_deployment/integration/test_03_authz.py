"""Layer 3: Authorization tests for www redirect pre-deployment validation.

Verify permission to inspect prerequisite resources (not existence, not capability).
"""
import pytest
from botocore.exceptions import ClientError


def test_can_call_s3_head_bucket(s3_client, state_bucket_name):
    """Verify permission to call s3:HeadBucket on state bucket."""
    try:
        s3_client.head_bucket(Bucket=state_bucket_name)
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code in ("403", "AccessDenied"):
            pytest.fail(f"No permission to call s3:HeadBucket on '{state_bucket_name}'")
        if error_code != "404":
            raise
    assert True  # Explicit pass


def test_can_call_route53_get_hosted_zone(route53_client, hosted_zone_id):
    """Verify permission to call route53:GetHostedZone."""
    try:
        route53_client.get_hosted_zone(Id=hosted_zone_id)
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "AccessDenied":
            pytest.fail(f"No permission to call route53:GetHostedZone on '{hosted_zone_id}'")
        if error_code != "NoSuchHostedZone":
            raise
    assert True  # Explicit pass


def test_can_call_route53_list_resource_record_sets(route53_client, hosted_zone_id):
    """Verify permission to call route53:ListResourceRecordSets."""
    try:
        route53_client.list_resource_record_sets(HostedZoneId=hosted_zone_id, MaxItems="1")
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "AccessDenied":
            pytest.fail(
                f"No permission to call route53:ListResourceRecordSets on '{hosted_zone_id}'"
            )
        if error_code != "NoSuchHostedZone":
            raise
    assert True  # Explicit pass

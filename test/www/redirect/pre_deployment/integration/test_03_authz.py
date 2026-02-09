"""Layer 3: Authorization tests for www redirect pre-deployment validation.

Verify permission to inspect prerequisite resources (not existence, not
capability).
"""
import pytest
from botocore.exceptions import ClientError

from test_fixtures.authz import check_s3_head_bucket_authorized


def test_can_call_s3_head_bucket(s3_client, state_bucket_name):
    """Verify permission to call s3:HeadBucket on state bucket."""
    assert check_s3_head_bucket_authorized(
        s3_client, state_bucket_name
    )


def test_can_call_route53_get_hosted_zone(route53_client, hosted_zone_id):
    """Verify permission to call route53:GetHostedZone."""
    try:
        route53_client.get_hosted_zone(Id=hosted_zone_id)
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "AccessDenied":
            pytest.fail(
                f"No permission to call route53:GetHostedZone "
                f"on '{hosted_zone_id}'"
            )
        if error_code != "NoSuchHostedZone":
            raise
    assert True  # Explicit pass


def test_can_call_route53_list_resource_record_sets(
    route53_client, hosted_zone_id
):
    """Verify permission to call route53:ListResourceRecordSets."""
    try:
        route53_client.list_resource_record_sets(
            HostedZoneId=hosted_zone_id, MaxItems="1"
        )
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "AccessDenied":
            pytest.fail(
                f"No permission to call "
                f"route53:ListResourceRecordSets "
                f"on '{hosted_zone_id}'"
            )
        if error_code != "NoSuchHostedZone":
            raise
    assert True  # Explicit pass

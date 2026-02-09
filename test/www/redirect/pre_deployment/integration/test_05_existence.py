"""Layer 5: Existence tests for www redirect pre-deployment validation.

Verify prerequisite resources created by the bootstrap stack exist.
Assumes state tests passed.
"""
import pytest
from botocore.exceptions import ClientError


def test_state_bucket_exists(s3_client, state_bucket_name):
    """Verify OpenTofu state bucket exists."""
    try:
        response = s3_client.head_bucket(Bucket=state_bucket_name)
        assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "404":
            pytest.fail(f"State bucket '{state_bucket_name}' does not exist")
        raise


def test_hosted_zone_exists(route53_client, hosted_zone_id):
    """Verify Route53 hosted zone exists."""
    try:
        response = route53_client.get_hosted_zone(Id=hosted_zone_id)
        zone_id_from_response = response["HostedZone"]["Id"]
        assert zone_id_from_response.endswith(hosted_zone_id), (
            f"Zone ID mismatch: expected {hosted_zone_id}, got {zone_id_from_response}"
        )
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "NoSuchHostedZone":
            pytest.fail(f"Hosted zone '{hosted_zone_id}' does not exist")
        raise

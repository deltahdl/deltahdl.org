"""Layer 5: Existence tests for www redirect pre-deployment validation.

Verify prerequisite resources created by the bootstrap stack exist.
Assumes state tests passed.
"""
from test.www.redirect.pre_deployment.integration.conftest import (
    head_bucket_status_code,
)

import pytest
from botocore.exceptions import ClientError


def test_state_bucket_exists(s3_client, state_bucket_name):
    """Verify OpenTofu state bucket exists."""
    assert head_bucket_status_code(s3_client, state_bucket_name) == 200


def test_hosted_zone_exists(route53_client, hosted_zone_id):
    """Verify Route53 hosted zone exists."""
    try:
        response = route53_client.get_hosted_zone(Id=hosted_zone_id)
        zone_id_from_response = response["HostedZone"]["Id"]
        assert zone_id_from_response.endswith(hosted_zone_id), (
            f"Zone ID mismatch: expected {hosted_zone_id}, "
            f"got {zone_id_from_response}"
        )
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "NoSuchHostedZone":
            pytest.fail(
                f"Hosted zone '{hosted_zone_id}' does not exist"
            )
        raise

"""Layer 6: Configuration tests for www redirect pre-deployment validation.

Verify prerequisite resources are configured correctly. Assumes existence tests passed.
"""
import os


def _is_github_actions():
    """Check if running in GitHub Actions."""
    return os.environ.get("GITHUB_ACTIONS") == "true"


def test_state_bucket_has_encryption(s3_client, state_bucket_name):
    """Verify state bucket has encryption enabled."""
    response = s3_client.get_bucket_encryption(Bucket=state_bucket_name)
    rules = response["ServerSideEncryptionConfiguration"]["Rules"]
    assert len(rules) > 0, f"State bucket '{state_bucket_name}' has no encryption rules"


def test_state_bucket_has_versioning(s3_client, state_bucket_name):
    """Verify state bucket has versioning enabled."""
    response = s3_client.get_bucket_versioning(Bucket=state_bucket_name)
    status = response.get("Status", "Disabled")
    assert status == "Enabled", (
        f"State bucket '{state_bucket_name}' versioning is '{status}', expected 'Enabled'"
    )


def test_hosted_zone_has_ns_records(route53_client, hosted_zone_id):
    """Verify hosted zone has NS records configured."""
    response = route53_client.list_resource_record_sets(
        HostedZoneId=hosted_zone_id,
    )
    records = response.get("ResourceRecordSets", [])
    ns_records = [r for r in records if r["Type"] == "NS"]
    assert len(ns_records) > 0, (
        f"Hosted zone '{hosted_zone_id}' has no NS records"
    )

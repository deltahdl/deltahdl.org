"""Layer 7: Capability tests for www redirect pre-deployment validation.

Verify we can perform required operations on prerequisite resources.
Assumes configuration tests passed.
"""
import uuid

import pytest
from botocore.exceptions import ClientError


@pytest.fixture(name="test_object_key")
def object_key_fixture():
    """Generate a unique test object key."""
    return f".pre-deployment-test/{uuid.uuid4()}.txt"


@pytest.fixture(name="zone_name")
def zone_name_fixture(route53_client, hosted_zone_id):
    """Get the zone name for constructing test record names."""
    response = route53_client.get_hosted_zone(Id=hosted_zone_id)
    return response["HostedZone"]["Name"]


@pytest.fixture(name="test_record_name")
def record_name_fixture(zone_name):
    """Generate a unique test record name."""
    unique_id = str(uuid.uuid4())[:8]
    return f"_pre-deployment-test-{unique_id}.{zone_name}"


def test_can_list_objects_in_state_bucket(s3_client, state_bucket_name):
    """Verify we can call s3:ListObjectsV2."""
    try:
        response = s3_client.list_objects_v2(Bucket=state_bucket_name, MaxKeys=1)
        assert "Contents" in response or "KeyCount" in response
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "AccessDenied":
            pytest.fail(f"No permission to call s3:ListObjectsV2 on '{state_bucket_name}'")
        raise


def test_can_get_object_from_state_bucket(s3_client, state_bucket_name):
    """Verify we can call s3:GetObject on a state file."""
    try:
        response = s3_client.list_objects_v2(Bucket=state_bucket_name, MaxKeys=1)
        if not response.get("Contents"):
            pytest.skip("No objects in bucket to test GetObject")
        key = response["Contents"][0]["Key"]
        obj_response = s3_client.get_object(Bucket=state_bucket_name, Key=key)
        assert obj_response["ResponseMetadata"]["HTTPStatusCode"] == 200
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "AccessDenied":
            pytest.fail(f"No permission to call s3:GetObject on '{state_bucket_name}'")
        raise


def test_can_put_object_to_state_bucket(s3_client, state_bucket_name, test_object_key):
    """Verify we can call s3:PutObject."""
    try:
        response = s3_client.put_object(
            Bucket=state_bucket_name,
            Key=test_object_key,
            Body=b"pre-deployment capability test"
        )
        assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "AccessDenied":
            pytest.fail(f"No permission to call s3:PutObject on '{state_bucket_name}'")
        raise
    finally:
        s3_client.delete_object(Bucket=state_bucket_name, Key=test_object_key)


def test_can_delete_object_from_state_bucket(s3_client, state_bucket_name, test_object_key):
    """Verify we can call s3:DeleteObject."""
    try:
        s3_client.put_object(
            Bucket=state_bucket_name,
            Key=test_object_key,
            Body=b"pre-deployment capability test"
        )
        response = s3_client.delete_object(Bucket=state_bucket_name, Key=test_object_key)
        assert response["ResponseMetadata"]["HTTPStatusCode"] == 204
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "AccessDenied":
            pytest.fail(f"No permission to call s3:DeleteObject on '{state_bucket_name}'")
        raise
    finally:
        s3_client.delete_object(Bucket=state_bucket_name, Key=test_object_key)


def test_can_create_route53_record(route53_client, hosted_zone_id, test_record_name):
    """Verify we can call route53:ChangeResourceRecordSets to create."""
    try:
        response = route53_client.change_resource_record_sets(
            HostedZoneId=hosted_zone_id,
            ChangeBatch={
                "Comment": "Pre-deployment capability test - create",
                "Changes": [{
                    "Action": "CREATE",
                    "ResourceRecordSet": {
                        "Name": test_record_name,
                        "Type": "TXT",
                        "TTL": 60,
                        "ResourceRecords": [{"Value": '"pre-deployment-test-v1"'}]
                    }
                }]
            }
        )
        assert response["ChangeInfo"]["Status"] in ("PENDING", "INSYNC")
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "AccessDenied":
            pytest.fail(f"No permission to create records in zone '{hosted_zone_id}'")
        raise
    finally:
        route53_client.change_resource_record_sets(
            HostedZoneId=hosted_zone_id,
            ChangeBatch={
                "Changes": [{
                    "Action": "DELETE",
                    "ResourceRecordSet": {
                        "Name": test_record_name,
                        "Type": "TXT",
                        "TTL": 60,
                        "ResourceRecords": [{"Value": '"pre-deployment-test-v1"'}]
                    }
                }]
            }
        )


def test_can_delete_route53_record(route53_client, hosted_zone_id, test_record_name):
    """Verify we can call route53:ChangeResourceRecordSets to delete."""
    try:
        route53_client.change_resource_record_sets(
            HostedZoneId=hosted_zone_id,
            ChangeBatch={
                "Comment": "Pre-deployment capability test - setup",
                "Changes": [{
                    "Action": "CREATE",
                    "ResourceRecordSet": {
                        "Name": test_record_name,
                        "Type": "TXT",
                        "TTL": 60,
                        "ResourceRecords": [{"Value": '"pre-deployment-test-delete"'}]
                    }
                }]
            }
        )
        response = route53_client.change_resource_record_sets(
            HostedZoneId=hosted_zone_id,
            ChangeBatch={
                "Comment": "Pre-deployment capability test - delete",
                "Changes": [{
                    "Action": "DELETE",
                    "ResourceRecordSet": {
                        "Name": test_record_name,
                        "Type": "TXT",
                        "TTL": 60,
                        "ResourceRecords": [{"Value": '"pre-deployment-test-delete"'}]
                    }
                }]
            }
        )
        assert response["ChangeInfo"]["Status"] in ("PENDING", "INSYNC")
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "AccessDenied":
            pytest.fail(f"No permission to delete records in zone '{hosted_zone_id}'")
        raise

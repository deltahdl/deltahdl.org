"""AWS fixtures for pytest tests.

Use by adding to conftest.py:
    pytest_plugins = ['test_fixtures.aws']
"""
import boto3
import pytest
from opentofu_config import get_shared_config


@pytest.fixture(scope="session")
def shared_config():
    """Provide parsed configuration from the shared OpenTofu module."""
    return get_shared_config()


@pytest.fixture(scope="session")
def aws_region(request):
    """Provide the AWS region from shared config."""
    config = request.getfixturevalue("shared_config")
    return config["aws_region"]


@pytest.fixture(scope="session")
def state_bucket_name(request):
    """Provide the OpenTofu state bucket name."""
    config = request.getfixturevalue("shared_config")
    return config["name_for_opentofu_state_bucket"]


@pytest.fixture(scope="session")
def sts_client(request):
    """Create an STS client."""
    region = request.getfixturevalue("aws_region")
    return boto3.client("sts", region_name=region)


@pytest.fixture(scope="session")
def iam_client(request):
    """Create an IAM client."""
    region = request.getfixturevalue("aws_region")
    return boto3.client("iam", region_name=region)


@pytest.fixture(scope="session")
def s3_client(request):
    """Create an S3 client."""
    region = request.getfixturevalue("aws_region")
    return boto3.client("s3", region_name=region)


@pytest.fixture(scope="session")
def cloudfront_client(request):
    """Create a CloudFront client."""
    region = request.getfixturevalue("aws_region")
    return boto3.client("cloudfront", region_name=region)


@pytest.fixture(scope="session")
def route53_client(request):
    """Create a Route 53 client."""
    region = request.getfixturevalue("aws_region")
    return boto3.client("route53", region_name=region)


@pytest.fixture(scope="session")
def acm_client():
    """Create an ACM client for us-east-1 (CloudFront requirement)."""
    return boto3.client("acm", region_name="us-east-1")


@pytest.fixture(scope="session")
def cloudtrail_client(request):
    """Create a CloudTrail client."""
    region = request.getfixturevalue("aws_region")
    return boto3.client("cloudtrail", region_name=region)


@pytest.fixture(scope="session")
def logs_client(request):
    """Create a CloudWatch Logs client."""
    region = request.getfixturevalue("aws_region")
    return boto3.client("logs", region_name=region)


@pytest.fixture(scope="session")
def caller_identity(request):
    """Get the current caller identity."""
    client = request.getfixturevalue("sts_client")
    return client.get_caller_identity()


@pytest.fixture(scope="session")
def current_role_arn(request):
    """Extract the role ARN from caller identity."""
    identity = request.getfixturevalue("caller_identity")
    arn = identity.get("Arn", "")
    if ":assumed-role/" in arn:
        account = identity.get("Account", "")
        role_name = arn.split("/")[1]
        return f"arn:aws:iam::{account}:role/{role_name}"
    return arn


@pytest.fixture(scope="session")
def current_role_name(request):
    """Extract the role name from the role ARN."""
    role_arn = request.getfixturevalue("current_role_arn")
    if not role_arn:
        return ""
    return role_arn.split("/")[-1]

"""Pytest fixtures for www redirect pre-deployment integration tests."""
import subprocess
from pathlib import Path

import boto3
import pytest
from botocore.exceptions import ClientError
from repo_utils import REPO_ROOT
from opentofu_config import TEST_AWS_REGION


BOOTSTRAP_DIR = REPO_ROOT / "src" / "bootstrap"


def _opentofu_init(tf_dir: Path) -> bool:
    """Initialize OpenTofu in the given directory."""
    result = subprocess.run(
        ["tofu", "init"],
        capture_output=True,
        text=True,
        cwd=tf_dir,
        timeout=60,
        check=False,
    )
    return result.returncode == 0


def _opentofu_output(tf_dir: Path, output_name: str) -> str:
    """Get an OpenTofu output value."""
    result = subprocess.run(
        ["tofu", "output", "-raw", output_name],
        capture_output=True,
        text=True,
        cwd=tf_dir,
        timeout=30,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def _get_bootstrap_outputs() -> dict:
    """Get all bootstrap OpenTofu outputs."""
    if not _opentofu_init(BOOTSTRAP_DIR):
        return {}
    return {
        "state_bucket_arn": _opentofu_output(BOOTSTRAP_DIR, "arn_for_state_bucket"),
        "github_actions_role_arn": _opentofu_output(
            BOOTSTRAP_DIR, "arn_for_github_actions_role"),
        "github_actions_role_name": _opentofu_output(
            BOOTSTRAP_DIR, "name_for_github_actions_role"),
        "hosted_zone_id": _opentofu_output(BOOTSTRAP_DIR, "hosted_zone_id"),
    }


@pytest.fixture(scope="session")
def aws_region():
    """Provide the AWS region."""
    return TEST_AWS_REGION


@pytest.fixture(scope="session")
def s3_client():
    """Create an S3 client."""
    return boto3.client("s3", region_name=TEST_AWS_REGION)


@pytest.fixture(scope="session")
def iam_client():
    """Create an IAM client."""
    return boto3.client("iam", region_name=TEST_AWS_REGION)


@pytest.fixture(scope="session")
def route53_client():
    """Create a Route53 client."""
    return boto3.client("route53", region_name=TEST_AWS_REGION)


@pytest.fixture(scope="session")
def sts_client():
    """Create an STS client."""
    return boto3.client("sts", region_name=TEST_AWS_REGION)


@pytest.fixture(scope="session")
def bootstrap_outputs():
    """Get bootstrap OpenTofu outputs."""
    outputs = _get_bootstrap_outputs()
    if not outputs:
        pytest.skip("OpenTofu init failed for bootstrap")
    return outputs


@pytest.fixture(scope="session")
def state_bucket_name(request):
    """Extract state bucket name from ARN."""
    outputs = request.getfixturevalue("bootstrap_outputs")
    arn = outputs.get("state_bucket_arn", "")
    if not arn:
        pytest.skip("state_bucket_arn not found in bootstrap outputs")
    return arn.split(":")[-1]


@pytest.fixture(scope="session")
def hosted_zone_id(request):
    """Get Route53 hosted zone ID."""
    outputs = request.getfixturevalue("bootstrap_outputs")
    zone_id = outputs.get("hosted_zone_id", "")
    if not zone_id:
        pytest.skip("hosted_zone_id not found in bootstrap outputs")
    return zone_id


@pytest.fixture
def src_dir():
    """Provide the redirect source directory path."""
    return REPO_ROOT / "src" / "www" / "redirect"


def head_bucket_status_code(s3_client_instance, bucket_name):
    """Call HeadBucket and return the HTTP status code.

    Calls pytest.fail if the bucket does not exist (404). Re-raises
    other ClientError exceptions. Returns 200 on success.
    """
    try:
        response = s3_client_instance.head_bucket(Bucket=bucket_name)
        return response["ResponseMetadata"]["HTTPStatusCode"]
    except ClientError as exc:
        error_code = exc.response["Error"]["Code"]
        if error_code == "404":
            pytest.fail(
                f"State bucket '{bucket_name}' does not exist"
            )
        raise

"""
OpenTofu drift detection module.

This module provides functions to detect when AWS resources exist but are not
in OpenTofu state. This catches scenarios where:
- Resources were created manually outside of OpenTofu
- OpenTofu state was lost or corrupted
- Resources exist from a previous deployment that wasn't imported

Example usage:
    from opentofu_drift import check_resource_exists, get_planned_creates

    exists = check_resource_exists('aws_s3_bucket', 'my-bucket', 'us-east-2')
    creates = get_planned_creates('/path/to/opentofu/dir')
"""

import json
import subprocess
from pathlib import Path
from typing import Any, Callable, Dict, List, cast

import boto3
from botocore.exceptions import ClientError


ResourceChecker = Callable[[Any, str], bool]


def _check_iam_role(client: Any, name: str) -> bool:
    """Check if IAM role exists."""
    try:
        client.get_role(RoleName=name)
        return True
    except client.exceptions.NoSuchEntityException:
        return False


def _check_log_group(client: Any, name: str) -> bool:
    """Check if CloudWatch log group exists."""
    response = client.describe_log_groups(logGroupNamePrefix=name, limit=1)
    for group in response.get("logGroups", []):
        if group.get("logGroupName") == name:
            return True
    return False


def _check_s3_bucket(client: Any, name: str) -> bool:
    """Check if S3 bucket exists."""
    try:
        client.head_bucket(Bucket=name)
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "404":
            return False
        raise


def _check_ssm_parameter(client: Any, name: str) -> bool:
    """Check if SSM parameter exists."""
    try:
        client.get_parameter(Name=name)
        return True
    except client.exceptions.ParameterNotFound:
        return False


RESOURCE_CHECKERS: Dict[str, ResourceChecker] = {
    "aws_iam_role": _check_iam_role,
    "aws_cloudwatch_log_group": _check_log_group,
    "aws_s3_bucket": _check_s3_bucket,
    "aws_ssm_parameter": _check_ssm_parameter,
}

RESOURCE_TO_CLIENT: Dict[str, str] = {
    "aws_iam_role": "iam",
    "aws_cloudwatch_log_group": "logs",
    "aws_s3_bucket": "s3",
    "aws_ssm_parameter": "ssm",
}


def get_supported_resource_types() -> List[str]:
    """Get list of resource types that can be checked for drift."""
    return list(RESOURCE_CHECKERS.keys())


def check_resource_exists(
    resource_type: str,
    resource_name: str,
    region: str = "us-east-2",
) -> bool:
    """Check if a resource exists in AWS.

    Args:
        resource_type: OpenTofu resource type (e.g., 'aws_s3_bucket')
        resource_name: The AWS resource name/identifier
        region: AWS region to check in

    Returns:
        True if the resource exists, False otherwise.

    Raises:
        ValueError: If the resource type is not supported.
    """
    if resource_type not in RESOURCE_CHECKERS:
        raise ValueError(
            f"Unsupported resource type: {resource_type}. "
            f"Supported types: {', '.join(RESOURCE_CHECKERS.keys())}"
        )

    client_name = RESOURCE_TO_CLIENT[resource_type]
    client = cast(Any, boto3).client(client_name, region_name=region)
    checker = RESOURCE_CHECKERS[resource_type]

    return checker(client, resource_name)


def get_planned_creates(
    opentofu_dir: Path,
    timeout: int = 120,
) -> List[Dict[str, Any]]:
    """Run tofu plan and extract resources marked for creation.

    Args:
        opentofu_dir: Path to directory containing OpenTofu files
        timeout: Timeout in seconds for tofu plan command

    Returns:
        List of dicts with keys: type, name, address, values
    """
    result = subprocess.run(
        ["tofu", "plan", "-json", "-input=false"],
        capture_output=True,
        text=True,
        cwd=opentofu_dir,
        timeout=timeout,
        check=False,
    )

    creates = []
    for line in result.stdout.splitlines():
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue

        if entry.get("type") != "planned_change":
            continue

        change = entry.get("change", {})
        if change.get("action") != "create":
            continue

        resource = change.get("resource", {})
        resource_type = resource.get("resource_type", "")

        if resource_type not in RESOURCE_CHECKERS:
            continue

        after_values = change.get("change", {}).get("after", {})
        name_field = _get_name_field(resource_type)
        resource_name = after_values.get(name_field, "")

        if resource_name:
            creates.append({
                "type": resource_type,
                "name": resource_name,
                "address": resource.get("addr", ""),
                "values": after_values,
            })

    return creates


def _get_name_field(resource_type: str) -> str:
    """Get the attribute name that contains the AWS resource name."""
    name_fields = {
        "aws_iam_role": "name",
        "aws_cloudwatch_log_group": "name",
        "aws_s3_bucket": "bucket",
        "aws_ssm_parameter": "name",
    }
    return name_fields.get(resource_type, "name")


def get_opentofu_state_resources(opentofu_dir: Path) -> List[str]:
    """Get list of resource addresses currently in OpenTofu state.

    Args:
        opentofu_dir: Path to directory containing OpenTofu files

    Returns:
        List of resource addresses (e.g., 'aws_s3_bucket.my_bucket')
    """
    result = subprocess.run(
        ["tofu", "state", "list"],
        capture_output=True,
        text=True,
        cwd=opentofu_dir,
        timeout=60,
        check=False,
    )
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def find_orphaned_resources(
    opentofu_dir: Path,
    region: str = "us-east-2",
) -> List[Dict[str, str]]:
    """Find resources that exist in AWS but not in OpenTofu state.

    Args:
        opentofu_dir: Path to directory containing OpenTofu files
        region: AWS region to check in

    Returns:
        List of dicts with keys: type, name, address, import_command
    """
    planned = get_planned_creates(opentofu_dir)
    orphaned = []

    for resource in planned:
        if check_resource_exists(resource["type"], resource["name"], region):
            orphaned.append({
                "type": resource["type"],
                "name": resource["name"],
                "address": resource["address"],
                "import_command": f"tofu import {resource['address']} {resource['name']}",
            })

    return orphaned

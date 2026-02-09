"""Layer 1: Existence tests for bootstrap post-deployment.

These tests verify that resources were created by OpenTofu.
Tests are organized by resource domain for readability.
"""


# =============================================================================
# S3 Buckets
# =============================================================================


def test_central_logs_bucket_exists(s3_client, config):
    """Test that central logs bucket exists."""
    bucket_name = config['name_for_central_logs_bucket']
    response = s3_client.head_bucket(Bucket=bucket_name)
    assert response['ResponseMetadata']['HTTPStatusCode'] == 200


def test_opentofu_state_bucket_exists(s3_client, config):
    """Test that OpenTofu state bucket exists."""
    bucket_name = config['name_for_opentofu_state_bucket']
    response = s3_client.head_bucket(Bucket=bucket_name)
    assert response['ResponseMetadata']['HTTPStatusCode'] == 200


def test_opentofu_state_file_exists(s3_client, config):
    """Test that OpenTofu state file exists in S3."""
    bucket_name = config['name_for_opentofu_state_bucket']
    s3_client.head_object(
        Bucket=bucket_name,
        Key='bootstrap/terraform.tfstate'
    )
    assert True  # Explicit pass


# =============================================================================
# CloudTrail
# =============================================================================


def test_cloudtrail_trail_exists(cloudtrail_client):
    """Test that CloudTrail trail exists."""
    trails = cloudtrail_client.describe_trails()
    assert len(trails['trailList']) > 0


def test_cloudtrail_s3_bucket_exists(s3_client, cloudtrail_client):
    """Test that CloudTrail S3 bucket exists."""
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    bucket_name = trail['S3BucketName']
    response = s3_client.head_bucket(Bucket=bucket_name)
    assert response['ResponseMetadata']['HTTPStatusCode'] == 200


def test_cloudtrail_log_group_exists(logs_client, cloudtrail_log_group_name):
    """Test that CloudTrail log group exists."""
    response = logs_client.describe_log_groups(logGroupNamePrefix=cloudtrail_log_group_name)
    assert len(response['logGroups']) > 0


def test_cloudwatch_logs_iam_role_exists(cloudtrail_client, iam_client):
    """Test that CloudWatch Logs IAM role exists for CloudTrail."""
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    if 'CloudWatchLogsRoleArn' in trail:
        role_name = trail['CloudWatchLogsRoleArn'].split('/')[-1]
        role = iam_client.get_role(RoleName=role_name)
        assert role['Role']['RoleName'] == role_name


# =============================================================================
# Route53 / DNS
# =============================================================================


def test_hosted_zone_exists(route53_client, config):
    """Test that hosted zone exists in Route53."""
    domain_name = config['domain_name']
    zones = route53_client.list_hosted_zones_by_name(DNSName=f"{domain_name}.")
    zone = zones['HostedZones'][0]
    assert zone['Name'] == f"{domain_name}."


# =============================================================================
# IAM
# =============================================================================


def test_iam_role_exists_in_aws(iam_client, config):
    """Test that GitHub Actions IAM role exists in AWS."""
    role_name = config['name_for_github_actions_role']
    response = iam_client.get_role(RoleName=role_name)
    assert response['Role']['RoleName'] == role_name


# =============================================================================
# OIDC
# =============================================================================


def test_oidc_provider_exists_in_aws(iam_client, config):
    """Test that OIDC provider exists in AWS."""
    account_id = config['aws_account_id']
    provider_arn = f"arn:aws:iam::{account_id}:oidc-provider/token.actions.githubusercontent.com"
    response = iam_client.get_open_id_connect_provider(OpenIDConnectProviderArn=provider_arn)
    assert response['Url'] == 'token.actions.githubusercontent.com'

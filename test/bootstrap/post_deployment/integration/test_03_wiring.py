"""Layer 3: Wiring tests for bootstrap post-deployment.

These tests verify that components are connected properly.
Tests assume Layer 1 existence and Layer 2 configuration tests have passed.
"""



# =============================================================================
# CloudTrail Wiring
# =============================================================================


def test_cloudtrail_writes_logs_to_s3(s3_client, cloudtrail_client):
    """Test that CloudTrail writes logs to S3."""
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    bucket_name = trail['S3BucketName']
    objects = s3_client.list_objects_v2(Bucket=bucket_name, MaxKeys=10)
    key_count = objects['KeyCount']
    assert key_count > 0


def test_cloudtrail_writes_logs_to_cloudwatch(logs_client, cloudtrail_client):
    """Test that CloudTrail writes logs to CloudWatch."""
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    log_group_arn = trail['CloudWatchLogsLogGroupArn']
    log_group_name = log_group_arn.split(':log-group:')[1].split(':')[0]
    streams = logs_client.describe_log_streams(
        logGroupName=log_group_name,
        orderBy='LastEventTime',
        descending=True,
        limit=1
    )
    assert len(streams['logStreams']) > 0


# =============================================================================
# Central Logs Wiring
# =============================================================================


def test_central_logs_write_policy_exists(iam_client):
    """Test that central logs write policy exists."""
    policy_name = 'central-logs-write-policy'
    response = iam_client.list_policies(Scope='Local')
    policy_names = [p['PolicyName'] for p in response['Policies']]
    assert policy_name in policy_names


# =============================================================================
# CloudTrail IAM Wiring
# =============================================================================


def test_cloudtrail_iam_role_trust_policy_allows_cloudtrail(iam_client, cloudtrail_client):
    """Test that CloudTrail IAM role trust policy allows CloudTrail service."""
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    if 'CloudWatchLogsRoleArn' in trail:
        role_name = trail['CloudWatchLogsRoleArn'].split('/')[-1]
        response = iam_client.get_role(RoleName=role_name)
        trust_policy = response['Role']['AssumeRolePolicyDocument']
        principals = []
        for statement in trust_policy['Statement']:
            principal = statement.get('Principal', {})
            if 'Service' in principal:
                if isinstance(principal['Service'], list):
                    principals.extend(principal['Service'])
                else:
                    principals.append(principal['Service'])
        assert 'cloudtrail.amazonaws.com' in principals


def test_cloudtrail_iam_role_has_inline_policy(iam_client, cloudtrail_client):
    """Test that CloudTrail IAM role has inline policy."""
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    if 'CloudWatchLogsRoleArn' in trail:
        role_name = trail['CloudWatchLogsRoleArn'].split('/')[-1]
        response = iam_client.list_role_policies(RoleName=role_name)
        assert len(response['PolicyNames']) > 0


def test_cloudtrail_iam_role_policy_allows_log_actions(iam_client, cloudtrail_client):
    """Test that CloudTrail IAM role policy allows log actions."""
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    if 'CloudWatchLogsRoleArn' in trail:
        role_name = trail['CloudWatchLogsRoleArn'].split('/')[-1]
        policies = iam_client.list_role_policies(RoleName=role_name)
        policy_name = policies['PolicyNames'][0]
        policy = iam_client.get_role_policy(RoleName=role_name, PolicyName=policy_name)
        policy_doc = str(policy['PolicyDocument'])
        assert 'logs:CreateLogStream' in policy_doc or 'logs:*' in policy_doc


# =============================================================================
# OpenTofu State Bucket Wiring
# =============================================================================


def test_opentofu_state_bucket_policy_allows_github_actions_role(s3_client, config):
    """Test that OpenTofu state bucket policy allows GitHub Actions role."""
    bucket_name = config['name_for_opentofu_state_bucket']
    policy = s3_client.get_bucket_policy(Bucket=bucket_name)
    policy_doc = policy['Policy']
    role_name = config['name_for_github_actions_role']
    assert role_name in policy_doc


# =============================================================================
# GitHub Actions OIDC Wiring
# =============================================================================


def test_github_actions_role_is_attached_to_oidc_provider(iam_client, config):
    """Test that GitHub Actions role is attached to OIDC provider."""
    role_name = config['name_for_github_actions_role']
    response = iam_client.get_role(RoleName=role_name)
    trust_policy = response['Role']['AssumeRolePolicyDocument']
    oidc_provider = 'token.actions.githubusercontent.com'
    trust_doc = str(trust_policy)
    assert oidc_provider in trust_doc

"""End-to-end tests for OIDC workflow."""
import json
import os
import subprocess
import urllib.request
import pytest


def get_github_oidc_token():
    """Get GitHub OIDC token from environment."""
    token_url = os.environ.get('ACTIONS_ID_TOKEN_REQUEST_URL')
    token_request_token = os.environ.get('ACTIONS_ID_TOKEN_REQUEST_TOKEN')
    if not token_url or not token_request_token:
        pytest.skip("OIDC token not available")
    url = f'{token_url}&audience=sts.amazonaws.com'
    request = urllib.request.Request(
        url,
        headers={'Authorization': f'Bearer {token_request_token}'}
    )
    with urllib.request.urlopen(request) as response:
        data = json.loads(response.read().decode('utf-8'))
    token = data.get('value')
    if not token:
        pytest.fail("Could not retrieve OIDC token")
    return token


def assume_role_with_oidc(account_id, region, role_name, oidc_token):
    """Assume IAM role using OIDC token."""
    role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"
    result = subprocess.run(
        ['aws', 'sts', 'assume-role-with-web-identity',
         '--role-arn', role_arn,
         '--role-session-name', 'e2e-test-session',
         '--web-identity-token', oidc_token,
         '--region', region,
         '--output', 'json'],
        capture_output=True,
        text=True,
        check=True
    )
    data = json.loads(result.stdout)
    creds = data['Credentials']
    return {
        'access_key_id': creds['AccessKeyId'],
        'secret_access_key': creds['SecretAccessKey'],
        'session_token': creds['SessionToken']
    }


def get_caller_identity_arn(aws_creds, region):
    """Get the caller identity ARN using the provided credentials."""
    env = os.environ.copy()
    env['AWS_ACCESS_KEY_ID'] = aws_creds['access_key_id']
    env['AWS_SECRET_ACCESS_KEY'] = aws_creds['secret_access_key']
    env['AWS_SESSION_TOKEN'] = aws_creds['session_token']
    result = subprocess.run(
        ['aws', 'sts', 'get-caller-identity',
         '--region', region,
         '--output', 'json'],
        capture_output=True,
        text=True,
        check=True,
        env=env
    )
    identity = json.loads(result.stdout)
    return identity['Arn']


class TestCompleteOIDCWorkflow:
    """Test class for complete OIDC workflow."""

    @pytest.fixture
    def oidc_token(self):
        """Get OIDC token fixture."""
        return get_github_oidc_token()

    @pytest.fixture
    def aws_creds(self, config, oidc_token):
        """Get AWS credentials fixture."""
        return assume_role_with_oidc(
            config['aws_account_id'],
            config['aws_region'],
            config['name_for_github_actions_role'],
            oidc_token
        )

    @pytest.fixture
    def caller_arn(self, config, aws_creds):
        """Get caller identity ARN fixture."""
        return get_caller_identity_arn(aws_creds, config['aws_region'])

    # =========================================================================
    # OIDC Token Tests (atomic)
    # =========================================================================

    def test_oidc_token_is_not_none(self, oidc_token):
        """Test that OIDC token is not None."""
        assert oidc_token is not None

    def test_oidc_token_is_not_empty(self, oidc_token):
        """Test that OIDC token is not empty."""
        assert len(oidc_token) > 0

    # =========================================================================
    # AWS Credentials Tests (atomic)
    # =========================================================================

    def test_aws_credentials_has_access_key_id(self, aws_creds):
        """Test that AWS credentials have access key ID."""
        assert aws_creds['access_key_id'] is not None

    def test_aws_credentials_has_secret_access_key(self, aws_creds):
        """Test that AWS credentials have secret access key."""
        assert aws_creds['secret_access_key'] is not None

    def test_aws_credentials_has_session_token(self, aws_creds):
        """Test that AWS credentials have session token."""
        assert aws_creds['session_token'] is not None

    # =========================================================================
    # Assumed Role Identity Tests (atomic)
    # =========================================================================

    def test_assumed_role_arn_contains_role_name(self, config, caller_arn):
        """Test that assumed role ARN contains the role name."""
        role_name = config['name_for_github_actions_role']
        assert role_name in caller_arn

    def test_assumed_role_arn_contains_assumed_role_prefix(self, caller_arn):
        """Test that assumed role ARN contains 'assumed-role' prefix."""
        assert 'assumed-role' in caller_arn

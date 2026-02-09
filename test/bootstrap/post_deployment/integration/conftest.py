"""Fixtures for bootstrap post-deployment integration tests."""
import pytest


@pytest.fixture(scope="module", name="cloudtrail_trail")
def cloudtrail_trail_fixture(cloudtrail_client):
    """Get the CloudTrail trail."""
    trails = cloudtrail_client.describe_trails()
    return trails['trailList'][0]


@pytest.fixture(scope="module", name="cloudtrail_log_group_name")
def cloudtrail_log_group_name_fixture(cloudtrail_trail):
    """Get the CloudTrail log group name."""
    log_group_arn = cloudtrail_trail['CloudWatchLogsLogGroupArn']
    return log_group_arn.split(':log-group:')[1].split(':')[0]

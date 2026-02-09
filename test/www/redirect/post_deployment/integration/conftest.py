"""Pytest fixtures for www redirect post-deployment integration tests."""
import pytest


@pytest.fixture(name="distribution_config", scope="module")
def distribution_config_fixture(cloudfront_client, config):
    """Get CloudFront distribution config for redirect domain."""
    distributions = cloudfront_client.list_distributions()
    if distributions["DistributionList"]["Quantity"] > 0:
        for item in distributions["DistributionList"]["Items"]:
            aliases = item.get("Aliases", {}).get("Items", [])
            if config["apex_fqdn"] in aliases:
                dist_id = item["Id"]
                return cloudfront_client.get_distribution_config(Id=dist_id)
    assert False, f"CloudFront distribution for {config['apex_fqdn']} not found"


@pytest.fixture(name="default_cache_behavior", scope="module")
def default_cache_behavior_fixture(distribution_config):
    """Get CloudFront default cache behavior from distribution."""
    return distribution_config["DistributionConfig"]["DefaultCacheBehavior"]

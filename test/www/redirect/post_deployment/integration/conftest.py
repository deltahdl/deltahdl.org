"""Pytest fixtures for www redirect post-deployment integration tests."""
import pytest


@pytest.fixture(name="hosted_zone_id", scope="module")
def hosted_zone_id_fixture(route53_client, config):
    """Look up Route53 hosted zone ID for the redirect domain."""
    domain_name = config["apex_fqdn"]
    response = route53_client.list_hosted_zones_by_name(
        DNSName=domain_name, MaxItems="1"
    )
    zones = response.get("HostedZones", [])
    for zone in zones:
        zone_name = zone["Name"].rstrip(".")
        if zone_name == domain_name:
            return zone["Id"].replace("/hostedzone/", "")
    pytest.fail(f"No hosted zone found for {domain_name}")
    return None


@pytest.fixture(name="distribution_config", scope="module")
def distribution_config_fixture(cloudfront_client, config):
    """Get CloudFront distribution config for redirect domain."""
    distributions = cloudfront_client.list_distributions()
    if distributions["DistributionList"]["Quantity"] > 0:
        for item in distributions["DistributionList"]["Items"]:
            aliases = item.get("Aliases", {}).get("Items", [])
            if config["apex_fqdn"] in aliases:
                dist_id = item["Id"]
                return cloudfront_client.get_distribution_config(
                    Id=dist_id
                )
    assert False, (
        f"CloudFront distribution for {config['apex_fqdn']} not found"
    )
    return None


@pytest.fixture(name="default_cache_behavior", scope="module")
def default_cache_behavior_fixture(distribution_config):
    """Get CloudFront default cache behavior from distribution."""
    return distribution_config["DistributionConfig"]["DefaultCacheBehavior"]


def query_dns_a_record(route53_client_instance, hosted_zone, fqdn):
    """Query Route53 for an A record matching the given FQDN.

    Returns the matching record dict, or None if not found.
    """
    response = route53_client_instance.list_resource_record_sets(
        HostedZoneId=hosted_zone,
        StartRecordName=fqdn,
        StartRecordType="A",
        MaxItems="1"
    )
    records = response.get("ResourceRecordSets", [])
    matching = [
        r for r in records
        if r["Name"].rstrip(".") == fqdn
    ]
    return matching[0] if matching else None

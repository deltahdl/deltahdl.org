"""Layer 3: Wiring tests for www redirect post-deployment validation.

Verify components are connected properly. Assumes configuration tests passed.
"""
import pytest


@pytest.fixture(name="cloudfront_origins", scope="module")
def cloudfront_origins_fixture(distribution_config):
    """Extract CloudFront origins from distribution config."""
    return distribution_config["DistributionConfig"]["Origins"]["Items"]


@pytest.fixture(name="viewer_certificate", scope="module")
def viewer_certificate_fixture(distribution_config):
    """Extract viewer certificate from distribution config."""
    return distribution_config["DistributionConfig"]["ViewerCertificate"]


@pytest.fixture(name="apex_dns_record", scope="module")
def apex_dns_record_fixture(route53_client, config, hosted_zone_id):
    """Get the DNS A record for the apex domain."""
    response = route53_client.list_resource_record_sets(
        HostedZoneId=hosted_zone_id,
        StartRecordName=config["apex_fqdn"],
        StartRecordType="A",
        MaxItems="1"
    )
    records = response.get("ResourceRecordSets", [])
    matching = [r for r in records if r["Name"].rstrip(".") == config["apex_fqdn"]]
    return matching[0] if matching else None


@pytest.fixture(name="www_dns_record", scope="module")
def www_dns_record_fixture(route53_client, config, hosted_zone_id):
    """Get the DNS A record for the www domain."""
    response = route53_client.list_resource_record_sets(
        HostedZoneId=hosted_zone_id,
        StartRecordName=config["www_fqdn"],
        StartRecordType="A",
        MaxItems="1"
    )
    records = response.get("ResourceRecordSets", [])
    matching = [r for r in records if r["Name"].rstrip(".") == config["www_fqdn"]]
    return matching[0] if matching else None


def test_apex_dns_record_exists(apex_dns_record, config):
    """Verify apex DNS A record exists."""
    assert apex_dns_record is not None, f"No A record found for {config['apex_fqdn']}"


def test_apex_dns_record_is_alias(apex_dns_record, config):
    """Verify apex DNS record is an alias record."""
    assert "AliasTarget" in apex_dns_record, (
        f"Record for {config['apex_fqdn']} is not an alias"
    )


def test_apex_dns_record_points_to_cloudfront(apex_dns_record, config):
    """Verify apex DNS alias target points to CloudFront."""
    alias_target = apex_dns_record["AliasTarget"]["DNSName"]
    assert "cloudfront.net" in alias_target, (
        f"Apex alias does not point to CloudFront: {alias_target}"
    )


def test_www_dns_record_exists(www_dns_record, config):
    """Verify www DNS A record exists."""
    assert www_dns_record is not None, f"No A record found for {config['www_fqdn']}"


def test_www_dns_record_is_alias(www_dns_record, config):
    """Verify www DNS record is an alias record."""
    assert "AliasTarget" in www_dns_record, (
        f"Record for {config['www_fqdn']} is not an alias"
    )


def test_www_dns_record_points_to_cloudfront(www_dns_record, config):
    """Verify www DNS alias target points to CloudFront."""
    alias_target = www_dns_record["AliasTarget"]["DNSName"]
    assert "cloudfront.net" in alias_target, (
        f"WWW alias does not point to CloudFront: {alias_target}"
    )


def test_cloudfront_uses_acm_certificate(viewer_certificate):
    """Verify CloudFront has an ACM certificate configured."""
    assert "ACMCertificateArn" in viewer_certificate, (
        "CloudFront not using ACM certificate"
    )


def test_cloudfront_acm_certificate_arn_format(viewer_certificate):
    """Verify CloudFront ACM certificate ARN has correct format."""
    arn = viewer_certificate.get("ACMCertificateArn", "")
    assert arn.startswith("arn:aws:acm:"), f"Invalid ACM ARN format: {arn}"


def test_cloudfront_function_associated_with_distribution(default_cache_behavior):
    """Verify CloudFront Function is associated with distribution."""
    associations = default_cache_behavior.get("FunctionAssociations", {})
    items = associations.get("Items", [])
    viewer_request = [a for a in items if a["EventType"] == "viewer-request"]
    assert len(viewer_request) == 1, (
        f"Expected 1 viewer-request function, found {len(viewer_request)}"
    )


def test_cloudfront_function_is_redirect(default_cache_behavior, config):
    """Verify CloudFront Function is the redirect function."""
    associations = default_cache_behavior.get("FunctionAssociations", {})
    items = associations.get("Items", [])
    viewer_request = [a for a in items if a["EventType"] == "viewer-request"]
    function_arn = viewer_request[0]["FunctionARN"]
    expected_name = f"{config['resource_prefix']}Function"
    assert expected_name in function_arn, (
        f"Function ARN does not contain {expected_name}: {function_arn}"
    )

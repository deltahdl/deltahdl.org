"""Layer 1: Existence tests for www redirect post-deployment validation.

Verify resources created by this deployment exist. No configuration checks.
"""
from test.www.redirect.post_deployment.integration.conftest import (
    query_dns_a_record,
)

import pytest


def test_cloudfront_distribution_exists(cloudfront_client, config):
    """Verify CloudFront distribution exists for redirect domains."""
    distributions = cloudfront_client.list_distributions()
    distribution_list = distributions["DistributionList"]
    if distribution_list["Quantity"] > 0:
        all_aliases = []
        for item in distribution_list["Items"]:
            aliases = item.get("Aliases", {}).get("Items", [])
            all_aliases.extend(aliases)
        assert config["apex_fqdn"] in all_aliases, (
            f"No CloudFront distribution found with alias "
            f"{config['apex_fqdn']}. Found aliases: {all_aliases}"
        )
    else:
        pytest.fail("No CloudFront distributions found")


def test_acm_certificate_exists(acm_client):
    """Verify ACM certificate exists in us-east-1."""
    certificates = acm_client.list_certificates()
    assert certificates["CertificateSummaryList"], (
        "No ACM certificates found in us-east-1"
    )


def test_apex_dns_record_exists(route53_client, config, hosted_zone_id):
    """Verify DNS A record exists for apex domain."""
    record = query_dns_a_record(
        route53_client, hosted_zone_id, config["apex_fqdn"]
    )
    assert record, f"No A record found for {config['apex_fqdn']}"


def test_www_dns_record_exists(route53_client, config, hosted_zone_id):
    """Verify DNS A record exists for www domain."""
    record = query_dns_a_record(
        route53_client, hosted_zone_id, config["www_fqdn"]
    )
    assert record, f"No A record found for {config['www_fqdn']}"


def test_cloudfront_function_exists(cloudfront_client, config):
    """Verify CloudFront Function exists."""
    function_name = f"{config['resource_prefix']}Function"
    response = cloudfront_client.list_functions()
    functions = response.get("FunctionList", {}).get("Items", [])
    function_names = [f["Name"] for f in functions]
    assert function_name in function_names, (
        f"CloudFront Function '{function_name}' not found. "
        f"Found: {function_names}"
    )

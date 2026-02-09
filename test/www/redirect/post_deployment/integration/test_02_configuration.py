"""Layer 2: Configuration tests for www redirect post-deployment validation.

Verify resources are configured correctly. Assumes existence tests passed.
"""


def test_cloudfront_aliases_include_apex(distribution_config, config):
    """Verify CloudFront aliases include the apex domain."""
    aliases = distribution_config["DistributionConfig"]["Aliases"].get("Items", [])
    assert config["apex_fqdn"] in aliases, (
        f"CloudFront aliases missing {config['apex_fqdn']}. Found: {aliases}"
    )


def test_cloudfront_aliases_include_www(distribution_config, config):
    """Verify CloudFront aliases include the www domain."""
    aliases = distribution_config["DistributionConfig"]["Aliases"].get("Items", [])
    assert config["www_fqdn"] in aliases, (
        f"CloudFront aliases missing {config['www_fqdn']}. Found: {aliases}"
    )


def test_acm_certificate_is_issued(acm_client, config):
    """Verify ACM certificate is validated and issued."""
    certificates = acm_client.list_certificates(CertificateStatuses=["ISSUED"])
    cert_domains = [c["DomainName"] for c in certificates["CertificateSummaryList"]]
    assert config["apex_fqdn"] in cert_domains, (
        f"No ISSUED certificate found for {config['apex_fqdn']}. "
        f"Issued certs: {cert_domains}"
    )


def test_cloudfront_tls_minimum_version(distribution_config):
    """Verify CloudFront uses TLSv1.2_2021 minimum protocol version."""
    viewer_cert = distribution_config["DistributionConfig"]["ViewerCertificate"]
    min_version = viewer_cert.get("MinimumProtocolVersion", "")
    assert min_version == "TLSv1.2_2021", (
        f"Expected TLSv1.2_2021, got {min_version}"
    )


def test_cloudfront_function_runtime(cloudfront_client, config):
    """Verify CloudFront Function uses cloudfront-js-2.0 runtime."""
    function_name = f"{config['resource_prefix']}Function"
    response = cloudfront_client.describe_function(Name=function_name)
    runtime = response["FunctionSummary"]["FunctionConfig"]["Runtime"]
    assert runtime == "cloudfront-js-2.0", (
        f"Expected cloudfront-js-2.0 runtime, got {runtime}"
    )


def test_cloudfront_uses_https_redirect(default_cache_behavior):
    """Verify CloudFront distribution uses HTTPS redirect."""
    policy = default_cache_behavior["ViewerProtocolPolicy"]
    assert policy == "redirect-to-https", (
        f"Expected redirect-to-https, got {policy}"
    )


def test_cloudfront_ssl_support_method(distribution_config):
    """Verify CloudFront uses SNI-only SSL support method."""
    viewer_cert = distribution_config["DistributionConfig"]["ViewerCertificate"]
    ssl_method = viewer_cert.get("SSLSupportMethod", "")
    assert ssl_method == "sni-only", (
        f"Expected sni-only, got {ssl_method}"
    )

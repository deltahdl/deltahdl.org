"""Unit tests for www redirect cloudfront.tf configuration."""


def test_cloudfront_file_exists(src_dir):
    """Verify cloudfront.tf file exists."""
    assert (src_dir / "cloudfront.tf").exists()


def test_cloudfront_distribution_defined(src_dir):
    """Verify CloudFront distribution resource is defined."""
    content = (src_dir / "cloudfront.tf").read_text()
    assert 'resource "aws_cloudfront_distribution" "redirect"' in content


def test_cloudfront_distribution_enabled(src_dir):
    """Verify CloudFront distribution is enabled."""
    content = (src_dir / "cloudfront.tf").read_text()
    assert "enabled         = true" in content


def test_cloudfront_function_resource_defined(src_dir):
    """Verify CloudFront function resource is defined."""
    content = (src_dir / "cloudfront.tf").read_text()
    assert 'resource "aws_cloudfront_function" "redirect"' in content


def test_cloudfront_function_uses_js_2_0_runtime(src_dir):
    """Verify CloudFront function uses cloudfront-js-2.0 runtime."""
    content = (src_dir / "cloudfront.tf").read_text()
    assert 'runtime = "cloudfront-js-2.0"' in content


def test_cloudfront_viewer_protocol_redirect_https(src_dir):
    """Verify CloudFront redirects to HTTPS."""
    content = (src_dir / "cloudfront.tf").read_text()
    assert 'viewer_protocol_policy = "redirect-to-https"' in content


def test_cloudfront_has_s3_origin(src_dir):
    """Verify CloudFront has an S3 origin."""
    content = (src_dir / "cloudfront.tf").read_text()
    assert "origin {" in content
    assert "module.redirect_bucket.bucket_regional_domain_name" in content


def test_cloudfront_has_function_association(src_dir):
    """Verify CloudFront has function association."""
    content = (src_dir / "cloudfront.tf").read_text()
    assert "function_association {" in content


def test_cloudfront_function_event_type_viewer_request(src_dir):
    """Verify CloudFront function is associated with viewer-request event."""
    content = (src_dir / "cloudfront.tf").read_text()
    assert 'event_type   = "viewer-request"' in content


def test_cloudfront_function_arn_reference(src_dir):
    """Verify CloudFront function ARN references the redirect function."""
    content = (src_dir / "cloudfront.tf").read_text()
    assert "aws_cloudfront_function.redirect.arn" in content


def test_cloudfront_ssl_sni_only(src_dir):
    """Verify CloudFront uses SNI-only SSL support."""
    content = (src_dir / "cloudfront.tf").read_text()
    assert 'ssl_support_method       = "sni-only"' in content


def test_cloudfront_tls_minimum_version(src_dir):
    """Verify CloudFront uses TLSv1.2_2021 minimum."""
    content = (src_dir / "cloudfront.tf").read_text()
    assert 'minimum_protocol_version = "TLSv1.2_2021"' in content


def test_cloudfront_geo_restriction_none(src_dir):
    """Verify CloudFront has no geo restriction."""
    content = (src_dir / "cloudfront.tf").read_text()
    assert 'restriction_type = "none"' in content


def test_cloudfront_depends_on_certificate_validation(src_dir):
    """Verify CloudFront depends on certificate validation."""
    content = (src_dir / "cloudfront.tf").read_text()
    assert "aws_acm_certificate_validation.redirect" in content


def test_cloudfront_aliases_include_both_domains(src_dir):
    """Verify CloudFront aliases include both www and apex domains."""
    content = (src_dir / "cloudfront.tf").read_text()
    assert "local.www_fqdn" in content
    assert "local.apex_fqdn" in content


def test_cloudfront_origin_access_control_defined(src_dir):
    """Verify CloudFront origin access control is defined."""
    content = (src_dir / "cloudfront.tf").read_text()
    assert 'resource "aws_cloudfront_origin_access_control" "redirect"' in content


def test_cloudfront_oac_s3_origin_type(src_dir):
    """Verify OAC origin type is s3."""
    content = (src_dir / "cloudfront.tf").read_text()
    assert 'origin_access_control_origin_type = "s3"' in content


def test_cloudfront_oac_signing_always(src_dir):
    """Verify OAC signing behavior is always."""
    content = (src_dir / "cloudfront.tf").read_text()
    assert 'signing_behavior                  = "always"' in content


def test_cloudfront_oac_sigv4_protocol(src_dir):
    """Verify OAC uses sigv4 protocol."""
    content = (src_dir / "cloudfront.tf").read_text()
    assert 'signing_protocol                  = "sigv4"' in content


def test_cloudfront_ipv6_disabled(src_dir):
    """Verify CloudFront distribution has IPv6 disabled."""
    content = (src_dir / "cloudfront.tf").read_text()
    assert "is_ipv6_enabled = false" in content


def test_cloudfront_redirect_bucket_module_defined(src_dir):
    """Verify redirect_bucket module is defined."""
    content = (src_dir / "cloudfront.tf").read_text()
    assert 'module "redirect_bucket"' in content


def test_cloudfront_redirect_bucket_module_source(src_dir):
    """Verify redirect_bucket module uses s3_bucket source."""
    content = (src_dir / "cloudfront.tf").read_text()
    assert 'source = "../../../lib/opentofu/s3_bucket"' in content

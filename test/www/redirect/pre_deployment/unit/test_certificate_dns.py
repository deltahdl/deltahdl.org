"""Unit tests for www redirect certificate_dns.tf configuration."""


def test_certificate_dns_file_exists(src_dir):
    """Verify certificate_dns.tf file exists."""
    assert (src_dir / "certificate_dns.tf").exists()


def test_route53_zone_data_source_defined(src_dir):
    """Verify Route53 zone data source is defined."""
    content = (src_dir / "certificate_dns.tf").read_text()
    assert 'data "aws_route53_zone" "parent"' in content


def test_route53_zone_uses_local_domain_name(src_dir):
    """Verify Route53 zone uses local.domain_name."""
    content = (src_dir / "certificate_dns.tf").read_text()
    assert "name = local.domain_name" in content


def test_acm_certificate_defined(src_dir):
    """Verify ACM certificate resource is defined."""
    content = (src_dir / "certificate_dns.tf").read_text()
    assert 'resource "aws_acm_certificate" "redirect"' in content


def test_acm_certificate_uses_us_east_1_provider(src_dir):
    """Verify ACM certificate uses us-east-1 provider."""
    content = (src_dir / "certificate_dns.tf").read_text()
    assert "provider = aws.us-east-1" in content


def test_acm_certificate_domain_name(src_dir):
    """Verify ACM certificate uses local.apex_fqdn as domain name."""
    content = (src_dir / "certificate_dns.tf").read_text()
    assert "domain_name               = local.apex_fqdn" in content


def test_acm_certificate_san_www(src_dir):
    """Verify ACM certificate has www domain as SAN."""
    content = (src_dir / "certificate_dns.tf").read_text()
    assert "subject_alternative_names = [local.www_fqdn]" in content


def test_acm_certificate_dns_validation(src_dir):
    """Verify ACM certificate uses DNS validation."""
    content = (src_dir / "certificate_dns.tf").read_text()
    assert 'validation_method         = "DNS"' in content


def test_acm_certificate_create_before_destroy(src_dir):
    """Verify ACM certificate has create_before_destroy lifecycle."""
    content = (src_dir / "certificate_dns.tf").read_text()
    assert "create_before_destroy = true" in content


def test_cert_validation_record_defined(src_dir):
    """Verify certificate validation DNS record is defined."""
    content = (src_dir / "certificate_dns.tf").read_text()
    assert 'resource "aws_route53_record" "cert_validation"' in content


def test_cert_validation_record_for_each(src_dir):
    """Verify certificate validation uses for_each over domain_validation_options."""
    content = (src_dir / "certificate_dns.tf").read_text()
    assert "domain_validation_options" in content


def test_cert_validation_allow_overwrite(src_dir):
    """Verify certificate validation records allow overwrite."""
    content = (src_dir / "certificate_dns.tf").read_text()
    assert "allow_overwrite = true" in content


def test_acm_certificate_validation_defined(src_dir):
    """Verify ACM certificate validation resource is defined."""
    content = (src_dir / "certificate_dns.tf").read_text()
    assert 'resource "aws_acm_certificate_validation" "redirect"' in content


def test_www_dns_record_defined(src_dir):
    """Verify www DNS A record is defined."""
    content = (src_dir / "certificate_dns.tf").read_text()
    assert 'resource "aws_route53_record" "www"' in content


def test_www_dns_record_name(src_dir):
    """Verify www DNS record uses local.www_fqdn."""
    content = (src_dir / "certificate_dns.tf").read_text()
    assert "name    = local.www_fqdn" in content


def test_www_dns_record_type_a(src_dir):
    """Verify www DNS record is type A."""
    content = (src_dir / "certificate_dns.tf").read_text()
    assert 'type    = "A"' in content


def test_www_dns_record_alias_cloudfront(src_dir):
    """Verify www DNS record aliases CloudFront distribution."""
    content = (src_dir / "certificate_dns.tf").read_text()
    assert "aws_cloudfront_distribution.redirect.domain_name" in content


def test_apex_dns_record_defined(src_dir):
    """Verify apex DNS A record is defined."""
    content = (src_dir / "certificate_dns.tf").read_text()
    assert 'resource "aws_route53_record" "apex"' in content


def test_apex_dns_record_name(src_dir):
    """Verify apex DNS record uses local.apex_fqdn."""
    content = (src_dir / "certificate_dns.tf").read_text()
    assert "name    = local.apex_fqdn" in content


def test_dns_records_use_hosted_zone(src_dir):
    """Verify DNS records use the parent hosted zone."""
    content = (src_dir / "certificate_dns.tf").read_text()
    assert "data.aws_route53_zone.parent.zone_id" in content


def test_alias_evaluate_target_health_false(src_dir):
    """Verify alias records have evaluate_target_health = false."""
    content = (src_dir / "certificate_dns.tf").read_text()
    assert "evaluate_target_health = false" in content

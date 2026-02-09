"""Unit tests for www redirect outputs.tf configuration."""


def test_outputs_file_exists(src_dir):
    """Verify outputs.tf file exists."""
    assert (src_dir / "outputs.tf").exists()


def test_output_distribution_id_defined(src_dir):
    """Verify cloudfront_distribution_id output is defined."""
    content = (src_dir / "outputs.tf").read_text()
    assert 'output "cloudfront_distribution_id"' in content


def test_output_distribution_id_value(src_dir):
    """Verify cloudfront_distribution_id output references redirect distribution."""
    content = (src_dir / "outputs.tf").read_text()
    assert "value = aws_cloudfront_distribution.redirect.id" in content


def test_output_domain_name_defined(src_dir):
    """Verify cloudfront_domain_name output is defined."""
    content = (src_dir / "outputs.tf").read_text()
    assert 'output "cloudfront_domain_name"' in content


def test_output_domain_name_value(src_dir):
    """Verify cloudfront_domain_name output references redirect distribution."""
    content = (src_dir / "outputs.tf").read_text()
    assert "value = aws_cloudfront_distribution.redirect.domain_name" in content


def test_output_redirect_target_defined(src_dir):
    """Verify redirect_target output is defined."""
    content = (src_dir / "outputs.tf").read_text()
    assert 'output "redirect_target"' in content


def test_output_redirect_target_value(src_dir):
    """Verify redirect_target output uses local.redirect_target."""
    content = (src_dir / "outputs.tf").read_text()
    assert "value = local.redirect_target" in content

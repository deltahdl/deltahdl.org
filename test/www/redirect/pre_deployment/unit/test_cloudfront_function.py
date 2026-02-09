"""Unit tests for www redirect cloudfront_function.js."""


def test_cloudfront_function_file_exists(src_dir):
    """Verify cloudfront_function.js file exists."""
    assert (src_dir / "cloudfront_function.js").exists()


def test_cloudfront_function_returns_301_status(src_dir):
    """Verify CloudFront function returns 301 status code."""
    content = (src_dir / "cloudfront_function.js").read_text()
    assert "statusCode: 301" in content


def test_cloudfront_function_has_location_header(src_dir):
    """Verify CloudFront function sets location header."""
    content = (src_dir / "cloudfront_function.js").read_text()
    assert "location:" in content


def test_cloudfront_function_target_is_github(src_dir):
    """Verify CloudFront function redirects to GitHub repository."""
    content = (src_dir / "cloudfront_function.js").read_text()
    assert "https://github.com/deltahdl/deltahdl" in content


def test_cloudfront_function_has_moved_permanently_description(src_dir):
    """Verify CloudFront function has Moved Permanently status description."""
    content = (src_dir / "cloudfront_function.js").read_text()
    assert '"Moved Permanently"' in content


def test_cloudfront_function_has_handler(src_dir):
    """Verify CloudFront function defines a handler function."""
    content = (src_dir / "cloudfront_function.js").read_text()
    assert "function handler(event)" in content


def test_cloudfront_function_returns_response_object(src_dir):
    """Verify CloudFront function returns a response object."""
    content = (src_dir / "cloudfront_function.js").read_text()
    assert "return {" in content


def test_cloudfront_function_has_headers_block(src_dir):
    """Verify CloudFront function has headers in response."""
    content = (src_dir / "cloudfront_function.js").read_text()
    assert "headers:" in content

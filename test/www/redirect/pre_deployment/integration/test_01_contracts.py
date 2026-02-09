"""Layer 1: Contract tests for www redirect pre-deployment validation.

Verify local files that must work together are compatible. No AWS calls.
"""
import re

from repo_utils import REPO_ROOT


SRC_DIR = REPO_ROOT / "src" / "www" / "redirect"


def _read_file(filename: str) -> str:
    """Read a file from the source directory."""
    with open(SRC_DIR / filename, encoding="utf-8") as f:
        return f.read()


def _extract_local_references(content: str) -> set:
    """Extract all local.* references from OpenTofu content."""
    return set(re.findall(r'local\.(\w+)', content))


def _extract_local_definitions(content: str) -> set:
    """Extract all local variable definitions from locals.tf content."""
    definitions = set()
    for match in re.finditer(r'^\s*(\w+)\s*=', content, re.MULTILINE):
        name = match.group(1)
        if name != 'locals':
            definitions.add(name)
    return definitions


def test_cloudfront_local_references_exist_in_locals():
    """Verify all local.* references in cloudfront.tf are defined in locals.tf."""
    cloudfront_content = _read_file("cloudfront.tf")
    locals_content = _read_file("locals.tf")

    references = _extract_local_references(cloudfront_content)
    definitions = _extract_local_definitions(locals_content)

    missing = references - definitions
    assert not missing, (
        f"cloudfront.tf references undefined locals: {missing}. "
        f"Defined locals: {definitions}"
    )


def test_certificate_dns_local_references_exist_in_locals():
    """Verify all local.* references in certificate_dns.tf are defined in locals.tf."""
    cert_content = _read_file("certificate_dns.tf")
    locals_content = _read_file("locals.tf")

    references = _extract_local_references(cert_content)
    definitions = _extract_local_definitions(locals_content)

    missing = references - definitions
    assert not missing, (
        f"certificate_dns.tf references undefined locals: {missing}. "
        f"Defined locals: {definitions}"
    )


def test_providers_local_references_exist_in_locals():
    """Verify all local.* references in providers.tf are defined in locals.tf."""
    providers_content = _read_file("providers.tf")
    locals_content = _read_file("locals.tf")

    references = _extract_local_references(providers_content)
    definitions = _extract_local_definitions(locals_content)

    missing = references - definitions
    assert not missing, (
        f"providers.tf references undefined locals: {missing}. "
        f"Defined locals: {definitions}"
    )


def test_cloudfront_references_certificate_from_certificate_dns():
    """Verify cloudfront.tf references ACM certificate from certificate_dns.tf."""
    cloudfront_content = _read_file("cloudfront.tf")
    assert "aws_acm_certificate.redirect.arn" in cloudfront_content, (
        "cloudfront.tf does not reference aws_acm_certificate.redirect.arn"
    )


def test_cloudfront_depends_on_certificate_validation():
    """Verify cloudfront.tf depends on certificate validation from certificate_dns.tf."""
    cloudfront_content = _read_file("cloudfront.tf")
    assert "aws_acm_certificate_validation.redirect" in cloudfront_content, (
        "cloudfront.tf does not depend on aws_acm_certificate_validation.redirect"
    )


def test_locals_references_module_common_values():
    """Verify locals.tf references module.common for shared values."""
    locals_content = _read_file("locals.tf")
    assert "module.common.aws_region" in locals_content
    assert "module.common.domain_name" in locals_content
    assert "module.common.resource_prefix" in locals_content


def test_shared_module_source_declaration_exists():
    """Verify shared.tf has a module source declaration."""
    shared_content = _read_file("shared.tf")
    match = re.search(r'source\s*=\s*"([^"]+)"', shared_content)
    assert match, "shared.tf missing module source declaration"


def test_shared_module_source_path_exists():
    """Verify shared module source path exists on disk."""
    shared_content = _read_file("shared.tf")
    match = re.search(r'source\s*=\s*"([^"]+)"', shared_content)
    source_path = match.group(1)
    resolved_path = SRC_DIR / source_path
    assert resolved_path.exists(), (
        f"Module source path does not exist: {resolved_path}"
    )


def test_redirect_bucket_module_source_path_exists():
    """Verify redirect_bucket module source path exists on disk."""
    cloudfront_content = _read_file("cloudfront.tf")
    match = re.search(
        r'module\s+"redirect_bucket"\s*\{[^}]*source\s*=\s*"([^"]+)"',
        cloudfront_content,
        re.DOTALL
    )
    assert match, "cloudfront.tf missing redirect_bucket module source"
    source_path = match.group(1)
    resolved_path = SRC_DIR / source_path
    assert resolved_path.exists(), (
        f"S3 bucket module source path does not exist: {resolved_path}"
    )


def test_cloudfront_function_file_referenced():
    """Verify cloudfront.tf references cloudfront_function.js."""
    cloudfront_content = _read_file("cloudfront.tf")
    assert "cloudfront_function.js" in cloudfront_content, (
        "cloudfront.tf does not reference cloudfront_function.js"
    )


def test_cloudfront_function_file_exists():
    """Verify cloudfront_function.js exists on disk."""
    assert (SRC_DIR / "cloudfront_function.js").exists(), (
        "cloudfront_function.js not found in source directory"
    )

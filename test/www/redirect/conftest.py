"""Pytest fixtures for www redirect tests."""
from typing import Dict

import pytest
from repo_utils import REPO_ROOT
from test_fixtures.config import parse_locals_file


@pytest.fixture(name="config", scope="module")
def config_fixture(shared_config) -> Dict[str, str]:
    """Provide redirect configuration for tests."""
    locals_path = REPO_ROOT / "src" / "www" / "redirect" / "locals.tf"
    redirect_locals = parse_locals_file(locals_path, shared_config)
    domain_name = shared_config.get('domain_name', '')
    prefix = shared_config.get('resource_prefix', '')
    return {
        'aws_region': shared_config['aws_region'],
        'apex_fqdn': domain_name,
        'www_fqdn': f"www.{domain_name}",
        'redirect_target': redirect_locals.get(
            'redirect_target', 'https://github.com/deltahdl/deltahdl'),
        'resource_prefix': f"{prefix}Redirect",
    }


@pytest.fixture(name="redirect_src_path")
def fixture_redirect_src_path():
    """Provide path to redirect source directory."""
    return REPO_ROOT / "src" / "www" / "redirect"


@pytest.fixture(name="cloudfront_tf_content")
def fixture_cloudfront_tf_content(redirect_src_path):
    """Provide CloudFront OpenTofu file content."""
    with open(redirect_src_path / "cloudfront.tf", encoding="utf-8") as f:
        return f.read()


@pytest.fixture(name="certificate_dns_tf_content")
def fixture_certificate_dns_tf_content(redirect_src_path):
    """Provide certificate DNS OpenTofu file content."""
    with open(redirect_src_path / "certificate_dns.tf", encoding="utf-8") as f:
        return f.read()

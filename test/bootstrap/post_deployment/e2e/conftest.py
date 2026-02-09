"""Pytest fixtures for bootstrap E2E tests."""
import dns.resolver
import pytest


@pytest.fixture(scope="module")
def public_dns_resolver(zone_nameservers):
    """Create a DNS resolver configured to query Route53 nameservers."""
    ns_ip = dns.resolver.resolve(zone_nameservers[0], 'A')[0].to_text()
    resolver = dns.resolver.Resolver()
    resolver.nameservers = [ns_ip]
    return resolver

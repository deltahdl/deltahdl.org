# Post-Deployment Integration Test Tenets

These are the non-negotiable rules for post-deployment integration tests.

## Table of Contents

- [Only Test This Deployment's Resources](#only-test-this-deployments-resources)
- [Three-Layer Testing Model](#three-layer-testing-model)
- [Test File Organization](#test-file-organization)
- [Fail Fast with Granular Diagnostics](#fail-fast-with-granular-diagnostics)
- [Boundary with E2E Tests](#boundary-with-e2e-tests)
- [No Cleanup Required](#no-cleanup-required)
- [Fixture Usage](#fixture-usage)
- [Quick Reference](#quick-reference)

## Only Test This Deployment's Resources

**Post-deployment tests ONLY test resources created by THIS workflow.**

- Do test: Resources created by OpenTofu apply
- Do test: Resource configuration matches expected values
- Do test: Component wiring (DNS records pointing to CloudFront, ACM cert attached)
- Do NOT test: Full user journeys (those are e2e tests)
- Do NOT test: Resources created by other workflows
- Do NOT test: Application logic or business rules (unit tests)

Post-deployment tests answer: "Did my deployment succeed?"
E2E tests answer: "Does the user journey work?"

## Three-Layer Testing Model

Every deployed resource must be tested through three layers, in order:

| Layer | Purpose | Example |
|-------|---------|---------|
| 1. Existence | Resource was created | CloudFront distribution exists |
| 2. Configuration | Resource configured correctly | ACM certificate covers both domains |
| 3. Wiring | Components connected properly | Route 53 alias points to CloudFront |

Each layer catches different failure modes:
- Layer 1 fails -> OpenTofu didn't create the resource
- Layer 2 fails -> resource exists but misconfigured
- Layer 3 fails -> resources exist and configured, but not connected

## Test File Organization

Tests MUST be organized into exactly three files by layer:

```
test/{module}/post_deployment/integration/
├── test_01_existence.py       # Layer 1: All resources exist
├── test_02_configuration.py   # Layer 2: All resources configured correctly
└── test_03_wiring.py          # Layer 3: All components connected properly
```

Do NOT organize by resource (test_cloudfront.py, test_acm.py, test_route53.py).
Organizing by resource makes it impossible to know which layer failed.

### Layer 1: Existence Tests (test_01_existence.py)

Test ONLY that resources exist. No configuration checks.

```python
# CORRECT - existence only
def test_cloudfront_distribution_exists(cloudfront_client, config):
    """Verify DeltaHDL redirect CloudFront distribution exists."""
    response = cloudfront_client.get_distribution(Id=config["distribution_id"])
    assert response["Distribution"]["Id"] == config["distribution_id"]

def test_acm_certificate_exists(acm_client, config):
    """Verify ACM certificate exists."""
    response = acm_client.describe_certificate(CertificateArn=config["certificate_arn"])
    assert response["Certificate"]["CertificateArn"] == config["certificate_arn"]

def test_route53_apex_record_exists(route53_client, config):
    """Verify Route 53 A record exists for deltahdl.org."""
    records = route53_client.list_resource_record_sets(
        HostedZoneId=config["hosted_zone_id"],
        StartRecordName="deltahdl.org",
        StartRecordType="A",
        MaxItems="1"
    )
    assert any(r["Name"] == "deltahdl.org." for r in records["ResourceRecordSets"])
```

```python
# WRONG - mixing existence with configuration
def test_cloudfront_exists_with_correct_aliases(cloudfront_client, config):
    response = cloudfront_client.get_distribution(Id=config["distribution_id"])
    aliases = response["Distribution"]["DistributionConfig"]["Aliases"]["Items"]
    assert "deltahdl.org" in aliases  # This is configuration, not existence
```

### Layer 2: Configuration Tests (test_02_configuration.py)

Test that resources have correct settings. Assumes existence tests passed.

```python
# CORRECT - configuration only
def test_cloudfront_has_both_aliases(cloudfront_client, distribution_config):
    """Verify CloudFront has aliases for both apex and www."""
    aliases = distribution_config["Aliases"]["Items"]
    assert "deltahdl.org" in aliases
    assert "www.deltahdl.org" in aliases

def test_acm_certificate_is_issued(acm_client, config):
    """Verify ACM certificate status is ISSUED."""
    response = acm_client.describe_certificate(CertificateArn=config["certificate_arn"])
    assert response["Certificate"]["Status"] == "ISSUED"

def test_cloudfront_redirects_http_to_https(cloudfront_client, distribution_config):
    """Verify CloudFront redirects HTTP to HTTPS."""
    behavior = distribution_config["DefaultCacheBehavior"]
    assert behavior["ViewerProtocolPolicy"] == "redirect-to-https"
```

Use fixtures to get resource identifiers. Don't re-check existence.

### Layer 3: Wiring Tests (test_03_wiring.py)

Test that components are connected. Assumes existence and configuration passed.

```python
# CORRECT - wiring only
def test_route53_apex_points_to_cloudfront(route53_client, config):
    """Verify Route 53 A record for deltahdl.org aliases to CloudFront."""
    records = route53_client.list_resource_record_sets(
        HostedZoneId=config["hosted_zone_id"]
    )
    a_records = [r for r in records["ResourceRecordSets"]
                 if r["Name"] == "deltahdl.org." and r["Type"] == "A"]
    assert len(a_records) == 1
    assert "cloudfront.net" in a_records[0]["AliasTarget"]["DNSName"]

def test_cloudfront_uses_acm_certificate(cloudfront_client, distribution_config, config):
    """Verify CloudFront uses the ACM certificate."""
    cert = distribution_config["ViewerCertificate"]
    assert cert["ACMCertificateArn"] == config["certificate_arn"]

def test_cloudfront_function_attached_to_distribution(cloudfront_client, distribution_config):
    """Verify CloudFront Function is attached to viewer-request."""
    associations = distribution_config["DefaultCacheBehavior"].get(
        "FunctionAssociations", {}
    ).get("Items", [])
    viewer_request = [a for a in associations if a["EventType"] == "viewer-request"]
    assert len(viewer_request) == 1
```

```python
# WRONG - sending HTTP request (that's e2e)
def test_redirect_works(config):
    response = requests.get(f"https://{config['domain']}", allow_redirects=False)
    assert response.status_code == 301
```

## Fail Fast with Granular Diagnostics

- Each test must be atomic: one assertion per test
- Tests must run in layer order (existence before configuration before wiring)
- When a test fails, the developer must know exactly what's wrong
- Failure messages must include resource names and expected values

## Boundary with E2E Tests

Post-deployment integration tests verify the deployment. E2E tests verify user journeys.

### This belongs in post-deployment integration:
- CloudFront distribution exists
- CloudFront has correct aliases
- ACM certificate is issued
- Route 53 records exist
- CloudFront Function is attached
- CloudFront uses ACM cert

### This belongs in e2e tests:
- HTTPS request to deltahdl.org returns 301
- Redirect Location header is correct
- DNS resolves deltahdl.org to CloudFront
- TLS handshake succeeds
- Both apex and www redirect correctly

**Rule of thumb**: If the test sends an HTTP request or performs DNS resolution, it's an e2e test.

## No Cleanup Required

Post-deployment tests MUST NOT create test artifacts. They only inspect what OpenTofu created.

- Do: Read resource configuration (get_distribution, describe_certificate)
- Do: Verify resource exists (get_distribution, list_resource_record_sets)
- Do: Check component connections (verify alias targets, cert attachments)
- Do NOT: Create test DNS records
- Do NOT: Send HTTP requests to endpoints
- Do NOT: Modify CloudFront configuration

If a test needs cleanup, it's probably an e2e test.

## Fixture Usage

Use fixtures to:
1. Create AWS clients once per module
2. Cache resource identifiers (distribution IDs, certificate ARNs)

```python
# conftest.py
@pytest.fixture(scope="module")
def cloudfront_client(config):
    return boto3.client("cloudfront", region_name=config["aws_region"])

@pytest.fixture(scope="module")
def distribution_config(cloudfront_client, config):
    response = cloudfront_client.get_distribution(Id=config["distribution_id"])
    return response["Distribution"]["DistributionConfig"]
```

## Quick Reference

| If you want to test... | Layer | File |
|------------------------|-------|------|
| CloudFront distribution exists | 1. Existence | test_01_existence.py |
| ACM certificate exists | 1. Existence | test_01_existence.py |
| Route 53 records exist | 1. Existence | test_01_existence.py |
| S3 origin bucket exists | 1. Existence | test_01_existence.py |
| CloudFront Function exists | 1. Existence | test_01_existence.py |
| CloudFront has correct aliases | 2. Configuration | test_02_configuration.py |
| ACM cert is ISSUED status | 2. Configuration | test_02_configuration.py |
| CloudFront redirects HTTP to HTTPS | 2. Configuration | test_02_configuration.py |
| Route 53 points to CloudFront | 3. Wiring | test_03_wiring.py |
| CloudFront uses ACM cert | 3. Wiring | test_03_wiring.py |
| CloudFront Function attached | 3. Wiring | test_03_wiring.py |
| HTTP redirect works | N/A | e2e tests |
| DNS resolves correctly | N/A | e2e tests |

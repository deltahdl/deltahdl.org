# E2E Test Tenets

These are the non-negotiable rules for end-to-end tests.

## Table of Contents

- [Top of the Pyramid](#top-of-the-pyramid)
- [Production-Safe](#production-safe)
- [Test the Full Path](#test-the-full-path)
- [Last Line of Defense, Not First](#last-line-of-defense-not-first)
- [Run During CI/CD](#run-during-cicd)
- [Fail Fast](#fail-fast)
- [Clear Ownership](#clear-ownership)
- [Test File Organization](#test-file-organization)
- [Fixture Requirements](#fixture-requirements)
- [AWS Configuration vs Real-World Verification](#aws-configuration-vs-real-world-verification)
- [Boundary with Post-Deployment Integration](#boundary-with-post-deployment-integration)
- [Quick Reference](#quick-reference)

## Top of the Pyramid

**E2E tests are few in number. Only test critical user journeys.**

```
        /\
       /  \     E2E tests (few) <-- YOU ARE HERE
      /----\
     /      \   Integration tests (some)
    /--------\
   /          \
  /            \ Unit tests (many)
 /______________\
```

E2E tests are expensive:
- Slow (seconds to minutes, not milliseconds)
- Flaky (network, timing, external dependencies)
- Run in production (real resources, real costs)

Each test should represent a critical user journey that, if broken, would constitute a major incident.

```python
# CORRECT - critical user journeys only
def test_apex_https_redirects_to_github():
    """Verify HTTPS request to deltahdl.org returns 301 to GitHub."""
    ...

def test_www_https_redirects_to_github():
    """Verify HTTPS request to www.deltahdl.org returns 301 to GitHub."""
    ...
```

```python
# WRONG - testing edge cases in e2e
def test_redirect_with_query_params():
    """Verify redirect preserves query params."""
    # This level of detail is not a critical user journey
    ...
```

## Production-Safe

**E2E tests run in production. They must be non-destructive.**

There is no staging environment. E2E tests execute against production resources. For a redirect site, all e2e tests are naturally read-only:

### Pattern A: Read-Only Verification

Test only inspects state, creates nothing.

```python
# CORRECT - read-only HTTP request
def test_apex_returns_301(domain):
    """Verify deltahdl.org returns 301 redirect."""
    response = requests.get(f"https://{domain}", allow_redirects=False, timeout=5)
    assert response.status_code == 301

# CORRECT - read-only DNS resolution
def test_dns_resolves_apex(domain):
    """Verify deltahdl.org resolves via DNS."""
    answers = dns.resolver.resolve(domain, "A")
    assert len(answers) > 0
```

## Test the Full Path

**E2E tests verify end-to-end behavior that unit and integration tests cannot catch.**

E2E tests exercise the complete path:
- DNS resolution -> CloudFront -> CloudFront Function -> 301 redirect

```python
# CORRECT - full path
def test_apex_https_redirects_to_github():
    """Verify full redirect path: HTTPS -> CloudFront -> 301 -> GitHub."""
    response = requests.get(
        "https://deltahdl.org",
        allow_redirects=False,
        timeout=5
    )
    assert response.status_code == 301
    assert response.headers["Location"] == "https://github.com/deltahdl/deltahdl"
```

```python
# WRONG - partial path (this is integration, not e2e)
def test_cloudfront_function_returns_301(cloudfront_client):
    """Verify CloudFront Function exists."""
    # Checking CloudFront config bypasses DNS, TLS, and actual HTTP behavior
    response = cloudfront_client.describe_function(Name="DeltaHDLRedirect")
    assert response is not None
```

## Last Line of Defense, Not First

**If an e2e test catches a bug that a unit test should have caught, that's a unit test gap.**

E2E tests should only catch issues that cannot be caught earlier:
- DNS propagation failures
- TLS certificate issues visible to clients
- CloudFront caching behavior
- Network path failures

| Issue Type | Should Be Caught By |
|------------|---------------------|
| Wrong redirect URL in JS | Unit test |
| Missing CloudFront alias | Post-deployment integration |
| ACM cert not issued | Post-deployment integration |
| Route 53 record missing | Post-deployment integration |
| DNS doesn't resolve for real users | E2E test |
| TLS handshake fails | E2E test |
| HTTP redirect returns wrong Location | E2E test |

## Run During CI/CD

**E2E tests run as workflow steps, not on schedule.**

E2E tests execute:
- As a step in the deployment workflow
- After post-deployment integration tests pass
- Only for the component being deployed

```yaml
# CORRECT - e2e as workflow step
jobs:
  deploy:
    steps:
      - name: Deploy
        run: tofu apply -auto-approve

      - name: Post-deployment integration tests
        run: pytest test/www/redirect/post_deployment/integration/

      - name: E2E tests
        run: pytest test/www/redirect/post_deployment/e2e/
```

```yaml
# WRONG - scheduled e2e tests
on:
  schedule:
    - cron: '0 0 * * *'  # We don't run tests on schedule
```

## Fail Fast

**E2E tests should fail quickly when something is wrong.**

Don't wait for long timeouts. If the system is working, responses are fast.

```python
# CORRECT - aggressive timeouts
def test_redirect_response_time():
    """Verify redirect returns within 5 seconds."""
    response = requests.get(
        "https://deltahdl.org",
        allow_redirects=False,
        timeout=5  # Fail fast
    )
    assert response.status_code == 301
```

```python
# WRONG - waiting too long
def test_redirect_eventually_works():
    for attempt in range(30):
        try:
            response = requests.get("https://deltahdl.org", timeout=60)
            if response.status_code == 301:
                return
        except:
            pass
        time.sleep(10)
    pytest.fail("Redirect never worked")
```

## Clear Ownership

**Each e2e test must document the user journey it validates.**

```python
# CORRECT - clear documentation
def test_apex_https_redirects_to_github():
    """
    User Journey: Visitor navigates to deltahdl.org

    When: A user visits https://deltahdl.org in their browser
    Then: They are redirected to https://github.com/deltahdl/deltahdl

    Critical Path: DNS -> CloudFront -> CloudFront Function -> 301 redirect
    Failure Impact: Users cannot find the DeltaHDL project
    """
    ...
```

## Test File Organization

```
test/www/redirect/post_deployment/e2e/
├── conftest.py           # Fixtures for domains, expected redirect target
└── test_redirect.py      # All redirect verification tests
```

E2E tests are organized by journey type, not by component.

## Fixture Requirements

E2E fixtures must:
1. Provide domain names and expected redirect targets
2. Use aggressive timeouts
3. Not require cleanup (all tests are read-only)

```python
# conftest.py
@pytest.fixture
def apex_domain():
    """Apex domain under test."""
    return "deltahdl.org"

@pytest.fixture
def www_domain():
    """WWW domain under test."""
    return "www.deltahdl.org"

@pytest.fixture
def redirect_target():
    """Expected redirect target."""
    return "https://github.com/deltahdl/deltahdl"
```

## AWS Configuration vs Real-World Verification

**Integration tests verify what AWS says. E2E tests verify what the real world experiences.**

AWS API responses confirm configuration state. They do NOT confirm:
- DNS propagation completed successfully
- TLS certificates are trusted by browsers
- CloudFront edge locations are serving correctly
- The redirect actually works for real users

### Examples

| What You Want to Verify | Integration Test (AWS API) | E2E Test (Real World) |
|------------------------|---------------------------|----------------------|
| DNS record works | Route53 `list_resource_record_sets` returns record | `dns.resolver.resolve()` returns record |
| Certificate is valid | ACM shows certificate issued | TLS handshake succeeds |
| Redirect works | CloudFront Function attached to distribution | HTTP request returns 301 |
| Both domains work | CloudFront has correct aliases | Both apex and www return 301 |

### The Test

Ask yourself: "If AWS says it's configured correctly, could it still fail for a real user?"

- **Yes** -> E2E test (verify real-world behavior)
- **No** -> Integration test (verify AWS configuration)

## Boundary with Post-Deployment Integration

Post-deployment integration tests answer: "Did my deployment succeed?"
E2E tests answer: "Does the user journey work?"

| Post-Deployment Integration | E2E |
|----------------------------|-----|
| CloudFront distribution exists | HTTPS request returns 301 |
| ACM cert is ISSUED | TLS handshake succeeds |
| Route 53 record exists | DNS resolves correctly |
| CloudFront Function attached | Redirect Location header is correct |
| Aliases configured correctly | Both apex and www redirect |

## Quick Reference

| If you want to test... | Test Type | Why |
|------------------------|-----------|-----|
| CloudFront Function JS syntax | Unit | File content, no I/O |
| Redirect URL is correct in JS | Unit | File content, no I/O |
| CloudFront has correct aliases | Post-deployment integration | Resource configuration |
| ACM cert is ISSUED | Post-deployment integration | Resource configuration |
| Route 53 points to CloudFront | Post-deployment integration | Component wiring |
| HTTPS redirect works | E2E | Full path verification |
| DNS resolves for real users | E2E | Real-world verification |
| TLS certificate trusted | E2E | Real-world verification |
| Both domains redirect | E2E | End-to-end user journey |

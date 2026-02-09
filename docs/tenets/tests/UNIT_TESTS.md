# Unit Test Tenets

These are the non-negotiable rules for unit tests.

## Table of Contents

- [Unit Tests Are the Primary Line of Defense](#unit-tests-are-the-primary-line-of-defense)
- [Extreme Atomicity](#extreme-atomicity)
- [Test File Organization](#test-file-organization)
- [Complete Isolation](#complete-isolation)
- [Test Every Code Path](#test-every-code-path)
- [Descriptive Test Names](#descriptive-test-names)
- [Test Error Messages](#test-error-messages)
- [No Test Interdependence](#no-test-interdependence)
- [Fast Execution](#fast-execution)
- [Pre-Deployment Coverage Requirements](#pre-deployment-coverage-requirements)
- [Quick Reference](#quick-reference)

## Unit Tests Are the Primary Line of Defense

**Almost everything wrong should be caught by unit tests.**

The testing pyramid dictates that unit tests form the base - the number of unit tests should be absurdly larger than integration and e2e tests combined. If a bug could be caught by a unit test but wasn't, that's a failure of test coverage.

```
        /\
       /  \     E2E tests (few)
      /----\
     /      \   Integration tests (some)
    /--------\
   /          \
  /            \ Unit tests (many)
 /______________\
```

- Unit tests: Test a single component (function, class, module) in isolation
- Integration tests: Test how multiple components work together
- E2E tests: Test full user journeys

**Rule of thumb**: If you're testing a single component with all dependencies mocked, it's a unit test. If you're testing how two or more components interact, it's an integration test - regardless of whether network calls are involved.

## Extreme Atomicity

**One logical assertion per test. No exceptions.**

Each test must verify exactly one behavior. This ensures:
- When a test fails, you know exactly what broke
- Tests are independent and can run in any order
- Test names accurately describe what's being tested

```python
# CORRECT - atomic tests
def test_locals_has_aws_region():
    """Verify locals.tf defines aws_region."""
    assert "aws_region" in locals_content

def test_locals_aws_region_is_us_east_2():
    """Verify aws_region is us-east-2."""
    assert locals_content["aws_region"] == "us-east-2"

def test_locals_has_resource_prefix():
    """Verify locals.tf defines resource_prefix."""
    assert "resource_prefix" in locals_content
```

```python
# WRONG - multiple assertions testing different behaviors
def test_locals_configuration():
    """Verify locals.tf is correct."""
    assert "aws_region" in locals_content
    assert locals_content["aws_region"] == "us-east-2"
    assert "resource_prefix" in locals_content
    # If aws_region assertion fails, you don't know if resource_prefix is correct
```

## Test File Organization

**One test file per source file. 1:1 mapping.**

```
src/www/redirect/
├── backend.tf
├── providers.tf
├── locals.tf
├── cloudfront.tf
├── certificate_dns.tf
├── cloudfront_function.js
├── shared.tf
└── outputs.tf

test/www/redirect/pre_deployment/unit/
├── test_backend_opentofu.py        # Tests backend.tf
├── test_providers_opentofu.py      # Tests providers.tf
├── test_locals_opentofu.py         # Tests locals.tf
├── test_cloudfront_opentofu.py     # Tests cloudfront.tf
├── test_certificate_dns_opentofu.py # Tests certificate_dns.tf
├── test_cloudfront_function.py     # Tests cloudfront_function.js
├── test_shared_opentofu.py         # Tests shared.tf
└── test_outputs_opentofu.py        # Tests outputs.tf
```

Do NOT organize tests by behavior (test_happy_path.py, test_error_cases.py).
Do NOT put multiple source files' tests in one test file.

## Complete Isolation

**Unit tests must have zero external dependencies.**

- No network calls (HTTP, AWS SDK calls)
- No file system access (except test fixtures)
- No database connections
- No environment variable side effects

Read OpenTofu files as strings and validate their structure:

```python
# CORRECT - reads file content, no external calls
def test_backend_uses_s3(backend_content):
    """Verify backend.tf uses S3 backend."""
    assert 'backend "s3"' in backend_content

def test_backend_bucket_name(backend_content):
    """Verify backend.tf uses correct state bucket."""
    assert "deltahdl-terraform-state-us-east-2" in backend_content
```

```python
# WRONG - real AWS call
def test_state_bucket_exists():
    """Verify state bucket exists."""
    client = boto3.client("s3")
    client.head_bucket(Bucket="deltahdl-terraform-state-us-east-2")
    # This is an integration test, not a unit test
```

## Test Every Code Path

**100% branch coverage is the goal.**

Every `if`, `else`, `try`, `catch`, `switch` case, and early return must have a test.

```python
# Source: cloudfront_function.js
# function handler(event) {
#   return { statusCode: 301, ... location: { value: 'https://github.com/deltahdl/deltahdl' } }
# }

# CORRECT - tests all aspects
def test_cloudfront_function_returns_301(cf_function_content):
    assert "statusCode: 301" in cf_function_content

def test_cloudfront_function_redirects_to_github(cf_function_content):
    assert "https://github.com/deltahdl/deltahdl" in cf_function_content

def test_cloudfront_function_uses_location_header(cf_function_content):
    assert "location" in cf_function_content
```

## Descriptive Test Names

**Test names must describe the specific behavior being tested.**

Format: `[function/method] [condition] [expected result]`

```python
# CORRECT - descriptive names
def test_backend_uses_s3_backend_type()
def test_backend_enables_encryption()
def test_providers_requires_opentofu_version_1_14_or_higher()
def test_locals_redirect_target_is_github_url()
def test_cloudfront_function_returns_301_status_code()
```

```python
# WRONG - vague names
def test_backend()
def test_providers_work()
def test_cloudfront()
```

## Test Error Messages

**When tests fail, the error message must explain the problem.**

```python
# CORRECT - clear failure messages
def test_cloudfront_has_both_aliases(cloudfront_content):
    """Verify CloudFront distribution has both apex and www aliases."""
    assert "deltahdl.org" in cloudfront_content, \
        "CloudFront distribution missing deltahdl.org alias"
    # Note: this is ONE logical assertion about "both aliases present"
```

## No Test Interdependence

**Each test must be completely independent.**

- Tests must pass when run individually
- Tests must pass when run in any order
- Tests must not share mutable state

## Fast Execution

**Unit tests must be fast. Milliseconds, not seconds.**

If a test takes more than 100ms, something is wrong:
- You're making real network calls (mock them)
- You're doing expensive setup (optimize or share via fixtures)
- You're testing too much in one test (split it)

## Pre-Deployment Coverage Requirements

**Unit tests must catch these issues before deployment:**

| Issue Type | Must Be Caught By |
|------------|-------------------|
| Syntax errors | Unit tests (imports fail) |
| Type mismatches | Unit tests |
| Missing configuration values | Unit tests |
| Wrong backend bucket/key | Unit tests |
| Wrong provider region | Unit tests |
| Missing default_tags | Unit tests |
| Single-file configuration parsing | Unit tests |
| Cross-file contract mismatches | Integration tests (local) |
| AWS resource misconfiguration | Integration tests (AWS) |
| Missing IAM permissions | Integration tests (AWS) |
| DNS propagation | E2E tests |
| Full redirect behavior | E2E tests |

If a bug could have been caught by a unit test, the test suite failed.

## Quick Reference

| If you want to test... | Test Type | Location |
|------------------------|-----------|----------|
| OpenTofu file has correct values | Unit | pre_deployment/unit/ |
| CloudFront Function JS is valid | Unit | pre_deployment/unit/ |
| Backend uses correct bucket | Unit | pre_deployment/unit/ |
| Provider has default_tags | Unit | pre_deployment/unit/ |
| Resource naming is PascalCase | Unit | pre_deployment/unit/ |
| AWS resource exists | Integration | pre_deployment/integration/ or post_deployment/integration/ |
| IAM permissions work | Integration | pre_deployment/integration/ |
| HTTPS redirect works | E2E | post_deployment/e2e/ |
| DNS resolves correctly | E2E | post_deployment/e2e/ |

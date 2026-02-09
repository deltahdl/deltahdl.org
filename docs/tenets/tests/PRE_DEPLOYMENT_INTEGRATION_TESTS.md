# Pre-Deployment Integration Test Tenets

These are the non-negotiable rules for pre-deployment integration tests.

## Table of Contents

- [Integration Tests Verify Components Work Together](#integration-tests-verify-components-work-together)
- [Seven-Layer Testing Model](#seven-layer-testing-model)
- [Test File Organization](#test-file-organization)
- [Fail Fast with Granular Diagnostics](#fail-fast-with-granular-diagnostics)
- [Cleanup After Capability Tests](#cleanup-after-capability-tests)
- [Fixture Usage](#fixture-usage)
- [Why OpenTofu Plan is Not a Workflow Step](#why-opentofu-plan-is-not-a-workflow-step)
- [Workflow Step Ordering](#workflow-step-ordering)
- [Quick Reference](#quick-reference)
- [Workflow Reference](#workflow-reference)

## Integration Tests Verify Components Work Together

**Integration tests verify that multiple components integrate correctly.**

There are two types of pre-deployment integration tests:

### Local Integration Tests (Contract Tests)

Test that local files/components that must work together are compatible:

- Do test: Module references in shared.tf match actual common module outputs
- Do test: Cross-file configuration consistency (locals.tf values match outputs.tf)
- Do NOT test: Single-file parsing or structure (that's a unit test)

These tests catch contract mismatches between files before deployment.

### AWS Integration Tests (Prerequisite Tests)

Test that AWS resources created by OTHER workflows exist and are configured correctly:

- Do test: Bootstrap resources that must exist before deployment
- Do test: IAM permissions required for deployment
- Do test: External resources referenced by OpenTofu
- Do NOT test: Resources created by the deployment itself

Resources created by the workflow don't exist yet when pre-deployment tests run.

Pre-deployment tests answer: "Can I deploy?"
Post-deployment tests answer: "Did deployment succeed?"

## Seven-Layer Testing Model

Every deployment must pass through seven layers, in order:

| Layer | Purpose | Example |
|-------|---------|---------|
| 1. Contracts | Local files are compatible | module.common refs match actual outputs |
| 2. Authentication | Valid credentials exist | Can call sts:GetCallerIdentity |
| 3. Authorization | Permission to inspect resources | Can call s3:HeadBucket |
| 4. State | OpenTofu state matches AWS reality | Resources to create don't already exist |
| 5. Existence | Resource actually exists | State bucket exists |
| 6. Configuration | Resource configured correctly | IAM role has required policy |
| 7. Capability | Can perform required operations | Can call s3:PutObject |

Each layer catches different failure modes:
- Layer 1 fails -> local files are incompatible (contract mismatch)
- Layer 2 fails -> credentials invalid or expired
- Layer 3 fails -> credentials valid but lack permission to inspect
- Layer 4 fails -> state drift - resources exist but not in OpenTofu state
- Layer 5 fails -> have permission to check, but resource doesn't exist
- Layer 6 fails -> resource exists but misconfigured
- Layer 7 fails -> resource exists and configured, but can't perform operations

## Test File Organization

Tests MUST be organized into exactly seven files by layer:

```
test/{module}/pre_deployment/integration/
├── test_01_contracts.py       # Layer 1: Local files are compatible
├── test_02_authentication.py  # Layer 2: Can authenticate to AWS
├── test_03_authorization.py   # Layer 3: Have permission to inspect prerequisites
├── test_04_state.py           # Layer 4: OpenTofu state matches AWS reality
├── test_05_existence.py       # Layer 5: Prerequisite resources exist
├── test_06_configuration.py   # Layer 6: Prerequisites configured correctly
└── test_07_capability.py      # Layer 7: Can perform required operations
```

Do NOT organize by resource (test_s3.py, test_iam.py, test_cloudfront.py).
Organizing by resource makes it impossible to know which layer failed.

### Layer 1: Contract Tests (test_01_contracts.py)

Test that local files that must work together are compatible. No AWS calls.

```python
# CORRECT - cross-file contract validation
def test_shared_module_refs_exist_in_common_outputs(locals_content, common_outputs):
    """Verify all module.common.* refs in locals.tf exist in common module outputs."""
    import re
    refs = set(re.findall(r'module\.common\.(\w+)', locals_content))
    missing = refs - set(common_outputs.keys())
    assert not missing, f"Refs in locals.tf missing from common outputs: {missing}"
```

```python
# WRONG - this is a unit test (single file)
def test_locals_has_aws_region():
    """Verify locals.tf has aws_region."""
    assert "aws_region" in locals_content  # Single file = unit test
```

### Layer 2: Authentication Tests (test_02_authentication.py)

Test ONLY that credentials are valid. No authorization or resource checks.

```python
# CORRECT - authentication only
def test_aws_credentials_valid(sts_client):
    """Verify AWS credentials are valid."""
    response = sts_client.get_caller_identity()
    assert response["Account"] is not None
```

### Layer 3: Authorization Tests (test_03_authorization.py)

Test that credentials have permission to INSPECT prerequisite resources.

```python
# CORRECT - authorization to inspect only
def test_can_describe_s3_bucket(s3_client, config):
    """Verify permission to inspect S3 bucket."""
    try:
        s3_client.head_bucket(Bucket=config["state_bucket_name"])
    except ClientError as e:
        if e.response["Error"]["Code"] == "403":
            pytest.fail("No permission to inspect S3 bucket")
        if e.response["Error"]["Code"] != "404":
            raise
```

### Layer 4: State Tests (test_04_state.py)

Test that OpenTofu state matches AWS reality. Uses `opentofu_drift` from `lib/python/`.

```python
from opentofu_config import TEST_AWS_REGION
from opentofu_drift import check_resource_exists, get_planned_creates

def test_no_orphaned_resources():
    """Verify resources to be created don't already exist in AWS."""
    creates = get_planned_creates(OPENTOFU_DIR)
    orphaned = []
    for resource in creates:
        if check_resource_exists(resource["type"], resource["name"], TEST_AWS_REGION):
            orphaned.append(resource)
    if orphaned:
        msg = "\nOrphaned resources detected:\n"
        for r in orphaned:
            msg += f"  - {r['type']}: {r['name']}\n"
            msg += f"    Fix: tofu import {r['address']} {r['name']}\n"
        pytest.fail(msg)
```

**Cold state exception:** For bootstrap workflows, skip state tests if no prior state exists.

### Layer 5: Existence Tests (test_05_existence.py)

Test that prerequisite resources exist. Assumes authorization passed.

```python
def test_state_bucket_exists(s3_client, config):
    """Verify OpenTofu state bucket exists."""
    response = s3_client.head_bucket(Bucket=config["state_bucket_name"])
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
```

### Layer 6: Configuration Tests (test_06_configuration.py)

Test that prerequisite resources are configured correctly. Assumes existence passed.

```python
def test_state_bucket_has_encryption(s3_client, config):
    """Verify state bucket has encryption enabled."""
    response = s3_client.get_bucket_encryption(Bucket=config["state_bucket_name"])
    rules = response["ServerSideEncryptionConfiguration"]["Rules"]
    assert len(rules) > 0
```

### Layer 7: Capability Tests (test_07_capability.py)

Test that you can perform required operations. Assumes configuration passed.

```python
def test_can_write_to_state_bucket(s3_client, config):
    """Verify can write to OpenTofu state bucket."""
    test_key = f"test/{uuid.uuid4()}.txt"
    try:
        s3_client.put_object(
            Bucket=config["state_bucket_name"],
            Key=test_key,
            Body=b"test"
        )
    finally:
        try:
            s3_client.delete_object(Bucket=config["state_bucket_name"], Key=test_key)
        except ClientError:
            pass
```

**Always clean up in `finally` blocks.**

## Fail Fast with Granular Diagnostics

- Each test must be atomic: one assertion per test
- Tests must run in layer order (authentication before authorization before state before existence)
- When a test fails, the developer must know exactly where the chain broke
- Failure messages must include resource names and expected values

## Cleanup After Capability Tests

If testing write operations, delete test artifacts in `finally` blocks. No test artifacts should remain after test execution.

## Fixture Usage

Use fixtures to:
1. Create AWS clients once per module
2. Load configuration from shared config files
3. Cache resource identifiers discovered in earlier layers

## Why OpenTofu Plan is Not a Workflow Step

Layer 4 (State) tests replace the need for a separate `tofu plan` step in workflows.

### What Layer 4 Does

- Uses `opentofu_drift` library from `lib/python/`
- Runs `tofu plan` internally to detect planned creates
- Checks if those resources already exist in AWS
- Fails if orphaned resources detected (state drift)

### Why This is Better Than a Separate Plan Step

1. **Diagnostics**: Layer 4 tells you exactly which resources have drift
2. **Actionable**: Failure messages include `tofu import` commands
3. **Integrated**: Part of the test pyramid, not a separate manual step
4. **Granular**: Runs after authentication/authorization, so you know credentials work

## Workflow Step Ordering

```
1. Lint (pylint, mypy, yamllint, tflint)
2. Unit tests
3. Pre-deployment integration tests (layers 1-7)
4. OpenTofu apply
5. Post-deployment integration tests
6. E2E tests
```

## Quick Reference

| If you want to test... | Layer | File |
|------------------------|-------|------|
| Module refs match between files | 1. Contracts | test_01_contracts.py |
| Cross-file configuration consistency | 1. Contracts | test_01_contracts.py |
| AWS credentials valid | 2. Authentication | test_02_authentication.py |
| Can describe IAM role | 3. Authorization | test_03_authorization.py |
| Can head S3 bucket | 3. Authorization | test_03_authorization.py |
| OpenTofu state matches reality | 4. State | test_04_state.py |
| No orphaned resources | 4. State | test_04_state.py |
| IAM role exists | 5. Existence | test_05_existence.py |
| S3 bucket exists | 5. Existence | test_05_existence.py |
| Role has policy attached | 6. Configuration | test_06_configuration.py |
| Bucket has encryption | 6. Configuration | test_06_configuration.py |
| Can write to S3 | 7. Capability | test_07_capability.py |
| Can assume role | 7. Capability | test_07_capability.py |

## Workflow Reference

| Workflow | Prerequisites to Test | NOT Test (created by this workflow) |
|----------|----------------------|-------------------------------------|
| `bootstrap` | None (root) | State bucket, OIDC, CloudTrail, central logs |
| `www_redirect` | State bucket, OIDC role, hosted zone from bootstrap | CloudFront, ACM cert, Route 53 records, CloudFront Function |

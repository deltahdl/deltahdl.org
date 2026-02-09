# Test Architecture Overview

This document explains the test infrastructure, where to put common code, and what reusable utilities exist.

## Table of Contents

- [Test Hierarchy](#test-hierarchy)
- [Directory Scope](#directory-scope)
- [Reusable Utilities in lib/python/](#reusable-utilities-in-libpython)
  - [test_fixtures/](#test_fixtures)
  - [opentofu_config/](#opentofu_config)
  - [opentofu_drift/](#opentofu_drift)
  - [naming_conventions/](#naming_conventions)
  - [boto_mocks/](#boto_mocks)
- [Check Before You Create](#check-before-you-create)
- [Static Analysis in Workflows](#static-analysis-in-workflows)

## Test Hierarchy

Tests follow a cascading conftest.py pattern. Each level inherits from parents and adds specifics.

```
test/
├── conftest.py                              # Level 0: Path setup (lib/python)
├── bootstrap/
│   ├── conftest.py                          # Level 1: Bootstrap config parsing
│   ├── pre_deployment/
│   │   ├── unit/conftest.py                 # Level 2: Unit test fixtures
│   │   └── integration/conftest.py          # Level 2: Layer markers, AWS fixtures
│   └── post_deployment/
│       ├── integration/conftest.py          # Level 2: AWS clients, layer markers
│       └── e2e/conftest.py                  # Level 2: OIDC verification fixtures
└── www/
    └── redirect/
        ├── conftest.py                      # Level 1: Redirect config parsing
        ├── pre_deployment/
        │   ├── unit/conftest.py             # Level 2: Unit test fixtures
        │   └── integration/conftest.py      # Level 2: Layer markers, AWS fixtures
        └── post_deployment/
            ├── integration/conftest.py      # Level 2: CloudFront/ACM clients
            └── e2e/conftest.py              # Level 2: HTTP request fixtures
```

### Where to Put Common Things

| Scope | Location | Examples |
|-------|----------|----------|
| All tests | `test/conftest.py` | Path setup (already done) |
| All bootstrap tests | `test/bootstrap/conftest.py` | Config parsing from tfvars/locals |
| All redirect tests | `test/www/redirect/conftest.py` | CloudFront Function source, redirect config |
| Pre-deployment unit | `test/.../pre_deployment/unit/conftest.py` | File content fixtures |
| Pre-deployment integration | `test/.../pre_deployment/integration/conftest.py` | Layer markers, bootstrap fixtures |
| Post-deployment integration | `test/.../post_deployment/integration/conftest.py` | Layer markers, AWS service clients |

**Rule:** Put fixtures at the highest level where they apply. Don't duplicate.

## Directory Scope

Shared directories are for codebase-wide utilities, not module-specific code.

| Directory | Scope | Example Contents |
|-----------|-------|------------------|
| `lib/python/` | Entire codebase | `boto_mocks/`, `opentofu_config/`, `test_fixtures/aws.py` |
| `test/` root | All tests | `conftest.py` (path setup), codebase-wide test utilities |
| `test/<module>/` | Module-specific | `test/workflowctl/conftest.py`, inline `SAMPLE_GRAPH` constants |

**Key principle:** If a fixture or utility is only used by one module's tests, keep it within that module's test directory. Don't pollute shared directories with module-specific code.

## Reusable Utilities in lib/python/

Before creating new fixtures, check if they exist in `lib/python/`. Import via `pytest_plugins` or direct import.

### test_fixtures/

AWS fixtures ready to use via pytest plugin:

```python
# In conftest.py
pytest_plugins = ['test_fixtures.aws']

# Provides these fixtures:
# - shared_config: Parsed shared OpenTofu module config
# - aws_region: AWS region from config
# - state_bucket_name: OpenTofu state bucket
# - sts_client, iam_client, s3_client, ssm_client
# - cloudfront_client, route53_client, acm_client
# - caller_identity, current_role_arn, current_role_name
```

### opentofu_config/

Parse OpenTofu configuration as single source of truth:

```python
from opentofu_config import (
    get_shared_config,        # Combined locals + outputs
    parse_locals,             # Parse locals.tf
    parse_outputs,            # Parse outputs.tf
    get_resource_prefix,      # Resource naming prefix
    TEST_AWS_REGION,          # Standard region for test mocks
)
```

### opentofu_drift/

Detect orphaned resources (resources in AWS but not in OpenTofu state):

```python
from opentofu_drift import check_resource_exists, get_planned_creates
from opentofu_drift.test_helpers import create_orphaned_resource_tests

# Generate test class for orphaned resource detection
TestOrphanedResources = create_orphaned_resource_tests(
    opentofu_dir=OPENTOFU_DIR,
    region="us-east-2",
)
```

### naming_conventions/

Validate AWS resource names follow PascalCase:

```python
from naming_conventions import is_pascalcase, validate_name
from naming_conventions.test_helpers import (
    create_iam_role_tests,
)

# Generate parametrized naming tests
TestIAMNaming = create_iam_role_tests(role_names)
```

### boto_mocks/

Factory functions for boto3 mocks in unit tests:

```python
from boto_mocks import (
    create_client_error,      # Create ClientError for error testing
    create_boto_client_mock,  # Create flexible boto3.client mock
)
```

## Check Before You Create

Before writing new fixtures or utilities:

1. **Check parent conftest files** - The fixture may already exist at a higher level
2. **Check lib/python/** - Reusable utilities may already solve your problem
3. **Check test_fixtures.aws** - Common AWS fixtures are already available

If your fixture is useful beyond your specific test file:
- Put it in the appropriate conftest.py level
- Or add it to lib/python/ if it's broadly reusable

## Static Analysis in Workflows

Linting and type checking run on test code and shared libraries.

### Required Workflow Steps

| Step Name | Target |
|-----------|--------|
| `Run pylint on tests` | `lib/python/` and `test/.../` (with `PYTHONPATH=lib/python`) |
| `Run mypy on tests` | `lib/python/` and `test/.../` (with `MYPYPATH=lib/python`) |

### Why Separate PYTHONPATH?

Tests need `PYTHONPATH`/`MYPYPATH` set to resolve `lib/python/` imports. This ensures consistent import resolution across local development and CI.

### Example

```yaml
- name: Run pylint on tests
  run: |
    PYTHONPATH=lib/python:. python3 -m pylint \
      lib/python/ test/conftest.py test/bootstrap/ test/www/ \
      --fail-on=C,R,W \
      --fail-under=10.0
- name: Run mypy on tests
  run: |
    MYPYPATH=lib/python python3 -m mypy \
      lib/python/ test/conftest.py test/bootstrap/ test/www/
```

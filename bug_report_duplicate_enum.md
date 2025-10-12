# Bug Report: Duplicate Enum Value in Firefly III OpenAPI Spec 6.4.0

## Summary

The Firefly III OpenAPI specification version 6.4.0 contains a duplicate enum value in the `UserGroupReadRole` enum, which causes issues when generating client libraries.

## Environment

- **Firefly III API Version**: 6.4.0
- **OpenAPI Spec URL**: https://api-docs.firefly-iii.org/firefly-iii-6.4.0-v1.yaml
- **Generated Client**: firefly-iii-client Python library

## Issue Description

The `UserGroupReadRole` enum contains a duplicate `OWNER = 'owner'` value, which appears twice in the generated Python client code:

```python
class UserGroupReadRole(str, Enum):
    """
    The possible roles of the user in this user group are documented here: https://docs.firefly-iii.org/references/firefly-iii/api/
    """

    """
    allowed enum values
    """
    RO = 'ro'
    MNG_TRX = 'mng_trx'
    MNG_META = 'mng_meta'
    READ_BUDGETS = 'read_budgets'
    READ_PIGGIES = 'read_piggies'
    READ_SUBSCRIPTIONS = 'read_subscriptions'
    READ_RULES = 'read_rules'
    READ_RECURRING = 'read_recurring'
    READ_WEBHOOKS = 'read_webhooks'
    READ_CURRENCIES = 'read_currencies'
    MNG_BUDGETS = 'mng_budgets'
    MNG_PIGGIES = 'mng_piggies'
    MNG_SUBSCRIPTIONS = 'mng_subscriptions'
    MNG_RULES = 'mng_rules'
    MNG_RECURRING = 'mng_recurring'
    MNG_WEBHOOKS = 'mng_webhooks'
    MNG_CURRENCIES = 'mng_currencies'
    VIEW_REPORTS = 'view_reports'
    VIEW_MEMBERSHIPS = 'view_memberships'
    FULL = 'full'
    OWNER = 'owner'  # ← First occurrence
    OWNER = 'owner'  # ← Duplicate occurrence (causes Python syntax error)
```

## Impact

- **Severity**: Medium
- **Affected Components**: Generated client libraries (Python, and potentially other languages)
- **Symptoms**:
  - Python syntax error when importing the generated client
  - `SyntaxError: duplicate keyword argument` or similar
  - Client library fails to load/import

## Root Cause

The OpenAPI specification likely contains the `owner` value twice in the enum definition for `UserGroupReadRole`, causing the OpenAPI Generator to create duplicate enum entries in the generated code.

## Expected Behavior

The `UserGroupReadRole` enum should contain each value only once:

```python
class UserGroupReadRole(str, Enum):
    # ... other values ...
    FULL = 'full'
    OWNER = 'owner'  # Only one occurrence
```

## Workaround

For client library maintainers, the duplicate line can be manually removed from the generated code:

```python
# Remove the duplicate line:
# OWNER = 'owner'
```

## Steps to Reproduce

1. Download the Firefly III 6.4.0 OpenAPI spec: https://api-docs.firefly-iii.org/firefly-iii-6.4.0-v1.yaml
2. Generate a Python client using OpenAPI Generator
3. Attempt to import the generated client
4. Observe the syntax error due to duplicate enum value

## Suggested Fix

The Firefly III team should review the OpenAPI specification and ensure that the `UserGroupReadRole` enum contains each value only once. The duplicate `owner` value should be removed from the source specification.

## Additional Information

- This issue was discovered during the upgrade of firefly-iii-client to support Firefly III API 6.4.0
- The same issue was present in previous versions and was manually fixed in commit b9e36ac
- This suggests the issue is in the upstream OpenAPI specification rather than the client generation process

## Related

- Previous fix: https://github.com/jochemvangrondelle/firefly-iii-client/commit/b9e36ac
- Firefly III API Documentation: https://docs.firefly-iii.org/references/firefly-iii/api/

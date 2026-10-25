# Northstar demo deployment guide
This is a fictional deployment guide, not an operational production runbook.

## Release process
A production release requires a passing test suite and approval from one maintainer.
The staging environment uses the same database schema as production with synthetic data.

## Rollback
Rollback restores the previously approved application version.
Database schema changes need a separately reviewed migration and rollback plan.

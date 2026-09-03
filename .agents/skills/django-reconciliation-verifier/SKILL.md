---
name: django-reconciliation-verifier
description: Review Django payout-reconciliation changes for domain correctness, safe CSV imports, security, and sufficient verification. Use after implementing or changing this service; do not use for unrelated Django work.
---

# Django Reconciliation Verifier

Review the changed implementation against `AGENTS.md`, every applicable file in
`.agents/rules/`, and the active feature plan, including its verification
requirements. Report concrete findings before suggesting optional improvements.

## Required review

- Confirm orders are treated as the source of truth and no read endpoint
  recalculates reconciliation results.
- Confirm monetary input is converted from strings to `Decimal` and persisted
  with `DecimalField`; reject any use of float-based money comparison.
- Confirm imports validate the whole CSV and use an atomic transaction so a bad
  row cannot create a partial import.
- Confirm reconciliation status precedence, including the supplied amount,
  currency, and missing-order cases.
- Review upload validation, exposed errors, secrets/configuration, and tests for
  security and regression risks.

## Review output

Separate findings into `Blocking`, `Important`, and `Optional`. For each
blocking or important finding, give the affected file and a concise reason.
State which verification evidence was inspected and list any missing checks.

Do not mark a phase complete. The implementation owner updates the feature plan
only after resolving blocking findings and recording validation evidence.

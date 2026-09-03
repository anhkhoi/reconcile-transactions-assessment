# Repository instructions

## Current state

This repository is not yet implemented. It contains the assessment brief and
sample data under `requirements/`, an empty `postman/` directory, and `note.md`.
There is no Django project, `manage.py`, or dependency manifest yet. Project
bootstrap is part of the task.

## Assignment

Build a Django + Django REST Framework service using SQLite or PostgreSQL.

- `POST /api/payouts/upload`: accept a payout CSV with
  `provider,order_number,amount,currency` and return the count of imported records.
- Reconcile payouts against orders using `order_number`.
- Persist reconciliation results with statuses: `Matched`, `Missing Order`,
  `Amount Mismatch`, and optionally `Currency Mismatch`.
- `GET /api/reconciliation`: return each payout's `order_number` and status.
- Add README setup instructions, a discussion of scaling to 500,000 records and
  relevant AWS services, production-readiness improvements, and an AI-usage
  disclosure.
- Include tests, a sample CSV, and a Postman collection in `postman/`.

## Repository rules

Before making changes, read and follow every Markdown file in
`.agents/rules/`. These reviewer-visible documents contain the repository's
domain, implementation, validation, security, and Python/Django standards.

# Django Implementation Rules

- Parse CSV money values directly from strings into `Decimal`; use Django
  `DecimalField` for persisted monetary values. Do not use `float` or
  `FloatField` for monetary data.
- Validate the complete upload before writing it. Create payouts and their
  reconciliation results in one atomic database transaction, so an invalid row
  cannot leave a partial import.
- Keep reconciliation logic outside views so it can be tested independently and
  reused by a future asynchronous import worker.
- Do not recalculate results in `GET /api/reconciliation`; read the persisted
  reconciliation result instead.
- Add or update model, service, and API tests for every behavior change. A
  generated implementation has the same validation and review requirements as
  hand-written code.

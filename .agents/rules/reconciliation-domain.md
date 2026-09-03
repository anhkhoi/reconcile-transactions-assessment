# Reconciliation Domain Rules

- Orders are the source of truth.
- Compare monetary values using `Decimal`, never floating-point values.
- Store reconciliation results and rerun reconciliation on payout import; do not
  compute results on every `GET /api/reconciliation` request.
- The supplied sample cases must produce:
  - `100003`: `Amount Mismatch`
  - `100009`: `Currency Mismatch`
  - `100011`, `100012`: `Missing Order`

# Payout Reconciliation Service

A Django + Django REST Framework service that imports payout CSV rows,
reconciles them against source-of-truth orders, stores each outcome, and exposes
the persisted results. SQLite is the local development database.

## Setup and run

Prerequisite: Python 3.12 or newer.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_orders
python manage.py runserver
```

`seed_orders` loads the ten supplied orders from `requirements/orders.csv` and
is safe to rerun: it updates orders by `order_number`. The local server runs at
`http://127.0.0.1:8000`; its ignored SQLite database is `db.sqlite3`.

### Configuration

Local development defaults to `DJANGO_DEBUG=true`. For a non-local environment,
export a real secret and allowed hosts before starting Django:

```bash
export DJANGO_DEBUG=false
export DJANGO_SECRET_KEY='replace-with-a-long-random-secret'
export DJANGO_ALLOWED_HOSTS='api.example.com'
```

[.env.example](.env.example) documents available variables, but it is a
reference template only: this project does not automatically load `.env` files.
`DJANGO_SECRET_KEY` is required whenever debug mode is disabled.

## API

### `POST /api/payouts/upload`

Send multipart form-data with a `file` field. The default upload limit is 5 MiB;
when a content type is supplied it must be `text/csv` or `application/csv`.
The CSV header must be exactly:

```text
provider,order_number,amount,currency
```

Rows are fully parsed and validated as `Decimal` values before a transaction
creates a `Payout` and its persisted `ReconciliationResult`. Re-uploading a
file intentionally creates new payout rows for this assessment.

```bash
curl -X POST http://127.0.0.1:8000/api/payouts/upload \
  -F 'file=@requirements/payouts.csv;type=text/csv'
```

Success returns `201`:

```json
{"imported_count": 9}
```

Malformed headers, invalid or missing values, empty/absent files, oversized
files, and rejected MIME types return `400` with client-safe errors. Failed
uploads never leave a partial import.

### `GET /api/reconciliation`

Returns only stored results, ordered by `order_number` and result ID. It never
recalculates on read.

```bash
curl http://127.0.0.1:8000/api/reconciliation
```

```json
{"order_number": "100003", "status": "Amount Mismatch"}
```

Import precedence is `Missing Order`, `Currency Mismatch`, `Amount Mismatch`,
then `Matched`. The supplied sample produces `Amount Mismatch` for `100003`,
`Currency Mismatch` for `100009`, and `Missing Order` for `100011` and `100012`.

## Data model

The three assessment-domain tables are:

- `reconciliation_order`: source-of-truth order number, total amount, currency.
- `reconciliation_payout`: one imported CSV row.
- `reconciliation_reconciliationresult`: one-to-one persisted payout status.

`auth_*`, `django_*`, and `django_session` are standard Django infrastructure
tables created by enabled framework apps, not assessment-domain tables.

## Tests

Run the isolated test suite:

```bash
python manage.py test reconciliation
```

Useful preflight checks:

```bash
python manage.py makemigrations --check
python manage.py check
```

Coverage includes model constraints, order seeding, all statuses and precedence,
Decimal-safe comparison, full-file validation, transactional failure behavior,
upload validation, and persisted read behavior.

## Postman

1. Start the service and run `python manage.py seed_orders`.
2. Import [the collection](postman/payout-reconciliation.postman_collection.json).
3. Import/select [the local environment](postman/payout-reconciliation.local.postman_environment.json).
4. In **Upload payouts CSV**, select [postman/payouts.csv](postman/payouts.csv)
   for the multipart `file` field if Postman does not resolve its relative path.
5. Run **Upload payouts CSV**, then **Get reconciliation results**.

The collection asserts `201`, `imported_count: 9`, `200`, and the four required
outcomes. With the server running, it can also run through Newman:

```bash
npx -y newman@6.2.1 run postman/payout-reconciliation.postman_collection.json \
  -e postman/payout-reconciliation.local.postman_environment.json
```

## Scaling to 500,000 records

The synchronous local SQLite flow is intentionally small. At 500,000 records,
use asynchronous jobs and PostgreSQL.

| Concern | Production approach |
| --- | --- |
| File intake | Store files in S3 through pre-signed uploads; create an import record with checksum, owner, and idempotency key. |
| Parsing | Stream CSV rows in chunks; validate chunks and retain per-row errors in an import report. |
| Database work | Use PostgreSQL indexed order lookups, bounded `bulk_create` batches, and a staging table with `COPY`/set-based joins at higher throughput. |
| Execution | Publish jobs through SQS or EventBridge and scale independent workers. |
| Results API | Use cursor pagination, import filtering, tenant authorization, and indexed ordering. |
| Reliability | Persist import states, idempotency keys, retry policy, dead-letter handling, and replay-safe result creation. |

Suitable AWS services: S3 for files; SQS or EventBridge for jobs; ECS/Fargate
workers for long-running imports (Lambda for short bounded jobs); RDS PostgreSQL;
CloudWatch for logs, metrics, and alarms; IAM for least privilege; and Secrets
Manager for configuration secrets.

## Production readiness

Before deployment, add:

- Authentication, role/tenant authorization, rate limits, and audit logs.
- TLS, restrictive CORS, `DEBUG=false`, secure configuration, and secret rotation.
- Object-storage uploads, stricter content inspection/anti-malware scanning,
  quotas, and a durable import/error-report lifecycle.
- Idempotency keys, retries, dead-letter queues, and operator tooling for failures.
- Structured logs, correlation IDs, metrics, traces, error monitoring, alerts,
  dashboards, CI checks, dependency scanning, migration controls, backups,
  restore drills, and disaster-recovery testing.

## Validation performed

During implementation:

- `python manage.py migrate` succeeded on a fresh SQLite database.
- `python manage.py makemigrations --check` reported no changes.
- `python manage.py check` reported no issues.
- `python manage.py test reconciliation` created/destroyed an isolated test DB;
  the final validation run passed 23 tests.
- Local HTTP smoke tests returned `201 {"imported_count":9}` for the supplied
  payout file, `400` for an invalid header, and the expected persisted results.
- Newman completed 2 requests and 4 assertions with 0 failures.
- The focused Django reconciliation review had no blocking or important findings.

## AI usage disclosure

AI assistance (Codex) helped plan, scaffold, implement, test, review, and
document this assessment. The resulting work was checked against repository
rules, exercised with Django tests and local HTTP/Postman runs, and reviewed for
domain correctness, transactional behavior, validation, and security concerns.

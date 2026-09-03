# Reconciliation Service Plan

## Purpose

Build a small Django and Django REST Framework service that imports payout CSV
records, reconciles them against existing orders, stores the resulting status,
and exposes those persisted results. SQLite will be used for local development.

## Planning Artifacts

This feature folder keeps planning material and later validation evidence
together. The source assessment PDF and CSVs remain in
[`requirements/`](../../requirements/); they are referenced rather than copied.

Use [`resources/`](resources/) for feature-specific artifacts that cannot live
in the main source tree, such as API examples, review notes, or validation
screenshots. Do not commit credentials, generated databases, or redundant
copies of supplied input files.

## Scope and Completion Definition

The first version is a local, single-service Django application backed by
SQLite. It deliberately exposes only the two endpoints required by the
assessment; it will not add an order-management API, user interface, background
worker, or cloud deployment.

The implementation is complete when a developer can follow the README to seed
orders, start the server, upload `requirements/payouts.csv` through Postman,
and retrieve the four expected reconciliation outcomes. Automated tests and the
Postman assertions must pass.

## Phase Tracking Rules

This plan is designed to be implemented over multiple work sessions. The
current phase state must always be visible in the table below.

| Phase | Status | Mark complete only after |
| --- | --- | --- |
| 1. Quality guardrails | Complete | The phase's **Done when** criteria pass. |
| 2. Bootstrap | Complete | The phase's **Done when** criteria pass. |
| 3. Persist domain | Complete | The phase's **Done when** criteria pass. |
| 4. Reconcile and store outcomes | Complete | The phase's **Done when** criteria pass. |
| 5. API contract | Complete | The phase's **Done when** criteria pass. |
| 6. Postman assets | Complete | The phase's **Done when** criteria pass. |
| 7. Tests and generated-code review | Complete | The phase's **Done when** criteria pass. |
| 8. Documentation and production design | Complete | The phase's **Done when** criteria pass. |

**Update rule:** before ending a work session, update the relevant status to
`In progress`, `Blocked`, or `Complete`. A phase may be changed to `Complete`
only after its stated acceptance criteria have been run and the result is
recorded in the phase notes or final validation evidence. If the implementation
or validation uncovers a new decision, update this plan before starting the
next phase. Do not mark a phase complete merely because code was written.

## Verification Requirements for This Plan

Apply the relevant checks before completing each implementation phase:

1. Run Django system checks and apply migrations to a clean local database when
   models or settings change.
2. Run the relevant automated tests. New reconciliation behavior requires
   model, service, and API coverage as applicable.
3. Exercise changed HTTP endpoints locally. For payout imports, test a valid
   CSV and at least one invalid CSV; verify a failed upload writes no data.
4. Run the Postman collection or an equivalent repeatable HTTP smoke script
   once Postman assets exist.
5. Run the generated-code review and resolve blocking correctness or security
   findings before marking the affected phase complete.

The final service must also confirm that money uses `Decimal`, orders remain the
source of truth, results are stored during import, and the supplied data returns
`Amount Mismatch` for `100003`, `Currency Mismatch` for `100009`, and `Missing
Order` for `100011` and `100012`.

## Requirements Confirmed

- `POST /api/payouts/upload` accepts a CSV with `provider`, `order_number`,
  `amount`, and `currency`, and returns the number of imported records.
- Payouts are reconciled using `order_number`; orders are the source of truth.
- Reconciliation outcomes are persisted, not calculated on each read.
- `GET /api/reconciliation` returns each payout's `order_number` and status.
- Required statuses are `Matched`, `Missing Order`, and `Amount Mismatch`.
  `Currency Mismatch` will also be implemented because the supplied sample data
  explicitly requires it.
- Money comparisons must use `Decimal`, never binary floating-point values.
- Deliverables include tests, sample CSV data, Postman assets, README setup and
  design discussion, and an AI-use disclosure.

## Implementation Phases

### 1. Establish quality guardrails

Before implementation begins, make the quality expectations enforceable and
discoverable:

- Confirm the durable domain, implementation, validation, security, and
  Python/Django rules are clear and reviewer-visible in `.agents/rules/`.
- Define the generic evidence requirement in `plans/README.md` and the
  Django-specific checks in this feature plan.
- Record focused security rules: no committed secrets, debug mode only for local
  development, upload-size and content-type checks, CSV field validation, and
  authentication before production deployment.
- Define the review criteria that the later generated-code reviewer must apply:
  domain correctness, data integrity, validation/security, test coverage, and
  regression risk.

**Done when:** the repository has clear, reviewable rules and a verification
checklist that apply to every implementation phase. No application code starts
until this phase is complete.

**Phase notes:** Complete on 2026-09-04.

- Moved repository rules from `AGENTS.md` into reviewer-visible documents in
  `.agents/rules/`; `AGENTS.md` now provides repository context and a rules
  index.
- Added reviewer-visible Python and Django engineering rules in
  `.agents/rules/python-django.md` for pragmatic SOLID/DRY design, clear
  layers, loose coupling, explicit error handling, intentional ORM use, and
  testability.
- Consolidated the former verification guide into the generic
  phase-completion evidence rule in `plans/README.md` and the
  reconciliation-specific checks in this feature plan; removed the redundant
  standalone guide.
- Created `.agents/skills/django-reconciliation-verifier/` with an explicit
  reviewer workflow and review-output requirements. Codex discovers
  repository-scoped skills from `.agents/skills`.
- Manually confirmed required files, skill front matter, absence of scaffold
  TODOs, and whitespace with `git diff --check`.
- The supplied skill validator could not run because `PyYAML` is unavailable in
  the local environment. No dependency was installed solely for this document
  and skill-source change.

### 2. Bootstrap the application

- Create the Django project and a `reconciliation` application in the
  repository root.
- Add a dependency manifest for Django and Django REST Framework.
- Configure SQLite for local use, plus migrations and a test configuration.
- Keep environment-specific settings out of version control.

Expected initial layout:

```text
manage.py
config/                         # Django settings and root URL configuration
reconciliation/
  migrations/
  management/commands/          # Seed orders command
  models.py
  services.py                   # CSV parsing and reconciliation logic
  serializers.py
  views.py
  urls.py
  tests/
requirements/
postman/
```

**Done when:** `python manage.py migrate` succeeds against a fresh SQLite
database and Django's test runner discovers the app tests.

**Phase notes:** Complete on 2026-09-04.

- Added the Django project, `reconciliation` app skeleton, SQLite settings,
  dependency manifest, local-only environment example, and ignored local state.
- Installed Django 5.2.17 and Django REST Framework 3.16.1 into a local
  ignored `.venv` from `requirements.txt`.
- On a fresh `db.sqlite3`, `.venv/bin/python manage.py migrate` applied all
  built-in Django migrations successfully.
- `.venv/bin/python manage.py check` completed with no issues, and
  `.venv/bin/python manage.py test reconciliation` discovered and passed two
  bootstrap tests using Django's isolated test database.
- The Django reconciliation verifier reviewed the scaffold. It identified a
  production-secret fallback risk; settings now fail closed when debug is
  disabled and `DJANGO_SECRET_KEY` is absent. No unresolved blocking or
  important findings remain for this phase.

### 3. Persist the domain

Create these models:

- `Order`: `order_number`, `total_amount`, and `currency`.
- `Payout`: `provider`, `order_number`, `amount`, and `currency`.
- `ReconciliationResult`: a one-to-one result for each payout, with its status
  and timestamps.

Amounts will use `DecimalField` with an appropriate fixed precision. Order
numbers will be stored as strings so identifiers are not altered by numeric
conversion.

The service needs known orders but does not require an orders API. The supplied
`requirements/orders.csv` will therefore be loaded via a documented management
command as local seed data.

Decisions to make explicit in implementation:

- `order_number` is unique for `Order` and indexed for reconciliation lookup.
- A `Payout` represents one CSV row. Re-uploading a file creates new payout
  records; it is not silently deduplicated in this assessment version.
- A payout has exactly one persisted `ReconciliationResult`.
- Currency is stored as a three-character ISO code; the service validates its
  shape locally. Full ISO allow-list validation can be introduced later if the
  business requires it.

**Done when:** migrations describe the three models, the seed command imports
the supplied ten orders, and model-level tests confirm key constraints.

**Phase notes:** Complete on 2026-09-04.

- Added `Order`, `Payout`, and one-to-one `ReconciliationResult` models with
  fixed-precision `DecimalField` amounts, unique/indexed order lookup,
  currency-shape validation, non-negative amount constraints, result statuses,
  and result timestamps.
- Added and applied `reconciliation.0001_initial` locally; Django reports no
  pending model changes.
- Added `seed_orders`, which parses the supplied CSV into `Decimal` values and
  validates every row before atomically creating or updating source-of-truth
  orders. Running it against `requirements/orders.csv` reported `Seeded 10
  orders.` and confirmed a count of 10.
- `.venv/bin/python manage.py check` completed with no issues, and
  `.venv/bin/python manage.py test reconciliation` passed all 9 bootstrap,
  model, and seed-command tests.
- The Django reconciliation verifier found no blocking or important Phase 3
  findings. Upload transaction behavior, reconciliation precedence, and API
  read behavior remain intentionally scoped to Phases 4 and 5.

### 4. Reconcile and store outcomes

On each successful payout import, create the payouts and reconciliation results
in a database transaction. The import should validate the whole CSV before
committing so malformed data does not leave a partial import behind.

Use this documented precedence when a row has more than one discrepancy:

1. `Missing Order` when there is no matching order.
2. `Currency Mismatch` when the matching order has a different currency.
3. `Amount Mismatch` when currencies match but Decimal amounts differ.
4. `Matched` otherwise.

The supplied samples must produce:

| Order number | Expected status |
| --- | --- |
| `100003` | `Amount Mismatch` |
| `100009` | `Currency Mismatch` |
| `100011` | `Missing Order` |
| `100012` | `Missing Order` |

Implementation sequence:

1. Parse the uploaded file as UTF-8 CSV and confirm its required header.
2. Normalize and validate every row into in-memory input values, including
   `Decimal` conversion, before writing data.
3. Start an atomic database transaction.
4. Create payout records, look up their orders, determine each status, and
   create the matching reconciliation results.
5. Commit only if every row is valid; otherwise return a row-specific `400`
   error and write nothing.

**Done when:** a service-level test proves all four statuses, Decimal equality,
and no partial records after a failed upload.

**Phase notes:** Complete on 2026-09-04.

- Added a service-layer UTF-8 CSV parser that requires the documented header,
  validates and normalizes every row into in-memory `Decimal` input values,
  and produces client-safe, row-specific validation errors.
- Added transactional payout import that batch-loads source-of-truth orders,
  persists each payout and one reconciliation result, and applies the documented
  precedence: missing order, currency mismatch, amount mismatch, then matched.
  Re-uploads intentionally create additional payout records.
- `.venv/bin/python manage.py makemigrations --check` reported no changes,
  `.venv/bin/python manage.py check` completed with no issues, and
  `.venv/bin/python manage.py test reconciliation` passed all 15 tests.
  Coverage includes the supplied four outcomes, Decimal equality, precedence,
  invalid header/error handling, re-upload behavior, and no partial records
  after an invalid row.
- The Django reconciliation verifier found no blocking or important Phase 4
  issues. HTTP upload-size/content-type checks and HTTP error mapping remain
  intentionally scoped to Phase 5.

### 5. Implement the API contract

#### `POST /api/payouts/upload`

- Accept a multipart upload using a `file` field.
- Require the CSV header `provider,order_number,amount,currency`.
- Validate required values, decimal format, and currency values before import.
- Return a successful response such as `{"imported_count": 9}`.
- Return useful `400` validation errors for empty files, invalid headers, or
  invalid rows.
- Enforce a local upload-size limit and reject non-CSV content types where the
  client provides one.

#### `GET /api/reconciliation`

- Return persisted reconciliation data, including each payout's `order_number`
  and its `status`.
- Do not perform reconciliation work in this endpoint.
- Use a stable ordering. Pagination can remain lightweight locally and become a
  production requirement as record volume grows.

The initial read response will be a JSON array (or DRF's configured paginated
wrapper) whose records contain at least:

```json
{"order_number": "100003", "status": "Amount Mismatch"}
```

No calculated values, raw CSV contents, or internal exception details will be
returned.

**Done when:** API tests cover a valid multipart upload, bad input returning
`400`, and a results read that retrieves the stored statuses without invoking
new reconciliation work.

**Phase notes:** Complete on 2026-09-04.

- Added `POST /api/payouts/upload`, using multipart `file` input, local upload
  size and supplied content-type validation, and client-safe `400` responses
  for service-level CSV errors. A successful import returns `201` with only
  `{"imported_count": <count>}`.
- Added `GET /api/reconciliation`, which uses `select_related` and a stable
  order-number/result-id ordering to serialize only persisted `order_number`
  and `status` values; it does not rerun reconciliation.
- Added API tests for valid multipart upload, invalid row and empty upload
  errors with no writes, rejected non-CSV content type and oversized file, and
  persisted/stably ordered results after the source order changes.
- `.venv/bin/python manage.py makemigrations --check` reported no changes,
  `.venv/bin/python manage.py check` completed with no issues, and
  `.venv/bin/python manage.py test reconciliation` passed all 21 tests.
- Ran the local server after `seed_orders`. `curl` upload of
  `requirements/payouts.csv` returned `201 {"imported_count":9}`; uploading
  `requirements/orders.csv` returned the expected header `400`; the final
  results read returned 9 stored outcomes, including the four required sample
  statuses. The temporary server was stopped after verification.
- The Django reconciliation verifier found no blocking or important Phase 5
  findings. Consumer Postman coverage remains intentionally scoped to Phase 6.

### 6. Create Postman assets

Store all Postman deliverables in `postman/`:

- A collection with the upload and reconciliation requests.
- A local environment containing `baseUrl`, for example
  `http://127.0.0.1:8000`.
- Collection assertions for the upload response and all supplied expected
  reconciliation statuses.
- A copy of the sample payout CSV ready to choose in Postman's upload field.

Collection execution order:

1. Run the documented order-seed command once.
2. Send **Upload payouts CSV** with multipart key `file`.
3. Assert HTTP success and `imported_count: 9`.
4. Send **Get reconciliation results**.
5. Assert the four required order-number/status pairs.

**Done when:** a fresh machine can import the collection and environment, make
these requests against the local server, and receive passing assertions.

**Phase notes:** Complete on 2026-09-04.

- Added a Postman v2.1 collection with multipart **Upload payouts CSV** and
  **Get reconciliation results** requests, a local environment with `baseUrl`,
  and the supplied payout sample copied to `postman/payouts.csv`. The upload
  request references that repository-relative file and explains the manual
  selection fallback for Postman clients that cannot resolve it.
- Collection assertions require `201` and `imported_count: 9`, then `200` and
  the four required order-number/status pairs.
- Parsed both Postman JSON assets with Node and confirmed
  `postman/payouts.csv` is identical to `requirements/payouts.csv`.
- Started the local service after `seed_orders` and ran
  `npx -y newman@6.2.1 run postman/payout-reconciliation.postman_collection.json
  -e postman/payout-reconciliation.local.postman_environment.json`. The run
  completed 2 requests and 4 assertions with 0 failures. The temporary server
  was stopped after verification.

### 7. Test the service and review generated code

Add automated tests for:

- Every reconciliation status and the status-precedence rule.
- Decimal-safe amount comparison.
- Valid CSV upload and imported-record count.
- Invalid headers, malformed decimal values, missing required fields, and empty
  uploads.
- Transactional behavior: an invalid row must not partially import the file.
- The results endpoint returning stored, rather than freshly calculated, data.

Test layers and responsibility:

| Layer | What it proves |
| --- | --- |
| Model tests | constraints and Decimal storage |
| Service tests | parsing, status calculation, precedence, transaction behavior |
| API tests | request validation, response contract, and persisted results |
| Postman assertions | repeatable consumer-facing happy-path verification |

Complete or refine the focused reviewer skill, for example
`.agents/skills/django-reconciliation-verifier/SKILL.md`, and use it for an
independent senior-engineer review. It must check:

- domain-rule and Decimal correctness;
- model constraints, transactions, and persisted-result behavior;
- CSV validation, file-upload limits, and error handling;
- test coverage and regression risk; and
- concise, actionable review findings.

**Done when:** all automated tests run against an isolated test SQLite database
and report a clean pass, and the generated-code review has no unresolved
high-severity correctness or security finding.

**Phase notes:** Complete on 2026-09-04.

- Added explicit API tests for a CSV row with a missing required value and for
  a missing multipart `file`, both returning `400` without persisting payouts
  or results. Existing model, service, API, and Postman tests cover the
  remaining Phase 7 scenarios.
- `.venv/bin/python manage.py makemigrations --check` reported no changes,
  `.venv/bin/python manage.py check` completed with no issues, and
  `.venv/bin/python manage.py test reconciliation` created an isolated test
  SQLite database and passed all 23 tests.
- Performed the independent Django reconciliation verifier review of models,
  import service, serializers, views, URLs, and test inventory. **Blocking:**
  none. **Important:** none. **Optional:** accept additional common CSV MIME
  aliases only if a future client requires them. The review confirmed
  Decimal-only money handling, source-of-truth order lookups, full-file
  validation before atomic writes, status precedence, persisted read behavior,
  upload controls, and regression coverage.

### 8. Document setup and production design

The README will cover:

- Python environment setup, dependency installation, migrations, order seeding,
  server start, tests, and Postman collection import.
- Scaling to 500,000 records: chunked parsing/bulk inserts, indexed lookup,
  pagination, asynchronous workers, and a move to PostgreSQL.
- Suitable AWS services: S3 for files, SQS or EventBridge for asynchronous work,
  ECS/Fargate workers (or Lambda where suitable), RDS PostgreSQL, CloudWatch,
  IAM, and Secrets Manager.
- Production hardening: authentication and authorization, upload limits,
  idempotency/retries, observability, CI, backups, error monitoring, and rate
  limits.
- A brief AI-use disclosure and a list of the actual validation performed.

**Done when:** the README gives a new reviewer enough information to set up,
run, test, and assess the service and honestly records the validation evidence.

**Phase notes:** Complete on 2026-09-04.

- Replaced the planning-era README with setup, configuration, seed/server,
  endpoint, testing, Postman, data-model, scaling, AWS, production-hardening,
  validation, and AI-use documentation. It explicitly distinguishes the three
  domain tables from Django infrastructure tables and explains that
  `.env.example` is not auto-loaded.
- Final checks: `.venv/bin/python manage.py makemigrations --check` reported
  no changes; `.venv/bin/python manage.py check` reported no issues; and
  `.venv/bin/python manage.py test reconciliation` created an isolated SQLite
  test database and passed all 23 tests.
- Parsed the Postman collection/environment JSON and confirmed the copied
  Postman payout CSV matches the supplied source CSV. After `seed_orders`, ran
  `npx -y newman@6.2.1 run postman/payout-reconciliation.postman_collection.json
  -e postman/payout-reconciliation.local.postman_environment.json`; 2 requests
  and 4 assertions passed with 0 failures. The temporary local server was
  stopped after validation.

## Execution Order

Implement in this order to avoid building the API around unverified business
logic:

1. Establish quality guardrails and the verification checklist.
2. Bootstrap project, dependencies, settings, and migrations.
3. Add models and the order seed command; verify seeded source data.
4. Write reconciliation service tests first, then implement the service.
5. Add upload serializer/view/URL and API tests.
6. Add results serializer/view/URL and API tests.
7. Create the Postman collection and environment; run them against the local
   server.
8. Run automated tests and the generated-code review; address findings.
9. Write the README, scale/AWS discussion, production improvements, and AI-use
   disclosure using the validation evidence actually gathered.
10. Run this plan's verification requirements and record command output in the
    final handoff.

## Completion Evidence

After implementation, report the exact validation commands and their outcomes.
At minimum this will include the Django test command and a Postman collection
run (or equivalent reproducible HTTP checks), with the expected sample statuses
verified.

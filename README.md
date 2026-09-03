# Payout Reconciliation Service

A Django and Django REST Framework assessment project for importing payout CSV
files and reconciling them against orders. SQLite is the local database.

> **Current status:** Phase 2 (application bootstrap) is complete; the domain,
> reconciliation workflow, and API phases remain to be implemented.
> The detailed delivery plan is in
> [plans/001-reconciliation-service/FEATURE-PLAN.md](plans/001-reconciliation-service/FEATURE-PLAN.md).

## Proposed Project Structure

```text
.
├── config/                         # Django settings and root URLs
├── reconciliation/
│   ├── migrations/                 # Database migrations
│   ├── management/commands/        # Local order-seed command
│   ├── tests/                      # Model, service, and API tests
│   ├── models.py                   # Order, Payout, and result models
│   ├── services.py                 # CSV import and reconciliation logic
│   ├── serializers.py              # Request and response validation
│   ├── urls.py
│   └── views.py
├── postman/                        # Collection, environment, and sample upload CSV
├── plans/
│   ├── README.md                    # Numbering convention for all work plans
│   └── 001-reconciliation-service/
│       ├── FEATURE-PLAN.md          # Reviewed implementation plan
│       └── resources/               # Plan-specific evidence and references
├── requirements/                   # Assessment brief and supplied source CSVs
├── .agents/
│   ├── rules/                      # Reviewer-visible repository rules
│   │   ├── reconciliation-domain.md
│   │   ├── django-implementation.md
│   │   ├── python-django.md
│   │   ├── security.md
│   │   └── validation.md
│   └── skills/                     # Repository-scoped Codex skills
├── AGENTS.md                       # Repository context and rules index
├── README.md
└── manage.py
```

## How I Work

I use a plan-first, iterative workflow to reduce ambiguity before writing code:

1. Read the brief and inspect supplied data.
2. Create the next numbered work folder under `plans/`, with
   `FEATURE-PLAN.md` for scope, decisions, API contract, test cases, and
   completion criteria.
3. Review and adjust the plan until the implementation path is clear.
4. Establish quality guardrails and a verification checklist before coding.
5. Implement in small, testable slices: data model, reconciliation logic, APIs,
   and Postman collection.
6. Update the feature-plan phase status only after its acceptance criteria pass;
   record evidence before ending a work session.
7. Validate each slice with automated tests and local API checks.
8. Run the full verification checklist, then document the exact commands and
   results in the final handoff.

The plan remains a living document: it is updated when a requirement, design
decision, or validation finding changes the implementation approach.

## Engineering Principles

- Orders are the source of truth.
- Monetary values use `Decimal`, never floating-point numbers.
- Reconciliation results are stored during payout import, not calculated on
  every read request.
- CSV validation and database writes are transactional: invalid input must not
  create a partial import.
- Generated or manually written code receives the same test, security, and
  review checks.

## Planned Validation

Before submission, I will verify migrations, automated tests, upload and results
API behavior, and Postman assertions. The final README will record the exact
commands and outcomes, including the expected mismatch and missing-order sample
cases.

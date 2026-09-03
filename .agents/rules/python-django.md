# Python and Django Engineering Rules

## Purpose

These rules make generated and hand-written code easy to review, test, change,
and operate. Apply SOLID and DRY pragmatically: clarity and a simple design are
more valuable than unnecessary abstraction.

## Design and boundaries

- Keep functions and classes small, cohesive, and responsible for one clear
  concern. Reuse established domain logic, but do not add abstractions for a
  single use or merely similar code.
- Keep Django layers explicit: views coordinate HTTP concerns, serializers
  validate request and response data, services own business workflows, and
  models own persistence and database constraints.
- Prefer loose coupling and explicit dependencies. Avoid hidden mutable global
  state, circular imports, and cross-app knowledge that belongs behind an app
  boundary, function parameter, or defined interface.

## Code quality and data access

- Use descriptive names, type hints for non-trivial public functions, and small
  focused modules. Remove dead code and do not leave commented-out
  implementations or speculative helpers.
- Keep database access intentional: add constraints and indexes for invariants
  and lookup paths, use transactions for multi-record changes, and avoid N+1
  queries with appropriate ORM loading when listing related data.
- Handle expected failures explicitly with validation errors. Do not catch broad
  exceptions or expose internal exception details to API clients.
- Prefer idiomatic Django and standard-library solutions before adding a
  dependency. Every behavior change must remain independently testable.

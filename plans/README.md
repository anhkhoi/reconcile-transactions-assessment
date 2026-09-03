# Planning Convention

Create one folder for each planned unit of work, including a feature, bug fix,
refactor, operational change, or technical investigation. Use this format:

```text
NNN-short-description/
```

`NNN` is a zero-padded sequence number. Start at `001` and use the next highest
number for every new plan. For example:

```text
001-reconciliation-service/
002-payout-import-retry/
003-fix-csv-validation/
004-add-import-observability/
```

Each work folder contains `FEATURE-PLAN.md` and an optional `resources/`
directory for work-specific planning or validation artifacts. Do not rename or
reuse an existing number, even when a plan is completed.

## Plan Lifecycle and Evidence

Each `FEATURE-PLAN.md` must define its scope, acceptance criteria, relevant
validation checks, and phase status. Use `Not started`, `In progress`,
`Blocked`, and `Complete` consistently.

Before marking a phase `Complete`, run its relevant checks and record the
commands, outcomes, and unresolved follow-up work in that plan's phase notes
or validation evidence. Update the plan before continuing if implementation or
validation changes a design decision. Code written without recorded acceptance
evidence is not a completed phase.

# Git Commit Rules

- Use Conventional Commits for every commit subject:
  `type(optional-scope): concise imperative description`.
- Use the type that best describes the change. Common types are `feat`, `fix`,
  `docs`, `test`, `refactor`, `chore`, and `build`.
- When a commit completes work for a feature-plan phase, put the phase number
  in the description, not before the Conventional Commit type. For example:
  `feat: bootstrap reconciliation service (phase 2)`.
- Keep each commit focused on one coherent change; do not include unrelated
  formatting, generated local state, credentials, or temporary files.
- Before committing, inspect the staged diff and run the relevant validation
  checks. Do not commit a failing implementation unless the commit explicitly
  records an agreed investigation or blocked state.
- Do not amend, rebase, force-push, or otherwise rewrite published history
  without explicit user approval. If local commits are rewritten, report their
  replacement SHA values.

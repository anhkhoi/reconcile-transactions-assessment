# Security Rules

- Never commit credentials, local SQLite databases, or uploaded payout files.
- Restrict upload size, require CSV input, and return validation errors without
  exposing stack traces or internal configuration.
- Keep Django debug mode limited to local development. Production deployment
  requires authentication, authorization, secure configuration, and least-
  privilege access to infrastructure.

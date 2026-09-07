# Contributing

Thank you for contributing to AI-Forge. Product behavior for investigations
must stay **backward compatible**. Forensic engines, AI models, API
contracts, and schemas change only when a phase explicitly requires it.

## Process

1. Open an issue using `.github/ISSUE_TEMPLATE/`.
2. Branch from `main`: `feature/*` or `fix/*`.
3. Keep PRs additive and reviewable. Use `.github/PULL_REQUEST_TEMPLATE.md`.
4. CI on the pull request must be green
   ([release-engineering.md](release-engineering.md)).
5. Do not commit secrets, `.env` files, real evidence, or model weights that
   are not licensed for this repository.

## Local checks

Follow [development.md](development.md) and
[coding-standards.md](coding-standards.md).

## Review expectations

- No silent re-runs of AI inside fusion or reporting.
- Original evidence remains immutable.
- Errors and unavailable capabilities are explicit.
- Docs updated when you add endpoints, env vars, or operator steps.

## License

Contributions are under the repository [MIT License](../LICENSE).

# Contributing

Thank you for contributing to Transport Coordinator.

## Development Setup

1. Clone the repo and read `memory.md` for project context.
2. `make infra` — start Postgres + Redis.
3. Install Python deps: `pip install -e "packages/solver[dev]" -e "apps/api[dev]"`
4. Install web deps: `cd apps/web && npm install`
5. Run `make api` and `make web` in separate terminals.

## Conventions

- **Commits:** [Conventional Commits](https://www.conventionalcommits.org/) — `feat:`, `fix:`, `docs:`, `chore:`
- **Python:** Ruff for linting, pytest for tests. Target Python 3.12+.
- **TypeScript:** Strict mode, Prettier-compatible formatting.
- **Branches:** `main` (stable), `develop` (integration), feature branches off `develop`.

## Pull Requests

- Keep PRs focused and small.
- Ensure `make test` and `make lint` pass locally.
- Solver changes must include or update golden-file tests in `packages/solver/tests/`.

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.

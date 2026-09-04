# Contributing to Uptime Page

Thank you for helping improve Uptime Page. Small, focused changes with clear tests are the easiest to review and maintain.

## Before you start

- Search [existing issues](https://github.com/youssefsz/Uptime-page/issues) before opening a new one.
- Open an issue before investing in a large feature or a change to the data model.
- Do not use public issues for vulnerabilities. Follow [SECURITY.md](SECURITY.md) instead.
- Keep pull requests focused on one concern. Unrelated cleanup should be a separate change.

## Development setup

You need Python 3.11 or newer, [uv](https://docs.astral.sh/uv/), and PostgreSQL.

```bash
git clone https://github.com/YOUR-USERNAME/Uptime-page.git
cd Uptime-page
git remote add upstream https://github.com/youssefsz/Uptime-page.git
cp .env.example .env
uv sync --locked
```

Update `.env` with a local database URL and development-only credentials, then start the application:

```bash
uv run uvicorn app.main:app --reload
```

Docker users can run the complete local stack with:

```bash
docker compose -f compose.dev.yml up --build
```

## Make a change

1. Create a branch from the latest `master`:

   ```bash
   git fetch upstream
   git switch -c feat/short-description upstream/master
   ```

2. Use a clear prefix such as `feat/`, `fix/`, `docs/`, `test/`, `refactor/`, or `chore/`.
3. Match the surrounding code style and include tests for changed behavior.
4. If the database schema changes, create and review an Alembic migration:

   ```bash
   uv run alembic revision --autogenerate -m "describe the change"
   uv run alembic upgrade head
   uv run alembic downgrade -1
   uv run alembic upgrade head
   ```

5. Run the project checks:

   ```bash
   uv run ruff check .
   uv run pytest
   ```

## Pull requests

In the pull request description, explain the problem, the chosen approach, and how the change was tested. Include screenshots for visible interface changes and call out migrations, configuration changes, or compatibility concerns.

A pull request is ready for review when:

- CI passes on every supported Python version.
- New behavior has automated tests or a clear explanation of why testing is impractical.
- Public behavior and configuration changes are documented.
- The diff contains no credentials, local `.env` files, generated caches, or unrelated formatting changes.
- Commits are understandable and the branch is current with `master`.

Maintainers may ask for changes before merging. Reviews focus on correctness, security, maintainability, and fit with the project's scope.

## Reporting problems

Use the issue forms for reproducible bugs and feature proposals. For setup and usage help, read [SUPPORT.md](SUPPORT.md). Participation in the project is governed by [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

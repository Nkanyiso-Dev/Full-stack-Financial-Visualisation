# Roadmap

Each item is meant to be a self-contained issue/PR.

## Done
- [x] Strict file-type detection, row-level validation, transactional uploads
- [x] Logging, JSON error handling, `/api/health`
- [x] Docker Compose (MySQL + gunicorn + nginx)
- [x] CI: unit, integration, contract and Docker smoke tests

## Next
- [ ] **Unique constraint** on `(user_id, year, month)`. Duplicate checking is currently app-side, so two concurrent uploads could race. Enforce it in the schema.
- [ ] **Schema migrations** (Alembic or Flyway) replacing the raw `db_setup.sql`
- [ ] **Authentication**: register/login, JWT or sessions; users only see their own data (user ID no longer in the URL)
- [ ] **Income vs expense categories** instead of a single amount per month
- [ ] **Multi-year views**: trend line chart and year-over-year comparison
- [ ] **Pagination and rate limiting** (e.g. Flask-Limiter) on the API
- [ ] **Linting/formatting** (ruff) and a coverage report in CI
- [ ] **Delete / replace an uploaded year** from the UI

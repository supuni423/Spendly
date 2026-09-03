# Spendly — backend (Phase 2: foundation)

FastAPI + SQLAlchemy + Alembic + PostgreSQL, with email/password auth
issuing JWTs. Only the `users` table exists so far — purchases, products,
and everything else arrive in Phase 3+.

## Setup

```bash
python -m venv .venv
.venv/Scripts/activate        # .venv/bin/activate on macOS/Linux
pip install -r requirements.txt
cp .env.example .env          # edit JWT_SECRET_KEY at minimum
```

Create the database (defaults match `.env.example`; adjust if yours differ):

```sql
CREATE USER spendly WITH PASSWORD 'spendly';
CREATE DATABASE spendly OWNER spendly;
```

Or via Docker: `docker compose up -d db` from the repo root.

```bash
alembic upgrade head
uvicorn app.main:app --reload --port 8001
```

API docs at `http://localhost:8001/docs`.

## Tests

Tests run against a separate `spendly_test` database (never the dev one —
`tests/conftest.py` creates/drops tables there per test):

```sql
CREATE DATABASE spendly_test OWNER spendly;
```

```bash
pytest
```

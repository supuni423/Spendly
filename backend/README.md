# Spendly — backend

FastAPI + SQLAlchemy + Alembic + PostgreSQL. Email/password auth (JWT +
bcrypt, rate-limited, audit-logged), purchases and spending insights,
a deterministic product-matching and price-comparison pipeline against
pluggable `ProductSource`s, and a Gemini-powered shopping agent that
explains — but never computes — the recommendation. See the root
`README.md` for the overall architecture.

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

## Deploy

The backend is a standard containerized FastAPI app (`Dockerfile` in this
directory) — deployable to Render, Railway, Fly.io, or similar. There's no
one-click deploy; these are the steps to do by hand:

1. **Hosted Postgres**: create one on Neon, Supabase, or your host's own
   managed Postgres. Note the connection string.
2. **Create the service** from this repo/`Dockerfile` on your chosen host.
3. **Set environment variables** on that service (see `.env.example` for
   the full list): at minimum `DATABASE_URL` (the hosted Postgres from
   step 1), `JWT_SECRET_KEY` (a long random value — never reuse the dev
   default), `LLM_API_KEY` (your Gemini key), and `CORS_ORIGINS`. For
   `CORS_ORIGINS`, once the extension is loaded (`chrome://extensions`,
   with Developer Mode on) it has a stable `chrome-extension://<id>`
   origin — include that alongside `http://localhost:5173` for local
   development.
4. Migrations run automatically on container start (`alembic upgrade
   head`, see `Dockerfile`), so no separate migration step is needed
   after the first deploy.
5. **Point the extension at it**: build with
   `VITE_API_BASE_URL=https://your-deployed-url npm run build` in
   `extension/` (see `extension/README.md`), then reload the extension
   unpacked from `extension/dist`.

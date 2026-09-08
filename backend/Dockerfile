FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Most host platforms (Render, Railway, Fly) inject $PORT at runtime;
# migrations run against whatever DATABASE_URL is set before the app starts.
CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8001}

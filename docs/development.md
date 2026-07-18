# Development Guide

This document is a guide for setting up your local environment, managing configuration settings, running containers, and
troubleshooting common issues.

---

## Local Setup

### 1. Initialize Virtual Environment

Using Python's standard `venv`:

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# On Windows: .venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt -r requirements-dev.txt
```

### 3. Setup Configuration

Copy the configuration template:

```bash
cp .env.example .env
```

Generate a secure JWT secret:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Update your `.env` file with the generated `SECRET_KEY`.

### 4. Apply Migrations & Run Server

Ensure your database is running, then run:

```bash
alembic upgrade head
uvicorn main:app --reload
```

---

## Configuration Reference

Key settings loaded via Pydantic `BaseSettings` (`app/core/config.py`):

| Variable          | Default                 | Description                                                |
| ----------------- | ----------------------- | ---------------------------------------------------------- |
| `ENVIRONMENT`     | `development`           | Environment mode (`development`, `staging`, `production`). |
| `DEBUG`           | `false`                 | Enables verbose/debug logger messages.                     |
| `SECRET_KEY`      | (insecure default)      | Secret key for signing JWTs.                               |
| `POSTGRES_SERVER` | `localhost`             | PostgreSQL database host address.                          |
| `POSTGRES_DB`     | `fastapi_db`            | PostgreSQL database name.                                  |
| `CORS_ORIGINS`    | `http://localhost:3000` | Comma-separated list of allowed origins.                   |

---

## Running with Docker

- **Start PostgreSQL database only** (to run the app locally):
    ```bash
    docker compose up -d postgres
    ```
- **Start both database and application in Docker**:
    ```bash
    docker compose up --build
    ```
- **Stop and remove container instances**:
    ```bash
    docker compose down
    ```

---

## Troubleshooting FAQ

### Q: Why does Alembic not detect model changes?

Ensure the model module is imported in `app/db/base.py`. Alembic relies on this registry to auto-generate migrations.

### Q: I get `ConnectionRefusedError` when starting the app.

Verify that the PostgreSQL Docker container is running by typing `docker compose ps` and check database port matching
(`5432`).

### Q: How do I access the interactive API docs?

When running in `development` environment, open [http://localhost:8000/docs](http://localhost:8000/docs) in your
browser. API docs are disabled automatically when `ENVIRONMENT=production`.

---

## Related Documentation

- [Architecture & Database](architecture.md)
- [API Manual](api.md)
- [Pre-push Checks Guide](pre-push-checks.md)

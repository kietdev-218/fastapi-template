# Architecture & Database Setup

This document describes the architectural style, design principles, and database persistence layer used in this
microservice.

---

## Clean Architecture Overview

This project is built using a simplified Clean Architecture pattern. The main objective is to separate core business
logic from external delivery mechanisms (FastAPI) and databases.

```
HTTP Request ──> Delivery Layer (API) ──> Service Layer (Business) ──> Repository Layer ──> DB
```

### Layer Responsibilities

- **API Layer (`app/api/`)**: Exposes FastAPI routers and endpoints. It handles HTTP input parsing, authorization
  checks, and maps objects to response schemas. Endpoints must be thin and delegate logic to Services.
- **Service Layer (`app/services/`)**: Implements business logic and orchestration rules. It accepts standard Python
  types or Pydantic models and acts as the entrypoint for domain rules.
- **Repository Layer (`app/db/repositories/`)**: Abstracts all database queries. It manages CRUD operations and maps raw
  queries to models.
- **Domain Model Layer (`app/models/` & `app/schemas/`)**: Includes SQLAlchemy database tables (`models`) and Pydantic
  validation/serialization definitions (`schemas`).

---

## Design Principles

- **Dependency Injection (DI)**: We use FastAPI's native `Depends()` provider. Sessions are injected into repositories,
  repositories into services, and services into endpoints. This eliminates global singletons and simplifies mocking in
  tests.
- **Async-First**: All I/O calls to PostgreSQL are asynchronous, using `async def` and `await` with SQLAlchemy's
  `AsyncSession` and `asyncpg` driver.

---

## Database & Persistence Layer

The database connection is configured in `app/db/session.py`.

- **Connection Pool**: Uses PostgreSQL with pool size limits configured via environment settings.
- **Session Lifecycle**: The `get_db` dependency provides an isolated session per request and closes it automatically.

### Generic Repository Pattern

The `BaseRepository` (`app/db/repositories/base.py`) provides generic CRUD operations. You can extend it for specific
models:

```python
class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalars().first()
```

### Alembic Migrations Workflow

- **Autogenerate Revision**: After editing models, make sure they are imported in `app/db/base.py` and run:
    ```bash
    alembic revision --autogenerate -m "description"
    ```
- **Apply Migrations**:
    ```bash
    alembic upgrade head
    ```
- **Rollback Last Migration**:
    ```bash
    alembic downgrade -1
    ```
- **Resolve Multiple Heads**: If branch merges create parallel migrations, run:
    ```bash
    alembic merge -m "merge heads" <rev_1> <rev_2>
    ```

---

## Related Documentation

- [Development Guide](development.md)
- [API Manual](api.md)

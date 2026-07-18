# ============================================================
# Dockerfile — FastAPI Microservice Template
# Multi-stage, production-ready, security-hardened
#
# STAGES:
#   1. builder  — installs Python deps into a virtual env
#   2. runtime  — copies only the venv + app code (minimal image)
#
# BUILD:
#   docker build -t fastapi-service .
#   docker build --build-arg PYTHON_VERSION=3.13 -t fastapi-service .
#
# RUN:
#   docker run --env-file .env -p 8000:8000 fastapi-service
# ============================================================

# ------------------------------------------------------------------ #
# Build arguments (override at build time with --build-arg)
# ------------------------------------------------------------------ #
ARG PYTHON_VERSION=3.13


# ============================================================
# STAGE 1: builder — install dependencies into a virtual env
# ============================================================
FROM python:${PYTHON_VERSION}-slim AS builder

# Prevents Python from writing .pyc files and enables unbuffered stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # pip: disable version check, no cache, fail fast
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

WORKDIR /build

# Install build-time OS dependencies (needed by some Python C extensions)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create a virtual env inside the builder so we can copy it cleanly
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies — layer is cached unless requirements.txt changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# ============================================================
# STAGE 2: runtime — lean production image
# ============================================================
FROM python:${PYTHON_VERSION}-slim AS runtime

# ------------------------------------------------------------------ #
# Labels (OCI standard)
# ------------------------------------------------------------------ #
LABEL maintainer="Platform Team <platform@example.com>" \
      org.opencontainers.image.title="FastAPI Microservice" \
      org.opencontainers.image.description="Production-ready FastAPI microservice template" \
      org.opencontainers.image.source="https://github.com/your-org/template-fastapi" \
      org.opencontainers.image.vendor="Your Organisation"

# ------------------------------------------------------------------ #
# Python runtime optimisations
# ------------------------------------------------------------------ #
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    # Run-time defaults (overridden by .env or docker-compose env)
    ENVIRONMENT=production \
    HOST=0.0.0.0 \
    PORT=8000 \
    WORKERS=4 \
    LOG_LEVEL=INFO \
    LOG_FORMAT=json

# ------------------------------------------------------------------ #
# Minimal runtime OS deps
# ------------------------------------------------------------------ #
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libpq5 \
        curl \
    && rm -rf /var/lib/apt/lists/*

# ------------------------------------------------------------------ #
# Non-root user (security best practice)
# ------------------------------------------------------------------ #
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

# ------------------------------------------------------------------ #
# Copy the pre-built virtual env from the builder stage
# ------------------------------------------------------------------ #
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# ------------------------------------------------------------------ #
# Copy application source code
# ------------------------------------------------------------------ #
WORKDIR /app

COPY --chown=appuser:appuser alembic.ini ./
COPY --chown=appuser:appuser alembic/ ./alembic/
COPY --chown=appuser:appuser app/ ./app/
COPY --chown=appuser:appuser main.py ./

# ------------------------------------------------------------------ #
# Switch to non-root user
# ------------------------------------------------------------------ #
USER appuser

# ------------------------------------------------------------------ #
# Expose the application port
# ------------------------------------------------------------------ #
EXPOSE ${PORT}

# ------------------------------------------------------------------ #
# Health check — Kubernetes probes also work, but this covers
# standalone Docker and docker-compose deployments
# ------------------------------------------------------------------ #
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl --fail --silent http://localhost:${PORT}/api/v1/health || exit 1

# ------------------------------------------------------------------ #
# Entrypoint — Uvicorn in production mode
#
# • Uses SIGINT (--timeout-graceful-shutdown) for graceful shutdown
# • --access-log is disabled because our RequestLoggingMiddleware
#   already handles structured request logging
# • WORKERS, PORT, HOST, LOG_LEVEL are all overridable via env
# ------------------------------------------------------------------ #
CMD ["sh", "-c", \
    "uvicorn main:app \
        --host ${HOST} \
        --port ${PORT} \
        --workers ${WORKERS} \
        --log-level ${LOG_LEVEL} \
        --no-access-log \
        --timeout-graceful-shutdown 30 \
        --proxy-headers \
        --forwarded-allow-ips '*'"]

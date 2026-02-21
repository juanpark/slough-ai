FROM python:3.12-slim-bookworm

# Install UV for fast package management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_Link_MODE=copy

WORKDIR /app

# Install system dependencies (for building psycopg/pgvector if needed)
# Since we use psycopg[binary], this is minimal
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies using uv into isolated /venv
# Avoiding /app/.venv because host mounts overwrite it
ENV UV_PROJECT_ENVIRONMENT=/venv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy application code
COPY . .

# Sync project (installs the app itself if it's package-based, or just verify)
RUN uv sync --frozen --no-dev

# Ensure virtual env is in PATH
ENV PATH="/venv/bin:$PATH"

# Health check for ECS (web service only)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1

# Expose the app port
EXPOSE 3000

# Use entrypoint.py to decide which service to run
ENTRYPOINT ["uv", "run", "python", "entrypoint.py"]

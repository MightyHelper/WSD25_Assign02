FROM python:3.13-slim

# Install system deps for MariaDB client and any build tools (optional)
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy pyproject and install deps
COPY pyproject.toml poetry.lock* /app/
RUN python -m pip install --upgrade pip
# Install dependencies; in absence of lockfile, install test deps too
RUN pip install ".[dev]" || true

# Copy source
COPY src/ /app/src/

ENV PYTHONPATH=/app/src

CMD ["uvicorn", "app.main:create_app", "--host", "0.0.0.0", "--port", "8000"]


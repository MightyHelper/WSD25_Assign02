# Multi-stage Dockerfile for the async FastAPI project
FROM python:3.13-slim AS builder
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY pyproject.toml ./
RUN apt-get update && apt-get install -y --no-install-recommends build-essential gcc libffi-dev && rm -rf /var/lib/apt/lists/*
RUN pip install --upgrade pip setuptools wheel
RUN pip install --user -e .

FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app"
WORKDIR /app
# create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser && mkdir -p /home/appuser/.local
COPY --from=builder /root/.local /home/appuser/.local
COPY . /app
RUN chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
CMD ["/home/appuser/.local/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]


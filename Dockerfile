# Multi-stage production Dockerfile for GuardWAF Control Plane
# Stage 1: Build & Dependencies
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt pyproject.toml /build/
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt .

# Stage 2: Final Minimal Security-Hardened Runtime
FROM python:3.11-slim AS runner

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 curl && \
    rm -rf /var/lib/apt/lists/*

# Create unprivileged runtime user
RUN groupadd -g 10001 guardwaf && \
    useradd -u 10001 -g guardwaf -s /bin/false -m guardwaf

COPY --from=builder /install /usr/local
COPY . /app

# Ensure proper ownership
RUN chown -R guardwaf:guardwaf /app

USER guardwaf:guardwaf

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health/live || exit 1

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

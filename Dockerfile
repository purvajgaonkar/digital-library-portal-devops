# ==============================================================================
# Production Dockerfile: Digital Library Search Portal
# Multi-arch, lightweight Python 3.11 image with non-root security & healthcheck
# ==============================================================================

FROM python:3.11-slim-bookworm AS base

# Prevent Python from writing .pyc files and enable unbuffered terminal logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000 \
    FLASK_ENV=production

# Install minimal OS dependencies for healthcheck & clean apt cache
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Create dedicated non-root application user for least-privilege security
RUN groupadd -g 1001 appgroup && \
    useradd -u 1001 -g appgroup -s /bin/sh -m appuser

# Set working directory
WORKDIR /app

# Copy dependency definition first to leverage Docker layer caching
COPY requirements.txt .

# Install dependencies into system Python without storing pip cache
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code and template assets
COPY app.py .
COPY templates/ ./templates/

# Ensure application user owns the runtime directory and database mount path
RUN chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Expose application port
EXPOSE 5000

# Docker native healthcheck probe connecting to /health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Launch application
CMD ["python", "app.py"]

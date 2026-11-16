# Multi-stage lightweight Python Dockerfile for Render Docker deployment
FROM python:3.11-slim

# Avoid writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=10000

WORKDIR /app

# Install minimal OS dependencies for network & certificates
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency definition
COPY requirements.txt .

# Install dependencies with PyTorch CPU wheel
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code and weights
COPY . .

# Expose Render target port
EXPOSE $PORT

# Healthcheck to verify the web service is responding
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:${PORT}/health || exit 1

# Start FastAPI application
CMD exec uvicorn app:app --host 0.0.0.0 --port ${PORT}

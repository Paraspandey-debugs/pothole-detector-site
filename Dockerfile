# Multi-stage lightweight Python Dockerfile for Render Docker deployment
FROM python:3.11-slim

# Avoid writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=10000

WORKDIR /app

# Install OS dependencies for OpenCV, media rendering, network & certificates
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    libxcb1 \
    libx11-xcb1 \
    libxrender1 \
    libxext6 \
    libsm6 \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency definition
COPY requirements.txt .

# Install dependencies with PyTorch CPU wheel, removing conflicting GUI opencv-python if pulled by ultralytics
RUN pip install --no-cache-dir -r requirements.txt \
    && (pip uninstall -y opencv-python || true) \
    && pip install --no-cache-dir --force-reinstall opencv-python-headless

# Copy application source code and weights
COPY . .

# Expose Render target port
EXPOSE $PORT

# Healthcheck to verify the web service is responding
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:${PORT}/health || exit 1

# Start FastAPI application
CMD exec uvicorn app:app --host 0.0.0.0 --port ${PORT}

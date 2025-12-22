# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Copy application code (needed for editable install)
COPY . .

# Create venv and install dependencies
RUN uv venv && \
    . .venv/bin/activate && \
    uv pip install .

# Create directory for ML models cache
RUN mkdir -p /app/.cache/huggingface

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV TRANSFORMERS_CACHE=/app/.cache/huggingface
ENV HF_HOME=/app/.cache/huggingface

# Expose port 8000
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/up || exit 1

# Run database migrations and start the server
CMD ["/bin/bash", "-c", ". .venv/bin/activate && alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]


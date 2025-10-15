FROM python:3.11-slim

# Build arguments
ARG ENVIRONMENT=development
ARG INSTALL_DEV=true

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV ENVIRONMENT=${ENVIRONMENT}

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    $(if [ "$ENVIRONMENT" = "production" ]; then echo ""; else echo "vim"; fi) \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements*.txt ./

# Install Python dependencies based on environment
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    if [ "$ENVIRONMENT" = "production" ]; then \
        pip install --no-cache-dir -r requirements-web.txt; \
    elif [ "$INSTALL_DEV" = "true" ]; then \
        pip install --no-cache-dir -r requirements-dev.txt; \
    fi

# Copy project files
COPY . .

# Install the package
RUN pip install -e .

# Create non-root user
RUN useradd --create-home --shell /bin/bash omics && \
    chown -R omics:omics /app

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/config && \
    chown -R omics:omics /app/logs /app/data /app/config

# Switch to non-root user
USER omics

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${INTERNAL_PORT:-8001}/api/v2/health || exit 1

# Expose ports (configurable)
EXPOSE ${INTERNAL_PORT:-8001}

# Default command - start futuristic interface
CMD ["python", "-m", "interfaces.futuristic.main"]

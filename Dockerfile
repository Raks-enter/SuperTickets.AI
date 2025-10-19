# Simple, reliable Dockerfile for SuperTickets.AI
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (for better caching)
COPY requirements*.txt ./

# Install Python dependencies with fallback
RUN pip install --upgrade pip && \
    (pip install -r requirements-bedrock.txt || \
     pip install -r requirements-minimal.txt || \
     pip install -r requirements-simple.txt || \
     pip install -r requirements.txt)

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/credentials /app/logs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "mcp_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
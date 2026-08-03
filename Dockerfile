# ============================================================================
# Multi-stage Dockerfile for Vulnerable Flask App
# Stage 1: Builder - install dependencies
# Stage 2: Runtime - minimal image with only necessary files
# ============================================================================

# --- STAGE 1: BUILDER ---
FROM python:3.12-slim as builder

WORKDIR /build

# Copy requirements
COPY requirements.txt .

# Install dependencies to /build/install
RUN pip install --user --no-cache-dir -r requirements.txt


# --- STAGE 2: RUNTIME ---
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Create non-root user for security (best practice)
RUN useradd -m -u 1000 appuser

# Copy only necessary files from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code
COPY app/ ./app/
COPY app.py .
COPY requirements.txt .
COPY .env.example .

# Set environment variables
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Expose port
EXPOSE 5000

# Change to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/api/health', timeout=5)" || exit 1

# Run Flask app
CMD ["python", "app.py"]

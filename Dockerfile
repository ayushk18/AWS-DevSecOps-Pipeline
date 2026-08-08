FROM python:3.12-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-slim
WORKDIR /app
RUN useradd -m -u 1000 appuser

# Copy installed dependencies from prefix
COPY --from=builder /install /usr/local

# Copy application code
COPY app/ ./app/
COPY app.py .
COPY .env.example .

# Create instance directory with proper permissions BEFORE switching user
RUN mkdir -p /app/instance && chmod 755 /app/instance && chown appuser:appuser /app/instance

ENV PYTHONUNBUFFERED=1

EXPOSE 5000

USER appuser

# Remove the () from the app factory call
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "app:create_app"]
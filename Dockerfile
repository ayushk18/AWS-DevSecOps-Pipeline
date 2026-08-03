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

ENV PYTHONUNBUFFERED=1

EXPOSE 5000

USER appuser

# Use gunicorn with proper app factory syntax
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "app:create_app()"]
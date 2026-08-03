# app/utils.py
import logging
import sys
from datetime import datetime
from prometheus_client import Counter, Histogram, Gauge
import time

# ============================================================================
# LOGGING SETUP
# ============================================================================

def setup_logging(log_level: str = "INFO"):
    """
    Configure structured logging with timestamps and log levels.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Logger instance
    """
    logger = logging.getLogger("flask_app")
    logger.setLevel(getattr(logging, log_level, logging.INFO))
    
    # Console handler with formatted output
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger

logger = setup_logging()

# ============================================================================
# PROMETHEUS METRICS
# ============================================================================

# Counter: Track request count by endpoint and method
http_requests_total = Counter(
    name="http_requests_total",
    documentation="Total HTTP requests",
    labelnames=["method", "endpoint", "status"]
)

# Histogram: Track request latency (response time)
http_request_duration_seconds = Histogram(
    name="http_request_duration_seconds",
    documentation="HTTP request latency in seconds",
    labelnames=["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
)

# Gauge: Track active database connections
db_connections_active = Gauge(
    name="db_connections_active",
    documentation="Number of active database connections"
)

# Counter: Track authentication attempts
auth_attempts_total = Counter(
    name="auth_attempts_total",
    documentation="Total authentication attempts",
    labelnames=["result"]  # "success" or "failure"
)

# Counter: Track application errors
app_errors_total = Counter(
    name="app_errors_total",
    documentation="Total application errors",
    labelnames=["error_type"]  # "database_error", "validation_error", etc.
)

# ============================================================================
# MIDDLEWARE FUNCTIONS
# ============================================================================

def record_request_metrics(method: str, endpoint: str, status: int, duration: float):
    """
    Record HTTP request metrics.
    
    Args:
        method: HTTP method (GET, POST, etc.)
        endpoint: Request endpoint/path
        status: HTTP status code
        duration: Request duration in seconds
    """
    http_requests_total.labels(method=method, endpoint=endpoint, status=status).inc()
    http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)
    logger.info(f"{method} {endpoint} -> {status} ({duration:.3f}s)")

def record_error(error_type: str, message: str):
    """
    Record application error.
    
    Args:
        error_type: Type of error (e.g., "database_error", "validation_error")
        message: Error message
    """
    app_errors_total.labels(error_type=error_type).inc()
    logger.error(f"[{error_type}] {message}")

def record_auth_attempt(success: bool):
    """
    Record authentication attempt.
    
    Args:
        success: True if auth succeeded, False if failed
    """
    result = "success" if success else "failure"
    auth_attempts_total.labels(result=result).inc()
    logger.info(f"Authentication attempt: {result}")
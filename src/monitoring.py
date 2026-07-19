import json
import logging
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

from prometheus_client import (
    Counter,
    Histogram,
    generate_latest,
    CONTENT_TYPE_LATEST
)


# -------------------------------
# Prometheus Metrics
# -------------------------------

PROM_HTTP_REQUESTS_TOTAL = Counter(
    "fraud_api_http_requests_total",
    "Total HTTP requests received by Fraud Detection API",
    ["method", "path", "status_code"]
)

PROM_HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "fraud_api_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"]
)

PROM_PREDICTIONS_TOTAL = Counter(
    "fraud_predictions_total",
    "Total fraud predictions by risk level and final decision",
    ["risk_level", "final_decision"]
)

PROM_FRAUD_PROBABILITY = Histogram(
    "fraud_prediction_probability",
    "Fraud prediction probability distribution",
    buckets=[0.0, 0.1, 0.2, 0.3, 0.5, 0.7, 0.8, 0.9, 1.0]
)


def record_prometheus_request(method, path, status_code, duration_ms):
    duration_seconds = duration_ms / 1000

    PROM_HTTP_REQUESTS_TOTAL.labels(
        method=method,
        path=path,
        status_code=str(status_code)
    ).inc()

    PROM_HTTP_REQUEST_DURATION_SECONDS.labels(
        method=method,
        path=path
    ).observe(duration_seconds)


def record_prometheus_prediction(prediction):
    risk_level = prediction.get("risk_level", "UNKNOWN")
    final_decision = prediction.get("final_decision", "UNKNOWN")
    fraud_probability = float(prediction.get("fraud_probability", 0))

    PROM_PREDICTIONS_TOTAL.labels(
        risk_level=risk_level,
        final_decision=final_decision
    ).inc()

    PROM_FRAUD_PROBABILITY.observe(fraud_probability)


def get_prometheus_metrics():
    return generate_latest()


def get_prometheus_content_type():
    return CONTENT_TYPE_LATEST


# -------------------------------
# Structured JSON Logging
# -------------------------------

class JsonFormatter(logging.Formatter):
    """
    Converts API logs into JSON format.
    """

    def format(self, record):
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage()
        }

        extra_fields = [
            "request_id",
            "method",
            "path",
            "status_code",
            "duration_ms",
            "client_host",
            "error"
        ]

        for field in extra_fields:
            if hasattr(record, field):
                log_data[field] = getattr(record, field)

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def setup_logger():
    logger = logging.getLogger("fraud_api")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = JsonFormatter()

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    file_handler = logging.FileHandler(log_dir / "api_structured.log")
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


# -------------------------------
# In-Memory API Metrics
# -------------------------------

class MetricsStore:
    """
    In-memory API monitoring metrics.
    """

    def __init__(self):
        self.lock = Lock()
        self.total_requests = 0
        self.total_errors = 0
        self.total_latency_ms = 0.0
        self.max_latency_ms = 0.0
        self.by_path = defaultdict(
            lambda: {
                "requests": 0,
                "errors": 0,
                "total_latency_ms": 0.0,
                "max_latency_ms": 0.0
            }
        )

    def record(self, method, path, status_code, duration_ms):
        with self.lock:
            self.total_requests += 1
            self.total_latency_ms += duration_ms
            self.max_latency_ms = max(self.max_latency_ms, duration_ms)

            is_error = status_code >= 400

            if is_error:
                self.total_errors += 1

            key = f"{method} {path}"

            self.by_path[key]["requests"] += 1
            self.by_path[key]["total_latency_ms"] += duration_ms
            self.by_path[key]["max_latency_ms"] = max(
                self.by_path[key]["max_latency_ms"],
                duration_ms
            )

            if is_error:
                self.by_path[key]["errors"] += 1

    def snapshot(self):
        with self.lock:
            avg_latency_ms = (
                self.total_latency_ms / self.total_requests
                if self.total_requests > 0
                else 0
            )

            path_metrics = []

            for path, values in self.by_path.items():
                avg_path_latency = (
                    values["total_latency_ms"] / values["requests"]
                    if values["requests"] > 0
                    else 0
                )

                path_metrics.append({
                    "endpoint": path,
                    "requests": values["requests"],
                    "errors": values["errors"],
                    "avg_latency_ms": round(avg_path_latency, 2),
                    "max_latency_ms": round(values["max_latency_ms"], 2)
                })

            return {
                "total_requests": self.total_requests,
                "total_errors": self.total_errors,
                "avg_latency_ms": round(avg_latency_ms, 2),
                "max_latency_ms": round(self.max_latency_ms, 2),
                "by_endpoint": path_metrics,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }


metrics_store = MetricsStore()

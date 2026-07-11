from pathlib import Path
import sys
import os
import hmac
import time
from uuid import uuid4
from datetime import datetime
from typing import List

from fastapi import FastAPI, HTTPException, Header, Depends, Request, Response
from pydantic import BaseModel


# -------------------------------
# Project Path Setup
# -------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = BASE_DIR / "src"

sys.path.insert(0, str(SRC_DIR))


# -------------------------------
# Project Imports
# -------------------------------

from predict import predict_fraud, predict_batch
from explain import explain_transaction
from db_logger import init_db, log_prediction, fetch_recent_predictions
from monitoring import (
    setup_logger,
    metrics_store,
    record_prometheus_request,
    record_prometheus_prediction,
    get_prometheus_metrics,
    get_prometheus_content_type
)


# -------------------------------
# Security Configuration
# -------------------------------

API_KEY = os.environ.get("FRAUD_API_KEY", "dev_fraud_api_key_123")


def verify_api_key(x_api_key: str = Header(default=None, alias="X-API-Key")):
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API key. Please provide X-API-Key header."
        )

    if not hmac.compare_digest(x_api_key, API_KEY):
        raise HTTPException(
            status_code=403,
            detail="Invalid API key."
        )

    return True


# -------------------------------
# FastAPI App
# -------------------------------

app = FastAPI(
    title="Real-Time Fraud Detection and Risk Intelligence API",
    description="Production-style fraud detection API with ML, rule engine, SHAP, PostgreSQL, API key auth, structured logs, and Prometheus metrics.",
    version="1.0.0"
)

logger = setup_logger()


# -------------------------------
# Middleware: Structured Logs + Metrics
# -------------------------------

@app.middleware("http")
async def structured_logging_middleware(request: Request, call_next):
    request_id = str(uuid4())
    start_time = time.perf_counter()
    status_code = 500

    try:
        response = await call_next(request)
        status_code = response.status_code
        return response

    except Exception as e:
        logger.exception(
            "request_failed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": status_code,
                "client_host": request.client.host if request.client else None,
                "error": str(e)
            }
        )
        raise

    finally:
        duration_ms = round(
            (time.perf_counter() - start_time) * 1000,
            2
        )

        metrics_store.record(
            method=request.method,
            path=request.url.path,
            status_code=status_code,
            duration_ms=duration_ms
        )

        record_prometheus_request(
            method=request.method,
            path=request.url.path,
            status_code=status_code,
            duration_ms=duration_ms
        )

        logger.info(
            "request_completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": status_code,
                "duration_ms": duration_ms,
                "client_host": request.client.host if request.client else None
            }
        )


# -------------------------------
# Startup Event
# -------------------------------

@app.on_event("startup")
def startup_event():
    init_db()


# -------------------------------
# Request Models
# -------------------------------

class Transaction(BaseModel):
    step: int
    type: str
    amount: float
    oldbalanceOrg: float
    newbalanceOrig: float
    oldbalanceDest: float
    newbalanceDest: float
    isFlaggedFraud: int


class BatchTransactionRequest(BaseModel):
    transactions: List[Transaction]


# -------------------------------
# Helper Function
# -------------------------------

def pydantic_to_dict(model_object):
    if hasattr(model_object, "model_dump"):
        return model_object.model_dump()

    return model_object.dict()


# -------------------------------
# Public Routes
# -------------------------------

@app.get("/")
def root():
    return {
        "message": "Real-Time Fraud Detection API is running",
        "service": "fraud-risk-intelligence-platform",
        "status": "active"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/metrics")
def prometheus_metrics():
    return Response(
        content=get_prometheus_metrics(),
        media_type=get_prometheus_content_type()
    )


# -------------------------------
# Protected Routes
# -------------------------------

@app.post("/predict")
def predict(
    transaction: Transaction,
    authenticated: bool = Depends(verify_api_key)
):
    try:
        transaction_dict = pydantic_to_dict(transaction)

        result = predict_fraud(transaction_dict)
        record_prometheus_prediction(result)

        explanation = explain_transaction(transaction_dict)

        prediction_log_id = log_prediction(
            transaction=transaction_dict,
            prediction=result,
            explanation=explanation
        )

        return {
            "transaction": transaction_dict,
            "prediction": result,
            "explanation": explanation,
            "prediction_log_id": prediction_log_id,
            "timestamp": datetime.now().isoformat()
        }

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(e)}"
        )


@app.post("/predict_batch")
def predict_batch_api(
    request: BatchTransactionRequest,
    authenticated: bool = Depends(verify_api_key)
):
    try:
        transactions = [
            pydantic_to_dict(transaction)
            for transaction in request.transactions
        ]

        results = predict_batch(transactions)

        for result in results:
            record_prometheus_prediction(result)

        return {
            "total_transactions": len(results),
            "results": results,
            "timestamp": datetime.now().isoformat()
        }

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Batch prediction failed: {str(e)}"
        )


@app.get("/prediction_logs")
def get_prediction_logs(
    limit: int = 50,
    authenticated: bool = Depends(verify_api_key)
):
    try:
        if limit < 1:
            limit = 1

        if limit > 500:
            limit = 500

        logs = fetch_recent_predictions(limit=limit)

        return {
            "total_records": len(logs),
            "logs": logs,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch prediction logs: {str(e)}"
        )


@app.get("/monitoring/metrics")
def get_monitoring_metrics(
    authenticated: bool = Depends(verify_api_key)
):
    return metrics_store.snapshot()
from pathlib import Path
import sys
import os
import hmac
import json
import base64
import hashlib
import time
from uuid import uuid4
from datetime import datetime, timedelta, timezone
from typing import List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Header, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


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
from db_logger import (
    init_db,
    log_prediction,
    fetch_recent_predictions
)
from monitoring import (
    setup_logger,
    metrics_store,
    record_prometheus_request,
    record_prometheus_prediction,
    get_prometheus_metrics,
    get_prometheus_content_type
)
from big_data_views import (
    get_streaming_status,
    get_recent_scored,
    get_datalake_summary
)
from rbac import role_has_permission, role_summary
# -------------------------------
# Security Configuration
# -------------------------------

API_KEY = os.environ.get("FRAUD_API_KEY")
DEMO_ADMIN_EMAIL = os.environ.get("DEMO_ADMIN_EMAIL", "admin@fraud.local")
DEMO_ADMIN_PASSWORD = os.environ.get("DEMO_ADMIN_PASSWORD", "admin123")
DEMO_ADMIN_ROLE = os.environ.get("DEMO_ADMIN_ROLE", "admin")
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "local_demo_jwt_secret_change_me")
JWT_EXPIRES_MINUTES = int(os.environ.get("JWT_EXPIRES_MINUTES", "120"))


def csv_env(name, default=""):
    return [
        value.strip()
        for value in os.environ.get(name, default).split(",")
        if value.strip()
    ]


def base64url_encode(data):
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def base64url_decode(value):
    padded = value + "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(padded.encode("utf-8"))


def sign_jwt(payload):
    header = {"alg": "HS256", "typ": "JWT"}
    header_part = base64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_part = base64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_part}.{payload_part}".encode("utf-8")
    signature = hmac.new(JWT_SECRET_KEY.encode("utf-8"), signing_input, hashlib.sha256).digest()
    return f"{header_part}.{payload_part}.{base64url_encode(signature)}"


def decode_jwt(token):
    try:
        header_part, payload_part, signature_part = token.split(".")
        signing_input = f"{header_part}.{payload_part}".encode("utf-8")
        expected_signature = hmac.new(
            JWT_SECRET_KEY.encode("utf-8"),
            signing_input,
            hashlib.sha256
        ).digest()

        if not hmac.compare_digest(base64url_decode(signature_part), expected_signature):
            raise ValueError("Invalid token signature.")

        payload = json.loads(base64url_decode(payload_part))
        expires_at = payload.get("exp")

        if expires_at and datetime.now(timezone.utc).timestamp() > float(expires_at):
            raise ValueError("Token expired.")

        return payload

    except Exception as exc:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid bearer token: {str(exc)}"
        )


def create_access_token(email):
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRES_MINUTES)
    return sign_jwt({
        "sub": email,
        "role": DEMO_ADMIN_ROLE,
        "exp": expires_at.timestamp(),
        "iat": datetime.now(timezone.utc).timestamp(),
    })


def verify_authenticated_request(
    authorization: str = Header(default=None, alias="Authorization"),
    x_api_key: str = Header(default=None, alias="X-API-Key")
):
    if API_KEY and x_api_key and hmac.compare_digest(x_api_key, API_KEY):
        return {"auth_type": "api_key", "subject": "service", "role": "service"}

    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        payload = decode_jwt(token)
        return {"auth_type": "jwt", "subject": payload.get("sub"), "role": payload.get("role")}

    raise HTTPException(
        status_code=401,
        detail="Missing or invalid credentials. Use X-API-Key or Authorization: Bearer token."
    )


def require_permission(permission):
    def checker(auth_context: dict = Depends(verify_authenticated_request)):
        role = auth_context.get("role", "viewer")

        if role_has_permission(role, permission):
            return auth_context

        raise HTTPException(
            status_code=403,
            detail=f"Role '{role}' is not allowed to access permission '{permission}'."
        )

    return checker


# -------------------------------
# FastAPI App
# -------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Real-Time Fraud Detection and Risk Intelligence API",
    description="Production-style fraud detection API with ML, rule engine, SHAP, PostgreSQL, API key auth, structured logs, and Prometheus metrics.",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=csv_env(
        "FRAUD_CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3001,http://127.0.0.1:3001"
    ),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
# Request Models
# -------------------------------

class Transaction(BaseModel):
    step: int = Field(..., ge=0)
    type: str = Field(..., min_length=1)
    amount: float = Field(..., ge=0)
    oldbalanceOrg: float = Field(..., ge=0)
    newbalanceOrig: float = Field(..., ge=0)
    oldbalanceDest: float = Field(..., ge=0)
    newbalanceDest: float = Field(..., ge=0)
    isFlaggedFraud: int = Field(..., ge=0, le=1)


class BatchTransactionRequest(BaseModel):
    transactions: List[Transaction]


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=1)


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


@app.post("/auth/login")
def login(request: LoginRequest):
    if (
        hmac.compare_digest(request.email, DEMO_ADMIN_EMAIL)
        and hmac.compare_digest(request.password, DEMO_ADMIN_PASSWORD)
    ):
        return {
            "access_token": create_access_token(request.email),
            "token_type": "bearer",
            "expires_in_minutes": JWT_EXPIRES_MINUTES,
            "user": {
                "email": request.email,
                "role": DEMO_ADMIN_ROLE,
                "permissions": role_summary(DEMO_ADMIN_ROLE)["permissions"],
            }
        }

    raise HTTPException(
        status_code=401,
        detail="Invalid demo credentials."
    )


@app.get("/auth/me")
def auth_me(
    auth_context: dict = Depends(verify_authenticated_request)
):
    return {
        "authenticated": True,
        "auth_type": auth_context.get("auth_type"),
        "subject": auth_context.get("subject"),
        "role": auth_context.get("role", "service"),
        "permissions": role_summary(auth_context.get("role", "service"))["permissions"],
    }


# -------------------------------
# Protected Routes
# -------------------------------

@app.post("/predict")
def predict(
    transaction: Transaction,
    authenticated: dict = Depends(require_permission("predict"))
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
    authenticated: dict = Depends(require_permission("batch_predict"))
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
    authenticated: dict = Depends(require_permission("read_logs"))
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
    authenticated: dict = Depends(require_permission("read_monitoring"))
):
    return metrics_store.snapshot()


@app.get("/streaming/status")
def streaming_status(
    authenticated: dict = Depends(require_permission("read_streaming"))
):
    return get_streaming_status()


@app.get("/streaming/recent-scored")
def streaming_recent_scored(
    limit: int = 20,
    authenticated: dict = Depends(require_permission("read_streaming"))
):
    if limit < 1:
        limit = 1

    if limit > 200:
        limit = 200

    return get_recent_scored(limit=limit)


@app.get("/datalake/summary")
def datalake_summary(
    authenticated: dict = Depends(require_permission("read_datalake"))
):
    return get_datalake_summary()

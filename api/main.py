from pathlib import Path
import sys
from datetime import datetime
from typing import List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


BASE_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = BASE_DIR / "src"
sys.path.append(str(SRC_DIR))

from predict import predict_fraud, predict_batch
from explain import explain_transaction


app = FastAPI(
    title="Real-Time Fraud Detection API",
    description="API for scoring transaction fraud risk using a machine learning model.",
    version="1.0.0"
)


class Transaction(BaseModel):
    step: int
    type: str
    amount: float
    oldbalanceOrg: float
    newbalanceOrig: float
    oldbalanceDest: float
    newbalanceDest: float
    isFlaggedFraud: int = 0


class BatchTransactionRequest(BaseModel):
    transactions: List[Transaction]


@app.get("/")
def home():
    return {
        "message": "Fraud Detection API is running",
        "project": "Real-Time Fraud Detection and Risk Intelligence Platform"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/predict")
def predict(transaction: Transaction):
    try:
        transaction_dict = transaction.model_dump()

        result = predict_fraud(transaction_dict)
        explanation = explain_transaction(transaction_dict)

        return {
            "transaction": transaction_dict,
            "prediction": result,
            "explanation": explanation,
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
def predict_batch_transactions(request: BatchTransactionRequest):
    try:
        transactions = [txn.model_dump() for txn in request.transactions]

        results = predict_batch(transactions)

        return {
            "total_transactions": len(results),
            "results": results,
            "timestamp": datetime.now().isoformat()
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch prediction failed: {str(e)}")
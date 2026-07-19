from locust import HttpUser, between, task


API_KEY = "dev_fraud_api_key_123"

SAMPLE_TRANSACTION = {
    "step": 1,
    "type": "TRANSFER",
    "amount": 250000,
    "oldbalanceOrg": 250000,
    "newbalanceOrig": 0,
    "oldbalanceDest": 0,
    "newbalanceDest": 250000,
    "isFlaggedFraud": 1,
}


class FraudApiUser(HttpUser):
    wait_time = between(1, 3)

    def auth_headers(self):
        return {
            "Content-Type": "application/json",
            "X-API-Key": API_KEY,
        }

    @task(5)
    def health(self):
        self.client.get("/health", name="GET /health")

    @task(8)
    def predict(self):
        self.client.post(
            "/predict",
            json=SAMPLE_TRANSACTION,
            headers=self.auth_headers(),
            name="POST /predict",
        )

    @task(2)
    def predict_batch(self):
        self.client.post(
            "/predict_batch",
            json={"transactions": [SAMPLE_TRANSACTION, SAMPLE_TRANSACTION]},
            headers=self.auth_headers(),
            name="POST /predict_batch",
        )

    @task(3)
    def prediction_logs(self):
        self.client.get(
            "/prediction_logs?limit=20",
            headers=self.auth_headers(),
            name="GET /prediction_logs",
        )

    @task(3)
    def monitoring_metrics(self):
        self.client.get(
            "/monitoring/metrics",
            headers=self.auth_headers(),
            name="GET /monitoring/metrics",
        )

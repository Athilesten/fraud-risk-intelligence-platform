from pathlib import Path
from datetime import datetime, timedelta
import os
import subprocess


from airflow import DAG
from airflow.operators.python import PythonOperator


# -------------------------------
# Project Paths
# -------------------------------

PROJECT_HOME = Path(
    os.environ.get(
        "FRAUD_PROJECT_HOME",
        "/opt/fraud-project"
    )
)

DATA_PATH = PROJECT_HOME / "data" / "raw" / "paysim.csv"
MODEL_PATH = PROJECT_HOME / "models" / "fraud_model.pkl"
ENCODER_PATH = PROJECT_HOME / "models" / "label_encoder.pkl"
RETRAIN_SCRIPT_PATH = PROJECT_HOME / "src" / "retrain_model_pipeline.py"
REPORT_PATH = PROJECT_HOME / "reports" / "retraining_report.json"


# -------------------------------
# DAG Default Arguments
# -------------------------------

default_args = {
    "owner": "harshit",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


# -------------------------------
# Task 1: Validate Project Structure
# -------------------------------

def validate_project_structure():
    required_paths = [
        PROJECT_HOME,
        PROJECT_HOME / "src",
        PROJECT_HOME / "data",
        PROJECT_HOME / "data" / "raw",
        PROJECT_HOME / "models",
        PROJECT_HOME / "reports",
        RETRAIN_SCRIPT_PATH,
    ]

    missing_paths = []

    for path in required_paths:
        if not path.exists():
            missing_paths.append(str(path))

    if missing_paths:
        raise FileNotFoundError(
            "Missing required project paths: " + ", ".join(missing_paths)
        )

    print("Project structure validation passed.")
    print("Project home:", PROJECT_HOME)


# -------------------------------
# Task 2: Validate Dataset
# -------------------------------

def validate_dataset():
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found at {DATA_PATH}. "
            "Place PaySim dataset as data/raw/paysim.csv"
        )

    file_size_mb = DATA_PATH.stat().st_size / (1024 * 1024)

    if file_size_mb <= 0:
        raise ValueError("Dataset file is empty.")

    print("Dataset validation passed.")
    print(f"Dataset path: {DATA_PATH}")
    print(f"Dataset size: {file_size_mb:.2f} MB")


# -------------------------------
# Task 3: Run Retraining Pipeline
# -------------------------------

def run_retraining_pipeline():
    command = [
        "python",
        str(RETRAIN_SCRIPT_PATH)
    ]

    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_HOME / "src")

    result = subprocess.run(
        command,
        cwd=str(PROJECT_HOME),
        env=env,
        capture_output=True,
        text=True
    )

    print("STDOUT:")
    print(result.stdout)

    print("STDERR:")
    print(result.stderr)

    if result.returncode != 0:
        raise RuntimeError(
            f"Retraining pipeline failed with return code {result.returncode}"
        )

    print("Retraining pipeline task completed successfully.")


# -------------------------------
# Task 4: Validate Model Artifacts
# -------------------------------

def validate_model_artifacts():
    required_artifacts = [
        MODEL_PATH,
        ENCODER_PATH,
        REPORT_PATH,
    ]

    missing_artifacts = []

    for artifact in required_artifacts:
        if not artifact.exists():
            missing_artifacts.append(str(artifact))

    if missing_artifacts:
        raise FileNotFoundError(
            "Missing model artifacts: " + ", ".join(missing_artifacts)
        )

    print("Model artifact validation passed.")
    print("Model:", MODEL_PATH)
    print("Encoder:", ENCODER_PATH)
    print("Report:", REPORT_PATH)


# -------------------------------
# DAG Definition
# -------------------------------

with DAG(
    dag_id="fraud_model_retraining_pipeline",
    default_args=default_args,
    description="Automated fraud model retraining pipeline with validation and artifact checks",
    start_date=datetime(2026, 1, 1),
    schedule="@weekly",
    catchup=False,
    tags=["fraud-detection", "mlops", "retraining"],
) as dag:

    task_validate_project_structure = PythonOperator(
        task_id="validate_project_structure",
        python_callable=validate_project_structure,
    )

    task_validate_dataset = PythonOperator(
        task_id="validate_dataset",
        python_callable=validate_dataset,
    )

    task_run_retraining_pipeline = PythonOperator(
        task_id="run_retraining_pipeline",
        python_callable=run_retraining_pipeline,
    )

    task_validate_model_artifacts = PythonOperator(
        task_id="validate_model_artifacts",
        python_callable=validate_model_artifacts,
    )

    (
        task_validate_project_structure
        >> task_validate_dataset
        >> task_run_retraining_pipeline
        >> task_validate_model_artifacts
    )

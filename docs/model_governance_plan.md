# Model Governance Plan

## Current State

The project has training scripts, model artifacts, metadata, prediction code, and drift-monitoring helpers.

## Registry Target

Use MLflow Model Registry or a cloud registry:

- AWS SageMaker Model Registry
- Azure ML Registry
- Vertex AI Model Registry

## Model Stages

| Stage | Meaning |
|---|---|
| Development | Experimental model |
| Staging | Candidate model under validation |
| Approved | Passed metrics and review |
| Production | Serving traffic |
| Archived | Retired model |

## Approval Checklist

- Precision, recall, F1, ROC-AUC recorded
- Confusion matrix reviewed
- Fraud recall threshold approved
- Feature importance reviewed
- Bias/fairness considerations documented
- Drift baseline recorded
- Rollback model identified

## Drift And Retraining

Trigger retraining when:

- Amount distribution shifts materially
- Transaction type distribution shifts
- Fraud score distribution changes
- False positives or false negatives increase

## Rollback

Keep at least one previous approved model version available. Roll back by changing the active model version and redeploying FastAPI.

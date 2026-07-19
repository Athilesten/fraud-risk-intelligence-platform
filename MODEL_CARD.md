# Model Card: Fraud Risk Scoring Model

## Intended Use

This model scores PaySim-style financial transactions for fraud risk. It is designed for portfolio demonstration, analyst workflow simulation, and production-style architecture review.

It should not be represented as a live bank-grade model without validation on real, permissioned, institution-specific transaction data.

## Inputs

- `step`
- `type`
- `amount`
- `oldbalanceOrg`
- `newbalanceOrig`
- `oldbalanceDest`
- `newbalanceDest`
- `isFlaggedFraud`
- engineered balance and ratio features

## Output

- fraud probability
- ML risk level
- rule risk score
- final decision: `APPROVE`, `MANUAL REVIEW`, or `BLOCK / MANUAL REVIEW`
- top explanation features

## Validation Approach

The retraining pipeline now prefers a temporal holdout split by `step` because fraud behavior changes over time. If the temporal split loses one target class, it falls back to a stratified random holdout.

Metrics tracked:

- ROC-AUC
- PR-AUC
- precision
- recall
- F1-score
- threshold-level confusion matrix counts

## Threshold Policy

The default API thresholds are intentionally conservative for demonstration. A production deployment should select thresholds from business cost:

- false negatives: fraud loss, customer harm, regulatory exposure
- false positives: blocked legitimate payments, analyst workload, customer friction

## Known Limitations

- PaySim-style data is synthetic.
- Perfect scores should be treated as a validation warning, not a production guarantee.
- Real fraud labels may arrive late.
- Concept drift is expected in fraud because adversaries adapt.
- Feature leakage must be checked before any real deployment.

## Monitoring Requirements

- prediction volume
- fraud probability distribution
- risk decision distribution
- API latency and error rate
- transaction amount drift
- transaction type distribution shift
- false positive and false negative review outcomes when labels become available

## Governance Checklist

- model owner assigned
- training data version recorded
- model version recorded
- threshold selection documented
- rollback path documented
- analyst review process documented
- periodic retraining and drift review scheduled

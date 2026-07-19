"""create fraud predictions table

Revision ID: 0001_create_fraud_predictions
Revises:
Create Date: 2026-07-18
"""

from alembic import op


revision = "0001_create_fraud_predictions"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
    CREATE TABLE IF NOT EXISTS fraud_predictions (
        id SERIAL PRIMARY KEY,
        step INTEGER,
        transaction_type VARCHAR(50),
        amount NUMERIC,
        oldbalance_org NUMERIC,
        newbalance_orig NUMERIC,
        oldbalance_dest NUMERIC,
        newbalance_dest NUMERIC,
        is_flagged_fraud INTEGER,
        fraud_probability NUMERIC,
        risk_level VARCHAR(50),
        alert TEXT,
        rule_risk_score INTEGER,
        rule_risk_level VARCHAR(50),
        triggered_rules TEXT,
        final_decision TEXT,
        explanation JSONB,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)


def downgrade():
    op.drop_table("fraud_predictions")

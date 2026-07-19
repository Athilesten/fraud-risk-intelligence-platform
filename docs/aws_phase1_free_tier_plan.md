\# AWS Phase 1 Free-Tier Safe Plan



\## Project



Real-Time Fraud Detection and Risk Intelligence Platform



\## Selected Cloud



AWS



\## Region



ap-south-1 - Mumbai



\## Free-Tier Safety Rules



This project will first use AWS only for safe cloud preparation.



Do not create these services in Phase 1:

\- Amazon MSK

\- EMR

\- Glue

\- RDS

\- ECS with Load Balancer

\- NAT Gateway

\- Large EC2 instances



These can create cost if not managed carefully.



\## Phase 1 Scope



Included:

\- AWS account setup

\- MFA enabled

\- Budget alert

\- IAM user

\- AWS CLI configured

\- Cloud architecture documentation

\- Environment template



Not included:

\- Real backend deployment

\- Real database migration

\- Managed Kafka

\- Cloud Spark

\- Real SSO

\- Real compliance audit



\## Recommended Cloud Path



1\. React frontend to S3 + CloudFront

2\. FastAPI backend to ECS Fargate or Lambda later

3\. PostgreSQL to RDS later

4\. Secrets to AWS Secrets Manager later

5\. Kafka to MSK later

6\. Data lake to S3 later

7\. Spark to Glue/EMR later



\## Current Local Project



The local Docker project remains the main working demo.

AWS Phase 1 only prepares the safe cloud foundation.


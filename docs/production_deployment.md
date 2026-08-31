# GuardWAF Production Deployment Guide (AWS ECS Fargate & ALB)

This guide provides instructions for deploying GuardWAF Control Plane to production using AWS ECS Fargate, Application Load Balancers, Amazon RDS PostgreSQL, ElastiCache Redis, and AWS Secrets Manager.

---

## 🏛️ Production AWS Architecture Topology

```text
                         INTERNET / PUBLIC CLIENTS
                                    │
                                    ▼
                          Application Load Balancer (ALB)
                                HTTPS / TLS (443)
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │      VPC PRIVATE SUBNETS      │
                    │                               │
                    │        ECS FARGATE            │
                    │   GuardWAF Control Plane      │
                    │    (Security-Hardened)        │
                    └───────────────┬───────────────┘
                                    │
                        ┌───────────┴───────────┐
                        ▼                       ▼
                   Amazon RDS              ElastiCache
                   PostgreSQL                 Redis
                (Durable Metadata)      (Distributed State)
```

---

## 🚀 Deployment Steps

### 1. Provision Infrastructure with Terraform
```bash
cd infra/terraform
terraform init
terraform plan -out=tfplan
terraform apply tfplan
```

### 2. Build & Push Production Container Image to ECR
```bash
# Authenticate ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com

# Build multi-stage non-root container image
docker build -t guardwaf-control-plane:v1.0.0 .
docker tag guardwaf-control-plane:v1.0.0 123456789012.dkr.ecr.us-east-1.amazonaws.com/guardwaf-control-plane:v1.0.0
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/guardwaf-control-plane:v1.0.0
```

### 3. Store Production Secrets in AWS Secrets Manager
```bash
aws secretsmanager create-secret --name "guardwaf/production/secrets-GUARDWAF_SECRET_KEY" --secret-string "YOUR_CRYPTOGRAPHIC_HMAC_SECRET_KEY_32BYTES"
aws secretsmanager create-secret --name "guardwaf/production/secrets-DATABASE_URL" --secret-string "postgresql://user:pass@guardwaf-db.rds.amazonaws.com:5432/guardwaf"
```

### 4. Deploy ECS Task & Service
```bash
aws ecs register-task-definition --cli-input-json file://infra/ecs-task-def.json
aws ecs update-service --cluster guardwaf-cluster-production --service guardwaf-service --task-definition guardwaf-control-plane-production
```

### 5. Automated Staging Smoke Tests
```bash
python scripts/smoke_test.py --target-url https://controlplane.guardwaf.io
```

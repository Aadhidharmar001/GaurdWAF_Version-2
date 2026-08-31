# GuardWAF DevSecOps Deployment Checklist (AWS ECS Fargate + Amazon RDS)

Use this checklist to ensure a secure, production-ready deployment of GuardWAF.

---

## 1. Prerequisites & Environment
- [ ] AWS CLI v2 installed and configured with `ap-south-1` region credentials.
- [ ] Docker Engine running locally.
- [ ] AWS Account ID verified (`161012475437`).

## 2. Security & Credentials (AWS Secrets Manager)
- [ ] Created AWS Secrets Manager secret `guardwaf/db_url` containing the PostgreSQL connection string:
  `postgresql://guardwaf:STRONG_PASSWORD@<rds-endpoint>:5432/guardwaf`
- [ ] Created AWS Secrets Manager secret `guardwaf/openai_key` containing the OpenAI API Key.
- [ ] Created IAM Execution Role `ecsTaskExecutionRole` with inline policy granting `secretsmanager:GetSecretValue` permissions.

## 3. Database Layer (Amazon RDS PostgreSQL)
- [ ] Provisioned Amazon RDS PostgreSQL 15 instance `guardwaf-db`.
- [ ] Configured RDS Security Group (`guardwaf-db-sg`) to allow inbound TCP 5432 from ECS Task Security Group (`guardwaf-ecs-sg`).
- [ ] Database `guardwaf` created and initial connectivity verified.

## 4. Container Image Management (Amazon ECR)
- [ ] ECR repository `guardwaf` created in region `ap-south-1`.
- [ ] Docker image built: `docker build -t guardwaf:latest .`
- [ ] Docker image tagged: `docker tag guardwaf:latest 161012475437.dkr.ecr.ap-south-1.amazonaws.com/guardwaf:latest`
- [ ] Image pushed to ECR: `docker push 161012475437.dkr.ecr.ap-south-1.amazonaws.com/guardwaf:latest`

## 5. Logging & Governance (Amazon CloudWatch)
- [ ] CloudWatch Log Group `/ecs/guardwaf` created in `ap-south-1`.

## 6. ECS Task Definition & Fargate Service
- [ ] Verified `infra/ecs-task-def.json` contains single container `guardwaf-app` (no local postgres sidecar).
- [ ] Container health check configured on `/health`.
- [ ] Registered task definition: `aws ecs register-task-definition --cli-input-json file://infra/ecs-task-def.json`
- [ ] Created ECS Cluster `guardwaf-cluster`.
- [ ] Created ECS Service `guardwaf-service` with Fargate launch type, `assignPublicIp=ENABLED`, and container port 8000 exposed on Security Group.

## 7. Operational Verification
- [ ] Query `/health` endpoint: `http://<fargate-public-ip>:8000/health` (verify database status `"ok"`).
- [ ] Verify Dashboard UI: `http://<fargate-public-ip>:8000/static/index.html`.
- [ ] Run compliance suite against live Fargate instance: `BASE_URL="http://<fargate-public-ip>:8000" python simulation.py`.
- [ ] Inspect CloudWatch Logs under `/ecs/guardwaf`.

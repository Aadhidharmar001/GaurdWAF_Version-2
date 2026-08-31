# GuardWAF Production AWS Infrastructure Blueprint
# Provisions VPC, Private Subnets, ECS Fargate, ALB, RDS PostgreSQL, ElastiCache Redis, AWS Secrets Manager, and CloudWatch

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# --- VPC & Subnets ---
resource "aws_vpc" "guardwaf_vpc" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name        = "guardwaf-vpc-${var.environment}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

resource "aws_subnet" "public_a" {
  vpc_id                  = aws_vpc.guardwaf_vpc.id
  cidr_block              = var.public_subnet_a_cidr
  availability_zone       = "${var.aws_region}a"
  map_public_ip_on_launch = true

  tags = { Name = "guardwaf-pub-a-${var.environment}" }
}

resource "aws_subnet" "public_b" {
  vpc_id                  = aws_vpc.guardwaf_vpc.id
  cidr_block              = var.public_subnet_b_cidr
  availability_zone       = "${var.aws_region}b"
  map_public_ip_on_launch = true

  tags = { Name = "guardwaf-pub-b-${var.environment}" }
}

resource "aws_subnet" "private_a" {
  vpc_id            = aws_vpc.guardwaf_vpc.id
  cidr_block        = var.private_subnet_a_cidr
  availability_zone = "${var.aws_region}a"

  tags = { Name = "guardwaf-priv-a-${var.environment}" }
}

resource "aws_subnet" "private_b" {
  vpc_id            = aws_vpc.guardwaf_vpc.id
  cidr_block        = var.private_subnet_b_cidr
  availability_zone = "${var.aws_region}b"

  tags = { Name = "guardwaf-priv-b-${var.environment}" }
}

# --- Security Groups ---
resource "aws_security_group" "alb_sg" {
  name        = "guardwaf-alb-sg-${var.environment}"
  description = "ALB Public HTTPS Security Group"
  vpc_id      = aws_vpc.guardwaf_vpc.id

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "ecs_sg" {
  name        = "guardwaf-ecs-sg-${var.environment}"
  description = "ECS Fargate Task Security Group"
  vpc_id      = aws_vpc.guardwaf_vpc.id

  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb_sg.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "db_sg" {
  name        = "guardwaf-db-sg-${var.environment}"
  description = "RDS PostgreSQL Security Group"
  vpc_id      = aws_vpc.guardwaf_vpc.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_sg.id]
  }
}

resource "aws_security_group" "redis_sg" {
  name        = "guardwaf-redis-sg-${var.environment}"
  description = "ElastiCache Redis Security Group"
  vpc_id      = aws_vpc.guardwaf_vpc.id

  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_sg.id]
  }
}

# --- Application Load Balancer ---
resource "aws_lb" "guardwaf_alb" {
  name               = "guardwaf-alb-${var.environment}"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_sg.id]
  subnets            = [aws_subnet.public_a.id, aws_subnet.public_b.id]

  tags = { Environment = var.environment }
}

resource "aws_lb_target_group" "guardwaf_tg" {
  name        = "guardwaf-tg-${var.environment}"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.guardwaf_vpc.id
  target_type = "ip"

  health_check {
    path                = "/health/live"
    interval            = 15
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
    matcher             = "200"
  }
}

# --- Secrets Manager ---
resource "aws_secretsmanager_secret" "guardwaf_secrets" {
  name = "guardwaf/production/secrets-${var.environment}"
}

# --- ECS Cluster & Fargate Service ---
resource "aws_ecs_cluster" "guardwaf_cluster" {
  name = "guardwaf-cluster-${var.environment}"
}

resource "aws_cloudwatch_log_group" "ecs_logs" {
  name              = "/ecs/guardwaf-control-plane-${var.environment}"
  retention_in_days = 30
}

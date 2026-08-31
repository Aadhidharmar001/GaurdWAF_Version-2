variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "environment" {
  type    = string
  default = "production"
}

variable "vpc_cidr" {
  type    = string
  default = "10.0.0.0/16"
}

variable "public_subnet_a_cidr" {
  type    = string
  default = "10.0.1.0/24"
}

variable "public_subnet_b_cidr" {
  type    = string
  default = "10.0.2.0/24"
}

variable "private_subnet_a_cidr" {
  type    = string
  default = "10.0.10.0/24"
}

variable "private_subnet_b_cidr" {
  type    = string
  default = "10.0.11.0/24"
}

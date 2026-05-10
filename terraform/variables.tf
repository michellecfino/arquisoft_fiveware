# =============================================================================
# variables.tf
# Defines all input variables for the AWS infrastructure.
# Tácticas de Bass: (soporte de infraestructura para las tácticas de disponibilidad)
# =============================================================================

variable "project_name" {
  description = "Project name used as prefix for all resources"
  type        = string
  default     = "disponibilidad-asr"
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "ec2_instance_type" {
  description = "EC2 instance type for application servers"
  type        = string
  default     = "t2.micro"
}

variable "ec2_instance_count" {
  description = "Number of EC2 application server instances"
  type        = number
  default     = 4
}

variable "ec2_volume_size_gb" {
  description = "Root EBS volume size in GiB per EC2 instance"
  type        = number
  default     = 12
}

variable "rds_instance_class" {
  description = "RDS instance class for PostgreSQL"
  type        = string
  default     = "db.t3.micro"
}

variable "rds_db_name" {
  description = "Name of the PostgreSQL database"
  type        = string
  default     = "disponibilidad_db"
}

variable "rds_username" {
  description = "Master username for the RDS instance"
  type        = string
  default     = "dbadmin"
  sensitive   = true
}

variable "rds_password" {
  description = "Master password for the RDS instance"
  type        = string
  sensitive   = true
  default     = "12345678"
}

variable "ssh_password" {
  description = "Password for the 'miche' user on EC2 instances (SSH PasswordAuthentication)."
  type        = string
  sensitive   = true
  default     = "12345678"
}

variable "ubuntu_ami" {
  description = "Ubuntu 24.04 LTS AMI ID for us-east-1 (update if region changes)"
  type        = string
  # Ubuntu 24.04 LTS (Noble Numbat) official AMI for us-east-1
  default     = "ami-0e86e20dae9224db8"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets (one per AZ for EC2)"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets (one per AZ for RDS)"
  type        = list(string)
  default     = ["10.0.11.0/24", "10.0.12.0/24"]
}

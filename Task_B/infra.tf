terraform {
  required_providers {
    aws = {
      source = "hashicorp/aws"
      version = "~> 5.87.0"
    }
  }

  required_version = ">= 1.3.0"
}


# Variables
variable "region" {
  default = "us-west-2"
}

variable "bucket_name" {
  default = "airflow-dag-bucket-adsum-test-victor"
}

variable "deployment_name" {
  description = "The name of the database deployment."
  type = string
  default = "adsum-app-postgres-dev"
}

provider "aws" {
    region     = var.region
}

# Step 1: Create S3 Bucket
resource "aws_s3_bucket" "airflow_dag_bucket" {
  bucket = var.bucket_name

  tags = {
    Name        = "Airflow DAG bucket"
    Environment = "Dev"
  }
}

# Step 2: Upload the DAG to S3
resource "aws_s3_object" "upload_dag" {
  bucket = aws_s3_bucket.airflow_dag_bucket.bucket
  key    = "dags/etl_transactions.py" # Path inside the S3 bucket
  source = "${path.module}/../Task_A/dags/etl_transactions.py" # Local path to DAG file

  content_type = "application/x-python-code"
}


# Step 3: Output for reference
output "dag_s3_path" {
  value = "s3://${aws_s3_bucket.airflow_dag_bucket.bucket}/dags/etl_transactions.py"
}


# Generate random password (used for RDS database)
resource "random_password" "master_password"{
  length           = 16
  special          = true
  override_special = "_!%^"
}

# Set up audit logging and cloudwatch logging for RDS DB instance
resource "aws_db_parameter_group" "postgresql_param_group" {
  name   = var.deployment_name
  family = "postgres16"

  parameter {
    name  = "log_connections"
    value = "1"
    apply_method = "immediate"
  }

  parameter {
    name  = "log_disconnections"
    value = "1"
    apply_method = "immediate"
  }

  parameter {
    name  = "log_error_verbosity"
    value = "verbose"
    apply_method = "immediate"
  }

  parameter {
    name  = "log_min_duration_statement"
    value = "5000"
    apply_method = "immediate"
  }

  parameter {
    name  = "pgaudit.log"
    value = "all"
    apply_method = "immediate"
  }

  parameter {
    name  = "pgaudit.role"
    value = "rds_pgaudit"
    apply_method = "immediate"
  }

  parameter {
    name  = "shared_preload_libraries"
    value = "pgaudit,pg_stat_statements"
    apply_method = "pending-reboot"
  }
}



# create a RDS Database Instance
resource "aws_db_instance" "adsum-test-db-instance" {
  depends_on           = [aws_db_parameter_group.postgresql_param_group]
  engine               = "Postgres"
  identifier           = "adsum-test-db-instance"
  db_name              = "adsum"
  allocated_storage    =  20
  engine_version       = "16.3"
  instance_class       = "db.t3.micro"
  skip_final_snapshot  = true
  # Credentials
  username             = "adsum_user"
  password             = random_password.master_password.result
  # network
  publicly_accessible =  true
   # audit
  enabled_cloudwatch_logs_exports = ["postgresql","upgrade"]
  parameter_group_name            = aws_db_parameter_group.postgresql_param_group.name
}

resource "aws_secretsmanager_secret" "rds_credentials" {
  name = "adsum_db_credentials_2"
}

# Store the database's credentials on AWS Secrets manager
resource "aws_secretsmanager_secret_version" "rds_credentials" {
  secret_id     = aws_secretsmanager_secret.rds_credentials.id
  secret_string = jsonencode({
      "user": aws_db_instance.adsum-test-db-instance.username,
      "password": aws_db_instance.adsum-test-db-instance.password,
      "dbname":  aws_db_instance.adsum-test-db-instance.db_name,
      "host": aws_db_instance.adsum-test-db-instance.address,
      "port": aws_db_instance.adsum-test-db-instance.port,
  })
}
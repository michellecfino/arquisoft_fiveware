# =========================================================
# Terraform — Experimento Seguridad Sprint 4
# Cognito + Servicio de Seguridad Node.js + RDS
# =========================================================

# ── Cognito User Pool ──────────────────────────────────
resource "aws_cognito_user_pool" "biteco_pool" {
  name = "biteco-seguridad-pool"

  password_policy {
    minimum_length    = 8
    require_uppercase = true
    require_numbers   = true
    require_symbols   = false
  }

  auto_verified_attributes = ["email"]
  tags = { Name = "biteco-seguridad-pool" }
}

resource "aws_cognito_user_pool_client" "biteco_client" {
  name         = "biteco-seguridad-client"
  user_pool_id = aws_cognito_user_pool.biteco_pool.id

  explicit_auth_flows = [
    "ALLOW_USER_PASSWORD_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH"
  ]

  token_validity_units {
    id_token = "hours"
  }
  id_token_validity = 1
}

resource "aws_cognito_user_group" "financiero" {
  name         = "financiero"
  user_pool_id = aws_cognito_user_pool.biteco_pool.id
  description  = "Grupo con acceso a reportes financieros"
}

resource "aws_cognito_user_group" "tecnico" {
  name         = "tecnico"
  user_pool_id = aws_cognito_user_pool.biteco_pool.id
  description  = "Grupo tecnico sin acceso a reportes financieros"
}

# ── Security Group Servicio de Seguridad ───────────────
resource "aws_security_group" "seguridad_sg" {
  name        = "biteco-seguridad-sg"
  description = "Servicio de Seguridad Node.js"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Node.js"
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "biteco-seguridad-sg" }
}

# ── EC2 Servicio de Seguridad ──────────────────────────
resource "aws_instance" "seguridad" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.instance_type
  key_name                    = var.key_name
  associate_public_ip_address = true
  vpc_security_group_ids      = [aws_security_group.seguridad_sg.id]

  user_data = <<-EOF
    #!/bin/bash
    set -e
    apt-get update -y
    apt-get install -y curl git
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y nodejs
    cd /opt
    git clone -b seguridad https://github.com/michellecfino/arquisoft_fiveware.git
    cd arquisoft_fiveware/biteco/servicio_seguridad
    npm install
    npm install -g pm2
    COGNITO_REGION=us-east-1 \
    COGNITO_USER_POOL=${aws_cognito_user_pool.biteco_pool.id} \
    GRUPO_PERMITIDO=financiero \
    PORT=3000 \
    pm2 start src/index.js --name seguridad
    pm2 startup
    pm2 save
  EOF

  tags = { Name = "servicio-seguridad" }
}

# ── RDS PostgreSQL para el Manejador de Reportes ──────
resource "aws_db_instance" "bd_reportes" {
  identifier        = "biteco-seg-bd-reportes"
  engine            = "postgres"
  engine_version    = "16"
  instance_class    = "db.t3.micro"
  allocated_storage = 20
  db_name           = "biteco"
  username          = "postgres"
  password          = "postgres123"

  vpc_security_group_ids = [aws_security_group.traffic_db.id]
  skip_final_snapshot    = true
  publicly_accessible    = true

  tags = { Name = "biteco-seg-bd-reportes" }
}

# ── Outputs ────────────────────────────────────────────
output "cognito_user_pool_id" {
  value = aws_cognito_user_pool.biteco_pool.id
}

output "cognito_client_id" {
  value = aws_cognito_user_pool_client.biteco_client.id
}

output "seguridad_ip" {
  value       = aws_instance.seguridad.public_ip
  description = "IP del Servicio de Seguridad Node.js"
}

output "seguridad_url" {
  value = "http://${aws_instance.seguridad.public_ip}:3000"
}

output "bd_reportes_endpoint" {
  value = aws_db_instance.bd_reportes.address
}
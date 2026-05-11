# =============================================================================
# deployments.tf — Automatización Post-Despliegue
# =============================================================================

resource "null_resource" "db_seeding" {
  # Asegurar que se ejecute después de que la base de datos esté lista
  depends_on = [aws_db_instance.postgres]

  # Se ejecuta cada vez que cambia el endpoint de la DB o el script de seeding
  triggers = {
    db_endpoint = aws_db_instance.postgres.address
    script_hash = filemd5("${path.module}/seed_db.sql")
  }

  provisioner "local-exec" {
    command = <<EOF
      echo "Descargando certificado SSL de AWS RDS..."
      curl -sLO https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem
      
      echo "Ejecutando script de seeding (seed_db.sql) en ${aws_db_instance.postgres.address}..."
      PGPASSWORD="${var.rds_password}" psql \
        --host="${aws_db_instance.postgres.address}" \
        --port="${aws_db_instance.postgres.port}" \
        --username="${var.rds_username}" \
        --dbname="${var.rds_db_name}" \
        --file="${path.module}/seed_db.sql"
    EOF
  }
}

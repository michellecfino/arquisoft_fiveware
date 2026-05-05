from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Pobla la base de datos con esquema, seed y datos de prueba para el experimento de confidencialidad"

    def handle(self, *args, **kwargs):
        self.stdout.write("Iniciando población de la base de datos...")

        with connection.cursor() as cursor:

            # ── SCHEMAS ──────────────────────────────────────────
            self.stdout.write("Creando schemas...")
            cursor.execute("CREATE SCHEMA IF NOT EXISTS nucleo;")
            cursor.execute("CREATE SCHEMA IF NOT EXISTS nube;")
            cursor.execute("CREATE SCHEMA IF NOT EXISTS reportes;")

            # ── ENUMS ─────────────────────────────────────────────
            self.stdout.write("Creando enums...")
            cursor.execute("""
                DO $$ BEGIN
                    CREATE TYPE nucleo.moneda_enum AS ENUM ('USD', 'EUR', 'COP');
                EXCEPTION WHEN duplicate_object THEN NULL;
                END $$;
            """)
            cursor.execute("""
                DO $$ BEGIN
                    CREATE TYPE nube.proveedor_enum AS ENUM ('AWS', 'AZURE', 'GCP');
                EXCEPTION WHEN duplicate_object THEN NULL;
                END $$;
            """)

            # ── TABLAS ────────────────────────────────────────────
            self.stdout.write("Creando tablas...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS nucleo.empresas (
                    id_empresa SERIAL PRIMARY KEY,
                    nombre VARCHAR(150) UNIQUE NOT NULL,
                    tamano VARCHAR(50),
                    sector VARCHAR(100)
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS nucleo.areas (
                    id_area SERIAL PRIMARY KEY,
                    id_empresa INTEGER REFERENCES nucleo.empresas(id_empresa),
                    nombre VARCHAR(150),
                    UNIQUE(id_empresa, nombre)
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS nucleo.proyectos (
                    id_proyecto SERIAL PRIMARY KEY,
                    id_empresa INTEGER REFERENCES nucleo.empresas(id_empresa),
                    id_area INTEGER REFERENCES nucleo.areas(id_area),
                    nombre VARCHAR(150),
                    creado_en TIMESTAMP DEFAULT NOW(),
                    UNIQUE(id_empresa, nombre)
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS nucleo.usuarios (
                    id_usuario SERIAL PRIMARY KEY,
                    id_empresa INTEGER REFERENCES nucleo.empresas(id_empresa),
                    nombre VARCHAR(120),
                    correo VARCHAR(150),
                    rol VARCHAR(40),
                    activo BOOLEAN DEFAULT TRUE,
                    creado_en TIMESTAMP DEFAULT NOW()
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS nucleo.notificaciones (
                    id_notificacion BIGSERIAL PRIMARY KEY,
                    id_usuario INTEGER,
                    id_reporte BIGINT,
                    correo_destino VARCHAR(150),
                    fecha_creacion TIMESTAMP DEFAULT NOW(),
                    fecha_envio TIMESTAMP,
                    estado VARCHAR(30),
                    broker_message_id VARCHAR(200),
                    smtp_message_id VARCHAR(200),
                    intentos INTEGER DEFAULT 0,
                    mensaje TEXT,
                    url_acceso TEXT,
                    error_detalle TEXT
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS nube.regiones (
                    id_region SERIAL PRIMARY KEY,
                    nombre VARCHAR(80) UNIQUE NOT NULL
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS nube.cuentas_cloud (
                    id_cuenta_cloud SERIAL PRIMARY KEY,
                    identificador VARCHAR(100) UNIQUE NOT NULL,
                    proveedor nube.proveedor_enum
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS nube.servicios_cloud (
                    id_servicio_cloud BIGSERIAL PRIMARY KEY,
                    identificador_cuenta_cloud VARCHAR(100),
                    nombre VARCHAR(100),
                    UNIQUE(identificador_cuenta_cloud, nombre)
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS nube.registros_consumo (
                    id_registro_consumo BIGSERIAL PRIMARY KEY,
                    id_proyecto INTEGER,
                    id_servicio_cloud BIGINT,
                    id_region INTEGER,
                    fecha_consumo DATE,
                    grupo_recurso VARCHAR(150),
                    costo DECIMAL(14,4),
                    moneda nucleo.moneda_enum DEFAULT 'USD',
                    id_recurso_crudo TEXT
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reportes.reportes_generados (
                    id_reporte BIGSERIAL PRIMARY KEY,
                    id_empresa INTEGER,
                    id_area INTEGER,
                    id_proyecto INTEGER,
                    id_usuario INTEGER,
                    anio INTEGER,
                    mes INTEGER,
                    moneda VARCHAR(10),
                    total_costo DECIMAL(14,4),
                    cantidad_registros INTEGER,
                    request_id VARCHAR(100) UNIQUE,
                    instancia_origen VARCHAR(100),
                    fecha_generacion TIMESTAMP DEFAULT NOW()
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reportes.resumen_mensual_costos (
                    id SERIAL PRIMARY KEY,
                    id_empresa INTEGER,
                    id_area INTEGER,
                    id_proyecto INTEGER,
                    anio INTEGER,
                    mes INTEGER,
                    moneda nucleo.moneda_enum DEFAULT 'USD',
                    costo_total DECIMAL(14,4) DEFAULT 0,
                    cantidad_registros INTEGER DEFAULT 0,
                    ultima_actualizacion TIMESTAMP DEFAULT NOW(),
                    UNIQUE(id_empresa, id_area, id_proyecto, anio, mes)
                );
            """)

            # ── SEED ──────────────────────────────────────────────
            self.stdout.write("Cargando seed...")

            cursor.execute("""
                INSERT INTO nube.regiones (nombre)
                VALUES ('us east 2'),('us east'),('global'),('us-east-2'),
                       ('us-east-1'),('us-west-2'),('us-central1'),('us-east1')
                ON CONFLICT (nombre) DO NOTHING;
            """)

            cursor.execute("""
                INSERT INTO nucleo.empresas (nombre, tamano, sector)
                SELECT 'empresa-' || gs, 'mediana', 'tecnologia'
                FROM generate_series(1, 40) gs
                ON CONFLICT (nombre) DO NOTHING;
            """)

            cursor.execute("""
                INSERT INTO nucleo.areas (id_empresa, nombre)
                SELECT e.id_empresa, 'area-' || a.n
                FROM nucleo.empresas e
                CROSS JOIN generate_series(1, 5) a(n)
                ON CONFLICT (id_empresa, nombre) DO NOTHING;
            """)

            cursor.execute("""
                INSERT INTO nucleo.proyectos (id_empresa, id_area, nombre)
                SELECT a.id_empresa, a.id_area, 'proyecto-' || a.id_area || '-' || gs
                FROM nucleo.areas a
                CROSS JOIN generate_series(1, 15) gs
                ON CONFLICT (id_empresa, nombre) DO NOTHING;
            """)

            cursor.execute("""
                INSERT INTO nube.cuentas_cloud (identificador, proveedor)
                SELECT 'cuenta-aws-' || gs, 'AWS'::nube.proveedor_enum
                FROM generate_series(1, 80) gs
                ON CONFLICT (identificador) DO NOTHING;
            """)

            cursor.execute("""
                INSERT INTO nube.cuentas_cloud (identificador, proveedor)
                SELECT 'cuenta-azure-' || gs, 'AZURE'::nube.proveedor_enum
                FROM generate_series(1, 80) gs
                ON CONFLICT (identificador) DO NOTHING;
            """)

            cursor.execute("""
                INSERT INTO nube.cuentas_cloud (identificador, proveedor)
                SELECT 'cuenta-gcp-' || gs, 'GCP'::nube.proveedor_enum
                FROM generate_series(1, 40) gs
                ON CONFLICT (identificador) DO NOTHING;
            """)

            cursor.execute("""
                INSERT INTO nube.servicios_cloud (identificador_cuenta_cloud, nombre)
                SELECT c.identificador, s.nombre
                FROM nube.cuentas_cloud c
                JOIN (VALUES
                    ('Azure App Service'),('Azure DNS'),('Container Registry'),
                    ('Virtual Network'),('Virtual Machines'),('Storage'),
                    ('Application Gateway'),('Azure Bastion'),('Bandwidth'),
                    ('Log Analytics'),('Load Balancer'),('Microsoft Entra Domain Services')
                ) AS s(nombre) ON c.proveedor = 'AZURE'
                ON CONFLICT (identificador_cuenta_cloud, nombre) DO NOTHING;
            """)

            cursor.execute("""
                INSERT INTO nube.servicios_cloud (identificador_cuenta_cloud, nombre)
                SELECT c.identificador, s.nombre
                FROM nube.cuentas_cloud c
                JOIN (VALUES
                    ('EC2'),('S3'),('RDS'),('Lambda'),('CloudFront'),
                    ('VPC'),('Elastic Load Balancing'),('Route 53'),('ECR'),('CloudWatch')
                ) AS s(nombre) ON c.proveedor = 'AWS'
                ON CONFLICT (identificador_cuenta_cloud, nombre) DO NOTHING;
            """)

            cursor.execute("""
                INSERT INTO nube.servicios_cloud (identificador_cuenta_cloud, nombre)
                SELECT c.identificador, s.nombre
                FROM nube.cuentas_cloud c
                JOIN (VALUES
                    ('Compute Engine'),('Cloud Storage'),('Cloud SQL'),('Cloud Functions'),
                    ('BigQuery'),('Cloud DNS'),('Artifact Registry'),
                    ('Cloud Load Balancing'),('VPC'),('Cloud Logging')
                ) AS s(nombre) ON c.proveedor = 'GCP'
                ON CONFLICT (identificador_cuenta_cloud, nombre) DO NOTHING;
            """)

            # ── USUARIOS ──────────────────────────────────────────
            self.stdout.write("Insertando usuarios...")
            cursor.execute("""
                INSERT INTO nucleo.usuarios (id_empresa, nombre, correo, rol, activo)
                SELECT id_empresa, 'usuario-' || id_empresa,
                       'user' || id_empresa || '@biteco.com', 'admin', true
                FROM nucleo.empresas
                ON CONFLICT DO NOTHING;
            """)

            # ── DATOS DE CONSUMO ──────────────────────────────────
            self.stdout.write("Insertando registros de consumo para empresa 1...")
            cursor.execute("""
                INSERT INTO nube.registros_consumo
                (id_proyecto, id_servicio_cloud, id_region, fecha_consumo, costo, moneda, id_recurso_crudo)
                SELECT
                    p.id_proyecto,
                    sc.id_servicio_cloud,
                    1,
                    (date_trunc('month', d::timestamp) + (random()*27)::int * interval '1 day')::date,
                    (random()*1000)::decimal(14,4),
                    'USD',
                    'recurso-' || p.id_proyecto || '-' || sc.id_servicio_cloud
                FROM nucleo.proyectos p
                CROSS JOIN nube.servicios_cloud sc
                CROSS JOIN generate_series('2026-01-01'::date,'2026-04-30'::date,'1 month'::interval) d
                WHERE p.id_empresa = 1 AND sc.id_servicio_cloud <= 5
                LIMIT 50000;
            """)

        self.stdout.write(self.style.SUCCESS("Base de datos poblada exitosamente."))
        self.stdout.write(self.style.SUCCESS("El sistema está listo para el experimento de confidencialidad."))
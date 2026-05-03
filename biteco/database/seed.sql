INSERT INTO nube.regiones (nombre)
VALUES ('us east 2'), ('us east'), ('global'), ('us-east-2'), ('us-east-1'), ('us-west-2'), ('us-central1'), ('us-east1')
ON CONFLICT (nombre) DO NOTHING;

INSERT INTO nucleo.empresas (nombre, tamano, sector)
SELECT 'empresa-' || gs, 'mediana', 'tecnologia'
FROM generate_series(1, 40) gs
ON CONFLICT (nombre) DO NOTHING;

INSERT INTO nucleo.areas (id_empresa, nombre)
SELECT e.id_empresa, 'area-' || a.n
FROM nucleo.empresas e
CROSS JOIN generate_series(1, 5) a(n)
ON CONFLICT (id_empresa, nombre) DO NOTHING;

INSERT INTO nucleo.proyectos (id_empresa, id_area, nombre)
SELECT a.id_empresa, a.id_area, 'proyecto-' || a.id_area || '-' || gs
FROM nucleo.areas a
CROSS JOIN generate_series(1, 15) gs
ON CONFLICT (id_empresa, nombre) DO NOTHING;

INSERT INTO nube.cuentas_cloud (identificador, proveedor)
SELECT 'cuenta-aws-' || gs, 'AWS'::nube.proveedor_enum
FROM generate_series(1, 80) gs
ON CONFLICT (identificador) DO NOTHING;

INSERT INTO nube.cuentas_cloud (identificador, proveedor)
SELECT 'cuenta-azure-' || gs, 'AZURE'::nube.proveedor_enum
FROM generate_series(1, 80) gs
ON CONFLICT (identificador) DO NOTHING;

INSERT INTO nube.cuentas_cloud (identificador, proveedor)
SELECT 'cuenta-gcp-' || gs, 'GCP'::nube.proveedor_enum
FROM generate_series(1, 40) gs
ON CONFLICT (identificador) DO NOTHING;

INSERT INTO nube.servicios_cloud (identificador_cuenta_cloud, nombre)
SELECT c.identificador, s.nombre
FROM nube.cuentas_cloud c
JOIN (
    VALUES
    ('Azure App Service'),
    ('Azure DNS'),
    ('Container Registry'),
    ('Virtual Network'),
    ('Virtual Machines'),
    ('Storage'),
    ('Application Gateway'),
    ('Azure Bastion'),
    ('Bandwidth'),
    ('Log Analytics'),
    ('Load Balancer'),
    ('Microsoft Entra Domain Services')
) AS s(nombre)
ON c.proveedor = 'AZURE'
ON CONFLICT (identificador_cuenta_cloud, nombre) DO NOTHING;

INSERT INTO nube.servicios_cloud (identificador_cuenta_cloud, nombre)
SELECT c.identificador, s.nombre
FROM nube.cuentas_cloud c
JOIN (
    VALUES
    ('EC2'),
    ('S3'),
    ('RDS'),
    ('Lambda'),
    ('CloudFront'),
    ('VPC'),
    ('Elastic Load Balancing'),
    ('Route 53'),
    ('ECR'),
    ('CloudWatch')
) AS s(nombre)
ON c.proveedor = 'AWS'
ON CONFLICT (identificador_cuenta_cloud, nombre) DO NOTHING;

INSERT INTO nube.servicios_cloud (identificador_cuenta_cloud, nombre)
SELECT c.identificador, s.nombre
FROM nube.cuentas_cloud c
JOIN (
    VALUES
    ('Compute Engine'),
    ('Cloud Storage'),
    ('Cloud SQL'),
    ('Cloud Functions'),
    ('BigQuery'),
    ('Cloud DNS'),
    ('Artifact Registry'),
    ('Cloud Load Balancing'),
    ('VPC'),
    ('Cloud Logging')
) AS s(nombre)
ON c.proveedor = 'GCP'
ON CONFLICT (identificador_cuenta_cloud, nombre) DO NOTHING;

INSERT INTO reportes.resumen_mensual_costos
(
    id_empresa,
    id_area,
    id_proyecto,
    anio,
    mes,
    moneda,
    costo_total,
    cantidad_registros,
    ultima_actualizacion
)
SELECT
    p.id_empresa,
    p.id_area,
    p.id_proyecto,
    periodo.anio,
    periodo.mes,
    'USD'::nucleo.moneda_enum,
    0, -- costo en 0
    0, -- cantidad en 0
    NOW()
FROM nucleo.proyectos p
CROSS JOIN (
    VALUES
    (2026, 1),
    (2026, 2),
    (2026, 3),
    (2026, 4)
) AS periodo(anio, mes)
ON CONFLICT (id_empresa, id_area, id_proyecto, anio, mes) DO NOTHING;
INSERT INTO nube.regiones (nombre)
VALUES
('us east 2'),
('us east'),
('global'),
('us-east-2'),
('us-east-1'),
('us-west-2'),
('us-central1'),
('us-east1')
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

INSERT INTO nucleo.usuarios (id_empresa, nombre, correo, rol)
SELECT
    e.id_empresa,
    'usuario-' || e.id_empresa || '-' || gs,
    'usuario-' || e.id_empresa || '-' || gs || '@test.local',
    'ADMIN'
FROM nucleo.empresas e
CROSS JOIN generate_series(1, 5) gs
ON CONFLICT (correo) DO NOTHING;

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

INSERT INTO nube.proyectos_cuentas_cloud (id_proyecto, identificador_cuenta_cloud)
SELECT
    p.id_proyecto,
    cc.identificador
FROM nucleo.proyectos p
JOIN LATERAL (
    SELECT identificador
    FROM nube.cuentas_cloud
    ORDER BY random()
    LIMIT 1
) cc ON TRUE
ON CONFLICT (id_proyecto, identificador_cuenta_cloud) DO NOTHING;

INSERT INTO nube.registros_consumo
(
    id_proyecto,
    id_servicio_cloud,
    id_region,
    fecha_consumo,
    grupo_recurso,
    costo,
    moneda,
    id_recurso_crudo
)
SELECT
    p.id_proyecto,
    sc.id_servicio_cloud,
    r.id_region,
    make_date(periodo.anio, periodo.mes, LEAST(dia.n, 28)),
    'rg-' || p.id_proyecto || '-' || periodo.mes,
    round((10 + random() * 490)::numeric, 2),
    'USD'::nucleo.moneda_enum,
    'recurso-' || p.id_proyecto || '-' || periodo.anio || '-' || periodo.mes || '-' || dia.n
FROM nucleo.proyectos p
JOIN nube.proyectos_cuentas_cloud pcc
  ON pcc.id_proyecto = p.id_proyecto
JOIN LATERAL (
    SELECT sc.id_servicio_cloud
    FROM nube.servicios_cloud sc
    WHERE sc.identificador_cuenta_cloud = pcc.identificador_cuenta_cloud
    ORDER BY random()
    LIMIT 1
) sc ON TRUE
JOIN LATERAL (
    SELECT id_region
    FROM nube.regiones
    ORDER BY random()
    LIMIT 1
) r ON TRUE
CROSS JOIN (
    VALUES
    (2026, 1),
    (2026, 2),
    (2026, 3),
    (2026, 4)
) AS periodo(anio, mes)
CROSS JOIN generate_series(1, 20) dia(n);
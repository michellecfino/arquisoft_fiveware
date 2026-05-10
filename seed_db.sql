-- =============================================================================
-- SCRIPT DE SEEDING - EXPERIMENTO DISPONIBILIDAD ASR
-- PostgreSQL 14 (RDS) - Compatible con CloudShell
-- =============================================================================

-- 1. Poblar nucleo.empresas (5 Empresas)
INSERT INTO nucleo.empresas (nombre)
VALUES 
    ('Tech Solutions SAS'),
    ('Global Dynamics Corp'),
    ('Innovación Digital Ltda'),
    ('Sistemas Avanzados S.A.'),
    ('Servicios Cloud Pro')
ON CONFLICT (nombre) DO NOTHING;

-- 2. Poblar nucleo.areas (2 Áreas por cada empresa)
-- Usamos una subconsulta para obtener todas las empresas insertadas
INSERT INTO nucleo.areas (empresa_id, nombre)
SELECT e.id, sub.area_nombre
FROM nucleo.empresas e
CROSS JOIN (
    VALUES ('Infraestructura y Redes'), ('Operaciones Digitales')
) AS sub(area_nombre)
ON CONFLICT (nombre) DO NOTHING;

-- 3. Poblar nucleo.proyectos (3 Proyectos por cada área)
-- Esto generará 5 empresas * 2 áreas * 3 proyectos = 30 proyectos
INSERT INTO nucleo.proyectos (area_id, nombre)
SELECT a.id, sub.proyecto_nombre
FROM nucleo.areas a
CROSS JOIN (
    VALUES ('Migración AWS 2026'), ('Optimización PostgreSQL'), ('Ciberseguridad Perimetral')
) AS sub(proyecto_nombre)
ON CONFLICT (nombre) DO NOTHING;

-- 4. Poblar nube.registros_consumo (10 registros por proyecto para 2026, Enero a Mayo)
-- Generamos exactamente 2 registros por mes para cada proyecto
INSERT INTO nube.registros_consumo (proyecto_id, monto, moneda, proveedor, fecha)
SELECT 
    p.id,
    (random() * 1000 + 100)::numeric(10,2), -- Monto entre 100 y 1100
    (CASE WHEN random() > 0.5 THEN 'USD'::nucleo.moneda_enum ELSE 'COP'::nucleo.moneda_enum END),
    (CASE WHEN random() > 0.5 THEN 'AWS'::nube.proveedor_enum ELSE 'AZURE'::nube.proveedor_enum END),
    (make_date(2026, month_num, 1) + (random() * 27 || ' days')::interval)::date
FROM nucleo.proyectos p
CROSS JOIN generate_series(1, 5) AS month_num  -- Enero (1) a Mayo (5)
CROSS JOIN generate_series(1, 2) AS repeat_num -- 2 registros por mes = 10 por proyecto
ON CONFLICT DO NOTHING;

-- 5. Poblar reportes.reportes_generados (1 reporte por cada proyecto)
-- Simula un estado 'Sano' (Health)
INSERT INTO reportes.reportes_generados (proyecto_id, nombre_reporte, estado, fecha_generacion)
SELECT 
    p.id,
    'Reporte Mensual Salud - ' || p.nombre,
    'Sano', -- Se asume que 'Sano' es un valor válido para el estado (o se puede castear a nucleo.estado_notificacion_enum si aplica)
    now()
FROM nucleo.proyectos p
ON CONFLICT DO NOTHING;

-- Nota: Si nucleo.estado_notificacion_enum se usa en una tabla de auditoría, 
-- se puede agregar aquí un registro de ejemplo si es necesario.

CREATE SCHEMA IF NOT EXISTS nucleo;
CREATE SCHEMA IF NOT EXISTS nube;
CREATE SCHEMA IF NOT EXISTS reportes;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_type t
        JOIN pg_namespace n ON n.oid = t.typnamespace
        WHERE t.typname = 'estado_notificacion_enum'
        AND n.nspname = 'nucleo'
    ) THEN
        CREATE TYPE nucleo.estado_notificacion_enum AS ENUM ('Pendiente', 'Enviada', 'Fallida');
    END IF;
END
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_type t
        JOIN pg_namespace n ON n.oid = t.typnamespace
        WHERE t.typname = 'moneda_enum'
        AND n.nspname = 'nucleo'
    ) THEN
        CREATE TYPE nucleo.moneda_enum AS ENUM ('USD', 'COP', 'EUR');
    END IF;
END
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_type t
        JOIN pg_namespace n ON n.oid = t.typnamespace
        WHERE t.typname = 'proveedor_enum'
        AND n.nspname = 'nube'
    ) THEN
        CREATE TYPE nube.proveedor_enum AS ENUM ('AWS', 'AZURE', 'GCP');
    END IF;
END
$$;

CREATE TABLE IF NOT EXISTS nucleo.empresas (
    id_empresa SERIAL PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL UNIQUE,
    tamano VARCHAR(40) NOT NULL,
    sector VARCHAR(100) NOT NULL,
    creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS nucleo.areas (
    id_area SERIAL PRIMARY KEY,
    id_empresa INT NOT NULL REFERENCES nucleo.empresas(id_empresa) ON DELETE CASCADE,
    nombre VARCHAR(120) NOT NULL,
    creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (id_empresa, nombre)
);

CREATE TABLE IF NOT EXISTS nucleo.proyectos (
    id_proyecto SERIAL PRIMARY KEY,
    id_empresa INT NOT NULL REFERENCES nucleo.empresas(id_empresa) ON DELETE CASCADE,
    id_area INT NOT NULL REFERENCES nucleo.areas(id_area) ON DELETE CASCADE,
    nombre VARCHAR(150) NOT NULL,
    creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (id_empresa, nombre)
);

CREATE TABLE IF NOT EXISTS nucleo.usuarios (
    id_usuario SERIAL PRIMARY KEY,
    id_empresa INT NOT NULL REFERENCES nucleo.empresas(id_empresa) ON DELETE CASCADE,
    nombre VARCHAR(120) NOT NULL,
    correo VARCHAR(150) NOT NULL UNIQUE,
    rol VARCHAR(40) NOT NULL,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS nube.cuentas_cloud (
    identificador VARCHAR(100) PRIMARY KEY,
    proveedor nube.proveedor_enum NOT NULL
);

CREATE TABLE IF NOT EXISTS nube.proyectos_cuentas_cloud (
    id_proyecto INT NOT NULL REFERENCES nucleo.proyectos(id_proyecto) ON DELETE CASCADE,
    identificador_cuenta_cloud VARCHAR(100) NOT NULL REFERENCES nube.cuentas_cloud(identificador) ON DELETE CASCADE,
    PRIMARY KEY (id_proyecto, identificador_cuenta_cloud)
);

CREATE TABLE IF NOT EXISTS nube.servicios_cloud (
    id_servicio_cloud BIGSERIAL PRIMARY KEY,
    identificador_cuenta_cloud VARCHAR(100) NOT NULL REFERENCES nube.cuentas_cloud(identificador) ON DELETE CASCADE,
    nombre VARCHAR(100) NOT NULL,
    UNIQUE (identificador_cuenta_cloud, nombre)
);

CREATE TABLE IF NOT EXISTS nube.regiones (
    id_region SERIAL PRIMARY KEY,
    nombre VARCHAR(80) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS nube.registros_consumo (
    id_registro_consumo BIGSERIAL PRIMARY KEY,
    id_proyecto INT NOT NULL REFERENCES nucleo.proyectos(id_proyecto) ON DELETE CASCADE,
    id_servicio_cloud BIGINT NOT NULL REFERENCES nube.servicios_cloud(id_servicio_cloud) ON DELETE CASCADE,
    id_region INT REFERENCES nube.regiones(id_region) ON DELETE SET NULL,
    fecha_consumo DATE NOT NULL,
    grupo_recurso VARCHAR(150),
    costo NUMERIC(14,4) NOT NULL,
    moneda nucleo.moneda_enum NOT NULL,
    id_recurso_crudo TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reportes.resumen_mensual_costos (
    id_resumen BIGSERIAL PRIMARY KEY,
    id_empresa INT NOT NULL REFERENCES nucleo.empresas(id_empresa) ON DELETE CASCADE,
    id_area INT NOT NULL REFERENCES nucleo.areas(id_area) ON DELETE CASCADE,
    id_proyecto INT NOT NULL REFERENCES nucleo.proyectos(id_proyecto) ON DELETE CASCADE,
    anio INT NOT NULL CHECK (anio >= 2000),
    mes INT NOT NULL CHECK (mes BETWEEN 1 AND 12),
    moneda nucleo.moneda_enum NOT NULL,
    costo_total NUMERIC(14,4) NOT NULL DEFAULT 0,
    cantidad_registros INT NOT NULL DEFAULT 0,
    ultima_actualizacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (id_empresa, id_area, id_proyecto, anio, mes)
);

CREATE TABLE IF NOT EXISTS reportes.detalle_servicio (
    id_detalle BIGSERIAL PRIMARY KEY,
    id_resumen BIGINT NOT NULL REFERENCES reportes.resumen_mensual_costos(id_resumen) ON DELETE CASCADE,
    nombre_servicio VARCHAR(100) NOT NULL,
    cantidad_registros INT NOT NULL DEFAULT 0,
    costo_total NUMERIC(14,4) NOT NULL DEFAULT 0,
    moneda nucleo.moneda_enum NOT NULL,
    ultima_actualizacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (id_resumen, nombre_servicio)
);

CREATE TABLE IF NOT EXISTS reportes.reportes_generados (
    id_reporte BIGSERIAL PRIMARY KEY,
    id_resumen BIGINT NOT NULL REFERENCES reportes.resumen_mensual_costos(id_resumen) ON DELETE CASCADE,
    fecha_generacion TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS nucleo.notificaciones (
    id_notificacion BIGSERIAL PRIMARY KEY,
    id_usuario INT NOT NULL REFERENCES nucleo.usuarios(id_usuario) ON DELETE CASCADE,
    id_reporte BIGINT NOT NULL REFERENCES reportes.reportes_generados(id_reporte) ON DELETE CASCADE,
    fecha_envio TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    estado nucleo.estado_notificacion_enum NOT NULL DEFAULT 'Pendiente',
    mensaje TEXT NOT NULL,
    url_acceso TEXT
);

CREATE INDEX IF NOT EXISTS idx_registros_consumo_proyecto_fecha
ON nube.registros_consumo(id_proyecto, fecha_consumo);

CREATE INDEX IF NOT EXISTS idx_resumen_proyecto_periodo
ON reportes.resumen_mensual_costos(id_proyecto, anio, mes);

CREATE INDEX IF NOT EXISTS idx_detalle_resumen
ON reportes.detalle_servicio(id_resumen);
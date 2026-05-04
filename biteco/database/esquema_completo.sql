-- SCHEMAS
CREATE SCHEMA IF NOT EXISTS nucleo;
CREATE SCHEMA IF NOT EXISTS nube;
CREATE SCHEMA IF NOT EXISTS reportes;

-- ENUMS
CREATE TYPE nucleo.moneda_enum AS ENUM ('USD', 'EUR', 'COP');
CREATE TYPE nube.proveedor_enum AS ENUM ('AWS', 'AZURE', 'GCP');

-- NUCLEO
CREATE TABLE IF NOT EXISTS nucleo.empresas (
    id_empresa SERIAL PRIMARY KEY,
    nombre VARCHAR(150) UNIQUE NOT NULL,
    tamano VARCHAR(50),
    sector VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS nucleo.areas (
    id_area SERIAL PRIMARY KEY,
    id_empresa INTEGER REFERENCES nucleo.empresas(id_empresa),
    nombre VARCHAR(150),
    UNIQUE(id_empresa, nombre)
);

CREATE TABLE IF NOT EXISTS nucleo.proyectos (
    id_proyecto SERIAL PRIMARY KEY,
    id_empresa INTEGER REFERENCES nucleo.empresas(id_empresa),
    id_area INTEGER REFERENCES nucleo.areas(id_area),
    nombre VARCHAR(150),
    creado_en TIMESTAMP DEFAULT NOW(),
    UNIQUE(id_empresa, nombre)
);

CREATE TABLE IF NOT EXISTS nucleo.usuarios (
    id_usuario SERIAL PRIMARY KEY,
    id_empresa INTEGER REFERENCES nucleo.empresas(id_empresa),
    nombre VARCHAR(120),
    correo VARCHAR(150),
    rol VARCHAR(40),
    activo BOOLEAN DEFAULT TRUE,
    creado_en TIMESTAMP DEFAULT NOW()
);

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

-- NUBE
CREATE TABLE IF NOT EXISTS nube.regiones (
    id_region SERIAL PRIMARY KEY,
    nombre VARCHAR(80) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS nube.cuentas_cloud (
    id_cuenta_cloud SERIAL PRIMARY KEY,
    identificador VARCHAR(100) UNIQUE NOT NULL,
    proveedor nube.proveedor_enum
);

CREATE TABLE IF NOT EXISTS nube.servicios_cloud (
    id_servicio_cloud BIGSERIAL PRIMARY KEY,
    identificador_cuenta_cloud VARCHAR(100),
    nombre VARCHAR(100),
    UNIQUE(identificador_cuenta_cloud, nombre)
);

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

-- REPORTES
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
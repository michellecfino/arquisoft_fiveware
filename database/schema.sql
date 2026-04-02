-- =========================
-- CREACIÓN DE ESQUEMAS
-- =========================
CREATE SCHEMA IF NOT EXISTS nucleo;
CREATE SCHEMA IF NOT EXISTS costos_nube;
CREATE SCHEMA IF NOT EXISTS reportes;

-- =========================
-- TABLAS NÚCLEO
-- =========================

CREATE TABLE IF NOT EXISTS nucleo.empresas (
    id_empresa SERIAL PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS nucleo.areas (
    id_area SERIAL PRIMARY KEY,
    id_empresa INT NOT NULL REFERENCES nucleo.empresas(id_empresa),
    nombre VARCHAR(120) NOT NULL,
    creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (id_empresa, nombre)
);

CREATE TABLE IF NOT EXISTS nucleo.proyectos (
    id_proyecto SERIAL PRIMARY KEY,
    id_empresa INT NOT NULL,
    id_area INT NOT NULL,
    nombre VARCHAR(150) NOT NULL,
    creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_empresa) REFERENCES nucleo.empresas(id_empresa),
    FOREIGN KEY (id_area) REFERENCES nucleo.areas(id_area),
    UNIQUE (id_empresa, nombre)
);

CREATE TABLE IF NOT EXISTS nucleo.usuarios (
    id_usuario SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    correo VARCHAR(150) UNIQUE NOT NULL,
    id_empresa INT NOT NULL REFERENCES nucleo.empresas(id_empresa),
    creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =========================
-- TABLAS COSTOS NUBE
-- =========================

CREATE TABLE IF NOT EXISTS costos_nube.cuentas_cloud (
    id_cuenta_cloud SERIAL PRIMARY KEY,
    id_empresa INT NOT NULL REFERENCES nucleo.empresas(id_empresa),
    proveedor VARCHAR(30) NOT NULL,
    identificador_externo VARCHAR(120) NOT NULL,
    creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (proveedor, identificador_externo)
);

CREATE TABLE IF NOT EXISTS costos_nube.consumos_crudos (
    id_consumo_crudo BIGSERIAL PRIMARY KEY,
    id_empresa INT NOT NULL REFERENCES nucleo.empresas(id_empresa),
    id_area INT NULL REFERENCES nucleo.areas(id_area),
    id_proyecto INT NULL REFERENCES nucleo.proyectos(id_proyecto),
    id_cuenta_cloud INT NOT NULL REFERENCES costos_nube.cuentas_cloud(id_cuenta_cloud),
    fecha_consumo DATE NOT NULL,
    tipo_servicio VARCHAR(100) NOT NULL,
    region VARCHAR(80) NULL,
    grupo_recurso VARCHAR(150) NULL,
    costo NUMERIC(14,4) NOT NULL,
    moneda VARCHAR(10) NOT NULL,
    proyecto VARCHAR(150) NULL,
    id_recurso_crudo TEXT NOT NULL,
    creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_consumos_crudos_empresa_fecha
ON costos_nube.consumos_crudos (id_empresa, fecha_consumo);

CREATE INDEX IF NOT EXISTS idx_consumos_crudos_empresa_proyecto_fecha
ON costos_nube.consumos_crudos (id_empresa, id_proyecto, fecha_consumo);

-- =========================
-- TABLAS AGREGADAS REPORTES
-- =========================

CREATE TABLE IF NOT EXISTS reportes.resumen_mensual_costos (
    id_empresa INT NOT NULL REFERENCES nucleo.empresas(id_empresa),
    id_area INT NOT NULL REFERENCES nucleo.areas(id_area),
    id_proyecto INT NOT NULL REFERENCES nucleo.proyectos(id_proyecto),
    anio INT NOT NULL,
    mes INT NOT NULL,
    moneda VARCHAR(10) NOT NULL,
    costo_total NUMERIC(14,4) NOT NULL DEFAULT 0,
    cantidad_registros INT NOT NULL DEFAULT 0,
    ultima_actualizacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id_empresa, id_area, id_proyecto, anio, mes)
);

CREATE TABLE IF NOT EXISTS reportes.desglose_mensual_servicios (
    id_empresa INT NOT NULL REFERENCES nucleo.empresas(id_empresa),
    id_area INT NOT NULL REFERENCES nucleo.areas(id_area),
    id_proyecto INT NOT NULL REFERENCES nucleo.proyectos(id_proyecto),
    anio INT NOT NULL,
    mes INT NOT NULL,
    tipo_servicio VARCHAR(100) NOT NULL,
    cantidad_registros INT NOT NULL DEFAULT 0,
    costo_total NUMERIC(14,4) NOT NULL DEFAULT 0,
    moneda VARCHAR(10) NOT NULL,
    ultima_actualizacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id_empresa, id_area, id_proyecto, anio, mes, tipo_servicio)
);

CREATE INDEX IF NOT EXISTS idx_desglose_empresa_proyecto_periodo
ON reportes.desglose_mensual_servicios (id_empresa, id_proyecto, anio, mes);

-- =========================
-- TABLA DE NOTIFICACIONES
-- =========================

CREATE TABLE IF NOT EXISTS nucleo.notificaciones (
    id_notificacion BIGSERIAL PRIMARY KEY,
    id_usuario INT NOT NULL REFERENCES nucleo.usuarios(id_usuario),
    id_proyecto INT NULL REFERENCES nucleo.proyectos(id_proyecto),
    fecha_envio TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    estado VARCHAR(50) NOT NULL
);
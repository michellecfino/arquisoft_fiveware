-- =========================
-- CREACIÓN DE ESQUEMAS
-- =========================
CREATE SCHEMA IF NOT EXISTS nucleo;
CREATE SCHEMA IF NOT EXISTS facturacion;
CREATE SCHEMA IF NOT EXISTS analitica;

-- =========================
-- TABLAS CORE
-- =========================

-- EMPRESAS
CREATE TABLE nucleo.empresas (
    id_empresa SERIAL PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ÁREAS
CREATE TABLE nucleo.areas (
    id_area SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL
);

-- PROYECTOS
CREATE TABLE nucleo.proyectos (
    id_proyecto SERIAL PRIMARY KEY,
    id_empresa INT NOT NULL,
    id_area INT NOT NULL,
    nombre VARCHAR(150) NOT NULL,

    FOREIGN KEY (id_empresa) REFERENCES nucleo.empresas(id_empresa),
    FOREIGN KEY (id_area) REFERENCES nucleo.areas(id_area)
);

-- USUARIOS
CREATE TABLE nucleo.usuarios (
    id_usuario SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    empresa_id INT NOT NULL,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (empresa_id) REFERENCES nucleo.empresas(id_empresa)
);

-- =========================
-- TABLA CRUDA (FACTURACION)
-- =========================
CREATE TABLE facturacion.consumo_cloud (
    id_consumo BIGSERIAL PRIMARY KEY,
    empresa_id INT NOT NULL,
    proyecto_id INT NOT NULL,
    servicio VARCHAR(100),
    costo NUMERIC(12,2) NOT NULL,
    fecha TIMESTAMP NOT NULL,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (empresa_id) REFERENCES nucleo.empresas(id_empresa),
    FOREIGN KEY (proyecto_id) REFERENCES nucleo.proyectos(id_proyecto)
);

-- ÍNDICE PARA OPTIMIZAR BÚSQUEDAS
CREATE INDEX idx_consumo_empresa_proyecto_fecha
ON facturacion.consumo_cloud (empresa_id, proyecto_id, fecha);

-- =========================
-- TABLA AGREGADA (ANALITICA)
-- =========================
CREATE TABLE analitica.resumen_mensual_costos (
    empresa_id INT NOT NULL,
    proyecto_id INT NOT NULL,
    anio INT NOT NULL,
    mes INT NOT NULL,

    costo_total NUMERIC(14,2) NOT NULL DEFAULT 0,
    ultima_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (empresa_id, proyecto_id, anio, mes),

    FOREIGN KEY (empresa_id) REFERENCES nucleo.empresas(id_empresa),
    FOREIGN KEY (proyecto_id) REFERENCES nucleo.proyectos(id_proyecto)
);

-- =========================
-- TABLA DE NOTIFICACIONES
-- =========================
CREATE TABLE nucleo.notificaciones (
    id_notificacion BIGSERIAL PRIMARY KEY,
    id_usuario INT NOT NULL,
    id_proyecto INT,
    fecha_envio TIMESTAMP,
    estado VARCHAR(50),
    intentos INT DEFAULT 0,

    FOREIGN KEY (id_usuario) REFERENCES nucleo.usuarios(id_usuario)
);

-- =============================================================================
-- INICIALIZACIÓN DE ESQUEMAS (Obligatorio para nueva BD en AWS Academy)
-- =============================================================================
CREATE SCHEMA IF NOT EXISTS nucleo;
CREATE SCHEMA IF NOT EXISTS nube;
CREATE SCHEMA IF NOT EXISTS reportes;

-- =============================================================================
-- ESTRUCTURAS DE TABLAS
-- =============================================================================
CREATE TABLE IF NOT EXISTS nucleo.empresas (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS nucleo.areas (
    id SERIAL PRIMARY KEY,
    empresa_id INT REFERENCES nucleo.empresas(id),
    nombre VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS nucleo.proyectos (
    id SERIAL PRIMARY KEY,
    area_id INT REFERENCES nucleo.areas(id),
    nombre VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS nube.registros_consumo (
    id SERIAL PRIMARY KEY,
    proyecto_id INT REFERENCES nucleo.proyectos(id),
    monto NUMERIC(10,2) NOT NULL,
    moneda VARCHAR(10) DEFAULT 'USD'
);

CREATE TABLE IF NOT EXISTS reportes.reportes_generados (
    id SERIAL PRIMARY KEY,
    proyecto_id INT REFERENCES nucleo.proyectos(id),
    nombre_reporte VARCHAR(150) NOT NULL,
    status VARCHAR(50) NOT NULL,
    response_time_ms INT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Limpiar registros viejos si existieran
TRUNCATE TABLE nube.registros_consumo RESTART IDENTITY CASCADE;
TRUNCATE TABLE reportes.reportes_generados RESTART IDENTITY CASCADE;
TRUNCATE TABLE nucleo.proyectos RESTART IDENTITY CASCADE;
TRUNCATE TABLE nucleo.areas RESTART IDENTITY CASCADE;
TRUNCATE TABLE nucleo.empresas RESTART IDENTITY CASCADE;

-- =============================================================================
-- INYECCIÓN DE DATOS (Experimento ASR de Disponibilidad)
-- =============================================================================
INSERT INTO nucleo.empresas (id, nombre) VALUES (1, 'Empresa Matriz ASR');
INSERT INTO nucleo.areas (id, empresa_id, nombre) VALUES (1, 1, 'División de Distribución Lógica');
INSERT INTO nucleo.proyectos (id, area_id, nombre) VALUES (1, 1, 'Proyecto Central Rendimiento');

INSERT INTO nube.registros_consumo (proyecto_id, monto, moneda) 
VALUES (1, 1500.50, 'USD');

INSERT INTO reportes.reportes_generados (proyecto_id, nombre_reporte, status, response_time_ms)
VALUES 
  (1, 'Reporte de Telemetría Nivel 1', 'success', 85),
  (1, 'Reporte de Latencia Inyectada', 'graceful_failure', 380);

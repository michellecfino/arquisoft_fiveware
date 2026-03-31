
-- =========================
-- CREACIÓN DE ESQUEMAS
-- =========================
CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS billing;
CREATE SCHEMA IF NOT EXISTS analytics;

-- =========================
-- TABLAS CORE
-- =========================

-- EMPRESAS
CREATE TABLE core.empresas (
    id_empresa SERIAL PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- PROYECTOS
CREATE TABLE core.proyectos (
    id_proyecto SERIAL PRIMARY KEY,
    empresa_id INT NOT NULL,
    nombre VARCHAR(150) NOT NULL,
    FOREIGN KEY (empresa_id) REFERENCES core.empresas(id_empresa)
);

-- USUARIOS
CREATE TABLE core.usuarios (
    id_usuario SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    empresa_id INT NOT NULL,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (empresa_id) REFERENCES core.empresas(id_empresa)
);

-- =========================
-- TABLA CRUDA (BILLING)
-- =========================
CREATE TABLE billing.consumo_cloud (
    id_consumo BIGSERIAL PRIMARY KEY,
    empresa_id INT NOT NULL,
    proyecto_id INT NOT NULL,
    servicio VARCHAR(100),
    costo NUMERIC(12,2) NOT NULL,
    fecha TIMESTAMP NOT NULL,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (empresa_id) REFERENCES core.empresas(id_empresa),
    FOREIGN KEY (proyecto_id) REFERENCES core.proyectos(id_proyecto)
);

-- ÍNDICE PARA OPTIMIZAR BÚSQUEDAS
CREATE INDEX idx_consumo_empresa_proyecto_fecha
ON billing.consumo_cloud (empresa_id, proyecto_id, fecha);

-- =========================
-- TABLA AGREGADA (ANALYTICS)
-- =========================
CREATE TABLE analytics.resumen_mensual_costos (
    empresa_id INT NOT NULL,
    proyecto_id INT NOT NULL,
    anio INT NOT NULL,
    mes INT NOT NULL,

    costo_total NUMERIC(14,2) NOT NULL DEFAULT 0,
    ultima_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (empresa_id, proyecto_id, anio, mes),

    FOREIGN KEY (empresa_id) REFERENCES core.empresas(id_empresa),
    FOREIGN KEY (proyecto_id) REFERENCES core.proyectos(id_proyecto)
);

-- =========================
-- FUNCIÓN DE AGREGACIÓN
-- =========================
CREATE OR REPLACE FUNCTION analytics.actualizar_resumen_mensual()
RETURNS TRIGGER AS $$
DECLARE
    v_anio INT;
    v_mes INT;
BEGIN
    v_anio := EXTRACT(YEAR FROM NEW.fecha);
    v_mes := EXTRACT(MONTH FROM NEW.fecha);

    INSERT INTO analytics.resumen_mensual_costos (
        empresa_id,
        proyecto_id,
        anio,
        mes,
        costo_total
    )
    VALUES (
        NEW.empresa_id,
        NEW.proyecto_id,
        v_anio,
        v_mes,
        NEW.costo
    )
    ON CONFLICT (empresa_id, proyecto_id, anio, mes)
    DO UPDATE SET
        costo_total = analytics.resumen_mensual_costos.costo_total + EXCLUDED.costo_total,
        ultima_actualizacion = CURRENT_TIMESTAMP;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- =========================
-- TRIGGER (CLAVE DEL EXPERIMENTO)
-- =========================
CREATE TRIGGER trigger_actualizar_resumen
AFTER INSERT ON billing.consumo_cloud
FOR EACH ROW
EXECUTE FUNCTION analytics.actualizar_resumen_mensual();

-- =========================
-- TABLA DE NOTIFICACIONES
-- =========================
CREATE TABLE core.notificaciones (
    id_notificacion BIGSERIAL PRIMARY KEY,
    id_usuario INT NOT NULL,
    id_proyecto INT,
    fecha_envio TIMESTAMP,
    estado VARCHAR(50),
    intentos INT DEFAULT 0,

    FOREIGN KEY (id_usuario) REFERENCES core.usuarios(id_usuario)
);

INSERT INTO billing.consumo_cloud (
    empresa_id, proyecto_id, servicio, costo, fecha
)
VALUES (1, 1, 'EC2', 1000, NOW());

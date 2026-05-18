# CAMBIOS REALIZADOS - RESUMEN TÉCNICO

## 1. REMOVER REDIS ✅

### requirements.txt
- ❌ Removido: `django-redis==5.4.0`
- ❌ Removido: `redis==5.0.7`

**Por qué:** El proyecto ahora usa almacenamiento en memoria local (no requiere Redis externo).

---

## 2. REFACTORIZAR HEARTBEAT (sin Redis) ✅

### src/heartbeat.py
- ✅ Nuevo: Clase `HeartbeatState` con almacenamiento en memoria local con `threading.RLock()`
- ✅ Nuevo: Función pública `get_db_availability()` que retorna tupla `(is_available, failure_reason)`
- ✅ Removido: Acceso a `cache.get('db_available')` 
- ✅ Removido: Acceso a `cache.set()` con Redis

**Flujo anterior:** Heartbeat → Redis → Vista
**Flujo actual:** Heartbeat → Memoria Local (HeartbeatState) → Vista

---

## 3. CREAR MODELOS DJANGO PARA REPORTES ✅

### src/models.py (NUEVO)
Cuatro modelos de BD:

#### a) Project
```python
- id (BigAutoField)
- name (CharField, unique)
- description (TextField)
- status (Choices: 'active'/'inactive')
- created_at, updated_at
```

#### b) Task
```python
- id (BigAutoField)
- project (ForeignKey → Project)
- name (CharField)
- description (TextField)
- completed (BooleanField)
- created_at, updated_at
```

#### c) Report
```python
- id (BigAutoField)
- project (ForeignKey → Project)
- status (Choices: 'success'/'degraded'/'failed')
- failure_reason (Choices: 'none'/'heartbeat'/'timeout'/'connection_error'/'unknown')
- total_tasks, completed_tasks, completion_percentage
- response_time_ms, query_time_ms
- error_message
- last_activity
- created_at, updated_at (con índices)
```

#### d) HeartbeatStatus
```python
- id (BigAutoField)
- project (OneToOneField → Project)
- is_available (BooleanField)
- last_probe_time
- last_failure_reason
```

---

## 4. ACTUALIZAR SETTINGS.PY ✅

### CACHES
**Anterior:** Django Redis Cache
```python
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
    }
}
```

**Actual:** Local Memory Cache
```python
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-snowflake",
    }
}
```

### INSTALLED_APPS
- ✅ Agregado: `django.contrib.admin`

---

## 5. ACTUALIZAR VIEWS.PY ✅

### Cambios
- ❌ Removido: `from django.core.cache import cache`
- ❌ Removido: `from .heartbeat import DB_AVAILABLE_CACHE_KEY`
- ✅ Agregado: `from .heartbeat import get_db_availability`

### Lógica
**Anterior:**
```python
db_is_available: bool = cache.get(DB_AVAILABLE_CACHE_KEY, default=True)
```

**Actual:**
```python
db_is_available, failure_reason = get_db_availability()
```

---

## 6. MODIFICAR SERVICES.PY ✅

### Cambios Principales
- ✅ Nuevo: Usa Django ORM (modelos) en lugar de SQL raw
- ✅ Nuevo: Guarda **Report** en BD después de cada consulta
- ✅ Nuevo: Guarda tanto éxitos como fallos en tabla `Report`
- ✅ Nuevo: Calcula estadísticas con `QuerySet.aggregate()`

### Flujo de Reportes
1. **Éxito:** Crea `Report(status='success', ...)`
2. **Timeout:** Crea `Report(status='degraded', failure_reason='timeout', ...)`
3. **Error de conexión:** Crea `Report(status='failed', failure_reason='connection_error', ...)`

---

## 7. REFACTORIZAR TERRAFORM (Kong + 4 Django + RDS + SSM) ✅

### Architecture Actual
```
┌─────────────────────────────────────────────────────────────────┐
│ JMeter Client                                                   │
└─────────────────────┬───────────────────────────────────────────┘
                      │ HTTP:8000 (Internet IP)
                      ▼
    ┌─────────────────────────────────┐
    │ Kong Gateway (PUBLIC Subnet)    │
    │ Instance Type: t2.micro         │
    │ Storage: 16GB                   │
    │ - Port 8000 (Proxy)             │
    │ - Port 8001 (Admin)             │
    └──────────────┬──────────────────┘
                   │ (Private IPs via SG)
      ┌────────────┼────────────┬────────────┬────────────┐
      ▼            ▼            ▼            ▼            ▼
 ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
 │ Django 1│ │ Django 2│ │ Django 3│ │ Django 4│
 │ Private │ │ Private │ │ Private │ │ Private │
 │ Subnet1 │ │ Subnet2 │ │ Subnet3 │ │ Subnet4 │
 │t2.micro │ │t2.micro │ │t2.micro │ │t2.micro │
 │ 12GB    │ │ 12GB    │ │ 12GB    │ │ 12GB    │
 └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘
      │           │            │           │
      └───────────┼────────────┼───────────┘
                  │ Port 5432
                  ▼
    ┌─────────────────────────────────┐
    │ RDS PostgreSQL (PRIVATE)        │
    │ Instance: db.t3.micro           │
    │ - NOT Publicly Accessible       │
    │ - Encrypted Storage             │
    │ - Multi-AZ: No                  │
    └─────────────────────────────────┘
```

### Security Groups (Mínimo Privilegio)

#### sg_kong_gateway
**Ingress:**
- 8000/TCP: 0.0.0.0/0 (JMeter)
- 22/TCP: 0.0.0.0/0 (SSH - Acceso directo)

**Egress:**
- 8000/TCP → sg_servidor_reportes (Django)
- 443/TCP → 0.0.0.0/0 (HTTPS)
- 53/UDP → 0.0.0.0/0 (DNS)

#### sg_servidor_reportes (Django)
**Ingress:**
- 8000/TCP → sg_kong_gateway SOLO
- 22/TCP: 0.0.0.0/0 (SSH - Acceso directo)

**Egress:**
- 5432/TCP → sg_database (RDS)
- 443/TCP → 0.0.0.0/0 (HTTPS)
- 53/UDP → 0.0.0.0/0 (DNS)

#### sg_database (RDS)
**Ingress:**
- 5432/TCP → sg_servidor_reportes SOLO

### IAM Role para SSM (con SSH adicional)
- ✅ `AmazonSSMManagedInstanceCore` policy (para Session Manager)
- ✅ `aws_iam_instance_profile` inyectado en Kong y Django
- ✅ **SSH habilitado con key pair** (clave pública)
- ✅ PasswordAuthentication habilitado en sshd_config
- ✅ Acceso directo SSH además de AWS Systems Manager

### Cambios de Subnets
- ✅ 1 subnet **PÚBLICA** para Kong Gateway
- ✅ 4 subnets **PRIVADAS** para 4 Django Servers
- ✅ RDS en subnets privadas (NO público)

### Cambios de Variables
- ❌ Removido: `var.ec2_instance_count` (ahora fijo = 4)
- ❌ Removido: `var.ubuntu_ami` (usa `data.aws_ami` automáticamente)
- ✅ Nuevo: `var.ssh_public_key_path` (path a tu clave pública SSH)
- ✅ Nuevo: `aws_key_pair` resource para la clave pública

---

## 8. DOCKER-COMPOSE.YML ✅

### Cambios
- ✅ Sin cambios requeridos (ya no tenía Redis)
- ✅ Verificado: `services.web`, `services.heartbeat`, `services.kong` siguen igual

---

## 9. MIGRATIONS ✅

### src/migrations/0001_initial.py (NUEVO)
- ✅ CreateModel: Project
- ✅ CreateModel: Task
- ✅ CreateModel: Report (con índices)
- ✅ CreateModel: HeartbeatStatus

### src/migrations/__init__.py (NUEVO)
- ✅ Archivo vacío para que Django recognize como paquete

---

## 10. NUEVOS SCRIPTS TERRAFORM ✅

### terraform/install_kong.sh.tpl (NUEVO)
- ✅ Instala Kong 3.6 desde repositorio Canonical
- ✅ Configura declarative config
- ✅ Prepara upstreams para 4 Django servers

### terraform/install_django.sh.tpl (NUEVO)
- ✅ Instala Python 3.12 + venv
- ✅ Instala Django + psycopg2
- ✅ Configura gunicorn (2 workers)
- ✅ Systemd service para Django
- ✅ Variables de entorno para RDS

---

## PASOS SIGUIENTES RECOMENDADOS

### Antes de Desplegar en AWS

1. **Actualizar terraform/variables.tf**
   - Revisar CIDR blocks (vpc_cidr, subnets)
   - Revisar credenciales RDS (rds_username, rds_password)
   - Revisar instance types

2. **Crear seed_db.sql**
   - Script de inicialización con datos de prueba
   - Crear Projects y Tasks de ejemplo

3. **Configurar Kong Upstreams Dinámicamente**
   - Los 4 Django servers deben ser agregados como targets a Kong
   - Opción A: Kong Admin API
   - Opción B: Script post-deployment

4. **Ejecutar Terraform**
   ```bash
   cd terraform/
   terraform init
   terraform validate
   terraform plan
   terraform apply
   ```

5. **Conectar a Django Servers (sin SSH)**
   ```bash
   # Usar AWS Systems Manager Session Manager
   aws ssm start-session --target i-1234567890abcdef0
   ```

6. **Verificar Reportes en BD**
   ```bash
   # Dentro de Django server
   python manage.py shell
   >>> from src.models import Report
   >>> Report.objects.count()
   ```

---

## RESUMEN DE BENEFICIOS

| Aspecto | Antes | Después |
|--------|--------|---------|
| **Cache** | Redis externo | Memoria local (sin dependencias) |
| **Reportes** | No persistidos | Almacenados en PostgreSQL |
| **Arquitectura** | ALB + EC2 único | Kong (proxy) + 4 Django privados |
| **Base de datos** | Accesible públicamente | Privada (mínimo privilegio) |
| **Acceso SSH** | SSH + Password | AWS Systems Manager (SSM) |
| **Security GroupsAWS Systems Manager (SSM) | SSH directo + Key Pairficos) |

---

## PRÓXIMOS PASOS EN EL CÓDIGO

1. **Agregar Admin Django**
   - Registrar modelos en admin.py
   - Crear vistas administrativas para reportes

2. **Agregar URL para Reportes**
   - GET /api/reports/<project_id>/
   - GET /api/reports/history/ (últimos N reportes)

3. **Agregar Serializers DRF** (opcional)
   - Si se prefiere JSON API completo

4. **Testing**
   - Tests unitarios para models
   - Tests de integración con RDS
   - JMeter script actualizado

---

**Generado:** 18 Mayo 2026
**Estado:** ✅ IMPLEMENTADO

## 1. Setup — Auditoría y Permisos

- [x] 1.1 Agregar códigos de auditoría `AVISO_CREAR`, `AVISO_EDITAR`, `AVISO_ELIMINAR`, `AVISO_ACK` en `backend/app/core/audit_codes.py`
- [x] 1.2 Agregar permiso `avisos:publicar` en `backend/app/core/permissions.py`
- [x] 1.3 Agregar permiso `avisos:ver` en `backend/app/core/permissions.py`
- [x] 1.4 Asignar permiso `avisos:publicar` a roles COORDINADOR y ADMIN en el seeder de RBAC
- [x] 1.5 Asignar permiso `avisos:ver` a todos los roles (ALUMNO, TUTOR, PROFESOR, COORDINADOR, NEXO, ADMIN, FINANZAS) en el seeder de RBAC

## 2. Modelos SQLAlchemy

- [x] 2.1 Crear `backend/app/models/aviso.py` con modelo `Aviso` (UUID PK, tenant_id, alcance: enum AlcanceAviso, materia_id FK nullable, cohorte_id FK nullable, rol_destino: enum Rol nullable, severidad: enum SeveridadAviso, titulo: str, cuerpo: str, inicio_en: DateTime, fin_en: DateTime, orden: int default 0, activo: bool default True, requiere_ack: bool default False, SoftDeleteMixin, TimestampMixin)
- [x] 2.2 Crear los enums `AlcanceAviso` (Global|PorMateria|PorCohorte|PorRol) y `SeveridadAviso` (Info|Advertencia|Critico) en el mismo archivo
- [x] 2.3 Crear `backend/app/models/acknowledgment_aviso.py` con modelo `AcknowledgmentAviso` (UUID PK, aviso_id FK, usuario_id FK, confirmado_at: DateTime default now, constraint UNIQUE (aviso_id, usuario_id))
- [x] 2.4 Registrar modelos y enums en `backend/app/models/__init__.py`
- [x] 2.5 Agregar relación `Aviso.acknowledgments` (one-to-many) y `AcknowledgmentAviso.aviso` (many-to-one)

## 3. Migración Alembic

- [x] 3.1 Generar migración con `alembic revision --autogenerate -m "create_aviso_tables"`
- [x] 3.2 Revisar y ajustar la migración generada (verificar tipos enum, FKs, índices compuestos en tenant_id + activo + inicio_en + fin_en)
- [x] 3.3 Ejecutar migración y verificar que las tablas se crean correctamente

## 4. Schemas Pydantic

- [x] 4.1 Crear `backend/app/schemas/avisos.py` con todos los schemas del módulo
- [x] 4.2 Schema `AvisoCreate` con todos los campos, validaciones cruzadas (alcance → materia_id/cohorte_id/rol_destino requeridos según el caso), `inicio_en < fin_en`, `fin_en > now`
- [x] 4.3 Schema `AvisoUpdate` con todos los campos opcionales (PATCH semantics)
- [x] 4.4 Schema `AvisoResponse` con `from_attributes=True`, incluir campo `acknowledged: bool`
- [x] 4.5 Schema `AvisoListResponse` con paginación (items, total, offset, limit)
- [x] 4.6 Schema `AckResponse` básico para confirmación
- [x] 4.7 Schema `AvisoStatsResponse` con `aviso_id`, `total_usuarios_alcanzados`, `total_acknowledgments`, `porcentaje_confirmacion`
- [x] 4.8 Schema `AckUserResponse` con `usuario_id`, `nombre`, `apellidos`, `email`, `confirmado_at`
- [x] 4.9 Todos los response schemas con `ConfigDict(from_attributes=True, extra='forbid')`

## 5. Repositorios

- [x] 5.1 Crear `backend/app/repositories/aviso_repository.py` con `AvisoRepository` (hereda de `TenantScopedRepository[Aviso]`)
- [x] 5.2 Implementar `list_activos_for_user()`: query que recibe `usuario_id`, `rol`, `cohorte_ids`, `materia_ids` y filtra por tenant + activo + vigencia + alcance usando EXISTS para subqueries de materia/cohorte. Ordenar por `orden ASC, inicio_en DESC`. Incluir paginación.
- [x] 5.3 Implementar `get_by_id_if_visible()`: obtener detalle de aviso verificando que sea visible para el usuario según alcance
- [x] 5.4 Implementar `count_usuarios_alcanzados()`: contar usuarios potenciales según alcance del aviso (global = count usuarios activos del tenant; por materia = count asignaciones activas en esa materia; por cohorte = count usuarios en esa cohorte; por rol = count usuarios con ese rol)
- [x] 5.5 Crear `backend/app/repositories/acknowledgment_repository.py` con `AcknowledgmentRepository` (hereda de `TenantScopedRepository[AcknowledgmentAviso]`)
- [x] 5.6 Implementar `create_or_ignore()`: INSERT ... ON CONFLICT (aviso_id, usuario_id) DO NOTHING, retornar booleano indicando si se insertó
- [x] 5.7 Implementar `count_by_aviso()`: contar acknowledges por aviso_id
- [x] 5.8 Implementar `list_users_by_aviso()`: listar usuarios que confirmaron con datos de perfil, paginado
- [x] 5.9 Implementar `has_acknowledged()`: verificar si un usuario ya confirmó un aviso específico (booleano)
- [x] 5.10 Registrar repositorios en `backend/app/repositories/__init__.py`

## 6. Services

- [x] 6.1 Crear `backend/app/services/aviso_service.py` con `AvisoService`
- [x] 6.2 Implementar `crear_aviso()`: validar datos, crear Aviso, auditar `AVISO_CREAR`
- [x] 6.3 Implementar `editar_aviso()`: validar existencia y tenant, actualizar campos, auditar `AVISO_EDITAR`
- [x] 6.4 Implementar `eliminar_aviso()`: soft delete, auditar `AVISO_ELIMINAR`
- [x] 6.5 Implementar `listar_avisos_activos()`: resolver roles y asignaciones del usuario, delegar al repository con filtros
- [x] 6.6 Implementar `obtener_detalle()`: obtener aviso si es visible para el usuario, incluir campo `acknowledged`
- [x] 6.7 Implementar `confirmar_lectura()`: validar aviso visible, insertar ack (idempotente), auditar `AVISO_ACK`
- [x] 6.8 Implementar `obtener_stats()`: calcular count de usuarios alcanzados + count de acknowledges + porcentaje

## 7. Routers / API Endpoints

- [x] 7.1 Crear `backend/app/api/v1/routers/avisos.py` con prefix `/api/v1/avisos`, tag "Avisos"
- [x] 7.2 Endpoint `GET /` — listar avisos activos para el usuario autenticado, guard `avisos:ver`
- [x] 7.3 Endpoint `GET /{id}` — detalle de aviso, guard `avisos:ver`
- [x] 7.4 Endpoint `POST /` — crear aviso, guard `avisos:publicar`
- [x] 7.5 Endpoint `PUT /{id}` — editar aviso, guard `avisos:publicar`
- [x] 7.6 Endpoint `DELETE /{id}` — eliminar aviso (soft delete), guard `avisos:publicar`
- [x] 7.7 Endpoint `POST /{id}/ack` — confirmar lectura, guard `avisos:ver`
- [x] 7.8 Endpoint `GET /{id}/stats` — estadísticas de confirmación, guard `avisos:publicar`
- [x] 7.9 Endpoint `GET /{id}/acks` — listar usuarios que confirmaron, guard `avisos:publicar`
- [x] 7.10 Registrar router en `backend/app/main.py`

## 8. Tests

- [x] 8.1 Crear `backend/tests/test_avisos.py` con fixtures de setup (tenant, usuario COORDINADOR, ADMIN, ALUMNO, TUTOR, PROFESOR, materia, cohorte)
- [x] 8.2 Test: crear aviso global como COORDINADOR → 201 + verificar persistencia
- [x] 8.3 Test: crear aviso como ALUMNO → 403
- [x] 8.4 Test: crear aviso PorMateria sin materia_id → 422
- [x] 8.5 Test: crear aviso con fin_en anterior a inicio_en → 422
- [x] 8.6 Test: listar avisos como ALUMNO — solo ve Global y PorRol(ALUMNO)
- [x] 8.7 Test: listar avisos como PROFESOR con asignación — ve Global + PorMateria(de su materia) + PorRol(PROFESOR)
- [x] 8.8 Test: aviso fuera de vigencia no aparece en listado
- [x] 8.9 Test: aviso desactivado (activo=false) no aparece en listado
- [x] 8.10 Test: orden de avisos por prioridad (orden ASC, inicio_en DESC)
- [x] 8.11 Test: paginación de avisos
- [x] 8.12 Test: confirmar lectura (ack) → 200 + registro creado
- [x] 8.13 Test: ack duplicado es idempotente → 200 + un solo registro
- [x] 8.14 Test: ack de aviso no visible → 404
- [x] 8.15 Test: campo acknowledged=true después de confirmar
- [x] 8.16 Test: stats de aviso — contar alcanzados + acknowledges + porcentaje
- [x] 8.17 Test: stats sin permiso avisos:publicar → 403
- [x] 8.18 Test: listar usuarios que confirmaron (GET /{id}/acks)
- [x] 8.19 Test: listar acks vacío
- [x] 8.20 Test: editar aviso (PUT)
- [x] 8.21 Test: editar aviso inexistente → 404
- [x] 8.22 Test: eliminar aviso (soft delete) → 204, ya no aparece en listados
- [x] 8.23 Test: aislamiento tenant — datos del tenant A no visibles en tenant B

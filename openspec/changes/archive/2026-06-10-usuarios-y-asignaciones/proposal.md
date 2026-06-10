## Why

El modelo actual de `User` es mínimo (solo email, nombre, password, 2FA). No incluye los datos de identidad reales (DNI, CUIL, CBU, etc.) que el dominio requiere para liquidaciones, facturación y trazabilidad. Además, el sistema necesita el modelo `Asignacion` que vincula un usuario con un rol dentro de un contexto académico concreto, que es el eje del modelo de autorización.

Sin estas entidades no es posible: liquidar honorarios, facturar, ni granular permisos por contexto (materia/carrera/cohorte).

## What Changes

- **BREAKING**: Extender modelo `User` con campos PII: `dni`, `cuil`, `cbu`, `alias_cbu` (cifrados con AES-256-GCM), `banco`, `regional`, `legajo_profesional`, `facturador`, `estado` (Activo/Inactivo)
- Los campos cifrados (`dni`, `cuil`, `cbu`, `alias_cbu`) se encriptan automáticamente via SQLAlchemy TypeDecorator `EncryptedString`
- Crear modelo `Asignacion` que vincula: `usuario_id`, `rol`, `materia_id` (nullable), `carrera_id` (nullable), `cohorte_id` (nullable), `comisiones`, `responsable_id` (jerarquía), vigencia `desde/hasta`, `estado_vigencia` derivado
- ABM usuarios `/api/v1/admin/usuarios` con permiso `usuarios:gestionar`
- CRUD asignaciones `/api/v1/admin/asignaciones` con permiso `equipos:asignar`
- Migration 006: alter `users` (add PII fields) + create `asignaciones`
- Seed: agregar permisos `usuarios:gestionar` y `equipos:asignar` a roles ADMIN y COORDINADOR

## Capabilities

### New Capabilities
- `usuarios-gestion`: ABM de usuarios con PII cifrada
- `asignaciones`: Gestión de asignaciones usuario ↔ rol ↔ contexto académico con vigencia

### Modified Capabilities
- *(ninguna — capabilities nuevas)*

## Impact

- **Modelo modificado**: `User` — se agregan ~10 campos PII + cifrado
- **Nuevo modelo**: `Asignacion`
- **Nuevo TypeDecorator**: `EncryptedString` en `backend/app/core/encrypted_types.py`
- **Nuevo repositorio**: `AsignacionRepository`
- **Nuevos servicios**: `UsuarioService`, `AsignacionService`
- **Nuevos routers**: `/api/v1/admin/usuarios`, `/api/v1/admin/asignaciones`
- **Migración**: Alembic 006 — alter users + create asignaciones + seed permisos
- **Tests**: PII cifrada no expuesta, unicidad email, vigencia de asignación, multi-rol, jerarquía responsable

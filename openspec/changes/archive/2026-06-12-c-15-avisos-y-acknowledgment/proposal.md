## Why

El sistema necesita un **tablón de avisos institucionales** (F3.5 / HU-14, HU-15) que permita a COORDINADOR y ADMIN publicar notificaciones segmentadas por alcance (global, por materia, por cohorte), rol destinatario, severidad y ventana de vigencia temporal. Los usuarios deben ver solo los avisos que les corresponden según su rol y contexto, y confirmar lectura (acknowledgment) cuando el aviso lo requiera. Los contadores de vistos y acuses se derivan on-the-fly, sin campos denormalizados.

## What Changes

- **Nuevos modelos**: `Aviso` y `AcknowledgmentAviso` con soft delete y multi-tenancy row-level
- **Enum de alcance**: `AlcanceAviso` (Global | PorMateria | PorCohorte | PorRol)
- **Enum de severidad**: `SeveridadAviso` (Info | Advertencia | Critico)
- **Permiso**: `avisos:publicar` asignado a COORDINADOR y ADMIN
- **Códigos de auditoría**: `AVISO_CREAR`, `AVISO_EDITAR`, `AVISO_ELIMINAR`, `AVISO_ACK`
- **Endpoints REST** bajo `/api/v1/avisos/`:
  - CRUD completo de avisos (guard `avisos:publicar`)
  - Listado filtrado por scope del usuario autenticado (sin guard, todos los roles)
  - Confirmación de lectura `POST /avisos/{id}/acknowledge`
  - Métricas de un aviso `GET /avisos/{id}/metricas` (guard `avisos:publicar`)
- **Migración Alembic** para tablas `aviso` y `acknowledgment_aviso`
- **Tests**: filtrado por scope, ventana de vigencia, acknowledgment, orden de prioridad, contadores derivados

## Capabilities

### New Capabilities

- `avisos-gestion`: CRUD de avisos institucionales con alcance, severidad, vigencia y estado activo
- `avisos-acknowledgment`: Confirmación de lectura (ack) por parte de los destinatarios
- `avisos-visibilidad`: Listado filtrado automático según rol, alcance, cohorte y ventana temporal del usuario

### Modified Capabilities

*(ninguna — son capacidades nuevas)*

## Impact

- **BD**: 2 tablas nuevas (`aviso`, `acknowledgment_aviso`) con FKs a `tenant`, `materia`, `cohorte`, `usuario`
- **API**: Nuevo router `avisos.py` con 8 endpoints
- **Auth**: Nuevo permiso `avisos:publicar` en catálogo RBAC; todos los roles tienen acceso implícito a ver sus avisos
- **Audit**: 4 códigos nuevos en `audit_codes.py`
- **Dependencias**: Requiere `C-06` (estructura académica: Materia, Cohorte) y `C-04` (RBAC base)
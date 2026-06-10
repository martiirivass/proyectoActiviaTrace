## Why

La plataforma necesita poblar el padrón de alumnos por materia y cohorte como base para calificaciones, detección de atrasos y comunicación. Sin él ningún módulo downstream (calificaciones, umbrales, comunicaciones) puede operar sobre alumnos reales. Además, la integración con Moodle Web Services permite sincronización automática, reduciendo la carga manual de los docentes.

## What Changes

- Crear modelo `VersionPadron` (versión del padrón, scoped a materia×cohorte, con activa/inactiva)
- Crear modelo `EntradaPadron` (alumno en una versión, con datos desnormalizados y email cifrado)
- Sistema de versionado: al activar una nueva versión, la anterior se desactiva (no se borra)
- Import de padrón desde archivo `.xlsx`/`.csv` con vista previa (F1.3) y confirmación (F1.4)
- Integración Moodle Web Services (`integrations/moodle_ws.py`): sync de usuarios/actividades, sync nocturna + on-demand, errores → 502 con reintento
- Vaciar datos de materia (F1.5, RN-04): elimina todas las versiones y entradas de padrón de una materia (soft delete)
- Audit `PADRON_CARGAR` en todas las operaciones de carga/confirmación
- Endpoints:
  - `POST /api/v1/padron/preview` — subir archivo y obtener vista previa
  - `POST /api/v1/padron/confirm` — confirmar importación (crea versión activa)
  - `GET /api/v1/padron/versions?materia_id=&cohorte_id=` — listar versiones
  - `POST /api/v1/padron/sync-moodle` — disparar sync on-demand
  - `DELETE /api/v1/admin/materias/{id}/vaciar` — vaciar datos de materia

## Capabilities

### New Capabilities
- `padron-ingesta`: Ingestion de padrón de alumnos con soporte de archivos `.xlsx`/`.csv`, vista previa de datos importados, confirmación con versionado (una versión activa por materia×cohorte), listado histórico de versiones.
- `moodle-sync`: Integración con Moodle Web Services para sincronización automática (nocturna + on-demand) de usuarios y actividades del LMS; fallback a importación manual cuando Moodle no expone WS.
- `vaciar-materia`: Operación de limpieza total de datos importados de padrón para una materia (soft delete), scoped a los permisos del docente o coordinador.

### Modified Capabilities
- *(ninguna — es capability nueva)*

## Impact

- **Nuevos modelos**: `VersionPadron`, `EntradaPadron` en `backend/app/models/`
- **Nuevo repositorio**: `PadronRepository` scoped por tenant
- **Nuevo servicio**: `PadronService` con lógica de versionado, import y validación
- **Nueva integración**: `moodle_ws.py` en `backend/app/integrations/`
- **Nuevos schemas**: Pydantic DTOs para preview, confirm, listado de versiones, sync
- **Nuevos routers**: `/api/v1/padron/*` con permiso `padron:importar`, `/api/v1/admin/materias/{id}/vaciar` con `padron:vaciar`
- **Migración**: Alembic `0NN_create_padron_tables` (VersionPadron, EntradaPadron)
- **Audit**: código `PADRON_CARGAR` agregado al catálogo de auditoría
- **Tests**: versionado (activar desactiva anterior), import xlsx/csv, entrada sin usuario_id (alumno sin cuenta), aislamiento tenant, mock Moodle WS + fallback 502

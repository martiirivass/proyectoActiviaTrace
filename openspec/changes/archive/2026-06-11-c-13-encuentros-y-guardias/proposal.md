## Why

Los docentes necesitan planificar y registrar sus encuentros sincrónicos (clases virtuales) de forma recurrente o puntual, y los tutores necesitan registrar las guardias de atención a alumnos. Actualmente no existe un módulo dedicado — cada docente gestiona sus encuentros fuera del sistema, y la coordinación no tiene visibilidad de lo que ocurre en cada comisión. Implementar este módulo permite:

1. Que PROFESORES y COORDINADORES definan cronogramas de encuentros (recurrentes o únicos) y marquen su realización.
2. Que la coordinación supervise transversalmente qué encuentros se realizaron y cuáles no.
3. Que los TUTORES registren guardias y que COORDINADORES/ADMIN puedan consultar y exportar el registro global.
4. Generar bloques HTML embebibles para publicar el cronograma en el aula virtual del LMS.

## What Changes

- **Nuevos modelos**: `SlotEncuentro`, `InstanciaEncuentro`, `Guardia` con soft delete, UUID PK y tenant scope.
- **Endpoints `/api/v1/encuentros/*`**: CRUD de slots (recurrente y único), edición de instancias, generación de HTML para LMS, vista admin transversal.
- **Endpoints `/api/v1/guardias/*`**: registro de guardias (TUTOR), consulta global (COORDINADOR/ADMIN), export.
- **Guard `encuentros:gestionar`**: permiso nuevo que protege todos los endpoints del módulo.
- **Auditoría**: acciones `ENCUENTRO_CREAR`, `ENCUENTRO_EDITAR`, `GUARDIA_REGISTRAR` en audit log.
- **Migración Alembic**: creación de tablas `slot_encuentro`, `instancia_encuentro`, `guardia`.
- **Tests**: generación de instancias recurrentes (cant_semanas), encuentro único, edición de estado, registro de guardia, export HTML, aislamiento tenant.

## Capabilities

### New Capabilities

- `encuentros-slots`: gestión de slots de encuentro — creación de serie recurrente (F6.1, RN-13) y encuentro único (F6.2). Generación automática de N instancias a partir del slot recurrente.
- `encuentros-instancias`: edición individual de instancias de encuentro — cambio de estado (Programado↔Realizado↔Cancelado), actualización de meet_url, video_url, comentario (F6.3).
- `encuentros-export-html`: generación de bloque HTML embebible con el cronograma de encuentros para publicar en el LMS (F6.4).
- `encuentros-admin`: vista transversal de todos los encuentros del tenant para COORDINADOR/ADMIN (F6.5).
- `guardias-registro`: registro de guardias por TUTOR, consulta global y exportación para COORDINADOR/ADMIN (F6.6).

### Modified Capabilities

*(Ninguna — este change introduce capacidades nuevas, no modifica especificaciones existentes.)*

## Impact

- **Backend**: 3 nuevos modelos, 2 nuevos repositorios (`encuentro_repository.py`, `guardia_repository.py`), 1 nuevo service (`encuentro_service.py`, `guardia_service.py`), 2 nuevos routers (`encuentros.py`, `guardias.py`), schemas Pydantic para cada endpoint, nuevo código de auditoría `ENCUENTRO_CREAR`, `ENCUENTRO_EDITAR`, `GUARDIA_REGISTRAR`.
- **Base de datos**: migración Alembic con 3 tablas nuevas. Sin cambios en tablas existentes.
- **Permisos**: nuevo permiso `encuentros:gestionar` en la matriz de roles (PROFESOR, TUTOR, COORDINADOR, ADMIN según corresponda).
- **API**: nuevos namespaces `/api/v1/encuentros/` y `/api/v1/guardias/`.
- **Dependencias**: C-07 (usuarios y asignaciones) — completo. Se apoya en `Asignacion` para vincular slots/guardias a docentes/tutores.

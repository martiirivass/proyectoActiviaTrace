
## Why

La gestión de equipos docentes es un proceso manual que consume tiempo cada inicio de cuatrimestre. Actualmente el sistema tiene el modelo `Asignacion` con CRUD básico, pero carece de las operaciones de alto valor que los coordinadores y administrativos necesitan: vista de equipos por docente, asignación masiva, clonación entre períodos, modificación de vigencia en bloque y exportación. Sin estas capacidades, el setup de cada período requiere cientos de operaciones individuales.

## What Changes

Se agregan 5 operaciones sobre el modelo `Asignacion` existente, agrupadas bajo un nuevo router `/api/v1/equipos/`:

- **Mis equipos** (F4.2): endpoint para que un docente (PROFESOR, TUTOR, NEXO, COORDINADOR) vea sus propias asignaciones con filtros, sin necesidad de permisos especiales.
- **Asignación masiva** (F4.4): endpoint que recibe una lista de `usuario_id` y los asigna en bloque a una combinación materia × carrera × cohorte × rol con vigencia común. Atómico: o todas se crean o ninguna.
- **Clonar equipo** (F4.5): endpoint que duplica las asignaciones vigentes de un equipo origen (materia × carrera × cohorte) hacia un destino, respetando RN-12.
- **Modificar vigencia general** (F4.6): actualiza las fechas `desde`/`hasta` de todas las asignaciones de un equipo en una sola operación.
- **Exportar equipo** (F4.7): genera un archivo descargable (CSV) con el detalle de todas las asignaciones del equipo.

Se agrega el audit code `ASIGNACION_MODIFICAR` para las operaciones masivas.

## Capabilities

### New Capabilities
- `equipos-consulta`: Consulta de mis equipos (docente) y gestión de asignaciones individuales (coordinador)
- `asignacion-masiva`: Asignación masiva de docentes a un contexto académico
- `clonar-equipo`: Clonación de equipo docente entre períodos
- `vigencia-equipo`: Modificación de vigencia general del equipo
- `exportar-equipo`: Exportación de equipo docente a archivo

### Modified Capabilities
- `asignaciones`: Se agregan las operaciones de equipo al spec existente (operaciones masivas sobre asignaciones)

## Impact

- **Nuevo router**: `backend/app/api/v1/routers/equipos.py` (operaciones de equipo)
- **Servicio ampliado**: `backend/app/services/asignacion_service.py` — se agregan métodos `asignar_masivo()`, `clonar_equipo()`, `modificar_vigencia_general()`, `exportar_equipo()`
- **Repository ampliado**: `backend/app/repositories/asignacion_repository.py` — se agregan métodos de batch
- **Schemas**: nuevos schemas para request/response de operaciones masivas
- **Nuevo audit code**: `ASIGNACION_MODIFICAR` en `core/audit_codes.py`
- **Nueva migración Alembic**: solo si se requiere nuevo índice compuesto, no hay cambios de schema
- **Tests**: tests para cada nueva operación (masiva, clonado, vigencia, export, mis-equipos)

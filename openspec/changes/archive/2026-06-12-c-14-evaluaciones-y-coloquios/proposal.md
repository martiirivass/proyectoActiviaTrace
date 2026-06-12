## Why

Actualmente no existe un módulo para gestionar evaluaciones orales (coloquios). Los PROFESORES no tienen forma de convocar alumnos, definir cupos por día, ni gestionar la reserva de turnos. Los COORDINADORES no tienen visibilidad de las agendas de coloquio ni del registro académico consolidado. Implementar este módulo cierra el flujo académico completo: importar habilitados → crear convocatoria → reservar turno → registrar nota → auditar.

## What Changes

- **Nuevos modelos**: `Evaluacion` (convocatoria de coloquio), `ReservaEvaluacion` (turno reservado por alumno), `ResultadoEvaluacion` (nota final), con soft delete, UUID PK y tenant scope.
- **Endpoints `/api/v1/evaluaciones/*`**: CRUD de convocatorias, métricas del panel, registro académico.
- **Endpoints `/api/v1/evaluaciones/reservas/*`**: reserva y cancelación de turnos por alumnos, agenda consolidada para coordinación.
- **Permisos nuevos**: `coloquios:gestionar` (PROFESOR/COORDINADOR/ADMIN), `coloquios:reservar` (ALUMNO).
- **Auditoría**: acciones `COLOQUIO_CREAR`, `COLOQUIO_EDITAR`, `COLOQUIO_CERRAR`, `RESERVA_CREAR`, `RESERVA_CANCELAR`, `RESULTADO_REGISTRAR` en audit log.
- **Regla de cupos**: cada convocatoria define días disponibles con cupo máximo; al reservar se decrementa; al cancelar se libera.
- **Migración Alembic**: creación de tablas `evaluaciones`, `reservas_evaluacion`, `resultados_evaluacion`.

## Capabilities

### New Capabilities
- `evaluaciones-convocatorias`: gestión de convocatorias de coloquio — creación con materia, instancia, días disponibles y cupos; edición, cierre; listado tabular con métricas (convocados, reservas, cupos).
- `evaluaciones-reservas`: reserva de turnos por alumno en día disponible con cupo, cancelación (libera cupo), agenda consolidada con filtros para COORDINADOR/ADMIN.
- `evaluaciones-resultados`: registro académico consolidado de notas finales de coloquio; consulta por convocatoria, materia, cohorte.
- `evaluaciones-metricas`: panel de métricas del módulo — total alumnos cargados, instancias activas, reservas activas, notas registradas.

### Modified Capabilities
<!-- Ninguna — son capabilities nuevas -->

## Impact

- **Backend**: 3 nuevos modelos (`Evaluacion`, `ReservaEvaluacion`, `ResultadoEvaluacion`), 2 nuevos repositorios (`evaluacion_repository.py`, `reserva_repository.py`), 2 nuevos services (`evaluacion_service.py`, `reserva_service.py`), 1 nuevo router (`evaluaciones.py`), schemas Pydantic para cada endpoint, códigos de auditoría nuevos.
- **Base de datos**: migración Alembic con 3 tablas nuevas. Sin cambios en tablas existentes.
- **Permisos**: nuevos permisos `coloquios:gestionar` y `coloquios:reservar` en la matriz de roles.
- **API**: nuevo namespace `/api/v1/evaluaciones/` con sub-rutas para reservas y resultados.
- **Dependencias**: C-07 (usuarios y asignaciones) completo para vincular alumnos y docentes; C-06 (estructura académica) para materias y cohortes.
- **Cupo system**: control de concurrencia en reservas (integridad del cupo al reservar/cancelar).

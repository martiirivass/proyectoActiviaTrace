## ADDED Requirements

### Requirement: Monitor de seguimiento extendido agrega rango de fechas (COORDINADOR/ADMIN)

El sistema SHALL extender el monitor de seguimiento (F2.8) para COORDINADOR y ADMIN, agregando la capacidad de filtrar por rango de fechas (F2.9). Tiene alcance global (todos los alumnos del tenant, no solo asignaciones propias).

#### Scenario: Extendido permite filtrar por fecha desde
- **WHEN** un COORDINADOR consulta seguimiento extendido con `fecha_desde = "2026-03-01"`
- **THEN** solo se retornan calificaciones con `importado_at` o `created_at` >= 2026-03-01

#### Scenario: Extendido permite filtrar por fecha hasta
- **WHEN** un COORDINADOR consulta seguimiento extendido con `fecha_hasta = "2026-06-01"`
- **THEN** solo se retornan calificaciones con `importado_at` o `created_at` <= 2026-06-01

#### Scenario: Extendido permite rango completo de fechas
- **WHEN** un ADMIN consulta seguimiento extendido con `fecha_desde = "2026-03-01"` y `fecha_hasta = "2026-06-01"`
- **THEN** solo se retornan calificaciones dentro de ese rango

#### Scenario: Extendido tiene alcance global
- **WHEN** un COORDINADOR consulta seguimiento extendido sin filtros de alumno
- **THEN** se retornan alumnos de todas las materias del tenant (no solo asignaciones propias)

#### Scenario: Extendido combina filtros de seguimiento base + fechas
- **WHEN** un ADMIN consulta seguimiento extendido con `comision = "A"` y `fecha_desde = "2026-03-01"`
- **THEN** se retornan alumnos de comisión A con calificaciones dentro del rango de fechas

#### Scenario: Extendido requiere permiso atrasados:ver con scope global
- **WHEN** un PROFESOR (scope propio) intenta acceder al monitor extendido
- **THEN** el sistema rechaza con 403 Forbidden (el endpoint es solo para COORDINADOR/ADMIN)

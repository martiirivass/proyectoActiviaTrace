## ADDED Requirements

### Requirement: Panel de métricas de coloquios (F7.1)
El sistema SHALL exponer `GET /api/v1/evaluaciones/metricas` para COORDINADOR y ADMIN (permiso `coloquios:gestionar`).
Las métricas SHALL incluir:
- `total_alumnos_cargados`: cantidad de alumnos únicos en padrones de convocatorias activas
- `instancias_activas`: cantidad de convocatorias activas (no cerradas)
- `reservas_activas`: cantidad de reservas en estado Activa
- `notas_registradas`: cantidad de resultados en estado Definitivo
Todas las métricas SHALL estar scoped al tenant del usuario autenticado.

#### Scenario: Consultar métricas del panel
- **WHEN** un COORDINADOR envía GET `/api/v1/evaluaciones/metricas`
- **THEN** el sistema responde con las 4 métricas calculadas para el tenant

#### Scenario: ALUMNO no puede acceder a métricas
- **WHEN** un ALUMNO con permiso `coloquios:reservar` envía GET `/api/v1/evaluaciones/metricas`
- **THEN** el sistema responde 403 Forbidden

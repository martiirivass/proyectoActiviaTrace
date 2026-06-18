## ADDED Requirements

### Requirement: Historial de ejecuciones de cálculo

El frontend SHALL mostrar el historial de ejecuciones de cálculo de liquidaciones con paginación.

#### Scenario: Ver historial
- **WHEN** el usuario navega a la sección de historial (tab o sección expandible)
- **THEN** el frontend llama a `GET /api/v1/liquidaciones/historial?page=1&per_page=20`
- **AND** muestra una tabla con columnas: Fecha, Usuario, Cohorte, Período

#### Scenario: Paginación del historial
- **WHEN** hay más de 20 entradas en el historial
- **THEN** el frontend muestra controles de paginación (anterior/siguiente/números de página)
- **AND** al cambiar de página, llama a `GET /api/v1/liquidaciones/historial?page=N&per_page=20`

#### Scenario: Estado vacío
- **WHEN** no hay ejecuciones registradas
- **THEN** el frontend muestra "No hay ejecuciones registradas"

#### Scenario: Estado de carga
- **WHEN** la consulta del historial está en curso
- **THEN** el frontend muestra un spinner de carga

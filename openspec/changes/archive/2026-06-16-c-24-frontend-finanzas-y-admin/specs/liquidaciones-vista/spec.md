## ADDED Requirements

### Requirement: Listar liquidaciones del período con KPIs

El frontend SHALL mostrar una tabla de liquidaciones para un cohorte y período dado, con KPIs de totales facturante vs no-facturante y segmentación por tabs.

#### Scenario: Vista inicial sin filtros
- **WHEN** el usuario navega a `/finanzas/liquidaciones` sin parámetros
- **THEN** el frontend muestra filtros de cohorte y período (ambos requeridos)
- **AND** la tabla de liquidaciones está vacía hasta que se seleccionen ambos filtros

#### Scenario: Cargar liquidaciones con filtros
- **WHEN** el usuario selecciona cohorte y período y hace clic en "Calcular" o se cargan datos existentes
- **THEN** el frontend llama a `GET /api/v1/liquidaciones?cohorte_id=X&periodo=YYYY-MM&kpis=true`
- **AND** muestra la tabla con columnas: Docente, Rol, Monto Base, Monto Plus, Total, Facturante/NEXO, Estado
- **AND** muestra los KPIs: Total Facturante, Total No Facturante, Cantidad Facturante, Cantidad No Facturante

#### Scenario: Segmentación por tabs
- **WHEN** existen liquidaciones con docentes facturantes, no-facturantes y NEXO
- **THEN** el frontend muestra 3 tabs: "General" (todos), "NEXO" (solo es_nexo=true), "Factura" (solo excluido_por_factura=true)
- **AND** cada tab filtra la tabla client-side según la categoría
- **AND** los KPIs se muestran siempre para el total general

#### Scenario: Estado de carga
- **WHEN** la query de liquidaciones está en curso
- **THEN** el frontend muestra un spinner de carga en la tabla

#### Scenario: Error al cargar liquidaciones
- **WHEN** la query de liquidaciones falla
- **THEN** el frontend muestra un mensaje de error con opción de reintentar

#### Scenario: Estado vacío
- **WHEN** no existen liquidaciones para los filtros seleccionados
- **THEN** el frontend muestra "No hay liquidaciones para este período"

#### Scenario: Botón de exportar
- **WHEN** el usuario hace clic en "Exportar CSV"
- **THEN** el frontend llama a `GET /api/v1/liquidaciones/exportar?cohorte_id=X&periodo=YYYY-MM`
- **AND** descarga el archivo CSV resultante

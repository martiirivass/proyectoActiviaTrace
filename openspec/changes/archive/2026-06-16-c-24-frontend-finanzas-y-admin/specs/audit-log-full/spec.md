## ADDED Requirements

### Requirement: Log completo de auditoría con filtros

El frontend SHALL mostrar el log completo de auditoría con filtros por acción, actor, fecha, materia y paginación.

#### Scenario: Vista inicial del log
- **WHEN** el usuario navega a `/admin/auditoria/log`
- **THEN** el frontend llama a `GET /api/audit/log?limit=50`
- **AND** muestra una tabla paginada con columnas: Fecha/Hora, Actor, Acción, Materia, Detalle, IP

#### Scenario: Filtrar por acción
- **WHEN** el usuario selecciona una acción del filtro (dropdown con tipos de acción)
- **THEN** el frontend llama a `GET /api/audit/log?accion=CALIFICACIONES_IMPORTAR`

#### Scenario: Filtrar por actor
- **WHEN** el usuario selecciona un actor (select/search de usuarios)
- **THEN** el frontend llama a `GET /api/audit/log?actor_id=UUID`

#### Scenario: Filtrar por rango de fechas
- **WHEN** el usuario ingresa fecha Desde y Hasta
- **THEN** el frontend llama a `GET /api/audit/log?desde=YYYY-MM-DD&hasta=YYYY-MM-DD`

#### Scenario: Filtrar por materia
- **WHEN** el usuario selecciona una materia del filtro
- **THEN** el frontend llama a `GET /api/audit/log?materia_id=UUID`

#### Scenario: Filtros combinados
- **WHEN** el usuario selecciona múltiples filtros simultáneamente
- **THEN** el frontend combina todos los filtros en una sola llamada: `GET /api/audit/log?accion=X&actor_id=Y&desde=Z&hasta=W&materia_id=V`

#### Scenario: Paginación
- **WHEN** hay más de 50 resultados
- **THEN** el frontend muestra controles de paginación
- **AND** al cambiar de página, llama a `GET /api/audit/log?offset=N&limit=50` con los filtros actuales

#### Scenario: Ver detalle de entrada
- **WHEN** el usuario hace clic en una fila del log
- **THEN** se expande o abre un modal con el detalle completo de la entrada (todos los campos del AuditLog)

#### Scenario: Estados de carga, error y vacío
- **WHEN** el log está cargando → spinner
- **WHEN** ocurre un error → mensaje de error con reintentar
- **WHEN** no hay resultados → "No se encontraron registros de auditoría para los filtros seleccionados"

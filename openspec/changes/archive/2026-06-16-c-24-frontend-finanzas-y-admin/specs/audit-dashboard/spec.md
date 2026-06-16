## ADDED Requirements

### Requirement: Panel de métricas de auditoría

El frontend SHALL mostrar un dashboard con KPIs y métricas agregadas de auditoría en una sola vista.

#### Scenario: Cargar dashboard completo
- **WHEN** el usuario navega a `/admin/auditoria`
- **THEN** el frontend llama a `GET /api/audit/dashboard`
- **AND** muestra 4 secciones: Acciones por Día, Comunicaciones por Docente, Interacciones por Docente+Materia, Últimas Acciones

#### Scenario: Filtrar por rango de fechas
- **WHEN** el usuario selecciona fecha "Desde" y "Hasta"
- **THEN** el frontend llama a `GET /api/audit/dashboard?desde=YYYY-MM-DD&hasta=YYYY-MM-DD`
- **AND** todas las secciones se actualizan con los datos filtrados

#### Scenario: Filtrar por materia
- **WHEN** el usuario selecciona una materia del filtro
- **THEN** el frontend llama a `GET /api/audit/dashboard?materia_id=X`
- **AND** todas las secciones se actualizan filtradas por esa materia

#### Scenario: Acciones por día (gráfico de barras)
- **WHEN** el dashboard carga exitosamente
- **THEN** la sección "Acciones por Día" muestra un gráfico de barras simple (CSS/SVG) con fecha en eje X y total de acciones en eje Y
- **AND** se muestran como máximo los últimos 30 días

#### Scenario: Comunicaciones por docente (tabla)
- **WHEN** el dashboard carga exitosamente
- **THEN** la sección "Comunicaciones por Docente" muestra una tabla con columnas: Docente, Pendientes, Enviando, Enviados, Error, Cancelados, Total

#### Scenario: Interacciones por docente+materia (tabla)
- **WHEN** el dashboard carga exitosamente
- **THEN** la sección "Interacciones por Docente+Materia" muestra una tabla con columnas: Docente, Materia, Total Acciones
- **AND** al expandir una fila, muestra el desglose de acciones por tipo (CALIFICACIONES_IMPORTAR, COMUNICACION_ENVIAR, etc.)

#### Scenario: Últimas acciones (tabla)
- **WHEN** el dashboard carga exitosamente
- **THEN** la sección "Últimas Acciones" muestra una tabla con las 200 entradas más recientes
- **AND** columnas: Fecha/Hora, Actor, Acción, Materia, Detalle

#### Scenario: Estados de carga y error
- **WHEN** el dashboard está cargando → spinner general
- **WHEN** ocurre un error → mensaje de error con reintentar
- **WHEN** no hay datos en una sección → "Sin datos para este período" en esa sección

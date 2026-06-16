## ADDED Requirements

### Requirement: Layout de tabs agrupa todas las vistas de una comisión

El sistema SHALL proveer un layout con tabs de navegación para todas las operaciones de una comisión específica (materia + cohorte), donde cada tab carga su vista correspondiente como ruta hija.

#### Scenario: Layout carga con tabs verticales u horizontales
- **WHEN** el usuario navega a `/comision/:materiaId/:cohorteId`
- **THEN** el sistema muestra un layout con tabs: Calificaciones, Umbral, Atrasados, Ranking, Notas Finales, Reportes, Comunicaciones

#### Scenario: Primer tab activo por defecto
- **WHEN** el usuario navega a `/comision/:materiaId/:cohorteId`
- **THEN** el sistema redirige automáticamente a `/comision/:materiaId/:cohorteId/calificaciones`

#### Scenario: Tab activo persiste en la URL
- **WHEN** el usuario navega entre tabs
- **THEN** la URL refleja el tab activo (ej. `/comision/123/456/umbral`), permitiendo compartir/enlazar

#### Scenario: Nombre de materia y cohorte en el header del layout
- **WHEN** el layout carga
- **THEN** el header muestra el nombre de la materia y la cohorte correspondientes a los params de la ruta

#### Scenario: Layout muestra indicador de carga
- **WHEN** los datos básicos de la comisión se están cargando
- **THEN** el layout muestra un spinner

#### Scenario: Layout maneja IDs inválidos
- **WHEN** materiaId o cohorteId no existen
- **THEN** el sistema muestra un estado de error 404 con mensaje "Comisión no encontrada"

## ADDED Requirements

### Requirement: Dashboard muestra comisiones del docente con métricas resumidas

El sistema SHALL mostrar al PROFESOR/TUTOR un dashboard con el listado de sus comisiones asignadas (materia + cohorte), cada una con métricas resumidas para acceso rápido.

#### Scenario: Dashboard carga comisiones del usuario autenticado
- **WHEN** el usuario con rol PROFESOR navega a `/dashboard`
- **THEN** el sistema muestra una grilla de tarjetas, una por cada materia donde el usuario tiene asignación activa

#### Scenario: Cada tarjeta de comisión incluye métricas clave
- **WHEN** el dashboard carga las comisiones
- **THEN** cada tarjeta muestra: nombre de materia, cohorte, cantidad total de alumnos, cantidad de atrasados, y cantidad de actividades pendientes de corrección

#### Scenario: Tarjeta sin datos muestra valores en cero
- **WHEN** una comisión no tiene alumnos o calificaciones importadas aún
- **THEN** las métricas muestran 0 con indicador visual de "sin datos"

#### Scenario: Dashboard sin comisiones asignadas
- **WHEN** el usuario no tiene ninguna comisión asignada
- **THEN** el sistema muestra un estado vacío con mensaje informativo y sin error

#### Scenario: Clic en tarjeta navega a la gestión de comisión
- **WHEN** el usuario hace clic en una tarjeta de comisión
- **THEN** el sistema navega a `/comision/:materiaId/:cohorteId` con los parámetros de esa comisión

#### Scenario: Dashboard muestra indicador de carga mientras fetching
- **WHEN** el dashboard está obteniendo las comisiones
- **THEN** el sistema muestra un spinner de carga

#### Scenario: Dashboard muestra error si falla la carga
- **WHEN** la obtención de comisiones falla
- **THEN** el sistema muestra un alert de error con opción de reintentar

### Requirement: Dashboard tiene acceso rápido a comunicaciones y monitor

El sistema SHALL incluir en el dashboard acceso directo a las funcionalidades transversales: comunicaciones recientes y acceso al monitor.

#### Scenario: Dashboard incluye resumen de comunicaciones recientes
- **WHEN** el dashboard carga
- **THEN** el sistema muestra las últimas 5 comunicaciones enviadas con su estado (asunto truncado, fecha, estado)

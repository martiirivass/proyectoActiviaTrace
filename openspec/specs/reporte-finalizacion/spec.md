## ADDED Requirements

### Requirement: Usuario puede importar reporte de finalización del LMS
El sistema SHALL permitir al usuario importar un reporte de finalización de actividades (formato `.xlsx` o `.csv`) para detectar entregas finalizadas por el alumno pero sin calificación registrada (RN-07).

#### Scenario: Subir reporte de finalización válido
- **WHEN** el usuario sube un archivo de reporte de finalización con estado de actividades por alumno
- **THEN** el sistema parsea el archivo e identifica las actividades marcadas como "finalizadas" o "entregadas"

#### Scenario: Reporte con formato no soportado
- **WHEN** el usuario sube un archivo que no es `.xlsx` ni `.csv`
- **THEN** el sistema rechaza la operación con error 422

### Requirement: Sistema detecta entregas sin calificar (RN-07)
El sistema SHALL cruzar el reporte de finalización importado con las calificaciones existentes para identificar actividades finalizadas por el alumno pero sin calificación registrada.

#### Scenario: Actividad finalizada sin calificación es detectada
- **WHEN** el reporte indica que el alumno finalizó la actividad "TP1" pero no existe `Calificacion` para ese alumno × actividad
- **THEN** el sistema incluye esa entrada en el listado de "posibles trabajos sin corregir"

#### Scenario: Actividad finalizada con calificación no aparece en el listado
- **WHEN** el reporte indica que el alumno finalizó la actividad "TP1" y existe una `Calificacion` con nota
- **THEN** el sistema NO incluye esa entrada en el listado

### Requirement: Listado solo incluye actividades textuales (RN-08)
El sistema SHALL incluir en el listado de posibles trabajos sin corregir únicamente actividades de escala textual.

#### Scenario: Actividad numérica sin calificación no aparece
- **WHEN** una actividad numérica está finalizada pero sin calificación
- **THEN** el sistema NO la incluye en el listado, porque en escala numérica la ausencia de nota equivale a no entregado

### Requirement: Sistema retorna listado de actividades sin corregir
El sistema SHALL retornar el listado de actividades sin corregir detectadas, agrupado por alumno y actividad.

#### Scenario: Listado con múltiples actividades sin corregir
- **WHEN** se procesa el reporte y se detectan 3 actividades sin calificar de 2 alumnos distintos
- **THEN** el sistema retorna un listado con 3 entradas, cada una con: nombre del alumno, actividad, y fecha de finalización si está disponible

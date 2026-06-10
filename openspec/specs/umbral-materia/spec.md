## ADDED Requirements

### Requirement: Docente puede configurar umbral de aprobación por materia
El sistema SHALL permitir al PROFESOR configurar el porcentaje mínimo de nota para considerar aprobada una actividad en su materia (F2.1, RN-03). El valor por defecto es 60%.

#### Scenario: Configurar umbral porcentual
- **WHEN** el docente envía `umbral_pct = 75` para su asignación en una materia
- **THEN** el sistema crea o actualiza el registro de `UmbralMateria` con ese valor

#### Scenario: Crear umbral con valores textuales aprobatorios
- **WHEN** el docente envía `umbral_pct = 60` y `valores_aprobatorios = ["Satisfactorio", "Supera lo esperado", "Excelente"]`
- **THEN** el sistema guarda el umbral y los nuevos valores textuales aprobatorios para esa asignación

#### Scenario: Obtener umbral configurado
- **WHEN** el docente consulta el umbral de su asignación
- **THEN** el sistema retorna el `UmbralMateria` si existe, o el valor por defecto 60% con los valores aprobatorios del tenant

### Requirement: Umbral es por asignación (no afecta a otros docentes)
El sistema SHALL garantizar que la configuración de umbral de un docente no afecte a otros docentes asignados a la misma materia.

#### Scenario: Umbral del Docente A no cambia el del Docente B
- **WHEN** el Docente A configura umbral 80 para su asignación en Materia X
- **THEN** el Docente B, que también tiene asignación en Materia X, sigue viendo su propio umbral (o el default 60% si nunca lo configuró)

### Requirement: Cambio de umbral puede recalcular aprobados existentes
El sistema SHALL exponer un método para recalcular el campo `aprobado` de todas las calificaciones de una asignación cuando el umbral cambia.

#### Scenario: Recalcular aprobados tras cambio de umbral
- **WHEN** el docente cambia el umbral de 60 a 70 y solicita recalcular
- **THEN** el sistema actualiza el campo `aprobado` de todas las `Calificacion` de esa asignación según el nuevo umbral

#### Scenario: Recalcular solo afecta asignación del docente
- **WHEN** se solicita recalcular para la asignación del Docente A
- **THEN** las calificaciones del Docente B en la misma materia no se modifican

### Requirement: Validaciones de umbral
El sistema SHALL validar que el umbral porcentual esté en el rango 0-100.

#### Scenario: Umbral fuera de rango es rechazado
- **WHEN** el docente envía `umbral_pct = 150`
- **THEN** el sistema rechaza con error 422 indicando que el valor debe estar entre 0 y 100

#### Scenario: Umbral en límite inferior es aceptado
- **WHEN** el docente envía `umbral_pct = 0`
- **THEN** el sistema acepta el valor (todas las notas numéricas >= 0 cuentan como aprobadas)

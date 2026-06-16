## ADDED Requirements

### Requirement: Configuración de umbral con slider y valores textuales

El sistema SHALL mostrar un formulario de configuración del umbral de aprobación con un control numérico (slider + input) y un editor de valores textuales aprobatorios.

#### Scenario: Umbral actual se muestra precargado
- **WHEN** el usuario accede a la vista de umbral
- **THEN** el sistema muestra el valor actual (el configurado o 60% por defecto) precargado en un slider e input numérico

#### Scenario: Slider e input numérico están sincronizados
- **WHEN** el usuario mueve el slider
- **THEN** el input numérico se actualiza al mismo valor, y viceversa

#### Scenario: Validación 0-100 en el input
- **WHEN** el usuario ingresa un valor fuera del rango 0-100
- **THEN** el sistema muestra error de validación "El umbral debe estar entre 0 y 100" y no permite guardar

#### Scenario: Editor de valores textuales aprobatorios
- **WHEN** el usuario configura el umbral
- **THEN** el sistema muestra un editor de lista para agregar/quitar valores textuales aprobatorios (ej. "Satisfactorio", "Supera lo esperado")

#### Scenario: Guardar umbral muestra confirmación
- **WHEN** el usuario guarda la configuración exitosamente
- **THEN** el sistema muestra un toast/alert de éxito y persiste el valor

#### Scenario: Error al guardar umbral
- **WHEN** el guardado falla
- **THEN** el sistema muestra un alert de error con el mensaje del servidor

#### Scenario: Botón de recalcular aprobados
- **WHEN** el usuario hace clic en "Recalcular aprobados"
- **THEN** el sistema envía la solicitud al servidor y muestra confirmación al completar

#### Scenario: Recalcular muestra spinner y deshabilita botón
- **WHEN** el recalculo está en progreso
- **THEN** el botón "Recalcular aprobados" muestra un spinner y se deshabilita hasta completar

### Requirement: Umbral muestra indicador de carga y error

El sistema SHALL mostrar estados de carga y error para la consulta inicial del umbral.

#### Scenario: Carga del umbral muestra spinner
- **WHEN** el umbral se está obteniendo del servidor
- **THEN** el sistema muestra un spinner en lugar del formulario

#### Scenario: Error de carga muestra mensaje
- **WHEN** la obtención del umbral falla
- **THEN** el sistema muestra un alert de error con opción de reintentar

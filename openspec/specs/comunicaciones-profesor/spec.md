# comunicaciones-profesor Specification

## Purpose
TBD - created by archiving change c-22-frontend-academico-docente. Update Purpose after archive.
## Requirements
### Requirement: Formulario de redacción con selección de destinatarios

El sistema SHALL proveer un formulario para redactar comunicaciones, con campos de asunto y cuerpo, y selección de destinatarios desde la lista de alumnos.

#### Scenario: Formulario incluye asunto y cuerpo
- **WHEN** el usuario accede a la vista de comunicaciones
- **THEN** el sistema muestra un formulario con campos: asunto (requerido), cuerpo (requerido, textarea)

#### Scenario: Selección de destinatarios desde tabla de alumnos
- **WHEN** el usuario redacta una comunicación
- **THEN** el sistema muestra una tabla de alumnos de la comisión con checkboxes para seleccionar destinatarios

#### Scenario: Validación de campos requeridos
- **WHEN** el usuario intenta previsualizar sin asunto o cuerpo
- **THEN** el sistema muestra errores de validación en los campos vacíos

### Requirement: Preview modal antes del envío

El sistema SHALL mostrar un modal de preview con el contenido del mensaje antes de confirmar el envío (RN-16).

#### Scenario: Preview muestra asunto, cuerpo y destinatarios
- **WHEN** el usuario hace clic en "Previsualizar"
- **THEN** el sistema muestra un modal con: asunto, cuerpo renderizado, y cantidad de destinatarios seleccionados

#### Scenario: Preview con botones de enviar y cancelar
- **WHEN** el modal de preview está abierto
- **THEN** el modal tiene botón "Enviar" (confirma envío) y "Cancelar" (vuelve al formulario)

#### Scenario: Preview muestra error si falla validación
- **WHEN** el preview falla por datos inválidos
- **THEN** el sistema muestra el error en el modal sin cerrar el formulario

### Requirement: Envío individual y masivo de comunicaciones

El sistema SHALL permitir enviar comunicaciones individuales (1 destinatario) o masivas (lote a múltiples destinatarios seleccionados).

#### Scenario: Envío individual a un alumno
- **WHEN** el usuario selecciona un solo destinatario y confirma el envío
- **THEN** el sistema envía una comunicación individual y muestra confirmación

#### Scenario: Envío masivo a múltiples alumnos
- **WHEN** el usuario selecciona múltiples destinatarios y confirma el envío
- **THEN** el sistema crea un lote de comunicaciones y muestra el ID del lote y cantidad de mensajes

#### Scenario: Envío exitoso cierra modal y limpia formulario
- **WHEN** el envío se completa exitosamente
- **THEN** el modal se cierra, el formulario se limpia, y se muestra toast de éxito

#### Scenario: Error en envío mantiene modal abierto
- **WHEN** el envío falla
- **THEN** el modal permanece abierto y muestra el error con opción de reintentar

### Requirement: Tracking de estado de comunicaciones con polling

El sistema SHALL mostrar una tabla de tracking con el estado de las comunicaciones enviadas, actualizada mediante polling.

#### Scenario: Tracking muestra tabla de comunicaciones por materia
- **WHEN** el usuario navega al tracking
- **THEN** el sistema muestra una tabla con columnas: destinatario (enmascarado), asunto, estado, fecha de envío

#### Scenario: Estados se muestran con badge de color
- **WHEN** el tracking muestra el estado
- **THEN** Pendiente = badge gris, Enviando = badge azul, Enviado = badge verde, Error = badge rojo, Cancelado = badge naranja

#### Scenario: Tracking se actualiza cada 5 segundos
- **WHEN** hay comunicaciones en estado Pendiente o Enviando
- **THEN** la tabla se actualiza automáticamente cada 5 segundos con polling

#### Scenario: Polling se detiene en estado terminal
- **WHEN** todas las comunicaciones del lote están en Enviado, Error o Cancelado
- **THEN** el polling se detiene automáticamente

#### Scenario: Tracking muestra distribución de estados
- **WHEN** el tracking carga
- **THEN** el sistema muestra un resumen con la distribución de estados: X pendientes, X enviando, X enviados, X errores, X cancelados

### Requirement: Tracking vacío muestra mensaje informativo

El sistema SHALL mostrar un estado vacío cuando no hay comunicaciones enviadas para la comisión.

#### Scenario: Sin comunicaciones muestra mensaje
- **WHEN** no hay comunicaciones previas para la materia
- **THEN** el sistema muestra "No hay comunicaciones enviadas para esta comisión"


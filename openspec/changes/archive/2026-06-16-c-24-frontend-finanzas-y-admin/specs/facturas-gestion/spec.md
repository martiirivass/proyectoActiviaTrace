## ADDED Requirements

### Requirement: Gestionar facturas de docentes (CRUD con filtros)

El frontend SHALL permitir a usuarios con permiso `facturas:gestionar` crear, listar, ver detalle, abonar y eliminar (soft delete) facturas de docentes.

#### Scenario: Listar facturas con filtros
- **WHEN** el usuario navega a `/finanzas/facturas`
- **THEN** el frontend llama a `GET /api/v1/facturas` con filtros opcionales
- **AND** muestra una tabla con columnas: Docente, Período, Detalle, Monto, Estado, Fecha de Carga
- **AND** el usuario puede filtrar por período (AAAA-MM), estado (Pendiente/Abonada) y docente (select/search)

#### Scenario: Crear factura
- **WHEN** el usuario hace clic en "Nueva Factura"
- **THEN** se abre un modal con formulario RHF+Zod con campos: Docente (select/search), Período (AAAA-MM), Detalle (textarea), Referencia Archivo (texto opcional), Tamaño KB (número opcional), Materia (select opcional), Comisión (select opcional, visible solo si se seleccionó materia)
- **AND** al enviar, llama a `POST /api/v1/facturas`
- **AND** muestra toast de éxito y refresca la tabla

#### Scenario: Validación de período
- **WHEN** el usuario ingresa un período con formato inválido (no AAAA-MM)
- **THEN** el frontend muestra error de validación "Formato de período inválido (AAAA-MM)"

#### Scenario: Validación materia sin comisión
- **WHEN** el usuario selecciona una materia pero no una comisión
- **THEN** el frontend muestra error "Debe seleccionar una comisión si especifica una materia"

#### Scenario: Abonar factura
- **WHEN** el usuario hace clic en "Abonar" en una factura con estado Pendiente
- **THEN** se muestra modal de confirmación
- **AND** al confirmar, llama a `POST /api/v1/facturas/{id}/abonar`
- **AND** muestra toast de éxito y refresca la tabla

#### Scenario: Error 409 al abonar factura ya abonada
- **WHEN** el usuario intenta abonar una factura ya en estado Abonada
- **THEN** el frontend muestra mensaje de error "La factura ya está abonada"

#### Scenario: Eliminar factura (soft delete)
- **WHEN** el usuario hace clic en "Eliminar"
- **THEN** se muestra modal de confirmación
- **AND** al confirmar, llama a `DELETE /api/v1/facturas/{id}`
- **AND** muestra toast de éxito y refresca la tabla

#### Scenario: Estado vacío
- **WHEN** no hay facturas para los filtros seleccionados
- **THEN** el frontend muestra "No hay facturas para los filtros seleccionados"

#### Scenario: Botón "Abonar" no visible para facturas Abonadas
- **WHEN** una factura ya está en estado Abonada
- **THEN** el botón "Abonar" no se muestra en esa fila
- **AND** se muestra un badge "Abonada" con la fecha de abono

## ADDED Requirements

### Requirement: Gestionar SalarioBase (ABM con vigencia)

El frontend SHALL permitir crear, listar, editar y eliminar (soft delete) salarios base, con filtros por rol y vigencia.

#### Scenario: Listar salarios base
- **WHEN** el usuario navega a la pestaña "Salario Base"
- **THEN** el frontend llama a `GET /api/v1/grilla-salarial/base`
- **AND** muestra una tabla con columnas: Rol, Monto, Desde, Hasta, Estado (Vigente/Vencido)

#### Scenario: Filtrar por rol y vigencia
- **WHEN** el usuario selecciona un rol y/o toggle "Solo vigentes"
- **THEN** el frontend llama a `GET /api/v1/grilla-salarial/base?rol=X&vigente=true/false`

#### Scenario: Crear salario base
- **WHEN** el usuario hace clic en "Nuevo Salario Base"
- **THEN** se abre un modal con formulario RHF+Zod con campos: Rol (select), Monto (número > 0), Desde (date picker), Hasta (date picker opcional)
- **AND** al enviar, llama a `POST /api/v1/grilla-salarial/base`
- **AND** muestra toast de éxito y refresca la tabla

#### Scenario: Editar salario base
- **WHEN** el usuario hace clic en "Editar" en una fila
- **THEN** se abre el modal precargado con los datos actuales
- **AND** al enviar, llama a `PUT /api/v1/grilla-salarial/base/{id}`
- **AND** muestra toast de éxito y refresca la tabla

#### Scenario: Eliminar salario base (soft delete)
- **WHEN** el usuario hace clic en "Eliminar"
- **THEN** se muestra modal de confirmación
- **AND** al confirmar, llama a `DELETE /api/v1/grilla-salarial/base/{id}`
- **AND** muestra toast de éxito y refresca la tabla

#### Scenario: Validación de monto > 0
- **WHEN** el usuario ingresa un monto <= 0
- **THEN** el frontend muestra error de validación "El monto debe ser mayor a 0"

### Requirement: Gestionar SalarioPlus (ABM con vigencia)

El frontend SHALL permitir crear, listar, editar y eliminar (soft delete) pluses salariales, con filtros por grupo, rol y vigencia.

#### Scenario: Listar SalarioPlus
- **WHEN** el usuario navega a la pestaña "Salario Plus"
- **THEN** el frontend llama a `GET /api/v1/grilla-salarial/plus`
- **AND** muestra una tabla con columnas: Grupo, Rol, Descripción, Monto, Desde, Hasta

#### Scenario: Crear SalarioPlus
- **WHEN** el usuario hace clic en "Nuevo Salario Plus"
- **THEN** se abre un modal con campos: Grupo (texto), Rol (select), Descripción (texto), Monto (> 0), Desde/Hasta (date pickers)
- **AND** al enviar, llama a `POST /api/v1/grilla-salarial/plus`

#### Scenario: Editar y eliminar SalarioPlus
- **WHEN** el usuario edita o elimina un SalarioPlus
- **THEN** sigue el mismo patrón que SalarioBase (PUT/DELETE)

#### Scenario: Estado vacío
- **WHEN** no hay registros de SalarioBase o SalarioPlus
- **THEN** el frontend muestra "No hay registros"

#### Scenario: Error 409 duplicado
- **WHEN** el backend devuelve 409 (mismo rol+fecha para base, o mismo grupo+rol+fecha para plus)
- **THEN** el frontend muestra el mensaje de error del backend

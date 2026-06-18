## ADDED Requirements

### Requirement: Gestionar usuarios del tenant (ABM con PII)

El frontend SHALL permitir a usuarios con permiso `usuarios:read` crear, listar, editar y eliminar (soft delete) usuarios del tenant.

#### Scenario: Listar usuarios con filtros
- **WHEN** el usuario navega a `/admin/usuarios`
- **THEN** el frontend llama a `GET /api/v1/admin/usuarios`
- **AND** muestra una tabla paginada con columnas: Email, Nombre, Apellido, DNI, Rol(es), Regional, Facturador (Sí/No), Estado
- **AND** el usuario puede buscar por texto (email, nombre, apellido, DNI) y filtrar por rol

#### Scenario: Crear usuario
- **WHEN** el usuario hace clic en "Nuevo Usuario"
- **THEN** se abre un modal con formulario RHF+Zod con campos:
  - Email (email, requerido)
  - Nombre (texto, requerido)
  - Apellido (texto, requerido)
  - DNI (texto, requerido)
  - Password (password, requerido en creación, opcional en edición)
  - CUIL (texto, opcional)
  - CBU (texto, opcional)
  - Alias CBU (texto, opcional)
  - Banco (texto, opcional)
  - Regional (texto, opcional)
  - Legajo (texto, opcional)
  - Legajo Profesional (texto, opcional)
  - Facturador (checkbox)
- **AND** al enviar, llama a `POST /api/v1/admin/usuarios`
- **AND** muestra toast de éxito y refresca la tabla

#### Scenario: Editar usuario
- **WHEN** el usuario hace clic en "Editar"
- **THEN** se abre el modal precargado
- **AND** el campo Password es opcional (solo si se quiere cambiar)
- **AND** al enviar, llama a `PUT /api/v1/admin/usuarios/{id}`

#### Scenario: Eliminar usuario (soft delete)
- **WHEN** el usuario hace clic en "Eliminar"
- **THEN** se muestra modal de confirmación con advertencia
- **AND** al confirmar, llama a `DELETE /api/v1/admin/usuarios/{id}`

#### Scenario: Error 409 email duplicado
- **WHEN** el email ingresado ya existe en el tenant
- **THEN** el frontend muestra el mensaje de error del backend en el campo email

#### Scenario: Paginación de tabla
- **WHEN** hay más usuarios que el límite por página (default 20)
- **THEN** el frontend muestra controles de paginación
- **AND** al cambiar de página, llama a `GET /api/v1/admin/usuarios?page=N&per_page=20`

#### Scenario: Estados de carga, error y vacío
- **WHEN** la lista de usuarios está cargando → spinner
- **WHEN** ocurre un error → mensaje de error con reintentar
- **WHEN** no hay usuarios → "No hay usuarios registrados"

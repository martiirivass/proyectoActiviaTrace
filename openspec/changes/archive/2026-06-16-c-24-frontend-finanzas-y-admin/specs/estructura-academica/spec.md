## ADDED Requirements

### Requirement: Gestionar carreras (CRUD)

El frontend SHALL permitir crear, listar, editar y eliminar (soft delete) carreras.

#### Scenario: Listar carreras
- **WHEN** el usuario navega a la pestaña "Carreras"
- **THEN** el frontend llama a `GET /api/v1/admin/carreras`
- **AND** muestra una tabla con columnas: Código, Nombre, Estado, Fecha de Creación

#### Scenario: Crear carrera
- **WHEN** el usuario hace clic en "Nueva Carrera"
- **THEN** se abre un modal con campos: Código (texto, requerido), Nombre (texto, requerido)
- **AND** al enviar, llama a `POST /api/v1/admin/carreras`
- **AND** muestra toast de éxito y refresca la tabla

#### Scenario: Error 409 código duplicado
- **WHEN** el código ingresado ya existe en el tenant
- **THEN** el frontend muestra el mensaje de error del backend

#### Scenario: Editar carrera
- **WHEN** el usuario hace clic en "Editar"
- **THEN** se abre modal precargado
- **AND** al enviar, llama a `PUT /api/v1/admin/carreras/{id}`

#### Scenario: Eliminar carrera
- **WHEN** el usuario hace clic en "Eliminar"
- **THEN** se muestra modal de confirmación
- **AND** al confirmar, llama a `DELETE /api/v1/admin/carreras/{id}`

### Requirement: Gestionar cohortes (CRUD con filtro por carrera)

El frontend SHALL permitir gestionar cohortes asociadas a una carrera.

#### Scenario: Listar cohortes
- **WHEN** el usuario navega a la pestaña "Cohortes"
- **THEN** el frontend muestra un filtro de carrera (select)
- **AND** llama a `GET /api/v1/admin/cohortes?carrera_id=X` si hay carrera seleccionada
- **AND** muestra una tabla con columnas: Carrera, Nombre, Año, Estado

#### Scenario: Crear cohorte
- **WHEN** el usuario hace clic en "Nueva Cohorte"
- **THEN** se abre modal con campos: Carrera (select), Nombre (texto), Año (número)
- **AND** al enviar, llama a `POST /api/v1/admin/cohortes`

### Requirement: Gestionar materias (CRUD)

El frontend SHALL permitir gestionar materias del catálogo del tenant.

#### Scenario: Listar materias
- **WHEN** el usuario navega a la pestaña "Materias"
- **THEN** el frontend llama a `GET /api/v1/admin/materias`
- **AND** muestra una tabla con columnas: Código, Nombre, Estado

#### Scenario: Crear materia
- **WHEN** el usuario hace clic en "Nueva Materia"
- **THEN** se abre modal con campos: Código (texto), Nombre (texto)
- **AND** al enviar, llama a `POST /api/v1/admin/materias`

### Requirement: Gestionar dictados (CRUD con filtros)

El frontend SHALL permitir gestionar dictados (instancia materia × carrera × cohorte).

#### Scenario: Listar dictados
- **WHEN** el usuario navega a la pestaña "Dictados"
- **THEN** el frontend muestra filtros de Materia y Cohorte
- **AND** llama a `GET /api/v1/admin/dictados` con los filtros seleccionados
- **AND** muestra una tabla con columnas: Materia, Carrera, Cohorte, Nombre Dictado

#### Scenario: Crear dictado
- **WHEN** el usuario hace clic en "Nuevo Dictado"
- **THEN** se abre modal con campos: Materia (select), Carrera (select), Cohorte (select, filtrado por carrera), Nombre (texto)
- **AND** al enviar, llama a `POST /api/v1/admin/dictados`

#### Scenario: Error 409 combinación duplicada
- **WHEN** la combinación materia+cohorte ya existe
- **THEN** el frontend muestra el mensaje de error del backend

### Requirement: Estados de carga, error y vacío

#### Scenario: Estados consistentes
- **WHEN** cualquiera de las tablas de estructura está cargando
- **THEN** el frontend muestra un spinner
- **WHEN** ocurre un error en cualquier operación
- **THEN** el frontend muestra el mensaje de error con opción de reintentar
- **WHEN** no hay datos en ninguna tabla
- **THEN** el frontend muestra "No hay registros" con botón de crear

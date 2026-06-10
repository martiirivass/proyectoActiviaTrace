## ADDED Requirements

### Requirement: Importar padrón desde archivo
El sistema SHALL permitir importar el padrón de alumnos de una materia desde archivos `.xlsx` o `.csv`.

#### Scenario: Subir archivo xlsx exitosamente
- **WHEN** se envía POST `/api/v1/padron/preview` con un archivo `.xlsx` válido conteniendo columnas `nombre`, `apellidos`, `email`, `comision`, `regional`
- **THEN** retorna 200 con la vista previa de los registros parseados
- **AND** la vista previa contiene la cantidad de filas detectadas

#### Scenario: Subir archivo csv exitosamente
- **WHEN** se envía POST `/api/v1/padron/preview` con un archivo `.csv` válido (delimitado por coma o punto y coma)
- **THEN** retorna 200 con la vista previa de los registros parseados

#### Scenario: Archivo con formato inválido
- **WHEN** se envía POST `/api/v1/padron/preview` con un archivo que no es `.xlsx` ni `.csv`
- **THEN** retorna 422 con error de formato no soportado

#### Scenario: Archivo malformado
- **WHEN** se envía POST `/api/v1/padron/preview` con un archivo `.xlsx` corrupto o malformado
- **THEN** retorna 422 con error de parseo

#### Scenario: Columnas faltantes en el archivo
- **WHEN** se envía POST `/api/v1/padron/preview` con un archivo que no contiene las columnas requeridas (`nombre`, `apellidos`, `email`)
- **THEN** retorna 422 indicando las columnas faltantes

### Requirement: Confirmar importación de padrón
El sistema SHALL permitir confirmar una importación de padrón previamente previsualizada, creando una nueva versión activa.

#### Scenario: Confirmar importación exitosamente
- **WHEN** se envía POST `/api/v1/padron/confirm` con los datos previsualizados (lista de entradas), `materia_id` y `cohorte_id` válidos
- **THEN** retorna 201 con la versión creada
- **AND** se crea una `VersionPadron` con `activa: true`
- **AND** se crean las `EntradaPadron` correspondientes

#### Scenario: Confirmar desactiva versión anterior
- **WHEN** existe una versión activa previa para la misma materia×cohorte y se confirma una nueva importación
- **THEN** la versión anterior pasa a `activa: false`
- **AND** la nueva versión se crea con `activa: true`

#### Scenario: Entrada sin usuario_id (alumno sin cuenta)
- **WHEN** se confirma un padrón con un email que no corresponde a ningún `Usuario` registrado en el tenant
- **THEN** la `EntradaPadron` se crea con `usuario_id: null`
- **AND** el resto de los datos se almacenan correctamente

### Requirement: Listar versiones de padrón
El sistema SHALL permitir listar las versiones de padrón de una materia y cohorte.

#### Scenario: Listar versiones por materia y cohorte
- **WHEN** se consulta GET `/api/v1/padron/versions?materia_id=<uuid>&cohorte_id=<uuid>`
- **THEN** retorna 200 con la lista de versiones ordenadas por `cargado_at` descendente
- **AND** cada versión incluye la cantidad de entradas asociadas

#### Scenario: Solo versión activa detectada
- **WHEN** se consulta GET `/api/v1/padron/versions`
- **THEN** la versión con `activa: true` está marcada en la respuesta

### Requirement: Acceso multi-tenant en padrón
El sistema SHALL aislar los datos de padrón por tenant.

#### Scenario: Tenant no ve datos de otro tenant
- **WHEN** el usuario del tenant A consulta versiones de padrón
- **THEN** solo recibe versiones del tenant A
- **AND** nunca recibe datos del tenant B

#### Scenario: Usuario sin permiso no puede importar
- **WHEN** un usuario sin permiso `padron:importar` intenta acceder a cualquier endpoint de padrón
- **THEN** retorna 403 Forbidden

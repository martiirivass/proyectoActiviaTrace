## ADDED Requirements

### Requirement: COORDINADOR/ADMIN crea un aviso
El sistema SHALL permitir a usuarios con permiso `avisos:publicar` crear avisos institucionales con los siguientes campos: alcance (Global | PorMateria | PorCohorte | PorRol), materia_id (nullable), cohorte_id (nullable), rol_destino (nullable), severidad (Info | Advertencia | Critico), título, cuerpo, inicio_en (datetime), fin_en (datetime), orden (entero), activo (booleano), requiere_ack (booleano).

#### Scenario: Crear aviso global con ack obligatorio
- **WHEN** COORDINADOR crea un aviso con alcance Global, requiere_ack=true, dentro de vigencia
- **THEN** el sistema retorna 201 con los datos del aviso creado

#### Scenario: Crear aviso sin cuerpo retorna 422
- **WHEN** COORDINADOR crea un aviso con título pero sin cuerpo
- **THEN** el sistema retorna 422 Unprocessable Content

### Requirement: COORDINADOR/ADMIN edita un aviso
El sistema SHALL permitir modificar campos editables de un aviso existente (alcance, materia_id, cohorte_id, rol_destino, severidad, título, cuerpo, inicio_en, fin_en, orden, activo, requiere_ack). El aviso debe existir y pertenecer al mismo tenant.

#### Scenario: Editar título y vigencia de aviso existente
- **WHEN** COORDINADOR edita el título y las fechas de vigencia de un aviso activo
- **THEN** el sistema retorna 200 con los datos actualizados

#### Scenario: Editar aviso de otro tenant retorna 404
- **WHEN** ADMIN del tenant A intenta editar un aviso del tenant B
- **THEN** el sistema retorna 404 Not Found

### Requirement: COORDINADOR/ADMIN elimina (soft delete) un aviso
El sistema SHALL permitir eliminar un aviso (soft delete) a usuarios con permiso `avisos:publicar`.

#### Scenario: Eliminar aviso existente
- **WHEN** COORDINADOR elimina un aviso activo
- **THEN** el sistema retorna 204 y el aviso deja de ser visible (deleted_at seteado)

### Requirement: Listado paginado de avisos con filtros
El sistema SHALL exponer un endpoint GET que liste avisos con paginación y filtros opcionales por alcance, severidad, activo, materia_id, cohorte_id y rango de vigencia. Para COORDINADOR/ADMIN: todos los avisos del tenant. Para otros roles: solo los que aplican según su contexto.

#### Scenario: ADMIN lista todos los avisos del tenant
- **WHEN** ADMIN consulta GET /api/avisos sin filtros
- **THEN** el sistema retorna lista paginada con todos los avisos del tenant

#### Scenario: Filtrar avisos por alcance PorMateria
- **WHEN** COORDINADOR filtra avisos con alcance=PorMateria y materia_id específico
- **THEN** el sistema retorna solo los avisos de esa materia

### Requirement: Obtener detalle de un aviso
El sistema SHALL exponer un endpoint GET /api/avisos/{id} que retorne el detalle completo de un aviso, incluyendo contadores derivados de acknowledgment (total vistos, total confirmados).

#### Scenario: Obtener detalle con métricas
- **WHEN** ADMIN consulta GET /api/avisos/{id}
- **THEN** el sistema retorna el aviso con total_vistos y total_confirmados calculados

### Requirement: Obtener métricas de un aviso
El sistema SHALL exponer un endpoint GET /api/avisos/{id}/metricas accesible solo con permiso `avisos:publicar`, que retorne total_vistos, total_confirmados y la lista de usuarios que confirmaron.

#### Scenario: ADMIN consulta métricas de aviso
- **WHEN** ADMIN consulta GET /api/avisos/{id}/metricas
- **THEN** el sistema retorna total_vistos, total_confirmados y listado de usuarios con sus fechas de confirmación

#### Scenario: ALUMNO consulta métricas retorna 403
- **WHEN** ALUMNO consulta GET /api/avisos/{id}/metricas
- **THEN** el sistema retorna 403 Forbidden

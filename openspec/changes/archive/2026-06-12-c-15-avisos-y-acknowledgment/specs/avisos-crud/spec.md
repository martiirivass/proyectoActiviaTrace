## ADDED Requirements

### Requirement: Crear aviso
El sistema SHALL permitir a usuarios con permiso `avisos:publicar` (COORDINADOR, ADMIN) crear nuevos avisos con los siguientes campos obligatorios y opcionales.

**Campos:**
- `titulo` (string, requerido) — título del aviso
- `cuerpo` (string, requerido) — cuerpo del aviso, puede contener texto enriquecido (rich text)
- `alcance` (enum: `Global | PorMateria | PorCohorte | PorRol`, requerido) — alcance del aviso
- `severidad` (enum: `Info | Advertencia | Critico`, requerido) — nivel de severidad
- `inicio_en` (datetime, requerido) — fecha/hora desde la que el aviso es visible
- `fin_en` (datetime, requerido) — fecha/hora hasta la que el aviso es visible
- `orden` (integer, opcional, default 0) — prioridad de presentación (menor = más prioritario)
- `activo` (boolean, opcional, default true) — si el aviso está activo
- `requiere_ack` (boolean, opcional, default false) — si requiere confirmación de lectura
- `materia_id` (UUID, opcional, nullable) — FK a Materia, requerido si alcance = PorMateria
- `cohorte_id` (UUID, opcional, nullable) — FK a Cohorte, requerido si alcance = PorCohorte
- `rol_destino` (enum: `ALUMNO | TUTOR | PROFESOR | COORDINADOR | NEXO | ADMIN | FINANZAS`, opcional, nullable) — rol destino, nullable = todos los roles

**Validaciones:**
- Si `alcance = PorMateria`, `materia_id` es requerido y debe existir en el tenant
- Si `alcance = PorCohorte`, `cohorte_id` es requerido y debe existir en el tenant
- Si `alcance = PorRol`, `rol_destino` es requerido
- `inicio_en` SHALL ser anterior a `fin_en`
- `fin_en` SHALL ser posterior a la fecha actual (no se pueden crear avisos ya vencidos)

#### Scenario: Crear aviso global exitosamente
- **WHEN** un COORDINADOR autenticado envía `POST /api/v1/avisos` con `titulo`, `cuerpo`, `alcance=Global`, `severidad=Info`, `inicio_en` y `fin_en` válidos
- **THEN** el sistema devuelve HTTP 201 con el aviso creado, incluyendo `id`, `tenant_id`, timestamps de creación/actualización

#### Scenario: Crear aviso con alcance PorMateria sin materia_id
- **WHEN** un ADMIN envía `POST /api/v1/avisos` con `alcance=PorMateria` y sin `materia_id`
- **THEN** el sistema devuelve HTTP 422 con error de validación indicando que `materia_id` es requerido

#### Scenario: Crear aviso con fin_en anterior a inicio_en
- **WHEN** un COORDINADOR envía `POST /api/v1/avisos` con `inicio_en` posterior a `fin_en`
- **THEN** el sistema devuelve HTTP 422 con error de validación

#### Scenario: Crear aviso sin permiso avisos:publicar
- **WHEN** un TUTOR autenticado envía `POST /api/v1/avisos`
- **THEN** el sistema devuelve HTTP 403 Forbidden

---

### Requirement: Editar aviso
El sistema SHALL permitir a usuarios con permiso `avisos:publicar` modificar un aviso existente. Todos los campos son opcionales en la actualización (PATCH semantics). No se permite cambiar `tenant_id`.

**Validaciones:**
- El aviso debe existir y no estar eliminado (soft delete)
- Las mismas validaciones de integridad que en creación aplican a los campos enviados
- Si se cambia `alcance` a `PorMateria`, `materia_id` pasa a ser requerido

#### Scenario: Editar título de aviso existente
- **WHEN** un ADMIN envía `PUT /api/v1/avisos/{id}` con `titulo` actualizado
- **THEN** el sistema devuelve HTTP 200 con el aviso actualizado

#### Scenario: Editar aviso inexistente
- **WHEN** un COORDINADOR envía `PUT /api/v1/avisos/{uuid-inexistente}`
- **THEN** el sistema devuelve HTTP 404 Not Found

---

### Requirement: Eliminar aviso (soft delete)
El sistema SHALL permitir a usuarios con permiso `avisos:publicar` eliminar (soft delete) un aviso existente.

**Efecto:**
- El aviso se marca como eliminado (no se borra físicamente)
- Los `AcknowledgmentAviso` asociados se conservan (histórico de confirmaciones)
- El aviso eliminado no aparece en listados de usuarios

#### Scenario: Eliminar aviso exitosamente
- **WHEN** un ADMIN envía `DELETE /api/v1/avisos/{id}`
- **THEN** el sistema devuelve HTTP 204 No Content y el aviso queda marcado como eliminado

#### Scenario: Eliminar aviso de otro tenant
- **WHEN** un COORDINADOR del Tenant A envía `DELETE /api/v1/avisos/{id}` donde el aviso pertenece al Tenant B
- **THEN** el sistema devuelve HTTP 404 Not Found (el aviso no existe en su tenant)

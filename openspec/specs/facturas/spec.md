# Facturas — Specification (FULL)

> **Domain**: Facturas (gestión de facturas docentes)
> **Design**: PA-24 (dual association periodo/comisión), referencia_archivo (no blob)
> **Icon legend**: ⚠️ = subject to functional validation (PA-24 pendiente)

---

## ADDED Requirements

### Requisito: Crear factura

El sistema SHALL permitir a usuarios con permiso `facturas:gestionar` registrar una nueva factura para un docente.

**Campos**: `usuario_id` (UUID, requerido), `periodo` (String 7, AAAA-MM, requerido), `detalle` (Text, requerido), `referencia_archivo` (String 512, opcional), `tamano_kb` (Decimal 10,2, opcional), `materia_id` (UUID, opcional, nullable), `comision_id` (UUID, opcional, nullable).

**Validaciones**:
- `usuario_id` SHALL existir en el mismo tenant
- `periodo` SHALL tener formato `AAAA-MM` válido
- `materia_id` y `comision_id`: AMBAS pueden ser NULL (factura global por período), o AMBAS provistas (factura por comisión específica). No se permite una sola de las dos.

#### Scenario: Crear factura por período (sin comisión específica)
  Given un usuario con permiso `facturas:gestionar`
  Given existe un docente en el tenant
  When envía `POST /api/v1/facturas` con `usuario_id`, `periodo=2026-06`, `detalle=Honorarios junio 2026`
  Then el sistema devuelve HTTP 201 con la Factura creada
  And `materia_id=null`, `comision_id=null`
  And `estado=Pendiente`
  And se registra evento de auditoría `FACTURA_CARGAR`

#### Scenario ⚠️: Crear factura asociada a comisión específica
  Given un docente asignado a una materia + comisión en la cohorte
  When envía `POST /api/v1/facturas` con `usuario_id`, `periodo=2026-06`, `materia_id=X`, `comision_id=Y`, `detalle=Complemento materia PROG`
  Then el sistema devuelve HTTP 201
  And `materia_id` y `comision_id` no son NULL
  And se registra evento de auditoría `FACTURA_CARGAR`

  > ⚠️ **PA-24**: Esta escenario depende de la definición final de cómo se asocian facturas a comisiones. El diseño actual soporta ambos escenarios. Pendiente de confirmación de FINANZAS.

#### Scenario: Crear factura con materia_id pero sin comision_id (inválido)
  Given un usuario con permiso `facturas:gestionar`
  When envía `POST /api/v1/facturas` con `materia_id=X` y `comision_id=null`
  Then el sistema devuelve HTTP 422
  And error: "Si se especifica materia_id, comision_id también es requerido"

#### Scenario: Crear factura con usuario_id inexistente en el tenant
  When envía `POST /api/v1/facturas` con `usuario_id={uuid-aleatorio}`
  Then el sistema devuelve HTTP 404 (usuario no encontrado en el tenant)

#### Scenario: Crear factura con periodo mal formado
  When envía `POST /api/v1/facturas` con `periodo=2026-13`
  Then el sistema devuelve HTTP 422 con error de validación de formato

#### Scenario: Crear factura sin permiso facturas:gestionar
  Given un usuario SIN permiso `facturas:gestionar`
  When intenta crear una factura
  Then el sistema devuelve HTTP 403 Forbidden

---

### Requisito: Listar facturas

El sistema SHALL permitir a usuarios con permiso `facturas:gestionar` listar facturas con filtros: `periodo`, `usuario_id`, `estado`.

#### Scenario: Listar facturas filtrado por estado y período
  Given existen facturas Pendiente y Abonada para varios períodos
  When el usuario envía `GET /api/v1/facturas?estado=Pendiente&periodo=2026-06`
  Then el sistema devuelve HTTP 200 con solo las facturas Pendiente de junio 2026

#### Scenario: Multi-tenant isolation en listado de facturas
  Given el Tenant A tiene facturas cargadas
  When un usuario del Tenant B lista facturas
  Then ninguna factura del Tenant A aparece en los resultados

---

### Requisito: Obtener detalle de factura

El sistema SHALL permitir obtener el detalle completo de una factura por ID.

#### Scenario: Obtener detalle de factura existente
  Given una Factura existente
  When el usuario envía `GET /api/v1/facturas/{id}`
  Then el sistema devuelve HTTP 200 con todos los campos incluyendo `cargada_at` y `referencia_archivo`

#### Scenario: Obtener factura de otro tenant
  Given una Factura del Tenant B
  When un usuario del Tenant A envía `GET /api/v1/facturas/{id}`
  Then el sistema devuelve HTTP 404

---

### Requisito: Abonar factura (transición de estado)

El sistema SHALL permitir a usuarios con permiso `facturas:gestionar` marcar una factura como Abonada.

**Reglas**:
- La transición SHALL ser unidireccional: Pendiente → Abonada
- Una factura Abonada NO puede volver a Pendiente
- Al abonar, se setea `abonada_at` con la fecha/hora actual

#### Scenario: Abonar factura exitosamente
  Given una Factura en estado Pendiente
  When el usuario envía `POST /api/v1/facturas/{id}/abonar`
  Then el sistema devuelve HTTP 200 con `estado=Abonada`
  And `abonada_at` no es NULL
  And se registra evento de auditoría `FACTURA_ABONAR`

#### Scenario: Abonar factura ya abonada
  Given una Factura en estado Abonada
  When el usuario intenta abonarla nuevamente
  Then el sistema devuelve HTTP 409 Conflict

#### Scenario: Abonar factura sin permiso
  Given un usuario SIN permiso `facturas:gestionar`
  When intenta abonar una factura
  Then el sistema devuelve HTTP 403 Forbidden

---

### Requisito: Eliminar factura (soft delete)

El sistema SHALL permitir eliminar (soft delete) una factura existente.

#### Scenario: Soft delete factura exitosamente
  Given una Factura existente (en cualquier estado)
  When el usuario envía `DELETE /api/v1/facturas/{id}`
  Then el sistema devuelve HTTP 204 No Content
  And `is_deleted=true`, `deleted_at` seteado
  And se registra evento de auditoría `FACTURA_ELIMINAR`

#### Scenario: Soft delete factura inexistente
  When el usuario envía `DELETE /api/v1/facturas/{uuid-inexistente}`
  Then el sistema devuelve HTTP 404 Not Found

---

## Resumen

| Tipo | Total |
|------|-------|
| Requirements | 5 (Crear, Listar, Detalle, Abonar, Eliminar) |
| Escenarios | 14 |
| ⚠️ Pendientes de validación | 1 (PA-24: factura asociada a comisión específica) |

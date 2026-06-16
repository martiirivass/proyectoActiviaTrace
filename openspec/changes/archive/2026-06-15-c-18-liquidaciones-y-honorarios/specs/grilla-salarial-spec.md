# Grilla Salarial — Specification (FULL)

> **Domain**: Grilla Salarial (SalarioBase + SalarioPlus)
> **Design**: ADR-007 (Base + Σ Plus × N), PA-22 (grupo_plus), PA-23 (sin tope)
> **Icon legend**: ⚠️ = subject to functional validation (PA-22/PA-23 pending)

---

## ADDED Requirements

### Requisito: Crear SalarioBase

El sistema SHALL permitir a usuarios con permiso `grilla-salarial:crear` registrar un nuevo salario base para un rol con vigencia temporal.

**Campos**: `rol` (enum: PROFESOR|TUTOR|NEXO|COORDINADOR), `monto` (Decimal 10,2), `desde` (Date), `hasta` (Date, nullable).

**Validaciones**:
- `monto` SHALL ser > 0
- `hasta` SHALL ser NULL o posterior a `desde`
- Unique constraint: `(tenant_id, rol, desde)` — no puede existir otro SalarioBase con mismo rol y misma fecha de inicio en el mismo tenant

#### Scenario: Crear salario base exitosamente
  Given un usuario autenticado con permiso `grilla-salarial:crear`
  When envía `POST /api/v1/grilla-salarial/base` con `rol=PROFESOR`, `monto=150000.00`, `desde=2026-01-01`, `hasta=null`
  Then el sistema devuelve HTTP 201 con el SalarioBase creado, incluyendo `id`, `tenant_id`, `rol`, `monto`, `desde`, `hasta`
  And se registra evento de auditoría `SALARIO_BASE_CREAR`

#### Scenario: Crear salario base sin permiso
  Given un usuario autenticado SIN permiso `grilla-salarial:crear`
  When envía `POST /api/v1/grilla-salarial/base` con datos válidos
  Then el sistema devuelve HTTP 403 Forbidden

#### Scenario: Crear salario base con monto cero o negativo
  Given un usuario con permiso `grilla-salarial:crear`
  When envía `POST /api/v1/grilla-salarial/base` con `monto=0`
  Then el sistema devuelve HTTP 422 con error de validación indicando que monto debe ser > 0

#### Scenario: Crear salario base violando unique constraint (mismo rol, misma fecha)
  Given existe un SalarioBase con `rol=PROFESOR`, `desde=2026-01-01`
  When el mismo usuario envía `POST /api/v1/grilla-salarial/base` con `rol=PROFESOR`, `desde=2026-01-01`
  Then el sistema devuelve HTTP 409 Conflict indicando que ya existe un registro para ese rol en esa fecha

#### Scenario: Crear salario base con vigencia traslapada (mismo rol, fecha solapada)
  Given existe un SalarioBase con `rol=TUTOR`, `desde=2026-01-01`, `hasta=2026-06-30`
  When el usuario envía `POST /api/v1/grilla-salarial/base` con `rol=TUTOR`, `desde=2026-03-01`
  Then el sistema NO bloquea por traslape (la validación es solo sobre unique `(tenant_id, rol, desde)`, no sobre rangos)

  > **Nota**: El diseño actual usa unique constraint sobre `(tenant_id, rol, desde)`. La responsabilidad de no crear rangos solapados es del usuario FINANZAS. Se documenta como decisión consciente.

#### Scenario: Multi-tenant isolation en SalarioBase
  Given el Tenant A tiene un SalarioBase para PROFESOR con `monto=150000`
  When un usuario del Tenant B lista salarios base (`GET /api/v1/grilla-salarial/base`)
  Then el registro del Tenant A NO aparece en los resultados del Tenant B

---

### Requisito: Listar SalarioBase

El sistema SHALL permitir a usuarios con permiso `grilla-salarial:ver` listar salarios base con filtros opcionales: `rol`, `vigente` (boolean).

#### Scenario: Listar salarios base filtrado por rol
  Given existen SalarioBase para PROFESOR y TUTOR
  When un usuario con permiso `grilla-salarial:ver` envía `GET /api/v1/grilla-salarial/base?rol=PROFESOR`
  Then el sistema devuelve HTTP 200 con solo los registros de PROFESOR

#### Scenario: Listar solo salarios base vigentes
  Given existen SalarioBase vigentes (desde <= hoy, hasta IS NULL o >= hoy) y vencidos (hasta < hoy)
  When el usuario envía `GET /api/v1/grilla-salarial/base?vigente=true`
  Then el sistema devuelve HTTP 200 con solo los registros vigentes

---

### Requisito: Editar SalarioBase

El sistema SHALL permitir a usuarios con permiso `grilla-salarial:editar` modificar `monto`, `desde` y/o `hasta` de un SalarioBase existente.

#### Scenario: Editar monto de SalarioBase exitosamente
  Given un SalarioBase existente con `monto=100000`
  When el usuario envía `PUT /api/v1/grilla-salarial/base/{id}` con `monto=120000`
  Then el sistema devuelve HTTP 200 con el monto actualizado
  And se registra evento de auditoría `SALARIO_BASE_MODIFICAR`

#### Scenario: Editar SalarioBase inexistente
  When el usuario envía `PUT /api/v1/grilla-salarial/base/{uuid-inexistente}`
  Then el sistema devuelve HTTP 404 Not Found

---

### Requisito: Eliminar SalarioBase (soft delete)

El sistema SHALL permitir a usuarios con permiso `grilla-salarial:eliminar` eliminar (soft delete) un SalarioBase existente.

#### Scenario: Soft delete SalarioBase exitosamente
  Given un SalarioBase existente
  When el usuario envía `DELETE /api/v1/grilla-salarial/base/{id}`
  Then el sistema devuelve HTTP 204 No Content
  And el registro queda con `is_deleted=true`, `deleted_at` seteado
  And no aparece en listados GET
  And se registra evento de auditoría `SALARIO_BASE_ELIMINAR`

---

### Requisito: Crear SalarioPlus

El sistema SHALL permitir a usuarios con permiso `grilla-salarial:crear` registrar un nuevo plus salarial para un grupo+rol con vigencia temporal.

⚠️ **PA-22**: El campo `grupo` es una clave string libre (ej: "PROG", "BD", "MAT"). Su mapeo a materias via `materia.grupo_plus` está pendiente de validación funcional.

**Campos**: `grupo` (String 50), `rol` (enum), `descripcion` (String 255), `monto` (Decimal 10,2), `desde` (Date), `hasta` (Date, nullable).

**Validaciones**:
- `monto` SHALL ser > 0
- Unique constraint: `(tenant_id, grupo, rol, desde)`

#### Scenario: Crear SalarioPlus exitosamente
  Given un usuario con permiso `grilla-salarial:crear`
  When envía `POST /api/v1/grilla-salarial/plus` con `grupo=PROG`, `rol=PROFESOR`, `monto=25000.00`, `desde=2026-01-01`
  Then el sistema devuelve HTTP 201 con el SalarioPlus creado
  And se registra evento de auditoría `SALARIO_PLUS_CREAR`

#### Scenario ⚠️: Crear SalarioPlus con grupo que no existe en ninguna materia del tenant
  Given el tenant NO tiene materias con `grupo_plus=ZZZ`
  When el usuario envía `POST /api/v1/grilla-salarial/plus` con `grupo=ZZZ`
  Then el sistema acepta la creación (no hay validación contra materia.grupo_plus — el grupo solo se valida al calcular liquidaciones)
  And se registra evento de auditoría `SALARIO_PLUS_CREAR`

  > ⚠️ **PA-22**: Esta escenario documenta el comportamiento actual. Si se decide que los grupos deben pre-existir como catálogo, esta regla cambiará.

#### Scenario: Crear SalarioPlus duplicado (mismo grupo, rol, desde)
  Given existe un SalarioPlus con `grupo=BD`, `rol=TUTOR`, `desde=2026-01-01`
  When el usuario envía `POST /api/v1/grilla-salarial/plus` con mismos valores
  Then el sistema devuelve HTTP 409 Conflict

---

### Requisito: Listar SalarioPlus

El sistema SHALL permitir listar pluses con filtros: `grupo`, `rol`, `vigente`.

#### Scenario: Listar pluses vigentes para un grupo y rol específico
  Given existen SalarioPlus para varios grupos y roles
  When el usuario envía `GET /api/v1/grilla-salarial/plus?grupo=PROG&rol=PROFESOR&vigente=true`
  Then el sistema devuelve HTTP 200 con solo los registros que matchean

---

### Requisito: Editar y Eliminar SalarioPlus

Mismas reglas que SalarioBase: edit con `grilla-salarial:editar`, soft delete con `grilla-salarial:eliminar`.

#### Scenario: Soft delete SalarioPlus
  Given un SalarioPlus existente
  When el usuario envía `DELETE /api/v1/grilla-salarial/plus/{id}`
  Then el sistema devuelve HTTP 204 No Content
  And se registra evento de auditoría `SALARIO_PLUS_ELIMINAR`

## Resumen

| Tipo | Total |
|------|-------|
| Requirements | 6 (Crear/Listar/Editar/Eliminar SalarioBase, Crear/Listar/Editar/Eliminar SalarioPlus) |
| Escenarios | 17 |
| ⚠️ Pendientes de validación | 1 (PA-22: grupo no existente en materias) |

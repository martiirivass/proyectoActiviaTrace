# Liquidaciones — Specification (FULL)

> **Domain**: Liquidaciones (cálculo, gestión, cierre, KPIs)
> **Dependencies**: SalarioBase, SalarioPlus, Asignacion (C-07), Materia.grupo_plus
> **Icon legend**: ⚠️ = subject to functional validation (PA-22/PA-23/ADR-007)

---

## ADDED Requirements

### Requisito: Calcular liquidación para cohorte + período

El sistema SHALL permitir a usuarios con permiso `liquidaciones:calcular` ejecutar el cálculo de liquidaciones para una cohorte y período específicos.

**Fórmula** (ADR-007): Por cada docente con asignaciones activas en la cohorte:  
`total = monto_base(rol) + Σ( Plus(grupo, rol) × N_comisiones_de_ese_grupo )`

**Reglas de negocio**:
- RN-31: Se usa el SalarioBase vigente para el rol en la fecha del período
- RN-33: Se usa el SalarioPlus vigente para (grupo, rol) en la fecha del período
- RN-34: Si un docente tiene N comisiones del mismo grupo, acumula N × el plus correspondiente (sin tope — PA-23 asumido)
- RN-35: Si el docente es facturante → `excluido_por_factura = true`, el cálculo se registra pero el docente no genera pago
- RN-36: Si el rol es NEXO → `es_nexo = true`, se calcula igual pero identificado para liquidación separada
- Si no existe SalarioBase para el rol del docente → la liquidación NO se genera y se reporta error
- Si no existe SalarioPlus para un (grupo, rol) → se usa monto_plus = 0 (no bloquea)

#### Scenario: Calcular liquidación simple (1 materia, 1 grupo, 1 comisión)
  Given un docente con rol PROFESOR asignado a 1 materia con `grupo_plus=PROG` en la cohorte
  And existe SalarioBase `PROFESOR` vigente con `monto=150000`
  And existe SalarioPlus `(PROG, PROFESOR)` vigente con `monto=25000`
  When un usuario con permiso `liquidaciones:calcular` envía `POST /api/v1/liquidaciones/calcular?cohorte_id=X&periodo=2026-06`
  Then el sistema crea 1 Liquidacion con `total=175000` (150000 + 1×25000)
  And `monto_base=150000`, `monto_plus=25000`
  And `comisiones` JSONB contiene 1 entrada con `grupo_plus=PROG`, `monto_plus=25000`
  And se registra evento de auditoría `LIQUIDACION_CALCULAR`

#### Scenario: Múltiples comisiones del mismo grupo (acumulación N × Plus)
  Given un docente con rol PROFESOR asignado a 3 comisiones de materias con `grupo_plus=PROG`
  And mismo SalarioBase y SalarioPlus que escenario anterior
  When se ejecuta el cálculo
  Then `monto_plus=75000` (3 × 25000)
  And `total=225000` (150000 + 75000)

  > ⚠️ **PA-23**: Sin tope de acumulación. Si FINANZAS define un tope máximo, esta regla cambia.

#### Scenario: Múltiples grupos distintos
  Given un docente con 2 materias grupo PROG y 1 materia grupo BD
  And SalarioPlus `(PROG, PROFESOR)=25000`, `(BD, PROFESOR)=30000`
  When se ejecuta el cálculo
  Then `monto_plus=80000` (2×25000 + 1×30000)
  And `comisiones` JSONB contiene 2 entradas agrupadas por grupo

#### Scenario: Docente facturante excluido
  Given un docente con `es_facturante=true`
  When se ejecuta el cálculo
  Then la Liquidacion se crea con `excluido_por_factura=true`
  And `total` se calcula normalmente pero el docente se marca como excluido
  And el docente aparece en KPIs como facturante (no genera pago)

#### Scenario: Docente con rol NEXO
  Given un docente con `rol=NEXO` en la cohorte
  When se ejecuta el cálculo
  Then la Liquidacion se crea con `es_nexo=true`
  And el cálculo usa SalarioBase y SalarioPlus para rol NEXO

#### Scenario: Sin SalarioBase definido para el rol
  Given un docente con rol COORDINADOR pero NO existe SalarioBase para COORDINADOR vigente en el período
  When se ejecuta el cálculo
  Then el sistema devuelve HTTP 422 con error indicando qué roles no tienen salario base definido
  And NO se genera ninguna Liquidacion (operación atómica)

#### Scenario: Sin SalarioPlus para un grupo (no bloquea)
  Given un docente con materia `grupo_plus=MAT` pero NO existe SalarioPlus para `(MAT, PROFESOR)`
  When se ejecuta el cálculo
  Then el sistema calcula con `monto_plus=0` para ese grupo
  And la Liquidacion se crea exitosamente

#### Scenario: Re-cálculo idempotente (misma cohorte + período)
  Given ya existe una Liquidacion para `(cohorte_id, periodo, usuario_id)` en estado Abierta
  When se ejecuta el cálculo nuevamente con los mismos parámetros
  Then el sistema ACTUALIZA la Liquidacion existente (no la duplica)
  And `monto_base`, `monto_plus` y `comisiones` reflejan los valores recalculados
  And se registra evento de auditoría `LIQUIDACION_CALCULAR`

#### Scenario: Re-cálculo de una liquidación Cerrada (bloqueo)
  Given la Liquidacion existente está en estado Cerrada
  When se ejecuta el cálculo nuevamente
  Then el sistema devuelve HTTP 409 Conflict
  And no se modifica la Liquidacion

#### Scenario: Sin asignaciones activas en la cohorte
  Given la cohorte no tiene docentes asignados
  When se ejecuta el cálculo
  Then el sistema devuelve HTTP 200 con arreglo vacío `[]`

#### Scenario: Multi-tenant isolation en cálculo
  Given el Tenant A tiene asignaciones en cohorte X
  When un usuario del Tenant B ejecuta cálculo con `cohorte_id=X` (UUID del Tenant A)
  Then el sistema devuelve error (cohorte no pertenece al tenant del usuario)

---

### Requisito: Cerrar liquidación

El sistema SHALL permitir a usuarios con permiso `liquidaciones:cerrar` cerrar una liquidación en estado Abierta, haciéndola inmutable.

#### Scenario: Cerrar liquidación exitosamente
  Given una Liquidacion en estado Abierta
  When el usuario envía `POST /api/v1/liquidaciones/{id}/cerrar`
  Then el sistema devuelve HTTP 200 con `estado=Cerrada`
  And se registra evento de auditoría `LIQUIDACION_CERRAR`
  And cualquier intento posterior de modificar o re-calcular esta liquidación devuelve 409

#### Scenario: Cerrar liquidación ya cerrada
  Given una Liquidacion en estado Cerrada
  When el usuario intenta cerrarla nuevamente
  Then el sistema devuelve HTTP 409 Conflict

#### Scenario: Cerrar liquidación de otro tenant
  Given una Liquidacion del Tenant B
  When un usuario del Tenant A envía `POST /api/v1/liquidaciones/{id}/cerrar`
  Then el sistema devuelve HTTP 404 (la liquidación no existe en su tenant)

#### Scenario: Cerrar sin permiso
  Given un usuario SIN permiso `liquidaciones:cerrar`
  When intenta cerrar una liquidación
  Then el sistema devuelve HTTP 403 Forbidden

---

### Requisito: Listar y obtener detalle de liquidaciones

El sistema SHALL permitir a usuarios con permiso `liquidaciones:ver` listar liquidaciones con filtros (`cohorte_id`, `periodo`, `usuario_id`) y obtener detalle individual.

#### Scenario: Listar liquidaciones con filtros combinados
  Given existen liquidaciones para varias cohortes y períodos
  When el usuario envía `GET /api/v1/liquidaciones?cohorte_id=X&periodo=2026-06`
  Then el sistema devuelve HTTP 200 con solo las liquidaciones que matchean ambos filtros

#### Scenario: Obtener detalle de liquidación
  Given una Liquidacion existente
  When el usuario envía `GET /api/v1/liquidaciones/{id}`
  Then el sistema devuelve HTTP 200 con todos los campos, incluyendo `comisiones` (JSONB expandido)

---

### Requisito: KPIs facturantes vs no-facturantes

El sistema SHALL exponer indicadores diferenciados de totales facturantes y no-facturantes (RN-38).

#### Scenario: KPIs para una cohorte y período
  Given existen liquidaciones con docentes facturantes y no-facturantes
  When el usuario envía `GET /api/v1/liquidaciones?cohorte_id=X&periodo=2026-06&kpis=true`
  Then el sistema devuelve en la respuesta:
  - `total_facturante`: suma de totales donde `excluido_por_factura=true`
  - `total_no_facturante`: suma de totales donde `excluido_por_factura=false`
  - `cantidad_facturante`: count de docentes facturantes
  - `cantidad_no_facturante`: count de docentes no-facturantes

---

### Requisito: Exportar liquidaciones

El sistema SHALL permitir a usuarios con permiso `liquidaciones:exportar` descargar listado de liquidaciones (CSV).

#### Scenario: Exportar liquidaciones a CSV
  Given existen liquidaciones para una cohorte
  When el usuario envía `GET /api/v1/liquidaciones/exportar?cohorte_id=X&periodo=2026-06`
  Then el sistema devuelve HTTP 200 con Content-Type `text/csv`
  And el CSV incluye columnas: usuario, rol, monto_base, monto_plus, total, excluido_por_factura, es_nexo, estado

---

### Requisito: Historial de cálculos

El sistema SHALL permitir a usuarios con permiso `liquidaciones:historial` ver el historial de ejecuciones de cálculo (fecha, usuario que calculó, cohorte, período).

#### Scenario: Ver historial de cálculos
  Given existen múltiples eventos `LIQUIDACION_CALCULAR` en el audit log
  When el usuario envía `GET /api/v1/liquidaciones/historial`
  Then el sistema devuelve HTTP 200 con listado paginado de ejecuciones

---

## Resumen

| Tipo | Total |
|------|-------|
| Requirements | 6 (Calcular, Cerrar, Listar/Detalle, KPIs, Exportar, Historial) |
| Escenarios | 20 |
| ⚠️ Pendientes de validación | 1 (PA-23: sin tope de acumulación N × Plus) |

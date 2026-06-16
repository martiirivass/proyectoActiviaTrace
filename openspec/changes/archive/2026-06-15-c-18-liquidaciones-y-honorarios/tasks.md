# Tasks: C-18 Liquidaciones y Honorarios

## Phase 1: Foundation (Models + Migration)

- [ ] 1.1 Add `grupo_plus: String(50), nullable` column to `app/models/materia.py`
- [ ] 1.2 Create enums in `app/models/liquidacion.py`: `RolLiquidacion`, `EstadoLiquidacion`, `EstadoFactura`
- [ ] 1.3 Create `app/models/salario_base.py` — model SalarioBase (E17) with unique(tenant_id, rol, desde)
- [ ] 1.4 Create `app/models/salario_plus.py` — model SalarioPlus (E18) with unique(tenant_id, grupo, rol, desde)
- [ ] 1.5 Create `app/models/liquidacion.py` — model Liquidacion (E19) with JSONB comisiones, unique(tenant_id, cohorte_id, periodo, usuario_id)
- [ ] 1.6 Create `app/models/factura.py` — model Factura (E20) with optional materia_id/comision_id per PA-24
- [ ] 1.7 Register all new models + enums in `app/models/__init__.py` and `__all__`
- [ ] 1.8 Create Alembic migration — 4 new tables + Materia.grupo_plus column

## Phase 2: Repositories

- [ ] 2.1 Create `app/repositories/grilla_salarial_repository.py` — GrillaSalarialRepository(TenantScopedRepository) with find_vigente_by_rol/find_vigente_by_grupo_rol queries
- [ ] 2.2 Create `app/repositories/liquidacion_repository.py` — LiquidacionRepository with find_by_cohorte_periodo, find_by_usuario_cohorte_periodo, kpi_aggregation
- [ ] 2.3 Create `app/repositories/factura_repository.py` — FacturaRepository with dual periodo/comision filter support (PA-24)

## Phase 3: Schemas

- [ ] 3.1 Create `app/schemas/liquidaciones.py` — all Pydantic v2 schemas with `extra='forbid'`: SalarioBaseCreate/Update/Response, SalarioPlusCreate/Update/Response, LiquidacionCreate/Response, LiquidacionCalcularRequest/Response, FacturaCreate/Response, KPIResponse, periodic format validator

## Phase 4: Services

- [x] 4.1 Create `app/services/grilla_salarial_service.py` — CRUD for SalarioBase + SalarioPlus with vigency validation, audit logging for all 6 action codes
- [x] 4.2 Create `app/services/liquidacion_service.py` — pure calculation function (Base + Σ Plus × N), Calcular/Cerrar/Listar/Obtener, recalculo idempotent, 409 on Cerrada, KPI aggregation
- [x] 4.3 Create `app/services/factura_service.py` — CRUD + abonar (Pendiente→Abonada, 409 if already Abonada), dual association validation (PA-24), audit logging

> ⚠️ Task 4.2 depends on PA-23 (no cap assumed) and ADR-007 (formula). Calculation logic may change.

## Phase 5: API Layer

- [ ] 5.1 Create `app/api/v1/routers/grilla_salarial.py` — 8 endpoints with `require_permission()` on all mutations
- [ ] 5.2 Create `app/api/v1/routers/liquidaciones.py` — 6 endpoints (POST /calcular, GET /, GET /{id}, POST /{id}/cerrar, GET /exportar, GET /historial)
- [ ] 5.3 Create `app/api/v1/routers/facturas.py` — 5 endpoints (GET /, POST /, GET /{id}, POST /{id}/abonar, DELETE /{id})
- [ ] 5.4 Register all 3 routers in `app/api/v1/routers/__init__.py`

## Phase 6: Permissions & Audit

- [ ] 6.1 Add 10 permission constants to `app/core/permissions.py` (GRILLA_SALARIAL_VER/CREAR/EDITAR/ELIMINAR, LIQUIDACIONES_VER/CALCULAR/CERRAR/EXPORTAR/HISTORIAL, FACTURAS_GESTIONAR)
- [ ] 6.2 Add 12 audit codes to `app/core/audit_codes.py` (LIQUIDACION_CALCULAR, LIQUIDACION_CERRAR, LIQUIDACION_REABRIR, SALARIO_BASE_CREAR/MODIFICAR/ELIMINAR, SALARIO_PLUS_CREAR/MODIFICAR/ELIMINAR, FACTURA_CARGAR/ABONAR/ELIMINAR)

## Phase 7: Tests

- [ ] 7.1 Create `backend/tests/test_liquidaciones/conftest.py` — fixtures: SalarioBase, SalarioPlus, Materia(grupo_plus), Liquidacion, Factura
- [ ] 7.2 Test GrillaSalarial — CRUD, unique constraint violation (409), vigency filters, soft delete, multi-tenant isolation
- [ ] 7.3 Test calculation — 1 materia/N comisiones/multi-grupo, facturante excluido, NEXO, missing SalarioBase (422), missing SalarioPlus (0), empty cohorte, multi-tenant
- [ ] 7.4 Test Liquidacion lifecycle — crear, listar, recalcular idempotent, cerrar, recalcular Cerrada (409), reabrir
- [ ] 7.5 Test Facturas — CRUD, Pendiente→Abonada, Abonada→Abonada (409), dual association (PA-24), invalid formato periodo (422), multi-tenant 404
- [ ] 7.6 Test permissions — each endpoint with and without required permission (403)
- [ ] 7.7 Test audit logging — each action generates correct audit code via AuditService

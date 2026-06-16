## 1. Feature module scaffolding y types

- [x] 1.1 Create `features/finanzas/` directory structure: `components/`, `hooks/`, `services/`, `types/`, `pages/`
- [x] 1.2 Create `features/admin/` directory structure: `components/`, `hooks/`, `services/`, `types/`, `pages/`
- [x] 1.3 Create `features/finanzas/types/index.ts` with DTOs: Liquidacion, LiquidacionKPI, SalarioBase, SalarioPlus, Factura
- [x] 1.4 Create `features/admin/types/index.ts` with DTOs: Carrera, Cohorte, Materia, Dictado, Usuario, AuditDashboard, AuditLogEntry

## 2. Services FINANZAS — Capa de API

- [x] 2.1 Create `liquidacionesService.ts`: listar(cohorteId, periodo, kpis?) → GET /liquidaciones, calcular(cohorteId, periodo) → POST /liquidaciones/calcular, cerrar(id) → POST /liquidaciones/{id}/cerrar, historial(page, perPage) → GET /liquidaciones/historial, exportar(cohorteId, periodo) → GET /liquidaciones/exportar (blob)
- [x] 2.2 Create `grillaSalarialService.ts`: getSalariosBase(rol?, vigente?) → GET /grilla-salarial/base, createSalarioBase(data) → POST /grilla-salarial/base, updateSalarioBase(id, data) → PUT /grilla-salarial/base/{id}, deleteSalarioBase(id) → DELETE /grilla-salarial/base/{id}, getSalariosPlus(grupo?, rol?, vigente?) → GET /grilla-salarial/plus, createSalarioPlus(data) → POST /grilla-salarial/plus, updateSalarioPlus(id, data) → PUT /grilla-salarial/plus/{id}, deleteSalarioPlus(id) → DELETE /grilla-salarial/plus/{id}
- [x] 2.3 Create `facturasService.ts`: listar(filtros) → GET /facturas, getById(id) → GET /facturas/{id}, create(data) → POST /facturas, abonar(id) → POST /facturas/{id}/abonar, delete(id) → DELETE /facturas/{id}

## 3. Services ADMIN — Capa de API

- [x] 3.1 Create `estructuraService.ts`: carreras CRUD (GET/POST/PUT/DELETE /admin/carreras[/{id}]), cohortes CRUD (GET/POST/PUT/DELETE /admin/cohortes[/{id}]), materias CRUD (GET/POST/PUT/DELETE /admin/materias[/{id}]), dictados CRUD (GET/POST/PUT/DELETE /admin/dictados[/{id}])
- [x] 3.2 Create `usuariosService.ts`: listar(params) → GET /admin/usuarios, getById(id) → GET /admin/usuarios/{id}, create(data) → POST /admin/usuarios, update(id, data) → PUT /admin/usuarios/{id}, delete(id) → DELETE /admin/usuarios/{id}
- [x] 3.3 Create `auditoriaService.ts`: getDashboard(filtros) → GET /api/audit/dashboard, getLog(filtros) → GET /api/audit/log

## 4. Hooks FINANZAS — TanStack Query wrappers

- [x] 4.1 Create `useLiquidaciones.ts`: useQuery(["liquidaciones", cohorteId, periodo]) con kpis=true, useMutation calcular (POST /liquidaciones/calcular), useMutation cerrar (POST /liquidaciones/{id}/cerrar) con invalidate de queries, useQuery(["liquidaciones-historial", page]), useMutation exportar (blob download)
- [x] 4.2 Create `useGrillaSalarial.ts`: useQuery(["grilla-base", rol, vigente]), useQuery(["grilla-plus", grupo, rol, vigente]), useMutation for create/update/delete on both SalarioBase and SalarioPlus; invalidate queries on success
- [x] 4.3 Create `useFacturas.ts`: useQuery(["facturas", filtros]), useQuery(["factura", id]), useMutation create, useMutation abonar, useMutation delete; invalidate queries on success

## 5. Hooks ADMIN — TanStack Query wrappers

- [x] 5.1 Create `useEstructura.ts`: hooks for carreras (list, create, update, delete), cohortes (list by carrera, create, update, delete), materias (list, create, update, delete), dictados (list with filters, create, update, delete); each entity has its own query key and mutations with invalidation
- [x] 5.2 Create `useUsuarios.ts`: useQuery(["usuarios", page, search, rol]), useQuery(["usuario", id]), useMutation create/update/delete with invalidate
- [x] 5.3 Create `useAuditoria.ts`: useQuery(["audit-dashboard", filtros]), useQuery(["audit-log", filtros, page, offset])

## 6. Liquidaciones — Vista principal

- [x] 6.1 Create `LiquidacionesPage.tsx`: lazy-loaded page, renders LiquidacionesView
- [x] 6.2 Create `FiltrosLiquidaciones.tsx`: cohorte select, período input (AAAA-MM), botón "Calcular" que dispara la mutación o query
- [x] 6.3 Create `KPILiquidaciones.tsx`: KPI cards row (Total Facturante, Total No Facturante, Cantidad Facturante, Cantidad No Facturante)
- [x] 6.4 Create `TabsSegmentacion.tsx`: 3 tabs "General" / "NEXO" / "Factura" que filtran la tabla client-side
- [x] 6.5 Create `LiquidacionesTable.tsx`: table with columns (Docente, Rol, Monto Base, Monto Plus, Total, Estado), shows loading/empty/error states
- [x] 6.6 Create `LiquidacionesHistorial.tsx`: expandible section or sub-page with paginated table of calculation history
- [x] 6.7 Create `ExportarButton.tsx`: button that triggers CSV download via useLiquidaciones export mutation
- [x] 6.8 Create `LiquidacionesView.tsx`: composes FiltrosLiquidaciones + KPILiquidaciones + TabsSegmentacion + LiquidacionesTable + LiquidacionesHistorial + ExportarButton

## 7. Grilla Salarial

- [x] 7.1 Create `GrillaSalarialPage.tsx`: lazy-loaded page, renders GrillaSalarialView
- [x] 7.2 Create `TabsGrilla.tsx`: tabs for "Salario Base" / "Salario Plus"
- [x] 7.3 Create `SalarioBaseTable.tsx`: table with columns (Rol, Monto, Desde, Hasta, Estado), filters for rol and vigencia, "Nuevo" button, "Editar" and "Eliminar" actions per row
- [x] 7.4 Create `SalarioBaseFormModal.tsx`: modal with RHF+Zod form (Rol select, Monto input, Desde date, Hasta date optional), create/edit mode
- [x] 7.5 Create `SalarioPlusTable.tsx`: table with columns (Grupo, Rol, Descripción, Monto, Desde, Hasta), filters for grupo/rol/vigencia
- [x] 7.6 Create `SalarioPlusFormModal.tsx`: modal with RHF+Zod form (Grupo, Rol, Descripción, Monto, Desde, Hasta)
- [x] 7.7 Create `ConfirmDeleteModal.tsx`: reusable confirmation modal for soft delete
- [x] 7.8 Create `GrillaSalarialView.tsx`: composes TabsGrilla + SalarioBaseTable / SalarioPlusTable based on active tab

## 8. Facturas

- [x] 8.1 Create `FacturasPage.tsx`: lazy-loaded page, renders FacturasView
- [x] 8.2 Create `FiltrosFacturas.tsx`: filters for período (AAAA-MM), estado (Pendiente/Abonada), usuario (select/search)
- [x] 8.3 Create `FacturasTable.tsx`: table with columns (Docente, Período, Detalle, Estado, Fecha Carga), actions "Abonar" / "Eliminar" per row (Abonar only for Pendiente)
- [x] 8.4 Create `FacturaFormModal.tsx`: modal with RHF+Zod form (Docente select, Período, Detalle, Referencia Archivo, Tamaño KB, Materia+Comisión optional pair)
- [x] 8.5 Create `ConfirmAbonarModal.tsx`: confirmation modal for abonar action with success/error feedback
- [x] 8.6 Create `FacturasView.tsx`: composes FiltrosFacturas + FacturasTable + FacturaFormModal

## 9. Estructura Académica

- [x] 9.1 Create `EstructuraPage.tsx`: lazy-loaded page, renders EstructuraView
- [x] 9.2 Create `TabsEntidades.tsx`: tabs for "Carreras" / "Cohortes" / "Materias" / "Dictados"
- [x] 9.3 Create `CarrerasTable.tsx`: table with columns (Código, Nombre, Estado), "Nueva Carrera" button, "Editar"/"Eliminar" actions
- [x] 9.4 Create `CarreraFormModal.tsx`: modal with RHF+Zod form (Código, Nombre)
- [x] 9.5 Create `CohortesTable.tsx`: table with filter by carrera (select), columns (Carrera, Nombre, Año, Estado)
- [x] 9.6 Create `CohorteFormModal.tsx`: modal with RHF+Zod form (Carrera select, Nombre, Año)
- [x] 9.7 Create `MateriasTable.tsx`: table with columns (Código, Nombre, Estado)
- [x] 9.8 Create `MateriaFormModal.tsx`: modal with RHF+Zod form (Código, Nombre)
- [x] 9.9 Create `DictadosTable.tsx`: table with filters for materia and cohorte, columns (Materia, Carrera, Cohorte, Nombre Dictado)
- [x] 9.10 Create `DictadoFormModal.tsx`: modal with RHF+Zod form (Materia select, Carrera select, Cohorte select filtered by carrera, Nombre)
- [x] 9.11 Create `EstructuraView.tsx`: composes TabsEntidades + active entity table based on active tab

## 10. Usuarios

- [x] 10.1 Create `UsuariosPage.tsx`: lazy-loaded page, renders UsuariosView
- [x] 10.2 Create `FiltrosUsuarios.tsx`: search input, rol filter (multi-select), estado filter
- [x] 10.3 Create `UsuariosTable.tsx`: paginated table with columns (Email, Nombre, Apellido, DNI, Roles, Regional, Facturador, Estado), "Editar"/"Eliminar" actions
- [x] 10.4 Create `UsuarioFormModal.tsx`: modal with RHF+Zod form with all user fields (Email, Nombre, Apellido, DNI, Password opcional en edición, CUIL, CBU, Alias CBU, Banco, Regional, Legajo, Legajo Profesional, Facturador checkbox); validation for email format, DNI required, password length in creation
- [x] 10.5 Create `UsuariosView.tsx`: composes FiltrosUsuarios + UsuariosTable + UsuarioFormModal

## 11. Auditoría — Dashboard

- [x] 11.1 Create `AuditoriaPage.tsx`: lazy-loaded page, renders AuditoriaDashboardView with link to /admin/auditoria/log
- [x] 11.2 Create `FiltrosAuditoria.tsx`: date range inputs (desde/hasta), materia select
- [x] 11.3 Create `KPIAuditoria.tsx`: summary KPI cards (total acciones, total comunicaciones, período)
- [x] 11.4 Create `AccionesPorDiaChart.tsx`: simple bar chart (CSS/SVG) showing actions per day from dashboard data
- [x] 11.5 Create `ComunicacionesPorDocenteTable.tsx`: table showing docente communication distribution (Pendiente, Enviando, Enviado, Error, Cancelado)
- [x] 11.6 Create `InteraccionesPorDocenteMateriaTable.tsx`: table with expandible rows showing docente+materia interactions with action type breakdown
- [x] 11.7 Create `UltimasAccionesTable.tsx`: table of most recent 200 audit entries (Fecha/Hora, Actor, Acción, Materia, Detalle)
- [x] 11.8 Create `AuditoriaDashboardView.tsx`: composes all dashboard sections, loading/error states

## 12. Auditoría — Log completo

- [x] 12.1 Create `AuditLogPage.tsx`: lazy-loaded page, renders AuditLogView
- [x] 12.2 Create `FiltrosLog.tsx`: filter form with acción (dropdown), actor (select/search), date range (desde/hasta), materia (select); "Limpiar filtros" button
- [x] 12.3 Create `AuditLogTable.tsx`: paginated table with columns (Fecha/Hora, Actor, Acción, Materia, Detalle, IP), expandible rows for detail view, loading/empty/error states
- [x] 12.4 Create `AuditLogView.tsx`: composes FiltrosLog + AuditLogTable

## 13. Router — Integrar nuevas rutas

- [x] 13.1 Add lazy imports for all new pages in `router/index.tsx`: LiquidacionesPage, GrillaSalarialPage, FacturasPage, EstructuraPage, UsuariosPage, AuditoriaPage, AuditLogPage
- [x] 13.2 Add new protected routes under existing AuthGuard/AppLayout:
  - `/finanzas/liquidaciones` → LiquidacionesPage
  - `/finanzas/grilla-salarial` → GrillaSalarialPage
  - `/finanzas/facturas` → FacturasPage
  - `/admin/estructura` → EstructuraPage
  - `/admin/usuarios` → UsuariosPage
  - `/admin/auditoria` → AuditoriaPage
  - `/admin/auditoria/log` → AuditLogPage
- [x] 13.3 Add permission guards to routes where appropriate
- [x] 13.4 Update AppLayout sidebar menu items to include new FINANZAS and ADMIN routes, filtered by user permissions

## 14. Tests

- [x] 14.1 Create MSW handlers for finanzas endpoints (liquidaciones, grilla-salarial, facturas) and admin endpoints (estructura, usuarios, auditoria)
- [x] 14.2 Write `LiquidacionesView.test.tsx`: renders with filters, loads data, tabs segment correctly, KPIs display, close action shows confirmation and handles success/error
- [x] 14.3 Write `GrillaSalarial.test.tsx`: renders tabs, creates SalarioBase, shows validation errors, deletes with confirmation
- [x] 14.4 Write `Facturas.test.tsx`: renders list with filters, creates factura with validation, abona and handles 409
- [x] 14.5 Write `Estructura.test.tsx`: creates carrera/cohorte, shows 409 on duplicate, filters cohortes by carrera
- [x] 14.6 Write `AuditDashboard.test.tsx`: loads dashboard data, shows all 4 sections, filters by date range

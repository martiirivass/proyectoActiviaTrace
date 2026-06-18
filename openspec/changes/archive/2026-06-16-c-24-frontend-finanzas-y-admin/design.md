## Context

El backend de activia-trace tiene todas las APIs de los módulos FINANZAS y ADMIN operativas: liquidaciones (cálculo, cierre, listado, KPIs, historial), grilla salarial (SalarioBase y SalarioPlus CRUD), facturas (CRUD, abonar, soft delete), estructura académica (carreras, cohortes, materias, dictados), usuarios del tenant (ABM con PII), y auditoría (dashboard con métricas agregadas y log completo con filtros). El frontend actual (C-21, C-22, C-23) provee el shell, las vistas de PROFESOR/TUTOR y las vistas de COORDINADOR.

No existen páginas para los roles FINANZAS y ADMIN. Este cambio implementa todas las vistas que ambos perfiles necesitan para operar la gestión financiera y administrativa del tenant.

**Stack vigente:** React 18 + TypeScript, Vite, TanStack Query v5, React Hook Form + Zod, Axios, Tailwind CSS v4, React Router v6 (createBrowserRouter).

**Restricciones:**
- No modificar backend.
- Consumir endpoints existentes de C-18 (liquidaciones/facturas/grilla), C-19 (auditoría), C-06 (estructura académica), C-07 (usuarios).
- Seguir la estructura feature-based de C-21/C-22/C-23: `features/finanzas/` y `features/admin/` con `{components, hooks, services, types, pages}`.
- Sin `any`, sin class components, componentes <200 LOC, lazy loading.
- Usar el patrón de servicio centralizado `api.ts` con `get/post/put/patch/del`.

## Goals / Non-Goals

**Goals:**
- Feature module `features/finanzas/` con vistas de liquidaciones, grilla salarial y facturas.
- Feature module `features/admin/` con vistas de estructura académica, usuarios y auditoría.
- Vista de liquidaciones con tabla segmentada (general / NEXO / factura), KPIs de totales facturante vs no-facturante, filtros por cohorte y período.
- Acción de cierre de liquidación con confirmación modal y manejo de errores.
- Historial de liquidaciones con tabla paginada.
- Grilla salarial ABM con tabs de SalarioBase y SalarioPlus, formularios con vigencia temporal.
- Gestión de facturas CRUD con listado filtrable por período, estado y usuario; acciones de abonar y soft delete.
- Estructura académica con CRUD anidado: carreras → cohortes; materias → dictados.
- Usuarios del tenant ABM con campos PII, selección de roles.
- Panel de auditoría con KPIs gráficos (acciones por día, comunicaciones por docente, interacciones).
- Log completo de auditoría con filtros por acción, actor, fecha, materia y paginación.
- Lazy loading de todas las páginas.
- Implementación en español (consistente con frontend existente).

**Non-Goals:**
- No implementar el cálculo de liquidaciones server-side (ya existe en C-18).
- No implementar lógica de aprobación de comunicaciones (ya existe en C-12/C-23).
- No implementar diseño visual final ni branding — mismo approach (Tailwind base + tema neutro).
- No implementar notificaciones en tiempo real vía WebSocket.
- No implementar i18n.
- No implementar tema oscuro.
- No implementar tests E2E — solo unit + integration con Vitest + RTL + MSW.

## Decisions

### ADR-FE-016: Dos feature modules separados `finanzas` y `admin`

**Decisión**: Crear `features/finanzas/` y `features/admin/` como módulos independientes.

**Racional**: Son dominios distintos con diferentes permisos, navegación y modelos de datos. Separarlos mantiene cohesión y evita que un módulo crezca sin límite. FINANZAS opera sobre liquidaciones/salarios/facturas; ADMIN opera sobre estructura/usuarios/auditoría. No comparten lógica de negocio.

**Alternativa considerada**: Un solo módulo `features/gestion/`. Mezclaría dos dominios no relacionados con distintos conjuntos de permisos, dificultando el mantenimiento.

### ADR-FE-017: Rutas planas para FINANZAS, rutas con sub-rutas para ADMIN

**Decisión**: FINANZAS usa rutas planas bajo `/finanzas/` (cada vista es una ruta). ADMIN tiene una ruta `/admin/auditoria` con sub-ruta `/admin/auditoria/log`.

**Racional**:
- FINANZAS tiene 3 vistas independientes (liquidaciones, grilla, facturas) que no comparten layout de tabs. Cada una es autónoma.
- ADMIN tiene una vista de auditoría que se compone de dashboard (panel) y log (tabla detalle). Usar sub-ruta permite navegar entre dashboard y log sin perder el contexto.
- Estructura académica y usuarios son páginas independientes.

```
/finanzas/liquidaciones       → LiquidacionesPage (tabla + KPIs + cerrar)
/finanzas/grilla-salarial     → GrillaSalarialPage (tabs Base/Plus)
/finanzas/facturas            → FacturasPage (CRUD + filtros)

/admin/estructura             → EstructuraPage (tabs Carreras/Cohortes/Materias/Dictados)
/admin/usuarios               → UsuariosPage (ABM + filtros)
/admin/auditoria              → AuditoriaPage (dashboard KPIs)
/admin/auditoria/log          → AuditLogPage (log filtrable paginado)
```

### ADR-FE-018: React Hook Form + Zod para formularios ABM

**Decisión**: Todos los formularios ABM (grilla salarial, facturas, estructura académica, usuarios) usan React Hook Form + Zod para validación.

**Racional**: Es el patrón establecido en C-21. Proporciona validación tipada con esquemas Zod que reflejan las reglas de negocio (montos > 0, formatos de fecha, unicidad de código, formato AAAA-MM para período, etc.).

### ADR-FE-019: TanStack Query para todo el fetching — incluyendo KPIs de auditoría

**Decisión**: Todo el fetching usa TanStack Query con custom hooks. Los KPIs del dashboard de auditoría se cargan como query única `GET /api/audit/dashboard` con `refetchInterval` opcional.

**Racional**: Los KPIs de auditoría son datos agregados server-side que pueden beneficiarse de refetch periódico (ej. cada 60s). TanStack Query maneja caching y re-fetch condicional. El endpoint devuelve las 4 secciones en una sola llamada, simplificando el estado.

### ADR-FE-020: Tabla de liquidaciones con segmentación client-side

**Decisión**: La segmentación general / NEXO / factura se implementa como tabs client-side que filtran la misma lista obtenida del backend.

**Racional**: El endpoint `GET /api/v1/liquidaciones?cohorte_id=X&periodo=YYYY-MM` devuelve todas las liquidaciones con metadatos (`es_nexo`, `excluido_por_factura`). Los tabs filtran client-side sin llamadas adicionales. Los KPIs (`total_facturante`, `total_no_facturante`, etc.) se incluyen en la misma respuesta del backend cuando `kpis=true`.

### ADR-FE-021: Tabla de estructura académica con CRUD en modales

**Decisión**: Las operaciones ABM de carreras, cohortes, materias y dictados se realizan en modales (create/edit) con confirmación para delete.

**Racional**: Mantiene la navegación en la página principal. Cada entidad tiene su propia tabla. Al crear/editar, se abre un modal con formulario RHF+Zod. Al eliminar, se muestra confirmación. Tras cada mutación, se invalida la query correspondiente.

### ADR-FE-022: Servicios organizados por dominio backend

**Decisión**: Cada grupo de endpoints tiene su propio archivo de servicio.

**Racional**:
- `liquidacionesService.ts` — listar, calcular, cerrar, historial, KPIs, exportar
- `grillaSalarialService.ts` — SalarioBase CRUD, SalarioPlus CRUD
- `facturasService.ts` — CRUD, abonar
- `estructuraService.ts` — carreras, cohortes, materias, dictados
- `usuariosService.ts` — CRUD usuarios del tenant
- `auditoriaService.ts` — dashboard KPIs, log con filtros

Cada servicio importa los helpers `get`, `post`, `put`, `patch`, `del` de `@/shared/api/api.ts`.

### ADR-FE-023: Tipos compartidos en cada feature module

**Decisión**: Los tipos DTO se definen en `features/finanzas/types/index.ts` y `features/admin/types/index.ts`.

**Racional**: Un único lugar de definición por módulo evita duplicación. Los tipos reflejan las respuestas del backend.

## Component Tree

```
<App>
  <QueryClientProvider>
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>
  </QueryClientProvider>
</App>

Router (createBrowserRouter) — nuevas rutas FINANZAS y ADMIN:

├── AuthLayout (AppLayout + AuthGuard)
│   ├── /finanzas/liquidaciones           → LiquidacionesPage  ← NUEVA
│   │   └── <LiquidacionesView>
│   │       ├── FiltrosLiquidaciones (cohorte, período, botón calcular)
│   │       ├── KPILiquidaciones (totales facturante/no-facturante)
│   │       ├── TabsSegmentacion (General / NEXO / Factura)
│   │       ├── LiquidacionesTable (segmentada)
│   │       │   ├── FilaLiquidacion (docente, montos, estado)
│   │       │   └── AccionCerrar (modal confirmación)
│   │       ├── LiquidacionesHistorial (tabla expandible)
│   │       └── ExportarButton (CSV)
│   │
│   ├── /finanzas/grilla-salarial         → GrillaSalarialPage  ← NUEVA
│   │   └── <GrillaSalarialView>
│   │       ├── TabsGrilla (SalarioBase | SalarioPlus)
│   │       ├── SalarioBaseTable (CRUD + vigencia)
│   │       │   ├── SalarioBaseFormModal
│   │       │   └── ConfirmDeleteModal
│   │       └── SalarioPlusTable (CRUD + vigencia)
│   │           ├── SalarioPlusFormModal
│   │           └── ConfirmDeleteModal
│   │
│   ├── /finanzas/facturas               → FacturasPage  ← NUEVA
│   │   └── <FacturasView>
│   │       ├── FiltrosFacturas (período, estado, usuario)
│   │       ├── FacturasTable
│   │       │   ├── FilaFactura (docente, período, monto, estado)
│   │       │   ├── AccionAbonar (con confirmación)
│   │       │   └── AccionEliminar (soft delete)
│   │       └── FacturaFormModal (create/edit)
│   │
│   ├── /admin/estructura                 → EstructuraPage  ← NUEVA
│   │   └── <EstructuraView>
│   │       ├── TabsEntidades (Carreras | Cohortes | Materias | Dictados)
│   │       ├── CarrerasTable (CRUD)
│   │       │   ├── CarreraFormModal
│   │       │   └── ConfirmDeleteModal
│   │       ├── CohortesTable (CRUD, filtro por carrera)
│   │       │   ├── CohorteFormModal
│   │       │   └── ConfirmDeleteModal
│   │       ├── MateriasTable (CRUD)
│   │       │   ├── MateriaFormModal
│   │       │   └── ConfirmDeleteModal
│   │       └── DictadosTable (CRUD, filtro por materia/cohorte)
│   │           ├── DictadoFormModal
│   │           └── ConfirmDeleteModal
│   │
│   ├── /admin/usuarios                   → UsuariosPage  ← NUEVA
│   │   └── <UsuariosView>
│   │       ├── FiltrosUsuarios (búsqueda, rol, estado)
│   │       ├── UsuariosTable
│   │       └── UsuarioFormModal (create/edit con campos PII)
│   │
│   └── /admin/auditoria                  → AuditoriaPage  ← NUEVA
│   │   ├── <AuditoriaDashboard>
│   │   │   ├── FiltrosAuditoria (fechas, materia)
│   │   │   ├── KPIAuditoria (totales)
│   │   │   ├── AccionesPorDiaChart (gráfico de barras)
│   │   │   ├── ComunicacionesPorDocenteTable
│   │   │   ├── InteraccionesPorDocenteMateriaTable
│   │   │   └── UltimasAccionesTable (limit 200)
│   │   └── /admin/auditoria/log          → AuditLogPage  ← NUEVA
│   │       └── <AuditLogView>
│   │           ├── FiltrosLog (acción, actor, fechas, materia)
│   │           └── AuditLogTable (paginada)
```

## Data Flow

```
1. Liquidaciones:
   Calcular: POST /api/v1/liquidaciones/calcular?cohorte_id=X&periodo=YYYY-MM
     → useMutation → onSuccess: invalidateQueries(["liquidaciones"])

   Listar: GET /api/v1/liquidaciones?cohorte_id=X&periodo=YYYY-MM&kpis=true
     → useQuery(["liquidaciones", cohorteId, periodo])
     → response: { items: Liquidacion[], kpis: { total_facturante, total_no_facturante, ... } }

   Cerrar: POST /api/v1/liquidaciones/{id}/cerrar
     → useMutation → onSuccess: invalidateQueries(["liquidaciones"])
     → manejo de error 409 (ya cerrada)

   Historial: GET /api/v1/liquidaciones/historial?page=1&per_page=20
     → useQuery(["liquidaciones-historial", page])

2. Grilla Salarial:
   SalarioBase CRUD:
     GET    /api/v1/grilla-salarial/base?rol=X&vigente=true
     POST   /api/v1/grilla-salarial/base
     PUT    /api/v1/grilla-salarial/base/{id}
     DELETE /api/v1/grilla-salarial/base/{id}

   SalarioPlus CRUD:
     GET    /api/v1/grilla-salarial/plus?grupo=X&rol=Y&vigente=true
     POST   /api/v1/grilla-salarial/plus
     PUT    /api/v1/grilla-salarial/plus/{id}
     DELETE /api/v1/grilla-salarial/plus/{id}

3. Facturas:
   GET    /api/v1/facturas?periodo=YYYY-MM&estado=Pendiente&usuario_id=X
   GET    /api/v1/facturas/{id}
   POST   /api/v1/facturas (create)
   POST   /api/v1/facturas/{id}/abonar
   DELETE /api/v1/facturas/{id}

4. Estructura Académica:
   Carreras:  GET/POST /api/v1/admin/carreras, PUT/DELETE /api/v1/admin/carreras/{id}
   Cohortes:  GET/POST /api/v1/admin/cohortes, PUT/DELETE /api/v1/admin/cohortes/{id}
   Materias:  GET/POST /api/v1/admin/materias, PUT/DELETE /api/v1/admin/materias/{id}
   Dictados:  GET/POST /api/v1/admin/dictados, PUT/DELETE /api/v1/admin/dictados/{id}

5. Usuarios:
   GET    /api/v1/admin/usuarios?page=1&per_page=20&search=...
   GET    /api/v1/admin/usuarios/{id}
   POST   /api/v1/admin/usuarios
   PUT    /api/v1/admin/usuarios/{id}
   DELETE /api/v1/admin/usuarios/{id}

6. Auditoría:
   Dashboard: GET /api/audit/dashboard?desde=...&hasta=...&materia_id=...
     → response: { acciones_por_dia[], comunicaciones_por_docente[], interacciones_por_docente_materia[], ultimas_acciones[] }
     → useQuery(["audit-dashboard", filtros])

   Log: GET /api/audit/log?accion=...&actor_id=...&desde=...&hasta=...&materia_id=...&page=1&per_page=50
     → useQuery(["audit-log", filtros, page])
     → paginación server-side con offset/limit
```

## Route Design

```
Rutas existentes (C-21, C-22, C-23) — sin cambios:
  /login, /2fa, /recuperar, /restablecer, /401, *
  /dashboard, /comision/:materiaId/:cohorteId/*, /monitor
  /coordinacion/*

Nuevas rutas protegidas (C-24):
  /finanzas/liquidaciones       → LiquidacionesPage        (require: liquidaciones:ver)
  /finanzas/grilla-salarial     → GrillaSalarialPage       (require: grilla-salarial:ver)
  /finanzas/facturas            → FacturasPage             (require: facturas:gestionar)
  /admin/estructura             → EstructuraPage           (require: estructura:gestionar)
  /admin/usuarios               → UsuariosPage             (require: usuarios:read)
  /admin/auditoria              → AuditoriaPage            (require: auditoria:read)
  /admin/auditoria/log          → AuditLogPage             (require: auditoria:read)
```

## Directory Structure

```
frontend/src/
├── features/
│   ├── auth/             (existente)
│   ├── academico/        (existente)
│   ├── coordinacion/     (existente)
│   │
│   ├── finanzas/                                  ← NUEVO
│   │   ├── components/
│   │   │   ├── LiquidacionesView.tsx
│   │   │   ├── FiltrosLiquidaciones.tsx
│   │   │   ├── KPILiquidaciones.tsx
│   │   │   ├── TabsSegmentacion.tsx
│   │   │   ├── LiquidacionesTable.tsx
│   │   │   ├── AccionCerrar.tsx
│   │   │   ├── LiquidacionesHistorial.tsx
│   │   │   ├── ExportarButton.tsx
│   │   │   ├── GrillaSalarialView.tsx
│   │   │   ├── TabsGrilla.tsx
│   │   │   ├── SalarioBaseTable.tsx
│   │   │   ├── SalarioBaseFormModal.tsx
│   │   │   ├── SalarioPlusTable.tsx
│   │   │   ├── SalarioPlusFormModal.tsx
│   │   │   ├── FacturasView.tsx
│   │   │   ├── FiltrosFacturas.tsx
│   │   │   ├── FacturasTable.tsx
│   │   │   ├── FacturaFormModal.tsx
│   │   │   ├── ConfirmDeleteModal.tsx
│   │   │   └── ConfirmAbonarModal.tsx
│   │   ├── hooks/
│   │   │   ├── useLiquidaciones.ts
│   │   │   ├── useGrillaSalarial.ts
│   │   │   └── useFacturas.ts
│   │   ├── services/
│   │   │   ├── liquidacionesService.ts
│   │   │   ├── grillaSalarialService.ts
│   │   │   └── facturasService.ts
│   │   ├── types/
│   │   │   └── index.ts
│   │   └── pages/
│   │       ├── LiquidacionesPage.tsx
│   │       ├── GrillaSalarialPage.tsx
│   │       └── FacturasPage.tsx
│   │
│   └── admin/                                     ← NUEVO
│       ├── components/
│       │   ├── EstructuraView.tsx
│       │   ├── TabsEntidades.tsx
│       │   ├── CarrerasTable.tsx
│       │   ├── CarreraFormModal.tsx
│       │   ├── CohortesTable.tsx
│       │   ├── CohorteFormModal.tsx
│       │   ├── MateriasTable.tsx
│       │   ├── MateriaFormModal.tsx
│       │   ├── DictadosTable.tsx
│       │   ├── DictadoFormModal.tsx
│       │   ├── UsuariosView.tsx
│       │   ├── FiltrosUsuarios.tsx
│       │   ├── UsuariosTable.tsx
│       │   ├── UsuarioFormModal.tsx
│       │   ├── AuditoriaDashboardView.tsx
│       │   ├── FiltrosAuditoria.tsx
│       │   ├── KPIAuditoria.tsx
│       │   ├── AccionesPorDiaChart.tsx
│       │   ├── ComunicacionesPorDocenteTable.tsx
│       │   ├── InteraccionesPorDocenteMateriaTable.tsx
│       │   ├── UltimasAccionesTable.tsx
│       │   ├── AuditLogView.tsx
│       │   ├── FiltrosLog.tsx
│       │   └── AuditLogTable.tsx
│       ├── hooks/
│       │   ├── useEstructura.ts
│       │   ├── useUsuarios.ts
│       │   └── useAuditoria.ts
│       ├── services/
│       │   ├── estructuraService.ts
│       │   ├── usuariosService.ts
│       │   └── auditoriaService.ts
│       ├── types/
│       │   └── index.ts
│       └── pages/
│           ├── EstructuraPage.tsx
│           ├── UsuariosPage.tsx
│           ├── AuditoriaPage.tsx
│           └── AuditLogPage.tsx
│
├── shared/  (existente, sin cambios estructurales)
│   ├── api/api.ts
│   ├── components/ui/...
│   ├── components/layout/AppLayout.tsx  (MODIFICADO: items de menú para FINANZAS y ADMIN)
│   └── ...
└── router/index.tsx  (MODIFICADO: agregar nuevas rutas)
```

## Risks / Trade-offs

| Riesgo | Mitigación |
|--------|------------|
| **Formularios ABM con muchos campos (usuarios con PII)**: el formulario de usuario tiene campos cifrados (DNI, CUIL, CBU) que requieren tratamiento especial | Los campos PII se manejan como inputs de texto normales; el backend se encarga del cifrado/descifrado. El frontend no necesita lógica de cifrado. |
| **Dashboard de auditoría con muchos datos**: `ultimas_acciones` puede devolver hasta 200 registros | La tabla se renderiza con virtualización simple si es necesario. El endpoint ya limita a 200. Los KPIs son agregaciones server-side. |
| **Múltiples CRUD anidados (estructura académica)**: la navegación entre tabs de entidades puede ser confusa | Cada entidad tiene su propio tab con tabla independiente. Los formularios son modales. Las relaciones (ej. cohorte → carrera) se muestran como selects en el modal. |
| **Permisos granulares**: las rutas de FINANZAS y ADMIN tienen distintos permisos que pueden no estar todos asignados | Cada ruta declara `require_permission`. Los items del menú lateral se filtran según permisos del usuario. Si falta un permiso, la ruta muestra 401. |
| **Tamaño del bundle**: ~7 nuevas páginas lazy-loaded | Cada página es un chunk independiente (Vite code-splitting con React.lazy). Las páginas oscilan entre 30-150 LOC. |

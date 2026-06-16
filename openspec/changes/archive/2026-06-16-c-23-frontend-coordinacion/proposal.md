## Why

Los módulos de backend para equipos docentes, avisos, tareas internas, monitores transversales, encuentros, coloquios y setup de cuatrimestre ya están implementados (C-08, C-13, C-14, C-15, C-16, C-17). Falta la interfaz web que permita a los roles COORDINADOR y ADMIN operar estas funcionalidades de gestión académica y comunicación.

## What Changes

- Nueva feature `coordinacion/` con páginas lazy-loaded para COORDINADOR/ADMIN
- Gestión de equipos docentes (mis-equipos, consulta global, asignación masiva, clonar entre períodos, modificar vigencia, exportar)
- ABM de avisos con alcance (global/materia/cohorte/rol), severidad, vigencia y acknowledgment stats
- Workflow de tareas internas (asignar, delegar, estados, comentarios)
- Monitore transversal: monitor general (F2.7) y monitor de coordinación/admin con rango de fechas (F2.9)
- Vista admin de encuentros (F6.5): tabla transversal de todos los encuentros del tenant
- Gestión de coloquios: panel de métricas (F7.1), crear convocatoria (F7.3), listado de convocatorias (F7.4), administración global (F7.5)
- Setup de cuatrimestre (FL-03): flujo paso a paso de inicio de período
- Nuevas rutas agrupadas bajo `/dashboard/coordinacion/*` (excepto monitores que extienden `/dashboard/monitor`)
- Integración con TanStack Query para fetching y mutations

## Capabilities

### New Capabilities
- `equipos-gestion-ui`: UI de gestión de equipos docentes — vista mis-equipos, consulta global, asignación masiva, clonar, vigencia, exportar
- `avisos-gestion-ui`: ABM completo de avisos del sistema con formulario de alcance/severidad/vigencia y tabla de acknowledgment stats
- `tareas-workflow-ui`: Workflow de tareas internas — lista de tareas, asignar, delegar, cambio de estados, comentarios
- `monitor-coordinacion-ui`: Monitor general (F2.7) y de coordinación/admin (F2.9) con filtros avanzados y rango de fechas
- `encuentros-admin-ui`: Vista transversal de encuentros del tenant con filtros por materia/docente/fecha
- `coloquios-gestion-ui`: Gestión de convocatorias de coloquio — panel de métricas, crear convocatoria, listado, admin global
- `setup-cuatrimestre-ui`: Flujo wizard de inicio de cuatrimestre (FL-03) — crear cohorte, clonar equipo, ajustar asignaciones, cargar programas y fechas, publicar aviso

### Modified Capabilities
- (ninguna — no se modifican specs existentes)

## Impact

- Frontend: nuevo feature module `features/coordinacion/` (~20 pages)
- Router: nuevas rutas protegidas por permiso bajo `/dashboard/coordinacion/*`
- Shared UI: puede requerir mejoras en componentes existentes (tablas complejas, wizard steps, date-range picker)
- Integración con APIs existentes: equipos (C-08), avisos (C-15), tareas (C-16), encuentros (C-13), coloquios (C-14), programas (C-17), monitor (C-11)

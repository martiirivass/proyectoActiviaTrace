## Why

El backend de activia-trace expone todas las APIs de los módulos de FINANZAS (liquidaciones, grilla salarial, facturas) y ADMIN (estructura académica, usuarios, auditoría) gracias a los cambios C-18, C-19, C-06 y C-07. Sin embargo, el frontend actual solo tiene las vistas para PROFESOR/TUTOR/COORDINADOR (C-22, C-23). No existe ninguna interfaz para que los roles FINANZAS y ADMIN operen sus casos de uso. Este cambio implementa todas las vistas de ambos módulos, completando el frontend de gestión del tenant.

## What Changes

1. **Feature `finanzas/`**: módulo completo con vistas de liquidaciones, grilla salarial y facturas.
2. **Feature `admin/`**: módulo completo con estructura académica (carreras, cohortes, materias, dictados), usuarios del tenant y panel de auditoría.
3. **Modificaciones en router**: nuevas rutas protegidas bajo el AppLayout existente para `/finanzas/*` y `/admin/*`.
4. **Modificaciones en AppLayout**: nuevos items de menú dinámicos para los perfiles FINANZAS y ADMIN.

### Finanzas — F10 (Épica 10)

1. **Vista de liquidaciones del período** (`/finanzas/liquidaciones`): tabla con segmentación general / NEXO / factura, KPIs (totales, cantidad, facturante vs no-facturante).
2. **Cerrar liquidación**: botón que hace inmutable una liquidación en estado Abierta.
3. **Historial de liquidaciones**: tabla de ejecuciones de cálculo con fecha, usuario, cohorte, período.
4. **Grilla salarial ABM** (`/finanzas/grilla-salarial`): gestión de SalarioBase y SalarioPlus con vigencia temporal.
5. **Gestión de facturas de docentes** (`/finanzas/facturas`): CRUD de facturas, listado con filtros, abonar, soft delete.
6. **Separación contable factura vs no-factura + KPIs**: indicadores en vista de liquidaciones.

### Admin — Épica 5, F4, F9

1. **Estructura académica** (`/admin/estructura`): gestión de carreras, cohortes, materias y dictados (CRUD completo).
2. **Usuarios del tenant** (`/admin/usuarios`): ABM de usuarios con PII, roles, filtros.
3. **Panel de auditoría y métricas** (`/admin/auditoria`): dashboard con KPIs agregados (acciones por día, comunicaciones por docente, interacciones por docente+materia).
4. **Log completo de auditoría con filtros** (`/admin/auditoria/log`): tabla paginada con filtros por acción, actor, fecha, materia.

## Capabilities

### New Capabilities

- `liquidaciones-vista`: Tabla de liquidaciones del período con segmentación (general/NEXO/factura) + KPIs de totales facturante/no-facturante.
- `liquidaciones-cerrar`: Acción de cierre de liquidación con confirmación y manejo de errores (409).
- `liquidaciones-historial`: Historial de ejecuciones de cálculo con paginación.
- `grilla-salarial`: ABM de SalarioBase y SalarioPlus con vigencia temporal, edición y soft delete.
- `facturas-gestion`: CRUD de facturas, listado con filtros por período/estado/usuario, abonar y soft delete.
- `estructura-academica`: Gestión de carreras, cohortes, materias y dictados (CRUD completo).
- `usuarios-gestion`: ABM de usuarios del tenant con PII, roles, filtros.
- `audit-dashboard`: Panel de métricas de auditoría con acciones por día, comunicaciones por docente, interacciones por docente+materia, últimas acciones.
- `audit-log-full`: Log completo de auditoría con filtros por acción, actor, fecha, materia y paginación.

### Modified Capabilities

- *(Ninguna — primer cambio frontend para estos módulos)*

## Impact

- **Nuevo feature module**: `frontend/src/features/finanzas/` con components, hooks, services, types, pages.
- **Nuevo feature module**: `frontend/src/features/admin/` con components, hooks, services, types, pages.
- **Modificaciones en router**: nuevas rutas protegidas bajo `/finanzas/*` y `/admin/*`.
- **Modificaciones en AppLayout**: nuevos items de menú dinámicos para los perfiles FINANZAS y ADMIN.
- **Sin impacto en backend**: solo consume endpoints existentes de C-18 (liquidaciones), C-19 (auditoría), C-06 (estructura), C-07 (usuarios).
- **Dependencias de frontend**: ninguna nueva — React Hook Form, TanStack Query, Axios ya instalados.

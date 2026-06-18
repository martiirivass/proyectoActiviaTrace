## Why

activia-trace necesita un módulo completo de **liquidaciones y honorarios** (Épica E) para que los equipos de FINANZAS de cada tenant puedan calcular, auditar y cerrar los pagos docentes por cohorte y período. Hoy no existe: los salarios base, los pluses por grupo de materias, el cálculo automático (Base + Σ Plus × N comisiones), el cierre inmutable, la grilla de configuración salarial y la gestión de facturas (facturantes vs no-facturantes) son procesos manuales o inexistentes. Este change cierra la brecha operativa crítica para facturación y contabilidad.

## What Changes

- **Nuevos modelos (E17–E20)**: `SalarioBase`, `SalarioPlus`, `Liquidacion`, `Factura` con soft-delete, auditoría y multi-tenancy row-level
- **Grilla salarial configurable por tenant**: ABM de salarios base (por rol, vigencia temporal) y pluses (por grupo + rol, vigencia temporal)
- **Cálculo automático de liquidaciones**: Por (cohorte × período), aplica RN-31 a RN-40: Base(rol) + Σ Plus(grupo,rol) × N_comisiones, exclusión facturantes, NEXO separado, cierre inmutable
- **Gestión de facturas**: CRUD con estados Pendiente/Abonada, referencia de archivo, trazabilidad completa
- **Endpoints REST**: Listar/calcular/detalle/cerrar/exportar liquidaciones; ABM grilla salarial; CRUD facturas
- **Permisos FINANZAS granulares**: 11 nuevos permisos `modulo:accion` (liquidaciones:ver, calcular, cerrar, configurar-salarios, exportar, historial; facturas:gestionar; grilla-salarial:*)
- **Códigos de auditoría**: 12 eventos nuevos para trazabilidad completa
- **KPIs diferenciados**: Totales facturantes vs no-facturantes por cohorte/período

**BREAKING**: Nueva tabla `SalarioPlus` introduce clave `grupo` configurable por tenant (PA-22). Migración de datos seed requerida.

## Capabilities

### New Capabilities
- `grilla-salarial-base`: Configuración de salarios base por rol y vigencia temporal (RN-31, RN-32)
- `grilla-salarial-plus`: Configuración de pluses por grupo+materia, rol y vigencia (RN-33, PA-22, PA-23)
- `liquidaciones-calculo`: Cálculo automático de liquidaciones por cohorte/período (RN-34 a RN-40)
- `liquidaciones-gestion`: Listado, detalle, cierre irreversible, exportación, historial (RN-22, RN-37)
- `facturas-gestion`: CRUD facturas con estados Pendiente/Abonada y archivo adjunto (RN-39, RN-40)
- `kpis-liquidaciones`: Indicadores diferenciados facturantes vs no-facturantes (RN-38)

### Modified Capabilities
- `usuarios-y-asignaciones`: Requiere que `Asignacion` exponga `comision_id` y `materia.grupo_plus` para alimentar el cálculo (C-07 ya implementado, solo lectura)

## Impact

- **Base de datos**: 4 nuevas tablas + índices únicos compuestos + migraciones Alembic
- **API**: 18 nuevos endpoints bajo `/api/v1/liquidaciones`, `/api/v1/grilla-salarial`, `/api/v1/facturas`
- **Auth/RBAC**: 11 permisos nuevos solo para rol FINANZAS; fail-closed en todos los endpoints
- **Auditoría**: 12 códigos de evento nuevos
- **Dependencias**: Requiere C-07 (User, Asignacion, Materia, Cohorte, Role) ✅; bloquea C-19 (reportes) y C-20 (dashboards FINANZAS)
- **Frontend**: Nueva feature `liquidaciones` + páginas grilla salarial, cálculo, facturas, exportación
- **Performance**: Cálculo por cohorte/período puede ser pesado → job async recomendado para tenants grandes
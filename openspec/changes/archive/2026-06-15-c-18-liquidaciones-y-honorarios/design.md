# Design: C-18 Liquidaciones y Honorarios

## Technical Approach

Módulo completo de liquidaciones siguiendo Clean Architecture existente: 4 modelos ORM nuevos (SalarioBase, SalarioPlus, Liquidacion, Factura) con sus correspondientes repositorios tenant-scoped, servicios de negocio, schemas Pydantic v2 con `extra='forbid'` y routers REST. El cálculo de liquidación es la pieza central: una función pura que recibe `(cohorte_id, periodo)` y genera registros `Liquidacion` por docente aplicando RN-31 a RN-40.

## Architecture Decisions

### Decision: Cálculo síncrono in-app (sin worker)

| Opción | Tradeoff | Decisión |
|--------|----------|----------|
| Worker async (cola) | + Escalable para N grandes, - Complejidad de infra, - Latencia de feedback | ❌ Rechazado |
| **Cálculo síncrono en Service** | + Feedback inmediato, + Simple, + Testeable, - Puede ser lento con muchos docentes | ✅ **Elegido** |

**Rationale**: El MVP no justifica la complejidad de un worker. Si un tenant tiene +100 docentes en una cohorte, se optimiza después. La función de cálculo es pura y fácil de extraer a worker más tarde.

### Decision: `grupo_plus` como columna en Materia (no tabla separada)

| Opción | Tradeoff | Decisión |
|--------|----------|----------|
| Tabla `MateriaGrupoPlus` separada | + Flexible (N grupos por materia), - Overingeniería para MVP | ❌ Rechazado |
| **Columna `grupo_plus` nullable en Materia** | + Simple, + Consulta directa, + Tenant-scoped por herencia | ✅ **Elegido** |

**Rationale**: PA-22 (mapeo materia→clave Plus) está abierta. Una columna nullable permite arrancar; si después se necesita N grupos por materia, se migra a tabla separada sin breaking change en la API.

### Decision: Acumulación `N × Plus` sin tope (PA-23 asumido)

| Opción | Tradeoff | Decisión |
|--------|----------|----------|
| Plus único sin importar comisiones | - No refleja carga real, + Simple | ❌ Rechazado |
| **N × Plus(grupo, rol) por comisión** | + Refleja carga docente real, + Consistente con RN-34, - Sin tope | ✅ **Elegido (default)** |
| Tope configurable | + Control de gasto, + El área FINANZAS lo pidió (PA-23) | 🔄 Pending |

**Rationale**: RN-34 dice "N comisiones de la misma categoría, acumula N veces el plus correspondiente". Implementamos eso sin tope como default. Pendiente de producto para definir si hay tope (PA-23).

### Decision: Factura storage como referencia_archivo (sin blob en DB)

| Opción | Tradeoff | Decisión |
|--------|----------|----------|
| Blob en PostgreSQL | + Transaccional, - DB pesada, + Sin storage externo | ❌ Rechazado |
| **referencia_archivo + storage externo** | + DB liviana, + Escalable, - Requiere servicio de storage | ✅ **Elegido** |

**Rationale**: Consistente con el resto del sistema (`referencia_archivo` en otros modelos). El storage externo (S3/local disk) se define en deploy, no en el modelo.

## Data Flow

### Cálculo de Liquidación (flujo principal)

```
POST /api/v1/liquidaciones/calcular?cohorte_id=X&periodo=2026-06
       │
       ▼
┌────────────────────────────────┐
│   LiquidacionService.calcular  │
└────────┬───────────────────────┘
         │
    [1] Obtener asignaciones activas en cohorte para el período
         │
    [2] Agrupar por (usuario_id, rol)
         │
    [3] Para cada (usuario, rol):
         ├── Buscar SalarioBase vigente para el rol y período → monto_base
         ├── Para cada materia del usuario en la cohorte:
         │     ├── Leer materia.grupo_plus
         │     ├── Buscar SalarioPlus(grupo, rol) vigente
         │     └── Σ plus por grupo × N comisiones de ese grupo
         ├── monto_plus = suma total
         ├── total = monto_base + monto_plus
         ├── Si usuario.es_facturante → excluido_por_factura = true
         └── Si rol == NEXO → es_nexo = true
         │
    [4] Crear Liquidacion (estado = Abierta)
         │
    [5] Audit: LIQUIDACION_CALCULAR
         │
         ▼
    Devolver listado de Liquidacion creadas
```

### Grilla Salarial (CRUD)

```
GrillaSalarialService
  ├── listar_base(filters)    → SalarioBaseResponse[]
  ├── crear_base(data)        → SalarioBaseResponse
  ├── editar_base(id, data)   → SalarioBaseResponse
  ├── eliminar_base(id)       → soft delete
  ├── listar_plus(filters)    → SalarioPlusResponse[]
  ├── crear_plus(data)        → SalarioPlusResponse
  ├── editar_plus(id, data)   → SalarioPlusResponse
  └── eliminar_plus(id)       → soft delete
```

### Facturas (CRUD)

```
FacturaService
  ├── listar(filters)         → FacturaResponse[]
  ├── crear(data)             → FacturaResponse
  ├── obtener(id)             → FacturaResponse
  ├── abonar(id)              → FacturaResponse (cambia estado a Abonada)
  ├── eliminar(id)            → soft delete
  └── listar_por_periodo()    → KPIs facturantes vs no-facturantes
```

## Modelos (SQLAlchemy)

### SalarioBase (E17)
| Campo | Tipo | Notas |
|-------|------|-------|
| id | UUID PK | default uuid4 |
| tenant_id | UUID, FK→Tenant | NOT NULL, index |
| rol | Enum(RolLiquidacion) | PROFESOR, TUTOR, NEXO, COORDINADOR |
| monto | Decimal(10,2) | |
| desde | Date | inicio vigencia |
| hasta | Date, nullable | NULL = vigente sin límite |
| is_deleted, deleted_at | SoftDeleteMixin | |

Unique: `(tenant_id, rol, desde)` — solo un registro vigente por rol a la vez.

### SalarioPlus (E18)
| Campo | Tipo | Notas |
|-------|------|-------|
| id | UUID PK | |
| tenant_id | UUID, FK→Tenant | |
| grupo | String(50) | clave de grupo (PROG, BD, MAT, etc.) |
| rol | Enum(RolLiquidacion) | |
| descripcion | String(255) | |
| monto | Decimal(10,2) | |
| desde | Date | |
| hasta | Date, nullable | |
| is_deleted, deleted_at | SoftDeleteMixin | |

Unique: `(tenant_id, grupo, rol, desde)`.

### Liquidacion (E19)
| Campo | Tipo | Notas |
|-------|------|-------|
| id | UUID PK | |
| tenant_id | UUID, FK→Tenant | |
| cohorte_id | UUID, FK→Cohorte | |
| periodo | String(7) | AAAA-MM |
| usuario_id | UUID, FK→User | |
| rol | Enum(RolLiquidacion) | |
| comisiones | JSONB | `[{"materia_id": UUID, "grupo_plus": str, "monto_plus": decimal}]` |
| monto_base | Decimal(10,2) | |
| monto_plus | Decimal(10,2) | |
| total | Decimal(10,2) | monto_base + monto_plus |
| es_nexo | Boolean, default false | |
| excluido_por_factura | Boolean, default false | |
| estado | Enum(EstadoLiquidacion) | Abierta, Cerrada |
| is_deleted, deleted_at | SoftDeleteMixin | |

Unique: `(tenant_id, cohorte_id, periodo, usuario_id)` — una liquidación por docente/cohorte/mes.

### Factura (E20)
| Campo | Tipo | Notas |
|-------|------|-------|
| id | UUID PK | |
| tenant_id | UUID, FK→Tenant | |
| usuario_id | UUID, FK→User | |
| periodo | String(7) | AAAA-MM |
| detalle | Text | |
| referencia_archivo | String(512) | opaco, no path |
| tamano_kb | Decimal(10,2) | |
| estado | Enum(EstadoFactura) | Pendiente, Abonada |
| cargada_at | DateTime | server_default=func.now() |
| abonada_at | DateTime, nullable | |
| is_deleted, deleted_at | SoftDeleteMixin | |

### Enums nuevos
```python
class RolLiquidacion(str, enum.Enum):
    PROFESOR = "PROFESOR"
    TUTOR = "TUTOR"
    NEXO = "NEXO"
    COORDINADOR = "COORDINADOR"

class EstadoLiquidacion(str, enum.Enum):
    Abierta = "Abierta"
    Cerrada = "Cerrada"

class EstadoFactura(str, enum.Enum):
    Pendiente = "Pendiente"
    Abonada = "Abonada"
```

### Modificación existente: Materia
Agregar columna nullable:
- `grupo_plus: String(50), nullable` — clave de grupo para cálculo de Plus

## Permisos nuevos (en `core/permissions.py`)

```
GRILLA_SALARIAL_VER = "grilla-salarial:ver"
GRILLA_SALARIAL_CREAR = "grilla-salarial:crear"
GRILLA_SALARIAL_EDITAR = "grilla-salarial:editar"
GRILLA_SALARIAL_ELIMINAR = "grilla-salarial:eliminar"
LIQUIDACIONES_VER = "liquidaciones:ver"
LIQUIDACIONES_CALCULAR = "liquidaciones:calcular"
LIQUIDACIONES_CERRAR = "liquidaciones:cerrar"
LIQUIDACIONES_EXPORTAR = "liquidaciones:exportar"
LIQUIDACIONES_HISTORIAL = "liquidaciones:historial"
FACTURAS_GESTIONAR = "facturas:gestionar"
```

## Códigos de auditoría nuevos

| Código | Descripción |
|--------|-------------|
| `LIQUIDACION_CALCULAR` | Cálculo de liquidación para cohorte/período |
| `LIQUIDACION_CERRAR` | Cierre de liquidación (inmutable) |
| `LIQUIDACION_REABRIR` | Reapertura (solo ADMIN) |
| `SALARIO_BASE_CREAR` | Alta de salario base en grilla |
| `SALARIO_BASE_MODIFICAR` | Edición de salario base |
| `SALARIO_BASE_ELIMINAR` | Soft delete de salario base |
| `SALARIO_PLUS_CREAR` | Alta de plus en grilla |
| `SALARIO_PLUS_MODIFICAR` | Edición de plus |
| `SALARIO_PLUS_ELIMINAR` | Soft delete de plus |
| `FACTURA_CARGAR` | Carga de factura por docente |
| `FACTURA_ABONAR` | Confirmación de pago por FINANZAS |
| `FACTURA_ELIMINAR` | Soft delete de factura |

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `backend/app/models/salario_base.py` | Create | Modelo SalarioBase (E17) |
| `backend/app/models/salario_plus.py` | Create | Modelo SalarioPlus (E18) |
| `backend/app/models/liquidacion.py` | Create | Modelo Liquidacion (E19) + enums |
| `backend/app/models/factura.py` | Create | Modelo Factura (E20) |
| `backend/app/models/materia.py` | Modify | + columna `grupo_plus` nullable |
| `backend/app/models/__init__.py` | Modify | Importar nuevos modelos y enums |
| `backend/app/repositories/grilla_salarial_repository.py` | Create | repo tenant-scoped para SalarioBase y SalarioPlus |
| `backend/app/repositories/liquidacion_repository.py` | Create | repo tenant-scoped para Liquidacion |
| `backend/app/repositories/factura_repository.py` | Create | repo tenant-scoped para Factura |
| `backend/app/services/liquidacion_service.py` | Create | Cálculo + gestión de liquidaciones |
| `backend/app/services/grilla_salarial_service.py` | Create | ABM grilla salarial |
| `backend/app/services/factura_service.py` | Create | CRUD facturas |
| `backend/app/schemas/liquidaciones.py` | Create | Schemas Pydantic v2 con extra='forbid' |
| `backend/app/api/v1/routers/liquidaciones.py` | Create | Router REST liquidaciones |
| `backend/app/api/v1/routers/grilla_salarial.py` | Create | Router REST grilla salarial |
| `backend/app/api/v1/routers/facturas.py` | Create | Router REST facturas |
| `backend/app/api/v1/routers/__init__.py` | Modify | Include nuevos routers |
| `backend/app/core/permissions.py` | Modify | +10 constantes de permisos |
| `backend/core/audit_codes.py` | Modify | +12 códigos de auditoría |
| `backend/alembic/versions/xxxx_liquidaciones_y_honorarios.py` | Create | Migración schema |
| `backend/tests/test_liquidaciones/test_grilla_salarial.py` | Create | Tests grilla |
| `backend/tests/test_liquidaciones/test_calculo.py` | Create | Tests cálculo |
| `backend/tests/test_liquidaciones/test_facturas.py` | Create | Tests facturas |
| `backend/tests/test_liquidaciones/conftest.py` | Create | Fixtures específicos |

## Endpoints REST

### Grilla Salarial `/api/v1/grilla-salarial`
| Método | Path | Permiso | Descripción |
|--------|------|---------|-------------|
| GET | `/base` | grilla-salarial:ver | Listar salarios base (filtros: rol, vigente) |
| POST | `/base` | grilla-salarial:crear | Crear salario base |
| PUT | `/base/{id}` | grilla-salarial:editar | Editar salario base |
| DELETE | `/base/{id}` | grilla-salarial:eliminar | Soft delete |
| GET | `/plus` | grilla-salarial:ver | Listar pluses |
| POST | `/plus` | grilla-salarial:crear | Crear plus |
| PUT | `/plus/{id}` | grilla-salarial:editar | Editar plus |
| DELETE | `/plus/{id}` | grilla-salarial:eliminar | Soft delete |

### Liquidaciones `/api/v1/liquidaciones`
| Método | Path | Permiso | Descripción |
|--------|------|---------|-------------|
| GET | `/` | liquidaciones:ver | Listar (filtros: cohorte_id, periodo, usuario_id) |
| POST | `/calcular` | liquidaciones:calcular | Ejecutar cálculo por cohorte+periodo |
| GET | `/{id}` | liquidaciones:ver | Detalle de liquidación |
| POST | `/{id}/cerrar` | liquidaciones:cerrar | Cierre irreversible |
| GET | `/exportar` | liquidaciones:exportar | Exportar listado |
| GET | `/historial` | liquidaciones:historial | Historial de cálculos |

### Facturas `/api/v1/facturas`
| Método | Path | Permiso | Descripción |
|--------|------|---------|-------------|
| GET | `/` | facturas:gestionar | Listar (filtros: periodo, usuario_id, estado) |
| POST | `/` | facturas:gestionar | Crear factura |
| GET | `/{id}` | facturas:gestionar | Detalle |
| POST | `/{id}/abonar` | facturas:gestionar | Marcar como abonada |
| DELETE | `/{id}` | facturas:gestionar | Soft delete |

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | Cálculo puro: Base + Σ(Plus × N) | Función aislada, múltiples casos (1 comisión, N comisiones, mismo grupo, grupos distintos, facturante, NEXO) |
| Unit | Transición de estados (abierta → cerrada) | Sin mock DB, función pura de validación |
| Integration | Repositorios tenant-scoped (CRUD, unique constraints) | DB real, fixture por test |
| Integration | Servicio: cálculo end-to-end (asignaciones → liquidaciones) | DB real, datos seed de Materia/Asignacion/SalarioBase/SalarioPlus |
| Integration | Servicio: cierre + re-intento da error | DB real, verifica 409 Conflict |
| Integration | Permisos: cada endpoint con y sin permiso | Test client autenticado |
| E2E | Flujo completo: crear grilla → calcular → listar → cerrar → ver historial | API tests |

## Open Questions / Bloqueantes

- [ ] **PA-22**: ¿Cuáles son las claves de Plus existentes y cómo se mapean a materias? Se asume columna `grupo_plus` en Materia como solución inicial — requiere confirmación del área FINANZAS.
- [ ] **PA-23**: ¿Tope de acumulación de Plus por N comisiones? Se implementa sin tope (interpretación literal de RN-34) — requiere confirmación.
- [ ] **PA-24**: ¿Las facturas se asocian a comisiones específicas o son globales por docente/período? Se implementan como globales con campo `detalle` libre.
- [ ] **ADR-007**: Fórmula de Plus (definición cerrada en este design: Base + Σ(Plus × N_comisiones) ) — requiere revisión de FINANZAS antes de apply.

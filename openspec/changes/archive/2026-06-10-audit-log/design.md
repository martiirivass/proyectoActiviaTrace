## Context

La plataforma requiere auditoría obligatoria (RN del modelo #6) para toda acción significativa. Actualmente no existe ningún mecanismo de trazabilidad. Este cambio introduce el modelo `AuditLog` append-only que será el sustrato para auditoría futura, incluyendo soporte para impersonación.

El diseño sigue los patrones establecidos en C-01..C-04 (Clean Architecture: Models → Repositories → Services → Routers). El modelo es inmutable por definición — el repositorio solo expone `create` y `find` (no update, no delete).

## Goals / Non-Goals

**Goals:**
- Modelo `AuditLog` con todos los campos de E-AUD: `id`, `tenant_id`, `fecha_hora`, `actor_id`, `impersonado_id`, `materia_id`, `accion`, `detalle`, `filas_afectadas`, `ip`, `user_agent`
- Repositorio con `create()` y `find(filters)` solamente — sin update ni delete
- Servicio `AuditService.log()` que centraliza la creación de registros
- Catálogo de códigos de acción como constantes tipadas
- Endpoint GET `/api/v1/audit/log` con filtros por tenant, acción, actor, fechas
- Middleware opcional que loguea automáticamente requests a endpoints marcados
- Migration 004 con tabla `audit_log`
- Impersonación: campo `impersonado_id` nullable + validación

**Non-Goals:**
- No se implementa la funcionalidad de impersonación en sí misma (eso va en otro change)
- No hay UI de auditoría (futuro)
- No hay exportación del log (futuro)
- No hay rotación/purga del log (futuro)
- No se auditan automáticamente todos los endpoints — solo los que el desarrollador marque explícitamente

## Decisions

### 1. Códigos de acción como string enum (no tabla separada)
| Opción | Veredicto |
|--------|-----------|
| Enum de strings en código | ✅ Elegido |
| Tabla `action_codes` en DB | ❌ Overkill — catálogo pequeño y estable |

**Rationale**: Los códigos de acción son un catálogo pequeño (~20-30 valores) que raramente cambia. Mantenerlos como constantes en código es más simple, tipado, y evita joins innecesarios. Si en el futuro se necesita administración dinámica, se migra.

### 2. Middleware opt-in vs automático
| Opción | Veredicto |
|--------|-----------|
| Decorador/ dependency opt-in | ✅ Elegido |
| Middleware global automático | ❌ Ruido excesivo |

**Rationale**: Loggear automáticamente TODOS los requests genera ruido (GETs de lectura, health-checks, etc.). Preferimos que cada endpoint declare explícitamente `AuditDependency(action_code=..., ...)` o use un decorador. Además respeta el principio de que las acciones se auditan a nivel de *intención de negocio*, no a nivel HTTP.

### 3. Append-only en repositorio
El repositorio solo implementa `create()` y `find()` — ni `update()` ni `delete()`. La BD no tiene cascade de delete hacia `audit_log`. Esto garantiza inmutabilidad.

### 4. `impersonado_id` como FK nullable a `users`
Cuando no hay impersonación activa, es NULL. Cuando hay impersonación, `actor_id` es el usuario REAL (quien impersona) e `impersonado_id` es el usuario impersonado. Esto cumple con la regla de negocio: "toda acción bajo impersonación se atribuye al actor real".

## Risks / Trade-offs

- **[Volumen]** El log de auditoría crece sin límite → mitigado con: (a) índice por `(tenant_id, fecha_hora)` para consultas eficientes, (b) purga/archivo queda como non-goal para futuro
- **[Performance]** El log es insert-only, pero en alta concurrencia puede competir con writes de negocio → mitigado: inserts sin FK checks costosos, tabla sin triggers, se puede mover a tabla separada en futuro
- **[Abuso]** Middleware opt-in puede hacer que desarrolladores olviden auditar → mitigado: code review checklist exige verificar que acciones significativas tengan su `AuditDependency` o llamada a `AuditService.log()`

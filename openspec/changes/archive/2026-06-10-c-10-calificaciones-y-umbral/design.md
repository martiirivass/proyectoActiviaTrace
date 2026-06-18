## Context

Este change se asienta sobre `C-09 padron-ingesta-moodle` que ya provee `VersionPadron` y `EntradaPadron` como base de alumnos por materia×cohorte. Ahora necesitamos el modelo de calificaciones y umbrales para completar el paso 3-5 del flujo FL-02.

**Estado actual del códigobase:**
- `Calificacion` y `UmbralMateria` no existen aún como modelos
- El código de auditoría `CALIFICACIONES_IMPORTAR` ya está definido en `app/core/audit_codes.py`
- El permiso `calificaciones:importar` ya fue seedeado en C-04 RBAC con scope `global` para PROFESOR, COORDINADOR, ADMIN
- Patrón de repositorio: `TenantScopedRepository` con filtro de tenant automático
- Patrón de servicio: inyección de `AsyncSession` + `tenant_id`, delega a `AuditService` para logging
- Convención: snake_case, Pydantic `extra='forbid'`, soft delete con `SoftDeleteMixin`, ≤500 LOC/archivo

## Goals / Non-Goals

**Goals:**
- Modelar `Calificacion` con nota numérica opcional, nota textual opcional, `aprobado` derivado en escritura, origen (Importado/Manual)
- Modelar `UmbralMateria` con umbral porcentual por asignación + valores textuales aprobatorios
- Implementar parseo de archivo de calificaciones LMS: detectar columnas numéricas (RN-01: sufijo `(Real)`) y textuales
- Vista previa con actividades detectadas → usuario selecciona cuáles incluir
- Importar reporte de finalización (F1.2) para detectar TPs entregados sin nota
- CRUD de umbral por materia (F2.1), con defecto 60% si no existe configuración
- Auditoría `CALIFICACIONES_IMPORTAR` en toda importación
- Tests de derivación, import, umbral por asignación, aislamiento tenant

**Non-Goals:**
- Cómputo de alumnos atrasados (C-11)
- Ranking de actividades aprobadas (C-11)
- Reportes rápidos, notas finales agrupadas (C-11)
- Exportación de TPs sin corregir (C-11)
- Frontend de importación/umbral (C-22)
- Integración con Moodle WS para calificaciones (futuro)

## Decisions

### D1 — `aprobado` como columna derivada persistida
**Decisión**: `aprobado` se computa en el momento de escritura (creación/actualización de `Calificacion`) y se almacena como booleano en la tabla.
**Rationale**: 
- La mayoría de lecturas de `Calificacion` necesitan saber si está aprobado
- Recalcular en cada lectura (comparando contra umbral o conjunto textual) agrega complejidad y carga innecesaria
- Si el umbral cambia después de importar, se puede re-derivar en lote (tarea del service)
- Patrón consistente con campos derivados en el sistema

### D2 — `UmbralMateria` scoped por asignación (no por materia global)
**Decisión**: La clave de `UmbralMateria` incluye `asignacion_id` además de `materia_id`. Cada docente tiene su propio umbral.
**Rationale**: RN-03 establece que el umbral es por docente (no afecta a otros). Diferentes profesores de la misma materia pueden tener criterios distintos. Si no existe registro para la asignación, se usa el default 60%.

### D3 — Vista previa en dos fases (detectar → seleccionar)
**Decisión**: El endpoint de preview (`POST /preview`) parsea el archivo y devuelve las actividades detectadas (nombres de columna con tipo inferido). El cliente envía de vuelta solo los nombres seleccionados en `POST /confirm`.
**Rationale**: 
- Similar al flujo de padrón (C-09), mantiene consistencia
- Permite al usuario revisar y seleccionar antes de persistir
- El archivo no se almacena en el servidor — solo se procesa en memoria

### D4 — `CalificacionRepository` separado (no extendiendo PadronRepository)
**Decisión**: Repositorio propio `CalificacionRepository` que extiende `TenantScopedRepository`.
**Rationale**: 
- `Calificacion` y `UmbralMateria` son entidades independientes del padrón
- Un repositorio por entidad es el patrón establecido (PadronRepository, CarreraRepository, etc.)
- Mantiene cohesión y ≤500 LOC/archivo

### D5 — Reuso del código de auditoría existente
**Decisión**: Usar `CALIFICACIONES_IMPORTAR` de `audit_codes.py` y `AuditService.log()` idéntico al patrón de `PadronService`.
**Rationale**: Consistencia con el resto del sistema. Sin cambios en `audit_codes.py` (el código ya existe).

### D6 — Parseo de columnas con detección por sufijo `(Real)`
**Decisión**: Las columnas del archivo LMS cuyo encabezado termina en `(Real)` se clasifican como numéricas. El resto de columnas con datos no-vacíos se clasifican como textuales. Columnas conocidas (nombre, apellido, email) se ignoran como metadatos.
**Rationale**: RN-01 especifica exactamente esa regla. RN-02 define los valores textuales aprobatorios. Es la semántica del LMS.

## Risks / Trade-offs

**[R1] Umbral se calcula al importar, no en tiempo real**
→ Si un docente cambia el umbral después de importar, las calificaciones existentes mantienen su `aprobado` original. 
→ **Mitigación**: El servicio expone un método `recalcular_aprobados(asignacion_id)` que actualiza en lote todas las calificaciones de esa asignación contra el umbral actual.

**[R2] Archivos LMS pueden tener formatos variables**
→ No hay un estándar único de exportación. Columnas pueden tener nombres distintos según la configuración del aula virtual.
→ **Mitigación**: La detección por sufijo `(Real)` es robusta ante cambios de idioma porque es el comportamiento del LMS. Para otros casos, el usuario puede seleccionar manualmente qué columnas incluir.

**[R3] Volumen de datos**
→ Una materia con 100 alumnos y 20 actividades genera ~2000 registros de `Calificacion`. Escala lineal.
→ **Mitigación**: Bulk insert con `session.add_all()` + flush, mismo patrón que `PadronRepository.bulk_create_entries()`.

## Migration Plan

1. Crear modelos `Calificacion` y `UmbralMateria`
2. Generar migración Alembic con ambas tablas + índices
3. Crear repositorio `CalificacionRepository`
4. Crear schemas Pydantic
5. Crear `CalificacionService`
6. Crear routers en `/api/v1/calificaciones/`
7. Registrar router en `main.py` y modelos en `__init__.py`
8. Escribir tests

**Rollback**: `alembic downgrade -1` elimina ambas tablas sin pérdida de otros datos.

## Open Questions

- *(ninguna — el dominio está cerrado en PA-01 a PA-25 y C-10 no está bloqueado)*

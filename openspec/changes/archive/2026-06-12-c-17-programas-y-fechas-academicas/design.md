## Context

El sistema ya cuenta con los modelos fundacionales de estructura académica (C-06): `Carrera`, `Cohorte`, `Materia`. Este change agrega dos entidades de calendarización y documentación académica que operan sobre esas bases:

- **ProgramaMateria** (E16): documento oficial del programa de una materia, asociado a una combinación materia × carrera × cohorte. Usa `referencia_archivo` como puntero opaco al servicio de almacenamiento (el archivo físico no se gestiona en este change — solo la referencia).
- **FechaAcademica** (E15): calendarización de instancias evaluativas (parciales, TPs, coloquios, recuperatorios) por materia × cohorte × tipo × número dentro de un período.

Ambas entidades siguen los mismos patrones establecidos en C-01..C-06: `TenantScopedRepository` para aislamiento multi-tenant, `SoftDeleteMixin` y `TimestampMixin`. Reutilizan el permiso `estructura:gestionar` sin crear nuevas capacidades RBAC.

## Goals / Non-Goals

**Goals:**
- Modelo `ProgramaMateria` con todos los campos de E16, unique constraint `(materia_id, carrera_id, cohorte_id)`
- Modelo `FechaAcademica` con todos los campos de E15, unique constraint `(materia_id, cohorte_id, tipo, numero)` por periodo
- CRUD completo para ambas entidades bajo `/api/v1/programas` y `/api/v1/fechas-academicas`
- Endpoint `GET /api/v1/fechas-academicas/exportar-lms` que genere un fragmento HTML/texto con las fechas del filtro solicitado
- Filtros en listados: por materia, carrera, cohorte (programas); por materia, cohorte, tipo, periodo (fechas)
- Reutilización del permiso `estructura:gestionar` — COORDINADOR y ADMIN
- Soft delete en ambas entidades
- Migración Alembic con tablas, FKs, índices y constraints

**Non-Goals:**
- No se implementa la subida/descarga real de archivos — `referencia_archivo` es un puntero opaco que otro módulo (futuro storage service) resolverá
- No se implementa el calendario visual frontend — la API expone datos para que el frontend lo renderice
- No se integra con Moodle Web Services — la exportación LMS es contenido generado para copia manual
- No se modifican modelos existentes de C-06

## Decisions

### 1. ProgramaMateria con unique constraint triple

| Opción | Veredicto |
|--------|-----------|
| Unique `(materia_id, carrera_id, cohorte_id)` | ✅ Elegido |
| Permitir múltiples programas por combo con vigencia | ❌ Scope no lo requiere — un programa vigente por combo |

**Rationale**: La KB define un único programa oficial por materia × carrera × cohorte. Si en el futuro se necesita versionado (programas reemplazados), se puede migrar a tabla versionada estilo `VersionPadron`. Por ahora, unique constraint evita duplicados accidentales.

### 2. FechaAcademica con unique compuesto incluyendo periodo

| Opción | Veredicto |
|--------|-----------|
| Unique `(materia_id, cohorte_id, tipo, numero, periodo)` | ✅ Elegido |
| Unique sin periodo | ❌ El mismo número de parcial se repite en cada cuatrimestre |

**Rationale**: El campo `periodo` (ej: "2026-1", "2026-2") desambigua la instancia. Un "1er Parcial" existe en cada cuatrimestre; sin periodo en el unique, no se podría tener el mismo tipo+número en distintos periodos para la misma materia y cohorte.

### 3. Exportación LMS como endpoint separado (no embebido en list)

| Opción | Veredicto |
|--------|-----------|
| Endpoint `GET /api/v1/fechas-academicas/exportar-lms` con query params | ✅ Elegido |
| Parámetro `?exportar_lms=true` en el GET list | ❌ Mezcla responsabilidades — el listado devuelve JSON, la exportación devuelve texto/HTML |

**Rationale**: El contrato REST es más limpio con un endpoint dedicado. El formato de salida es `text/plain` o `text/html` según el `Accept` header. El frontend puede mostrar una vista previa y luego copiar el contenido.

### 4. Soft delete + audit en ambas entidades

Ambas heredan `SoftDeleteMixin`. Las operaciones de escritura (create, update, soft delete) registran auditoría. Los códigos de acción sugeridos: `PROGRAMA_CARGAR`, `PROGRAMA_MODIFICAR`, `FECHA_ACADEMICA_CARGAR`, `FECHA_ACADEMICA_MODIFICAR`. Se añaden al catálogo existente.

### 5. Repositorio separado por entidad

Cada entidad tiene su propio repositorio (`ProgramaMateriaRepository`, `FechaAcademicaRepository`) con queries de filtrado específicas. Sigue el patrón de C-06.

## Risks / Trade-offs

- **[Referencia de archivo opaca]** `referencia_archivo` es un string sin validación de formato — no sabemos si apunta a un archivo real. **Mitigación**: este change solo modela la referencia; un change futuro de storage service agregará validación y gestión del archivo físico.
- **[Periodo como texto libre]** `periodo` es un string sin formato fijo — podría ingresarse "2026-1" o "2026/1" o "1er cuatrimestre 2026". **Mitigación**: en service, validar contra regex `^\d{4}-[12]$` (año-guión-semestre). Queda documentado como validación en el service.
- **[Calendario visual]** El endpoint devuelve fechas ordenadas, pero la visualización como calendario (mes/semana) es responsabilidad del frontend. **Mitigación**: el GET list incluye `fecha` como campo ordenable; el frontend puede agrupar con `date-fns` o similar.
- **[Volumen de fechas]** Una materia con 4 parciales + 4 TPs + 1 coloquio + 2 recuperatorios = ~11 fechas por cuatrimestre. Para un tenant con 100 materias activas = ~1100 filas. Volumen trivial para PostgreSQL.

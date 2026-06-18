## Context

El sistema ya cuenta con `Calificacion`, `UmbralMateria` y `EntradaPadron` importados desde C-10. Los datos existen pero no hay lógica que los transforme en información útil para los actores del sistema. Este change construye la capa de **análisis y reportes** (Épica 2) sobre esos datos.

Arquitectura actual:
- `CalificacionRepository` — queries básicas (`list_by_materia`, `list_by_asignacion`, `find_sin_calificar`)
- `calificacion_service.py` — lógica de importación y umbral
- Modelos: `Calificacion` (aprobado ya computado), `UmbralMateria` (umbral_pct + valores_aprobatorios), `EntradaPadron` (datos del alumno)

## Goals / Non-Goals

**Goals:**
- Módulo `/api/analisis/*` con 8 endpoints que cubren F2.2–F2.9
- Lógica de cómputo en **funciones puras** separadas de I/O (testables sin DB)
- Patrón consistente: Router → Service (orquesta I/O) → Pure Functions (computan) → Repository (queries)
- Export CSV sin dependencias externas
- Guard `atrasados:ver` ya seedeado en migración RBAC
- Solo operaciones READ — no se modifican datos existentes

**Non-Goals:**
- No se crean nuevas tablas ni modelos (salvo que se decida cache de monitores)
- No se implementa UI frontend (eso es C-21)
- No se implementa la cola de comunicaciones (C-12)
- No se modifica el schema de `Calificacion` ni `UmbralMateria`
- No se implementa autenticación/autorización desde cero (ya existe)

## Decisions

### D1 — Separación lógica pura / I/O en AnalisisService

**Decisión:** `AnalisisService` delega el cómputo a funciones puras (`analisis_calculos.py`) que reciben datos planos (listas de dicts o dataclasses) y retornan resultados estructurados. El Service solo orquesta: llama al Repository, pasa los datos a la función pura, y retorna el resultado.

```python
# Pure function (testable without DB)
def compute_atrasados(
    calificaciones: list[CalificacionData],
    umbral: UmbralData,
    actividades_esperadas: list[str],
) -> list[AtrasadoResult]:
    ...

# Service (orchestration)
class AnalisisService:
    async def get_atrasados(self, materia_id: UUID) -> list[AtrasadoResult]:
        calificaciones = await self.repo.list_by_materia(materia_id)
        umbral = await self.umbral_repo.get_by_materia(materia_id)
        actividades = await self.repo.get_actividades_by_materia(materia_id)
        return compute_atrasados(calificaciones, umbral, actividades)
```

**Alternativa considerada:** Toda la lógica dentro del Service. Descartada porque hace imposible testear la lógica de negocio sin instanciar DB. Las funciones puras son el núcleo testeable.

**Alternativa considerada:** Lógica en el Repository como queries SQL complejas. Descartada porque mezcla concerns y las RN (RN-06, RN-09) son lógica de negocio, no de persistencia.

### D2 — Cómputo de atrasados en memoria

**Decisión:** El cómputo de alumnos atrasados (RN-06) se hace en memoria a partir de todas las calificaciones de la materia. Se determina el conjunto de actividades esperadas (distinct de `Calificacion.actividad` para la materia), y para cada alumno se verifica: (a) tiene registro para cada actividad, (b) si lo tiene, `aprobado = true` según el umbral (ya computado al importar).

**Justificación:** El volumen de datos por materia es acotado (típicamente <200 alumnos × 20 actividades = 4000 registros). No justifica complejidad SQL adicional. Si en el futuro hay materias con miles de alumnos, se puede optimizar con queries agregadas.

### D3 — Export CSV con `csv.writer` nativo

**Decisión:** La exportación de TPs sin corregir (F2.6) usa el módulo `csv` de la stdlib de Python. No se agrega `openpyxl` ni `pandas`.

**Alternativa considerada:** XLSX con `openpyxl`. Descartado porque agrega una dependencia sin beneficio claro para este caso de uso (datos tabulares simples, el usuario los abre igual en Excel). Si en el futuro se requiere formato con estilos/múltiples hojas, se evalúa.

### D4 — Un solo router `analisis.py`

**Decisión:** Todos los endpoints de análisis van en `backend/app/api/v1/routers/analisis.py`, con prefijo `/api/v1/analisis`.

**Justificación:** Sigue el patrón existente (cada módulo tiene su router: `calificaciones.py`, `padron.py`, etc.). Si el módulo crece, se puede dividir más adelante.

### D5 — Filtros de monitores vía query params + filtrado en service

**Decisión:** Los monitores (F2.7–F2.9) reciben filtros como query params opcionales. El Repository devuelve el conjunto base (scope según rol), y el Service aplica los filtros en memoria o pasa los filtros al Repository como cláusulas WHERE según complejidad.

**Justificación:** Los filtros de texto libre (búsqueda por nombre) se aplican en memoria porque son case-insensitive y pueden tener múltiples términos. Los filtros estructurados (materia_id, comision, regional) se pasan al Repository como SQL para aprovechar índices.

### D6 — Nota final como promedio simple de notas numéricas

**Decisión:** La nota final (F2.5) se calcula como el promedio de todas las notas numéricas del alumno en la materia. Las actividades textuales no ponderan.

**Justificación:** No hay especificación de ponderación por actividad en la KB. Si en el futuro se requiere ponderación, se agrega como configuración por materia.

### D7 — Ranking descendente por count(aprobado=true)

**Decisión:** El ranking (F2.3) ordena alumnos por cantidad de actividades con `aprobado = true`, descendente. Solo incluye alumnos con count ≥ 1 (RN-09).

**Justificación:** Sigue RN-09 explícitamente. Es la métrica más útil para identificar alumnos destacados.

## Risks / Trade-offs

| Riesgo | Mitigación |
|--------|------------|
| **R1 — Performance en monitores generales**: el monitor general (F2.7) puede tener que procesar miles de alumnos × decenas de actividades si el tenant es grande | Agregar paginación desde el diseño; los filtros reducen el conjunto antes de computar. Si es necesario, agregar una tabla de materialized view para monitores. |
| **R2 — Umbral por asignación vs por materia**: el umbral está vinculado a `asignacion_id`, no a `materia_id`. Un mismo alumno puede tener diferente umbral según qué docente importó. | El cómputo de atrasados usa el umbral de la materia (el first o el más reciente). RN-03 define umbral por asignación, pero RN-06 habla de "umbral configurado en la materia". Consistencia: se usa el umbral por defecto 60% si hay múltiples. Esto es una pregunta abierta (PA-XX potencial). |
| **R3 — Alumno sin ninguna calificación**: un alumno en el padrón pero sin ningún registro en `Calificacion` no aparece en atrasados porque no hay datos. | Se cruza contra `EntradaPadron` de la materia: si el alumno está en el padrón pero no tiene calificaciones, se marca como "sin datos" o se excluye según criterio. Decisión: se incluye como atrasado por "actividades faltantes" (RN-06). |
| **R4 — CSV injection**: exportar datos con valores que Excel interpreta como fórmulas (=CMD, +, -) | Escapar valores que comienzan con caracteres peligrosos anteponiendo `\t` o comillas. |

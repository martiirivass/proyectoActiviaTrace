## Context

El sistema necesita los modelos fundacionales de la estructura académica. Según ADR-006 (cerrado):
- `Materia` = definición única en el catálogo del tenant (ej: "PROG_I" → "Programación I")
- `Dictado` = instancia de esa materia en una `carrera × cohorte` concreta (ej: "Programación I – Python" en TUPAD, cohorte MAR-2026)

El diseño sigue los mismos patrones de C-01..C-05 (Models → Repositories → Services → Routers), con TenantScopedRepository para aislamiento multi-tenant y SoftDeleteMixin.

## Goals / Non-Goals

**Goals:**
- Modelos `Carrera`, `Cohorte`, `Materia`, `Dictado` con todos los campos definidos en E1-E3 + ADR-006
- `Dictado` como entidad separada que relaciona `Materia` con `carrera_id` y `cohorte_id`, con nombre descriptivo propio
- ABM para cada entidad con permisos `estructura:gestionar`
- Reglas: unicidad por tenant, soft delete, carrera inactiva → no cohortes activas
- Repositorios scoped por tenant
- Migration 005 con tablas, FKs, índices, seed data de ejemplo

**Non-Goals:**
- No se implementan asignaciones (C-07)
- No se implementa la relación entre Dictado y calificaciones/encuentros (futuros changes)
- No hay seed de datos reales — solo estructural

## Decisions

### 1. Dictado como entidad separada con su propia semántica
| Opción | Veredicto |
|--------|-----------|
| `Dictado` como tabla separada FK a `Materia, Cohorte` | ✅ Elegido |
| Dictado como atributo de Materia (ej: campo `dictados: JSON`) | ❌ Rompe normalización |

**Rationale**: ADR-006 define que calificaciones, equipos docentes, encuentros y coloquios cuelgan del Dictado, no de Materia. Una materia se dicta en N carreras/cohortes, un dictado es una combinación específica (Materia × Carrera × Cohorte) y tiene su propio nombre ("Programación I – Python"). Separarlo evita duplicar Materia por cada dictado.

### 2. `Dictado.descripcion` opcional para nombre legible del dictado
El dictado tiene `nombre` obligatorio (ej: "Programación I - Python") que puede diferir del nombre de la materia. Esto permite que una misma materia tenga múltiples dictados con enfoques diferentes.

### 3. Soft delete en todas las entidades
Todas heredan `SoftDeleteMixin` para consistencia con el resto del sistema. Ninguna entidad académica se elimina físicamente.

### 4. Repositorios unificados vs separados
| Opción | Veredicto |
|--------|-----------|
| Un repositorio por entidad (4 repos) | ✅ Elegido |
| Un repositorio genérico "estructura" | ❌ Mezcla responsabilidades |

**Rationale**: Cada entidad tiene reglas de unicidad y consultas específicas. 4 repos pequeños son más fáciles de testear y mantener que uno grande.

## Risks / Trade-offs

- **[Volumen]** Dictado puede crecer si una materia se dicta en muchas cohortes → mitigado: índice compuesto `(materia_id, cohorte_id)` único
- **[Carrera inactiva]** Validar en servicio de Cohorte que la carrera esté activa al crear cohortes → validación en CohorteService
- **[Consistencia]** Soft delete de Carrera podría dejar cohortes huérfanas → la RN dice "no admite cohortes *abiertas*", no fuerza cascade delete

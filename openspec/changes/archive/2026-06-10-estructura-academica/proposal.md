## Why

La plataforma necesita los modelos raíz de la estructura académica: carreras, cohortes, materias (catálogo) y dictados (instancia concreta). Sin estas entidades no es posible modelar ninguna funcionalidad de negocio: asignaciones, calificaciones, encuentros, comunicaciones, liquidaciones. Es el cimiento del dominio académico.

## What Changes

- Crear modelo `Carrera` (programa académico por tenant)
- Crear modelo `Cohorte` (camada de estudiantes, exclusiva de una carrera)
- Crear modelo `Materia` (catálogo único de materias del tenant — ADR-006)
- Crear modelo `Dictado` (instancia de una materia en una carrera × cohorte — ADR-006)
- ABM `/api/v1/admin/carreras` con permiso `estructura:gestionar`
- ABM `/api/v1/admin/cohortes` con permiso `estructura:gestionar`
- ABM `/api/v1/admin/materias` con permiso `estructura:gestionar`
- ABM `/api/v1/admin/dictados` con permiso `estructura:gestionar`
- Reglas de negocio: unicidad por tenant, carrera inactiva no admite cohortes activas, soft delete en todas
- Migration 005: tablas `carreras`, `cohortes`, `materias`, `dictados`

## Capabilities

### New Capabilities
- `estructura-academica`: Gestión de carreras, cohortes, materias (catálogo) y dictados (instancias de dictado) con ABM completo, reglas de unicidad, aislamiento multi-tenant y soft delete.

### Modified Capabilities
- *(ninguna — es capability nueva)*

## Impact

- **Nuevos modelos**: `Carrera`, `Cohorte`, `Materia`, `Dictado` en `backend/app/models/`
- **Nuevos repositorios**: `CarreraRepository`, `CohorteRepository`, `MateriaRepository`, `DictadoRepository` scoped por tenant
- **Nuevos servicios**: `CarreraService`, `CohorteService`, `MateriaService`, `DictadoService`
- **Nuevos schemas**: Pydantic DTOs request/response para cada entidad
- **Nuevos routers**: ABM bajo `/api/v1/admin/carreras`, `.../cohortes`, `.../materias`, `.../dictados`
- **Migración**: Alembic 005_create_estructura_academica_tables
- **Tests**: CRUD, unicidad, multi-tenant aislamiento, soft delete, carrera inactiva bloquea cohortes

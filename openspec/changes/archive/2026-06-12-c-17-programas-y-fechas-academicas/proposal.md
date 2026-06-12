## Why

La plataforma necesita gestionar el calendario académico y los programas de materia por tenant. Sin `ProgramaMateria` no hay forma de asociar el documento oficial del programa a una combinación materia × carrera × cohorte. Sin `FechaAcademica` no hay calendarización de parciales, TPs, coloquios y recuperatorios. Ambos son insumos críticos para el setup de cuatrimestre (FL-03) y para generar contenido publicable en el LMS. C-06 ya proveyó `Materia`, `Carrera` y `Cohorte`; este change agrega las entidades de calendarización y programa que operan sobre esas bases.

## What Changes

- Crear modelo `ProgramaMateria` (E16): programa/documento oficial por materia × carrera × cohorte con referencia opaca al archivo.
- Crear modelo `FechaAcademica` (E15): fechas de parciales, TPs, coloquios y recuperatorios por materia × cohorte × tipo × número.
- CRUD `/api/v1/programas` con permiso `estructura:gestionar` — upload y asociación de programa.
- CRUD `/api/v1/fechas-academicas` con permiso `estructura:gestionar` — registro y edición de fechas evaluativas.
- Endpoint `GET /api/v1/fechas-academicas/exportar-lms` — genera fragmento de contenido listo para publicar en el aula virtual del LMS (F5.4 output).
- Vistas: listado tabular y calendarización de fechas académicas.
- Migración Alembic con tablas `programa_materia` y `fecha_academica`.
- Tests: CRUD, unicidad materia×carrera×cohorte en programa, unicidad materia×cohorte×tipo×numero×periodo en fecha, aislamiento multi-tenant, soft delete.

## Capabilities

### New Capabilities
- `programas-materia`: Gestión de programas/documentos oficiales de materia, asociados a una combinación materia × carrera × cohorte, con referencia de archivo opaca y soft delete.
- `fechas-academicas`: Calendarización de instancias evaluativas (parciales, TPs, coloquios, recuperatorios) por materia × cohorte con tipo, número y periodo, más exportación de contenido para LMS.

### Modified Capabilities
- *(ninguna — son capabilities nuevas)*

## Impact

- **Nuevos modelos**: `ProgramaMateria` y `FechaAcademica` en `backend/app/models/`
- **Nuevos schemas**: Pydantic DTOs request/response para cada entidad
- **Nuevos repositorios**: `ProgramaMateriaRepository`, `FechaAcademicaRepository` scoped por tenant
- **Nuevos servicios**: `ProgramaService`, `FechaAcademicaService` con lógica de negocio
- **Nuevos routers**: CRUD bajo `/api/v1/programas` y `/api/v1/fechas-academicas`
- **Nuevo endpoint**: `GET /api/v1/fechas-academicas/exportar-lms` para generación de contenido LMS
- **Migración**: Alembic (post-C-06) con tablas `programa_materia` y `fecha_academica`
- **Tests**: CRUD, unicidad compuesta, multi-tenant isolation, soft delete, exportación LMS
- **Permiso reutilizado**: `estructura:gestionar` (ya existe de C-06) — COORDINADOR y ADMIN
- **Audit**: operaciones de escritura registran auditoría con códigos del catálogo existente

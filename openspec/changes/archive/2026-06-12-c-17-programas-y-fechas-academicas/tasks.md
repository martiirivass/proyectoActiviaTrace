## 1. Modelos de Dominio

- [ ] 1.1 Crear `backend/app/models/programa_materia.py` — modelo `ProgramaMateria` con `id`, `tenant_id`, `materia_id`, `carrera_id`, `cohorte_id`, `titulo`, `referencia_archivo`, `cargado_at`, `SoftDeleteMixin`, `TimestampMixin`. Unique constraint `(materia_id, carrera_id, cohorte_id)`.
- [ ] 1.2 Crear `backend/app/models/fecha_academica.py` — modelo `FechaAcademica` con `id`, `tenant_id`, `materia_id`, `cohorte_id`, `tipo` (enum: Parcial|TP|Coloquio|Recuperatorio), `numero` (int), `periodo` (text), `fecha` (date), `titulo` (text), `SoftDeleteMixin`, `TimestampMixin`. Unique constraint `(materia_id, cohorte_id, tipo, numero, periodo)`.
- [ ] 1.3 Exportar modelos en `backend/app/models/__init__.py`.

## 2. Schemas Pydantic

- [ ] 2.1 Crear `backend/app/schemas/programas.py` — `ProgramaCreate` (materia_id, carrera_id, cohorte_id, titulo, referencia_archivo), `ProgramaUpdate` (titulo opcional, referencia_archivo opcional), `ProgramaResponse` (todos los campos + timestamps). `extra='forbid'` en todos.
- [ ] 2.2 Crear `backend/app/schemas/fechas_academicas.py` — `FechaAcademicaCreate` (materia_id, cohorte_id, tipo, numero, periodo, fecha, titulo), `FechaAcademicaUpdate` (todos opcionales), `FechaAcademicaResponse` (todos los campos + timestamps), `FechasExportLMSResponse` (contenido: str). `extra='forbid'` en todos.
- [ ] 2.3 Exportar schemas en `backend/app/schemas/__init__.py`.

## 3. Repositorios

- [ ] 3.1 Crear `backend/app/repositories/programa_repository.py` — `ProgramaMateriaRepository` con métodos: `find_by_materia_carrera_cohorte(materia_id, carrera_id, cohorte_id)`, `list(materia_id=None, carrera_id=None, cohorte_id=None)` con filtros opcionales.
- [ ] 3.2 Crear `backend/app/repositories/fecha_academica_repository.py` — `FechaAcademicaRepository` con métodos: `find_by_unique(materia_id, cohorte_id, tipo, numero, periodo)`, `list(materia_id=None, cohorte_id=None, tipo=None, periodo=None)` con filtros opcionales y orden por fecha ascendente.
- [ ] 3.3 Exportar repositorios en `backend/app/repositories/__init__.py`.

## 4. Servicios

- [ ] 4.1 Crear `backend/app/services/programa_service.py` — `ProgramaService` con CRUD completo + validación de unicidad materia×carrera×cohorte (409 si duplicado activo). Inyecta `ProgramaMateriaRepository`.
- [ ] 4.2 Crear `backend/app/services/fecha_academica_service.py` — `FechaAcademicaService` con CRUD completo + validación de unicidad + validación de periodo contra regex `^\d{4}-[12]$` + validación de tipo contra enum + validación de numero > 0. Método `exportar_lms(materia_id, cohorte_id, periodo)` que genera fragmento HTML/texto formateado.
- [ ] 4.3 Exportar servicios en `backend/app/services/__init__.py`.

## 5. Routers (API)

- [ ] 5.1 Crear `backend/app/api/v1/routers/programas.py` — `programas_router` con endpoints:
  - `GET /api/v1/programas` (list con filtros opcionales: materia_id, carrera_id, cohorte_id)
  - `POST /api/v1/programas` (create, 201)
  - `GET /api/v1/programas/{id}` (get by id)
  - `PUT /api/v1/programas/{id}` (update titulo/referencia_archivo)
  - `DELETE /api/v1/programas/{id}` (soft delete, 204)
- [ ] 5.2 Crear `backend/app/api/v1/routers/fechas_academicas.py` — `fechas_router` con endpoints:
  - `GET /api/v1/fechas-academicas` (list con filtros opcionales: materia_id, cohorte_id, tipo, periodo)
  - `POST /api/v1/fechas-academicas` (create, 201)
  - `GET /api/v1/fechas-academicas/{id}` (get by id)
  - `PUT /api/v1/fechas-academicas/{id}` (update)
  - `DELETE /api/v1/fechas-academicas/{id}` (soft delete, 204)
  - `GET /api/v1/fechas-academicas/exportar-lms` (exportar contenido LMS, requiere materia_id)
- [ ] 5.3 Proteger todos los endpoints con `require_permission("estructura:gestionar")` y `get_current_user`.
- [ ] 5.4 Registrar routers en `backend/app/api/v1/__init__.py` o `backend/app/api/router.py`.

## 6. Migración Alembic

- [ ] 6.1 Generar migración automática con Alembic: `alembic revision --autogenerate -m "create programa_materia and fecha_academica tables"`.
- [ ] 6.2 Revisar y ajustar la migración generada: asegurar FKs, unique constraints, índices por tenant_id y columnas de filtro.
- [ ] 6.3 Verificar `down_revision` apunte a la migración más reciente existente.

## 7. Tests

- [ ] 7.1 Tests de modelo `ProgramaMateria`: creación, unique constraint, soft delete, timestamps.
- [ ] 7.2 Tests de modelo `FechaAcademica`: creación con todos los tipos del enum, unique constraint, validación de numero positivo, soft delete, timestamps.
- [ ] 7.3 Tests de repositorio `ProgramaMateriaRepository`: filtros por materia/carrera/cohorte individuales y combinados, aislamiento multi-tenant.
- [ ] 7.4 Tests de repositorio `FechaAcademicaRepository`: filtros por materia/cohorte/tipo/periodo individuales y combinados, orden por fecha, aislamiento multi-tenant.
- [ ] 7.5 Tests de servicio `ProgramaService`: CRUD exitoso, 409 en duplicado, 404 en get/update/delete de inexistente, 403 sin permiso.
- [ ] 7.6 Tests de servicio `FechaAcademicaService`: CRUD exitoso, 409 en duplicado, 422 en tipo inválido, 422 en numero <= 0, 422 en periodo con formato inválido, 404 en inexistente.
- [ ] 7.7 Tests de exportación LMS: contenido generado correctamente con fechas, contenido vacío si no hay fechas, 422 si falta materia_id.
- [ ] 7.8 Tests de integración API: endpoints responden con códigos correctos, permiso `estructura:gestionar` requerido, multi-tenant isolation.
- [ ] 7.9 Verificar cobertura ≥80% líneas y ≥90% reglas de negocio para el módulo.

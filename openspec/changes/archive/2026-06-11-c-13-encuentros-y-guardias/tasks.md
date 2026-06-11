## 1. Setup — Auditoría y Permisos

- [x] 1.1 Agregar códigos de auditoría `ENCUENTRO_CREAR`, `ENCUENTRO_EDITAR`, `GUARDIA_REGISTRAR` en `backend/app/core/audit_codes.py`
- [x] 1.2 Agregar permiso `encuentros:gestionar` en el seeder de permisos de RBAC (en `backend/app/core/seed.py` o donde se definan permisos base)
- [x] 1.3 Asignar permiso `encuentros:gestionar` a roles PROFESOR, TUTOR, COORDINADOR y ADMIN en el seeder

## 2. Modelos SQLAlchemy

- [x] 2.1 Crear `backend/app/models/slot_encuentro.py` con modelo `SlotEncuentro` (UUID PK, tenant_id, asignacion_id, materia_id, titulo, hora: Time, dia_semana: enum, fecha_inicio: Date, cant_semanas: int, fecha_unica: Date nullable, meet_url: String, vig_desde: Date, vig_hasta: Date, SoftDeleteMixin)
- [x] 2.2 Crear `backend/app/models/instancia_encuentro.py` con modelo `InstanciaEncuentro` (UUID PK, tenant_id, slot_id UUID nullable, materia_id, fecha: Date, hora: Time, titulo, estado: enum Programado|Realizado|Cancelado, meet_url, video_url nullable, comentario, SoftDeleteMixin)
- [x] 2.3 Crear `backend/app/models/guardia.py` con modelo `Guardia` (UUID PK, tenant_id, asignacion_id, materia_id, carrera_id, cohorte_id, dia: enum, horario: String, estado: enum Pendiente|Realizada|Cancelada, comentarios nullable, creada_at, SoftDeleteMixin)
- [x] 2.4 Registrar los 3 modelos en `backend/app/models/__init__.py` con sus enums exportados

## 3. Migración Alembic

- [x] 3.1 Generar migración automática con `alembic revision --autogenerate -m "create_encuentros_guardias_tables"`
- [x] 3.2 Revisar y ajustar la migración generada (verificar tipos TIME, enums, FKs)
- [x] 3.3 Ejecutar migración y verificar que las tablas se crean correctamente

## 4. Repositorios

- [x] 4.1 Crear `backend/app/repositories/encuentro_repository.py` con `SlotEncuentroRepository` y `InstanciaEncuentroRepository` (ambos heredan de `TenantScopedRepository`)
- [x] 4.2 Agregar método `bulk_create_instancias()` para insert masivo de instancias generadas
- [x] 4.3 Agregar método `list_by_slot()` en `InstanciaEncuentroRepository`
- [x] 4.4 Agregar método `list_admin()` con filtros opcionales (materia_id, fecha_desde, fecha_hasta, estado, asignacion_id) para vista admin transversal
- [x] 4.5 Crear `backend/app/repositories/guardia_repository.py` con `GuardiaRepository` heredando de `TenantScopedRepository`
- [x] 4.6 Agregar método `list_with_filters()` para consulta global con filtros
- [x] 4.7 Agregar métodos de export (query optimizada para CSV) en `GuardiaRepository`
- [x] 4.8 Registrar repositorios en `backend/app/repositories/__init__.py`

## 5. Schemas Pydantic

- [x] 5.1 Crear `backend/app/schemas/encuentros.py` con schemas request/response para slots e instancias (todos con `ConfigDict(extra='forbid')`)
- [x] 5.2 Schemas para slots: `SlotEncuentroCreate` (con modos recurrente/único mutuamente excluyentes), `SlotEncuentroResponse`, `SlotEncuentroDetail`
- [x] 5.3 Schemas para instancias: `InstanciaUpdate` (estado, meet_url, video_url, comentario), `InstanciaResponse`, `InstanciaListResponse`
- [x] 5.4 Schema `EncuentroAdminResponse` para vista admin con datos del docente y materia
- [x] 5.5 Schema `EncuentroAdminListResponse` paginado
- [x] 5.6 Crear `backend/app/schemas/guardias.py` con: `GuardiaCreate`, `GuardiaUpdate`, `GuardiaResponse`, `GuardiaListResponse`
- [x] 5.7 Registrar schemas en `backend/app/schemas/__init__.py`

## 6. Services

- [x] 6.1 Crear `backend/app/services/encuentro_service.py` con `EncuentroService`
- [x] 6.2 Implementar `crear_slot()`: validar modo (recurrente vs único), crear SlotEncuentro, generar y bulk-insertar instancias, auditar `ENCUENTRO_CREAR`
- [x] 6.3 Implementar `editar_instancia()`: validar transición de estado, regla de video_url solo si Realizado, auditar `ENCUENTRO_EDITAR`
- [x] 6.4 Implementar `listar_instancias_por_slot()`: delegar a repository
- [x] 6.5 Implementar `exportar_html()`: query de instancias activas, generar tabla HTML como string, devolver Response con media_type text/html
- [x] 6.6 Implementar `listar_admin()`: con filtros y paginación, incluir join con materia y asignacion para mostrar nombres
- [x] 6.7 Crear `backend/app/services/guardia_service.py` con `GuardiaService`
- [x] 6.8 Implementar `registrar_guardia()`: validar que TUTOR solo registre para su propia asignación, auditar `GUARDIA_REGISTRAR`
- [x] 6.9 Implementar `actualizar_estado_guardia()`: validar ownership o rol COORDINADOR
- [x] 6.10 Implementar `listar_guardias()`: con filtros y paginación
- [x] 6.11 Implementar `exportar_csv()`: generar CSV en memoria, devolver StreamingResponse con media_type text/csv

## 7. Routers / API Endpoints

- [x] 7.1 Crear `backend/app/api/v1/routers/encuentros.py` con prefix `/api/v1/encuentros`
- [x] 7.2 Endpoint `POST /slots` — crear slot (recurrente o único), guard `encuentros:gestionar`
- [x] 7.3 Endpoint `GET /slots/{slot_id}/instancias` — listar instancias de un slot
- [x] 7.4 Endpoint `PATCH /instancias/{id}` — editar instancia, guard `encuentros:gestionar`
- [x] 7.5 Endpoint `GET /admin` — vista admin transversal, guard `encuentros:gestionar` + check rol COORDINADOR/ADMIN
- [x] 7.6 Endpoint `GET /{materia_id}/exportar-html` — exportar HTML, guard `encuentros:gestionar`
- [x] 7.7 Crear `backend/app/api/v1/routers/guardias.py` con prefix `/api/v1/guardias`
- [x] 7.8 Endpoint `POST /` — registrar guardia, guard `encuentros:gestionar`
- [x] 7.9 Endpoint `PATCH /{id}` — actualizar estado de guardia
- [x] 7.10 Endpoint `GET /` — listar guardias (con filtros), guard `encuentros:gestionar`
- [x] 7.11 Endpoint `GET /exportar` — exportar CSV de guardias
- [x] 7.12 Registrar ambos routers en `backend/app/main.py` (api/v1/__init__.py está vacío y se importan directamente)

## 8. Tests

- [ ] 8.1 Crear `backend/tests/test_encuentros.py` con fixtures de setup (tenant, user, materia, asignacion)
- [ ] 8.2 Test: crear slot recurrente con 4 instancias → verificar cantidad y fechas correctas
- [ ] 8.3 Test: crear encuentro único → verificar 1 instancia, slot con cant_semanas=0
- [ ] 8.4 Test: validar exclusión mutua (cant_semanas > 0 Y fecha_unica presente → 422)
- [ ] 8.5 Test: editar instancia — cambiar estado a Realizado con video_url
- [ ] 8.6 Test: editar instancia — rechazar transición Realizado → Programado (409)
- [ ] 8.7 Test: editar instancia — rechazar video_url si estado no es Realizado (422)
- [ ] 8.8 Test: exportar HTML — verificar formato y exclusión de Canceladas
- [ ] 8.9 Test: exportar HTML vacío — 200 con mensaje
- [ ] 8.10 Test: vista admin — COORDINADOR ve instancias de todo el tenant
- [ ] 8.11 Test: vista admin — TUTOR recibe 403
- [ ] 8.12 Test: registrar guardia como TUTOR — éxito
- [ ] 8.13 Test: registrar guardia con asignación ajena — 403
- [ ] 8.14 Test: actualizar estado de guardia (Pendiente → Realizada)
- [ ] 8.15 Test: listar guardias con filtros
- [ ] 8.16 Test: exportar guardias a CSV y verificar contenido
- [ ] 8.17 Test: aislamiento tenant — datos del tenant A no visibles en tenant B

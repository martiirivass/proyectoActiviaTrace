## 1. Modelos

- [x] 1.1 Crear modelo `VersionPadron` (id, tenant_id, materia_id, cohorte_id, cargado_por, cargado_at, activa — hereda SoftDeleteMixin)
- [x] 1.2 Crear modelo `EntradaPadron` (id, version_id, tenant_id, usuario_id nullable, nombre, apellidos, email cifrado, comision, regional — hereda SoftDeleteMixin)
- [x] 1.3 Registrar ambos modelos en `backend/app/models/__init__.py`

## 2. Migración

- [x] 2.1 Crear migration `0NN_create_padron_tables` con tablas `version_padron` y `entrada_padron`
- [x] 2.2 Índices: unique `(tenant_id, materia_id, cohorte_id, activa)` donde activa=true en version_padron; FK version_id → version_padron.id con cascade; FK usuario_id → usuarios.id nullable
- [x] 2.3 Agregar campo `moodle_integration_enabled` (booleano, default false) a la tabla `materias` (si no existe)

## 3. Repositorios

- [x] 3.1 Crear `PadronRepository` (scoped por tenant) con métodos:
  - [x] 3.1.1 `create_version(materia_id, cohorte_id, cargado_por)` → crea VersionPadron, desactiva versión activa previa
  - [x] 3.1.2 `bulk_create_entries(version_id, entries)` → crea múltiples EntradaPadron
  - [x] 3.1.3 `get_versions(materia_id, cohorte_id)` → lista versiones con conteo de entradas
  - [x] 3.1.4 `get_active_version(materia_id, cohorte_id)` → versión activa actual
  - [x] 3.1.5 `vaciar_materia(materia_id)` → soft delete de todas las versiones y entradas de una materia
  - [x] 3.1.6 `find_entries_by_email(email_cifrado)` → búsqueda de entrada por email cifrado

## 4. Schemas (Pydantic v2, extra='forbid')

- [x] 4.1 Crear `PadronPreviewResponse` (lista de entradas parseadas + cantidad de filas)
- [x] 4.2 Crear `PadronConfirmRequest` (materia_id, cohorte_id, entries: lista de entradas)
- [x] 4.3 Crear `PadronConfirmResponse` (version_id, activa, filas_creadas)
- [x] 4.4 Crear `VersionPadronResponse` (id, materia_id, cohorte_id, cargado_por, cargado_at, activa, entrada_count)
- [x] 4.5 Crear `VersionPadronListResponse` (versiones: lista, total)
- [x] 4.6 Crear `MoodleSyncRequest` (materia_id, cohorte_id)
- [x] 4.7 Crear `MoodleSyncResponse` (status, message, version_id opcional)
- [x] 4.8 Crear `VaciarMateriaResponse` (materia_id, versiones_afectadas)

## 5. Servicios

- [x] 5.1 Crear `PadronService` con:
  - [x] 5.1.1 `preview_import(file)` — parsea xlsx/csv, valida columnas, retorna vista previa
  - [x] 5.1.2 `confirm_import(materia_id, cohorte_id, entries, actor_id)` — crea versión activa, bulk insert entries, genera audit PADRON_CARGAR
  - [x] 5.1.3 `list_versions(materia_id, cohorte_id)` — lista versiones históricas
  - [x] 5.1.4 `vaciar_materia(materia_id, actor_id)` — soft delete, genera audit PADRON_VACIAR
  - [x] 5.1.5 `sync_from_moodle(materia_id, cohorte_id)` — invoca Moodle WS, mapea usuarios, crea versión

## 6. Integraciones

- [x] 6.1 Crear `backend/app/integrations/moodle_ws.py` con:
  - [x] 6.1.1 Cliente `MoodleWSClient(config)` — config con URL base, token, timeout
  - [x] 6.1.2 Método `get_users_by_cohort(cohorte_id)` → llama a `core_cohort_get_members`
  - [x] 6.1.3 Método `get_activities_by_course(materia_id)` → llama a `core_course_get_contents`
  - [x] 6.1.4 Manejo de errores: timeout, HTTP error, parse error → levanta `MoodleWSException`
  - [x] 6.1.5 Retry con backoff exponencial (3 intentos: 1s, 4s, 9s)
  - [x] 6.1.6 Mapeo de usuario Moodle → dict de entrada de padrón

## 7. Routers

- [x] 7.1 Crear router `/api/v1/padron` con:
  - [x] 7.1.1 `POST /preview` — subir archivo, retornar vista previa (permiso `padron:cargar`)
  - [x] 7.1.2 `POST /confirm` — confirmar importación (permiso `padron:cargar`)
  - [x] 7.1.3 `GET /versions` — listar versiones filtrado por materia_id, cohorte_id (permiso `padron:ver`)
  - [x] 7.1.4 `POST /sync-moodle` — disparar sync on-demand (permiso `moodle:sync`)
- [x] 7.2 Crear router `DELETE /api/v1/admin/materias/{id}/vaciar` en router admin existente (permiso `padron:vaciar`)
- [x] 7.3 Registrar routers en `backend/app/main.py`

## 8. Tests

- [x] 8.1 Tests de modelos: crear VersionPadron y EntradaPadron, relaciones, soft delete
- [x] 8.2 Tests de versionado: activar versión desactiva la anterior
- [x] 8.3 Tests de import xlsx: parseo correcto de archivo xlsx válido
- [x] 8.4 Tests de import csv: parseo correcto de archivo csv
- [x] 8.5 Tests de confirm: crea versión activa con entradas
- [x] 8.6 Tests de entrada sin usuario_id: alumno sin cuenta registrada
- [x] 8.7 Tests de tenant isolation: tenant A no ve datos de tenant B
- [x] 8.8 Tests de vaciar materia: soft delete de todas las versiones y entradas
- [x] 8.9 Tests de vaciar materia sin datos: no genera error
- [x] 8.10 Tests de vaciar solo afecta materia indicada
- [x] 8.11 Tests de permiso: 403 sin `padron:cargar` o `padron:vaciar`
- [x] 8.12 Tests de Moodle WS mock: sync on-demand exitosa con mock
- [x] 8.13 Tests de Moodle WS error: 502 con reintento
- [x] 8.14 Tests de audit log: `PADRON_CARGAR` y `PADRON_VACIAR` generados correctamente

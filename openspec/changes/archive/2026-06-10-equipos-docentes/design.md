
## Context

El módulo de gestión de equipos docentes se construye sobre el modelo `Asignacion` existente (creado en C-07), que ya cuenta con CRUD individual (`/api/v1/admin/asignaciones`), repository con scope de tenant y service con validación de roles. No hay cambios de schema de base de datos — todas las nuevas operaciones son lógica de negocio sobre el modelo actual.

El modelo `Asignacion` existente usa el patrón `Dictado` (materia × carrera × cohorte) como contexto académico, con `dictado_id` como FK. El service actual soporta filtros por `usuario_id`, `materia_id` y `rol`; se extiende para soportar filtros por `dictado_id` y `carrera_id`.

## Goals / Non-Goals

**Goals:**
- Proveer endpoints para que un docente vea sus propios equipos (F4.2)
- Implementar asignación masiva de docentes (F4.4) como operación atómica
- Implementar clonación de equipo entre períodos (F4.5) respetando RN-12
- Implementar modificación de vigencia general (F4.6)
- Implementar exportación de equipo a CSV (F4.7)
- Todas las operaciones generan audit log con código `ASIGNACION_MODIFICAR`
- Cobertura ≥80% líneas, ≥90% reglas de negocio

**Non-Goals:**
- No se modifica el schema de `Asignacion` (no hay migración)
- No se toca frontend (es C-23 o posterior)
- No se implementa F4.1 (administración de usuarios, ya existe en C-07)
- No se implementa integración con Moodle para equipos

## Decisions

### D1: Router separado para operaciones de equipo
- **Decisión**: Las operaciones de equipo (mis-equipos, masiva, clonar, vigencia, exportar) van en un nuevo router `backend/app/api/v1/routers/equipos.py` con prefijo `/api/v1/equipos/`.
- **Por qué**: Mantiene separación de concerns. El router existente `admin_asignaciones.py` maneja CRUD individual; el nuevo maneja operaciones de equipo. Evita que un archivo crezca >500 LOC.
- **Alternativa**: Agregar todo al mismo router → descartado por límite de LOC y mezcla de responsabilidades.

### D2: Asignación masiva como operación atómica con transacción
- **Decisión**: El endpoint POST `/api/v1/equipos/masiva` recibe `{ dictado_id, rol, desde, hasta, usuario_ids: UUID[] }` y crea todas las asignaciones en una sola transacción. Si alguna falla, ninguna se persiste.
- **Por qué**: El coordinador necesita que la operación sea todo-o-nada. Dejarlo a mitad de camino dejaría el equipo inconsistente.
- **Implementación**: Se usa `AsyncSession.begin_nested()` (savepoint) dentro del service.

### D3: Clonación de equipo como copia profunda con fechas ajustadas
- **Decisión**: POST `/api/v1/equipos/clonar` recibe `{ dictado_origen_id, dictado_destino_id }`. El service:
  1. Busca asignaciones vigentes del origen
  2. Para cada una, crea una copia en el destino con:
     - Mismos `usuario_id`, `rol`, `responsable_id`
     - Fechas ajustadas al nuevo dictado (desde/hasta del destino)
  3. Operación atómica (transacción única)
- **Por qué**: RN-12 exige que el clonado respete las fechas del nuevo período. La forma más limpia es leer las vigentes del origen y crearlas en el destino con los datos del dictado destino.
- **Validación**: Verifica que el dictado destino exista y no tenga ya asignaciones (para evitar duplicación accidental). Se permite re-clonado con flag `force: true`.

### D4: Filtro por dictado en repository existente
- **Decisión**: Se agrega `dictado_id` como filtro opcional en `AsignacionRepository.list()`, junto con `carrera_id` y `cohorte_id`.
- **Por qué**: Las operaciones de equipo (mis-equipos, exportar) necesitan filtrar por contexto académico completo. El repository ya soporta filtros, es una extensión natural.
- **Implementación**: Se agrega un join a `Dictado` y filtro por `Dictado.carrera_id` y `Dictado.cohorte_id` si se pasan esos parámetros.

### D5: Endpoint "mis equipos" sin permiso especial
- **Decisión**: GET `/api/v1/equipos/mis-equipos` usa `get_current_user` pero NO `require_permission`. El endpoint devuelve las asignaciones del usuario autenticado filtrando por `usuario_id = current_user.id`.
- **Por qué**: Cualquier usuario con asignaciones debe poder ver sus propios equipos. Esto es F4.2 — es un derecho del docente, no un permiso administrativo.
- **Seguridad**: El filtro forzado por `usuario_id` impide ver equipos ajenos. No hay riesgo de escalada.

### D6: Exportación como streaming response
- **Decisión**: GET `/api/v1/equipos/{dictado_id}/exportar` devuelve `StreamingResponse` con `Content-Type: text/csv`.
- **Por qué**: Los equipos pueden tener cientos de asignaciones; streaming evita cargar todo en memoria.
- **Implementación**: Se usa el módulo `csv` de la stdlib de Python para generar el archivo línea por línea.

### D7: Audit en operaciones de escritura
- **Decisión**: Toda operación de escritura (masiva, clonar, vigencia) genera un audit log con `accion = "ASIGNACION_MODIFICAR"`, detalle con metadata de la operación y `usuario_id = current_user.id`.
- **Por qué**: Governance ALTO del dominio. El audit code ya existe.

## Risks / Trade-offs

- **[Riesgo] Clonado con datos huérfanos**: Si se elimina una asignación origen entre la lectura y la escritura de la transacción, el clonado podría fallar parcialmente. → **Mitigación**: operación dentro de una sola transacción con `REPEATABLE READ` isolation level.
- **[Riesgo] Asignación masiva con datos inválidos**: Un `usuario_id` inválido en medio de la lista fallaría toda la operación. → **Mitigación**: es el comportamiento deseado (atómico). Se devuelve error con detalle del primer ítem inválido.
- **[Trade-off] Sin paginación en exportación**: El CSV exporta todo el equipo sin paginación. → **Aceptable** porque los equipos docentes rara vez superan los pocos cientos de registros.
- **[Riesgo] Superposición de vigencias en clonado**: Si el destino ya tiene asignaciones y se fuerza el clonado, podría haber duplicados. → **Mitigación**: por defecto se rechaza si el destino tiene asignaciones; con `force: true` se permite.

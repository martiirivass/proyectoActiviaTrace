## ADDED Requirements

### Requirement: Listar avisos activos para el usuario autenticado
El sistema SHALL exponer `GET /api/v1/avisos` que devuelve los avisos activos visibles para el usuario autenticado, aplicando los siguientes filtros automáticos:

1. **Tenant scope**: solo avisos del tenant del usuario
2. **Vigencia**: `activo = true` AND `inicio_en <= now()` AND `fin_en >= now()`
3. **Alcance**: el aviso debe coincidir con el perfil del usuario:
   - `Global`: visible para todos
   - `PorMateria`: visible si el usuario tiene al menos una asignación activa en esa materia
   - `PorCohorte`: visible si el usuario pertenece a esa cohorte
   - `PorRol`: visible si el rol del usuario coincide con `rol_destino`
4. **Rol destino**: si `rol_destino` no es nulo, solo visible si el usuario tiene ese rol
5. **No eliminado**: soft delete = false

**Ordenamiento**: `orden ASC, inicio_en DESC` (primero los de mayor prioridad numérica, luego los más recientes)

**Paginación**: cursor-based o page-based, default 20 ítems, máximo 100.

#### Scenario: Listar avisos visibles para ALUMNO
- **WHEN** un ALUMNO autenticado del Tenant A, sin asignaciones docentes, envía `GET /api/v1/avisos`
- **THEN** el sistema devuelve solo los avisos del Tenant A cuyo alcance es `Global` o `PorRol` con `rol_destino=ALUMNO`, que estén dentro de su ventana de vigencia y activos, ordenados por `orden ASC, inicio_en DESC`

#### Scenario: Listar avisos visibles para PROFESOR con materia asignada
- **WHEN** un PROFESOR autenticado con asignación activa en Materia X envía `GET /api/v1/avisos`
- **THEN** el sistema incluye avisos `Global`, avisos `PorMateria` con `materia_id = X`, avisos `PorRol` con `rol_destino=PROFESOR`, y avisos `PorCohorte` de las cohortes donde tiene asignaciones

#### Scenario: Aviso fuera de vigencia no se muestra
- **WHEN** un ALUMNO envía `GET /api/v1/avisos` y existe un aviso Global con `fin_en < now()` (vencido) o `inicio_en > now()` (aún no publicado)
- **THEN** el aviso vencido o no publicado NO aparece en el listado

#### Scenario: Aviso desactivado no se muestra
- **WHEN** un TUTOR envía `GET /api/v1/avisos` y existe un aviso Global con `activo = false`
- **THEN** el aviso desactivado NO aparece en el listado

#### Scenario: Paginación de avisos
- **WHEN** un COORDINADOR envía `GET /api/v1/avisos?limit=5&offset=0`
- **THEN** el sistema devuelve hasta 5 avisos con metadatos de paginación (total, offset, limit)

---

### Requirement: Obtener detalle de un aviso
El sistema SHALL exponer `GET /api/v1/avisos/{id}` que devuelve el detalle de un aviso específico. El aviso debe ser visible para el usuario según las reglas de alcance.

#### Scenario: Obtener detalle de aviso visible
- **WHEN** un ALUMNO envía `GET /api/v1/avisos/{id}` donde el aviso es Global y vigente
- **THEN** el sistema devuelve HTTP 200 con el detalle completo del aviso

#### Scenario: Obtener detalle de aviso no visible por alcance
- **WHEN** un ALUMNO envía `GET /api/v1/avisos/{id}` donde el aviso es `PorMateria` y el alumno no está asignado a esa materia
- **THEN** el sistema devuelve HTTP 404 (el aviso no es visible para este usuario)

#### Scenario: Obtener detalle de aviso eliminado
- **WHEN** un ADMIN envía `GET /api/v1/avisos/{id}` de un aviso eliminado (soft delete)
- **THEN** el sistema devuelve HTTP 404 Not Found

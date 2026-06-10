## ADDED Requirements

### Requirement: System SHALL support (propio) scope on permissions
The RolPermiso model SHALL include a `scope` field with values "global" or "propio". When a permission has scope "propio", the system SHALL ensure the user can only access resources that belong to them. The `require_permission` dependency SHALL accept an optional `scope_check` parameter. When provided, the system SHALL pass the current user's ID to the service/repository layer so it can filter resources by ownership.

#### Scenario: Permission with global scope allows access to all resources
- **WHEN** a COORDINADOR with "atrasados:ver" (scope="global") accesses atrasados of any professor's commission
- **THEN** the request is permitted (the service layer returns all matching records)

#### Scenario: Permission with scope propio filters by user
- **WHEN** a PROFESOR with "atrasados:ver" (scope="propio") accesses atrasados
- **THEN** the service layer filters results to only show atrasados for commissions where the PROFESOR is assigned as teacher

#### Scenario: Scope propio prevents accessing other user's data
- **WHEN** a PROFESOR with "calificaciones:importar" (scope="propio") tries to import calificaciones for another professor's commission
- **THEN** the service layer rejects with HTTP 403 or returns empty results (filtered by ownership)

---

### Requirement: System SHALL provide helper to check scope in services
The system SHALL provide `get_effective_scope(permission_codename, user_id)` that returns "global" or "propio" based on the user's RolPermiso entries for that permission. Services SHALL use this to decide whether to apply ownership filters.

#### Scenario: Check scope returns "propio" for PROFESOR's permission
- **WHEN** a PROFESOR's "calificaciones:importar" permission has scope="propio" in RolPermiso
- **THEN** `get_effective_scope("calificaciones:importar", profesor_id)` returns "propio"

#### Scenario: Check scope returns "global" for COORDINADOR's permission
- **WHEN** a COORDINADOR's "atrasados:ver" permission has scope="global" in RolPermiso
- **THEN** `get_effective_scope("atrasados:ver", coordinador_id)` returns "global"

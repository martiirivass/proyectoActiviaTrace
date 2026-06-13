## Why

This change establishes the foundational domain models and multi-tenancy infrastructure for the activia-trace platform. As the second change in the critical path (C-02), it builds upon C-01's foundation setup to create the core entities that all subsequent domain functionality depends on: Users, Tenants, Roles, Permissions, and their relationships. Without these models, no business logic can be implemented — authentication, authorization, academic management, communications, and liquidations all require identity and tenancy as prerequisites.

## What Changes

- **New Core Models**: User, Tenant, Role, Permission, UserRole, UserTenant entities with full SQLAlchemy 2.0 async mappings
- **Database Migrations**: Alembic migration creating all core tables with proper constraints, indexes, and foreign keys
- **Row-Level Tenancy**: `tenant_id` column on every table; repository base class enforces tenant filtering by default
- **Fine-Grained RBAC**: Permission system using `modulo:accion` format; `require_permission` decorator on all endpoints; fail-closed (403 if no explicit permission)
- **Identity Management**: Internal UUID as primary key; legajo as business attribute (never credential); Argon2id password hashing
- **Security**: AES-256 encryption for PII fields (DNI, CBU, etc.); soft delete pattern (audit append-only, no hard deletes)
- **Repositories**: Base repository with tenant-scoped queries; concrete repositories for each core entity

## Capabilities

### New Capabilities
- `core-models`: User, Tenant, Role, Permission, UserRole, UserTenant entities with relationships and constraints
- `multi-tenancy`: Row-level tenant isolation enforced at repository layer with default tenant scoping
- `rbac-fine-grained`: Permission system with `modulo:accion` format, fail-closed enforcement, endpoint decorators
- `identity-management`: UUID identity, Argon2id password hashing, legajo as business attribute
- `security-encryption`: AES-256 for PII fields, soft delete audit pattern
- `core-repositories`: Tenant-scoped repository base and concrete implementations for core entities

### Modified Capabilities
- None (no existing specs in project yet)

## Impact

- **Database**: New tables for all core entities; indexes on tenant_id, email, UUID; foreign key constraints for relationships
- **API**: New endpoints for tenant/user/role management (to be defined in subsequent changes); all future endpoints require RBAC
- **Dependencies**: Adds `argon2-cffi`, `cryptography` for encryption; uses existing `sqlalchemy`, `alembic`, `pydantic`
- **Architecture**: Establishes Clean Architecture layers (Models → Repositories → Services → Routers) for all future work
- **Testing**: Requires test database container; ≥80% line coverage, ≥90% business rule coverage mandatory
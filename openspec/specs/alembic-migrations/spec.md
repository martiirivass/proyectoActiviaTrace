# alembic-migrations Specification

## Purpose
TBD - created by archiving change core-models-y-tenancy. Update Purpose after archive.
## Requirements
### Requirement: Alembic configured for async SQLAlchemy with PostgreSQL
The system SHALL provide Alembic configuration supporting async migrations:
- `alembic.ini` in `backend/alembic/`
- `env.py` configured for async SQLAlchemy engine (asyncpg driver)
- Migration files in `backend/alembic/versions/`
- Naming convention: `V{number:03d}_{description}.py` (e.g., `V001_create_tenant.py`)

#### Scenario: Migration 001 creates tenant table
- **WHEN** running `alembic upgrade head` from clean database
- **THEN** `tenant` table is created with all columns from Tenant model

#### Scenario: Migration 001 creates indexes on tenant table
- **WHEN** Migration 001 is applied
- **THEN** indexes exist on: `slug` (unique), `estado`, `deleted_at`

#### Scenario: Migration files follow naming convention
- **WHEN** listing migration files
- **THEN** all files match pattern `V###_*.py` with sequential numbers

#### Scenario: Async engine used for migrations
- **WHEN** running alembic commands
- **THEN** asyncpg driver is used, no blocking sync calls

### Requirement: One migration per schema change
The system SHALL enforce the convention that each logical schema change corresponds to exactly one migration file.

#### Scenario: Adding a new model generates one migration
- **WHEN** a new domain model is added (e.g., Carrera in C-06)
- **THEN** exactly one migration file is created for that change

#### Scenario: Modifying a model generates one migration
- **WHEN** an existing model is modified (e.g., adding column to Usuario)
- **THEN** exactly one migration file is created for that change


## 1. Modelos

- [x] 1.1 Crear modelo `Carrera` (id, tenant_id, codigo, nombre, estado — hereda SoftDeleteMixin)
- [x] 1.2 Crear modelo `Cohorte` (id, tenant_id, carrera_id FK, nombre, anio, vig_desde, vig_hasta, estado — hereda SoftDeleteMixin)
- [x] 1.3 Crear modelo `Materia` (id, tenant_id, codigo, nombre, estado — hereda SoftDeleteMixin)
- [x] 1.4 Crear modelo `Dictado` (id, tenant_id, materia_id FK, carrera_id FK, cohorte_id FK, nombre — hereda SoftDeleteMixin)
- [x] 1.5 Registrar los 4 modelos en `backend/app/models/__init__.py`

## 2. Migración

- [x] 2.1 Crear migration 005 con tablas `carreras`, `cohortes`, `materias`, `dictados`
- [x] 2.2 Índices: unique `(tenant_id, codigo)` en carreras, unique `(tenant_id, carrera_id, nombre)` en cohortes, unique `(tenant_id, codigo)` en materias, unique `(tenant_id, materia_id, cohorte_id)` en dictados
- [x] 2.3 FKs: cohortes.carrera_id → carreras.id, dictados.materia_id → materias.id, dictados.carrera_id → carreras.id, dictados.cohorte_id → cohortes.id

## 3. Repositorios

- [x] 3.1 Crear `CarreraRepository` (scoped, con búsqueda por código)
- [x] 3.2 Crear `CohorteRepository` (scoped, con búsqueda por nombre+carrera, filtro por carrera)
- [x] 3.3 Crear `MateriaRepository` (scoped, con búsqueda por código)
- [x] 3.4 Crear `DictadoRepository` (scoped, con búsqueda por materia+cohorte, filtro por materia/cohorte)

## 4. Schemas

- [x] 4.1 Crear schemas `CarreraCreate`, `CarreraUpdate`, `CarreraResponse`, `CarreraList`
- [x] 4.2 Crear schemas `CohorteCreate`, `CohorteUpdate`, `CohorteResponse`, `CohorteList`
- [x] 4.3 Crear schemas `MateriaCreate`, `MateriaUpdate`, `MateriaResponse`, `MateriaList`
- [x] 4.4 Crear schemas `DictadoCreate`, `DictadoUpdate`, `DictadoResponse`, `DictadoList`

## 5. Servicios

- [x] 5.1 Crear `CarreraService` con CRUD + validación de código único
- [x] 5.2 Crear `CohorteService` con CRUD + validación: carrera activa, nombre único por carrera
- [x] 5.3 Crear `MateriaService` con CRUD + validación de código único
- [x] 5.4 Crear `DictadoService` con CRUD + validación: combinación materia-cohorte única

## 6. Routers

- [x] 6.1 Crear router `/api/v1/admin/carreras` con ABM + permiso `estructura:gestionar`
- [x] 6.2 Crear router `/api/v1/admin/cohortes` con ABM + permiso `estructura:gestionar`
- [x] 6.3 Crear router `/api/v1/admin/materias` con ABM + permiso `estructura:gestionar`
- [x] 6.4 Crear router `/api/v1/admin/dictados` con ABM + permiso `estructura:gestionar`
- [x] 6.5 Registrar los 4 routers en `backend/app/main.py`

## 7. Tests

- [x] 7.1 Tests CRUD carrera (crear, listar, obtener, actualizar, soft delete)
- [x] 7.2 Tests: código duplicado en carrera ✔, mismo código en distinto tenant ✔
- [x] 7.3 Tests CRUD cohorte
- [x] 7.4 Tests: cohorte con carrera inactiva → error
- [x] 7.5 Tests: nombre duplicado en misma carrera
- [x] 7.6 Tests CRUD materia
- [x] 7.7 Tests: código duplicado en materia
- [x] 7.8 Tests CRUD dictado
- [x] 7.9 Tests: combinación materia-cohorte duplicada en dictado
- [x] 7.10 Tests: multi-tenant aislamiento (cada tenant solo ve sus datos)
- [x] 7.11 Tests: 403 sin permiso `estructura:gestionar`
- [x] 7.12 Tests: soft delete — registro marcado como eliminado, no retorna en list/get

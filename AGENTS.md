# activia-trace — Instrucciones para Agentes

> Este archivo (y su copia `CLAUDE.md`) es lo PRIMERO que todo agente lee al entrar al repo.
> Generado a partir de `knowledge-base/`, `docs/ARQUITECTURA.md` y `CHANGES.md`. No editar a mano sin re-sincronizar ambos archivos.

**activia-trace** es una plataforma de gestión académica y trazabilidad multi-tenant que opera como capa de orquestación sobre Moodle: consolida calificaciones, detecta atrasos, gestiona comunicación saliente con aprobación, equipos docentes, encuentros, coloquios, liquidaciones de honorarios y auditoría completa. Cada institución es un tenant aislado; el nombre del producto es *trace* — todo audita.

Todos los 24 changes del roadmap original (C-01 a C-24) están **completados y archivados**. El proyecto se encuentra en estado de mantenimiento, correcciones y mejoras incrementales.

---

## Stack Tecnológico

Detalle completo en [docs/ARQUITECTURA.md §2](docs/ARQUITECTURA.md). Resumen funcional en [knowledge-base/02_descripcion_general.md](knowledge-base/02_descripcion_general.md).

### Backend
| Componente | Tecnología | Notas |
|------------|-----------|-------|
| Lenguaje | **Python 3.12** | snake_case en todo |
| Framework | **FastAPI** | API REST async |
| ORM | **SQLAlchemy 2.0** (async) | Queries SOLO en repositories |
| Migraciones | **Alembic** | Una migración por cambio de schema; 19 migraciones aplicadas |
| Base de datos | **PostgreSQL** | JSONB para criterios/scores configurables |
| Validación | **Pydantic v2** | DTOs request/response; `extra='forbid'` |
| Auth | **JWT** (access corto + refresh rotation) + **Argon2id** | hashing de passwords |
| 2FA | **TOTP** (pyotp + QR) | Opcional por usuario; enrolar + verificar |
| Cifrado en reposo | **AES-256** (cryptography) | PII sensible (CBU, DNI) y secretos |
| Background jobs | **Worker async** | cola de comunicaciones (Pend→Send→OK/Fail / Pend→Canc) |
| Integraciones | **N8N** + **Moodle Web Services** | cliente dedicado `moodle_ws.py` |
| Testing | **pytest** + coverage | ≥80% líneas, ≥90% reglas de negocio |

### Frontend
| Componente | Tecnología | Notas |
|------------|-----------|-------|
| Framework | **React 18** + **TypeScript** | Sin `any`, sin class components |
| Bundler | **Vite** | HMR en dev |
| Server state | **TanStack Query** | Todo fetch pasa por hooks de `services/` |
| Forms | **React Hook Form + Zod** | Validación tipada |
| Estilos | **Tailwind CSS** | Sin CSS modules, sin inline (salvo valores dinámicos) |
| HTTP | **Axios** | Cliente centralizado en `@/shared/services/api` |
| Estructura | **Feature-based modules** | `features/{name}/{components,hooks,services,types,pages}` |

### Infraestructura
| Componente | Tecnología |
|------------|-----------|
| Contenedores | **Docker** + docker-compose (local y prod) |
| Deploy | **Easypanel** |
| Observabilidad | Logs estructurados JSON + **OpenTelemetry** |
| CI/CD | **GitHub Actions** (`ci.yml`) — lint (ruff), test (pytest), build |

---

## Base de Conocimiento

La fuente de verdad del dominio vive en `knowledge-base/` (agnóstica de tecnología). El detalle técnico vive en `docs/`. **Leé el archivo relevante ANTES de implementar.**

| Archivo | Cuándo leerlo |
|---------|---------------|
| [01_vision_y_objetivos.md](knowledge-base/01_vision_y_objetivos.md) | Entender propósito y alcance |
| [02_descripcion_general.md](knowledge-base/02_descripcion_general.md) | Sistema, integraciones, propiedades de seguridad |
| [03_actores_y_roles.md](knowledge-base/03_actores_y_roles.md) | Auth, RBAC, permisos, matriz de capacidades, impersonación |
| [04_modelo_de_datos.md](knowledge-base/04_modelo_de_datos.md) | Entidades, ERD, migraciones |
| [05_reglas_de_negocio.md](knowledge-base/05_reglas_de_negocio.md) | Reglas codificadas (RN-XX) |
| [06_funcionalidades.md](knowledge-base/06_funcionalidades.md) | Funcionalidades por épica |
| [07_flujos_principales.md](knowledge-base/07_flujos_principales.md) | Flujos E2E (importación, mensajería, auth) |
| [08_arquitectura_propuesta.md](knowledge-base/08_arquitectura_propuesta.md) | Patrones y estructura de producto |
| [09_decisiones_y_supuestos.md](knowledge-base/09_decisiones_y_supuestos.md) | Decisiones cerradas y supuestos base |
| [10_preguntas_abiertas.md](knowledge-base/10_preguntas_abiertas.md) | ⚠️ Inconsistencias a resolver ANTES de codear |
| [11_historias_de_usuario.md](knowledge-base/11_historias_de_usuario.md) | Historias (Connextra) + criterios de aceptación |
| [docs/PRD.md](docs/PRD.md) | Requerimientos de producto y RNF |
| [docs/ARQUITECTURA.md](docs/ARQUITECTURA.md) | Stack, Clean Architecture, estructura de directorios, seguridad |

> ⚠️ **Roles del dominio**: ALUMNO · TUTOR · PROFESOR · COORDINADOR · NEXO · ADMIN · FINANZAS. Leé `03_actores_y_roles.md` para internalizar el modelo de permisos ANTES de cualquier implementación.

> ⚠️ **Preguntas ALTA pendientes** (resolver antes de tocar el dominio afectado): **PA-01** catálogo de materias (Materia vs InstanciaDictado), **PA-07** cohortes ↔ carrera, **PA-22**/**PA-23** claves de Plus y acumulación en liquidaciones, **PA-25** semántica del rol NEXO. Ver [10_preguntas_abiertas.md](knowledge-base/10_preguntas_abiertas.md). No modifiques el módulo de liquidaciones (C-18) sin cerrar las preguntas que lo bloquean.

---

## Memoria Persistente — Engram

El proyecto utiliza **Engram** para preservar decisiones, descubrimientos y progreso entre sesiones. Los datos de memoria se versionan en `.engram/`.

**Protocolo obligatorio para todo agente:**

1. **Antes de empezar**: ejecutá `engram sync --import` (si hay datos nuevos en `.engram/chunks/`) y usá `mem_context` / `mem_search` para recuperar contexto de sesiones previas.
2. **Después de decisiones significativas**: guardá con `mem_save` usando `topic_key: "opsx/{change-name}/{phase}"`.
3. **Al cerrar sesión**: ejecutá `mem_session_summary` para que la próxima sesión no arranque ciega.
4. **Al pushear**: sincronizá el proyecto memory con `engram sync` antes de `git push` (sin `--all` para no filtrar datos de otros proyectos).

---

## Skills Disponibles

Cargá la skill correspondiente al contexto **ANTES** de escribir código. Aplicá todos sus patrones.

### Skills del proyecto (`.agents/skills/` y `.claude/skills/`)

| Agente | Rol | Skills |
|--------|-----|--------|
| **Backend** | FastAPI / SQLAlchemy / migraciones / testing | `fastapi-templates`, `python-testing-patterns`, `test-driven-development` |
| **Frontend** | React / TanStack / Tailwind / componentes | `tailwind-design-system`, `dashboard-crud-page`, `help-system-content` |
| **Documentación** | KB, roadmap, instrucciones para agentes | `kb-creator` |
| **OPSX** | Proponer, implementar y archivar cambios | `openspec-explore`, `openspec-propose`, `openspec-apply-change`, `openspec-archive-change` |

### Skills globales disponibles (registradas en el sistema)

| Skill | Cuándo usarla |
|-------|---------------|
| `find-skill` | Descubrir qué skill existe para una tarea |
| `skill-registry` | Registrar skills nuevas en el proyecto |
| `roadmap-generator` | Generar/actualizar CHANGES.md |
| `agent-instruction` / `agents-md-generator` | Generar/actualizar AGENTS.md y CLAUDE.md |
| `openspec-init` | Inicializar OPSX en un proyecto nuevo |
| `openspec-design` | Crear diseño técnico para un change |
| `openspec-spec` | Escribir especificaciones |
| `openspec-tasks` | Crear checklist de tareas |
| `openspec-verify` | Validar implementación contra specs |
| `openspec-onboard` | Walkthrough guiado del flujo OPSX |
| `judgment-day` | Revisión adversarial paralela de código |
| `skill-creator` | Crear o modificar skills |
| `react-best-practices` | Buenas prácticas React (disponible global) |
| `modern-web-development` | Desarrollo web moderno (disponible global) |

> **Nota**: El proyecto está completo. Para cambios nuevos usá `/opsx:propose` → implementación → `/opsx:archive`. Para correcciones rápidas podés aplicar el cambio directamente.

---

## Roadmap de Changes

Los **24 changes originales** (`C-01`…`C-24`) están **completados y archivados** en `openspec/changes/archive/`. Ver [CHANGES.md](CHANGES.md) para la descripción detallada de cada uno.

### Resumen de lo implementado

| Fase | Cambio | Estado |
|------|--------|--------|
| FASE 0 — Cimiento | C-01 foundation-setup | ✅ Archivado |
| FASE 1 — Seguridad | C-02 core-models-y-tenancy, C-03 auth-jwt-2fa, C-04 rbac-permisos-finos, C-05 audit-log | ✅ Archivados |
| FASE 2 — Entidades | C-06 estructura-academica | ✅ Archivado |
| FASE 3 — Usuarios | C-07 usuarios-y-asignaciones, C-17 programas-y-fechas-academicas | ✅ Archivados |
| FASE 4 — Dominio | C-08 a C-20 (equipos, padron, calificaciones, análisis, comunicaciones, encuentros, evaluaciones, avisos, tareas, liquidaciones, auditoría, perfil) | ✅ Archivados |
| FASE 5 — Frontend | C-21 a C-24 (shell-auth, academico, coordinacion, finanzas-admin) | ✅ Archivados |

### Próximos pasos posibles

- Correcciones de rutas o bugs (`fix/` branches)
- Mejoras incrementales (`/opsx:propose`)
- Pendientes de dominio (PA-22, PA-23, etc.) cuando FINANZAS cierre las definiciones

**Antes de cualquier `/opsx:propose`**: leé [CHANGES.md](CHANGES.md) para entender qué ya existe, identificá si afecta a un change archivado y leé los archivos KB correspondientes.

---

## Reglas Duras (no negociables)

Estas reglas son **contrato**. Romperlas es un defecto, no una decisión de estilo. Ante conflicto entre la KB y este archivo, prevalecen las reglas duras.

### Generales
1. **No buildear automático.** Nunca ejecutar build/compile/bundle sin pedido explícito del usuario.
2. **No commitear sin pedido explícito.** `git add`/`commit`/`push` SOLO cuando el usuario lo pide. Si estás en la rama default, ramificá antes.
3. **Conventional Commits sin `Co-Authored-By`.** Formato `tipo(scope): mensaje`. Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`. Scopes: `auth`, `tenancy`, `users`, `alumnos`, `materias`, `comisiones`, `entregas`, `comunicacion`, `equipos`, `encuentros`, `coloquios`, `liquidaciones`, `auditoria`, `moodle`, `api`, `ui`. JAMÁS agregar atribución a IA ni `Co-Authored-By`.
4. **Tests sin mocks de DB.** Usar base real o contenedor de test (DB efímera). Mockear la base de datos invalida el test — no prueba nada.
5. **Pydantic schemas con `extra='forbid'`.** Todo schema rechaza campos no declarados (`model_config = ConfigDict(extra='forbid')`).
6. **snake_case en Python.** Funciones, variables, columnas de BD, módulos y paquetes.
7. **PascalCase en componentes React.** Nombre del componente y del archivo (`ProductCard.tsx`). Sin `any`, sin class components.

### Seguridad y arquitectura (fundacionales — fallan en code review)
8. **Identidad SIEMPRE desde la sesión** (JWT verificado). JAMÁS desde un parámetro de URL, body, header ni cualquier dato de la petición. Esto define quién es el usuario, sus roles y su tenant. Sin excepciones.
9. **Multi-tenancy row-level.** `tenant_id` en cada tabla; los repositories filtran por tenant **por defecto**. Un query sin scope de tenant es un bug que falla en code review.
10. **RBAC fino `modulo:accion`**, no flags binarios ni superusuario. Cada endpoint declara `require_permission(...)`. **Fail-closed**: sin permiso explícito → 403.
11. **Nunca lógica de negocio en Routers.** Nunca acceso directo a DB desde Services (siempre vía Repository). Flujo unidireccional Routers → Services → Repositories → Models.
12. **Secretos y PII (CBU, DNI) SIEMPRE AES-256.** Passwords con Argon2id. Nunca texto plano.
13. **Soft delete siempre** (auditoría append-only). Nunca hard delete.
14. **Identidad por UUID interno.** El legajo es un atributo de negocio, nunca credencial ni selector de sesión.
15. **≤500 LOC por archivo backend**, componentes React <200 LOC. Una migración Alembic por cambio de schema.
16. **Cobertura mínima**: ≥80% líneas, ≥90% reglas de negocio. **Strict TDD**: test que falla → código mínimo → triangulación → refactor.

---

## Arquitectura del Sistema — Interacción de Componentes

```
┌──────────────┐     HTTP/REST      ┌─────────────────────────────────────┐
│   Frontend   │ ──────────────────► │              Backend API            │
│  (React+TS)  │ ◄────────────────── │           (FastAPI + Py3.12)        │
│              │     JSON + JWT      │                                     │
│  features/   │                     │  routers/ → services/ → repos/      │
│   auth/      │                     │         → models/ → PostgreSQL      │
│   academico/ │                     │                                     │
│   admin/     │                     │  core/ (auth, config, security,     │
│   coordinacion/                     │         database, dependencies)     │
│   finanzas/  │                     │                                     │
└──────────────┘                     │  integrations/ (moodle_ws)          │
                                     │                                     │
                                     │  workers/ (cola de comunicaciones)  │
                                     └──────────┬──────────────────────────┘
                                                │
                                                ▼
                                     ┌──────────────────┐
                                     │    PostgreSQL    │
                                     │  (multi-tenant)  │
                                     └──────────────────┘
```

**Flujo de autenticación:**
1. Frontend envía credentials → `POST /api/auth/login`
2. Backend valida contra BD, genera JWT (access 15min + refresh rotation)
3. Si el usuario tiene 2FA habilitado → gate TOTP antes de emitir sesión
4. Frontend almacena tokens, Axios interceptor refresca transparentemente
5. Cada request valida JWT → extrae `user_id`, `tenant_id`, `roles` → `get_current_user`

**Flujo de autorización:**
1. Cada endpoint declara `require_permission("modulo:accion")`
2. El guard resuelve permisos efectivos del usuario (unión de sus roles, filtrados por tenant)
3. Sin permiso → 403. Fail-closed.

**Multi-tenancy:**
- Aislamiento row-level: `tenant_id` en cada tabla
- Repository base scoped: toda query filtrada por `tenant_id` automáticamente
- Identidad y tenant resueltos exclusivamente del JWT verificado

---

## Agent Governance — Autonomía por dominio

La autonomía del agente depende de la criticidad del dominio que toca.

| Nivel | Dominios | Comportamiento |
|-------|----------|----------------|
| **CRÍTICO** | auth, multi-tenancy, RBAC, audit log, liquidaciones, core-models | Solo análisis y propuesta. NO escribir código sin aprobación humana explícita. |
| **ALTO** | equipos-docentes, comunicaciones, panel auditoría | Proponer y esperar revisión antes de escribir. |
| **MEDIO** | lógica de dominio, integraciones (Moodle/N8N), pipelines | Implementar con checkpoints; surfacear decisiones no obvias para revisión. |
| **BAJO** | CRUDs simples, pages frontend sin lógica crítica, catálogos, configuración | Autonomía total si pasan los tests. Reportar en el resumen. |

Antes de cualquier acción no trivial: identificá el nivel de governance del dominio. En CRÍTICO o sus equivalentes de seguridad, describí el cambio planeado y esperá confirmación antes de escribir.

---

## Flujo de Trabajo

```
Para cambios nuevos:
  1. /opsx:explore [tema]          → explorar / pensar (opcional)
  2. /opsx:propose <nombre>        → crear proposal + design + specs + tasks
  3. /opsx:apply <nombre>          → implementar tasks (Strict TDD)
  4. /opsx:archive <nombre>        → sync specs + archivar

Para correcciones rápidas:
  1. Leer la KB relevante + docs    → entender el dominio
  2. Identificar el alcance         → afecta change archivado?
  3. Verificar governance           → CRÍTICO/ALTO = propuesta primero
  4. Implementar (Strict TDD)       → respetando las reglas duras
  5. ejectuar tests                 → pytest en backend
  6. git commit convencional        → solo cuando el usuario lo pida
```

Aplicá TODAS las reglas duras en cada paso. Ante conflicto entre la KB y este archivo, las reglas duras prevalecen.

---

## Testing

- Framework: **pytest** con base de datos real (sin mocks de DB)
- Tests en `backend/tests/`
- Para ejecutar: `docker compose exec api python -m pytest`
- Cobertura mínima: ≥80% líneas, ≥90% reglas de negocio
- **Strict TDD**: test que falla → código mínimo → triangulación → refactor

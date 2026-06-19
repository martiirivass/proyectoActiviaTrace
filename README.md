# activia-trace

> Plataforma de gestión académica y trazabilidad multi-tenant.
> Capa de orquestación sobre Moodle para consolidar calificaciones, detectar atrasos, gestionar comunicación, equipos docentes, liquidaciones y auditoría.

---

## Stack

| Capa | Tecnología |
|------|-----------|
| Backend | Python 3.13 · FastAPI · SQLAlchemy 2.0 async · PostgreSQL |
| Frontend | React 18 · TypeScript · Vite · TanStack Query · Tailwind CSS |
| Infra | Docker · docker-compose · Easypanel |

## Requisitos

- Docker Desktop
- Node.js 20+ (para frontend en dev)

## Inicio rápido

```bash
# 1. Clonar
git clone https://github.com/martiirivass/proyectoActiviaTrace.git
cd proyectoActiviaTrace

# 2. Levantar backend
docker compose up -d

# 3. Correr migraciones (la primera vez)
docker compose exec api alembic upgrade head

# 4. Poblar con datos de desarrollo
docker compose exec api python scripts/seed_dev.py

# 5. Levantar frontend (en otra terminal)
cd frontend
npm install
npm run dev
```

### Usuarios de prueba

| Email | Contraseña | Rol |
|-------|-----------|-----|
| admin@admin.com | admin123 | ADMIN |
| profesor@test.com | profesor123 | PROFESOR |

## Arquitectura

```
Backend (FastAPI)
├── api/v1/endpoints/   → Routers (solo validación)
├── services/           → Lógica de negocio
├── repositories/       → Queries SQLAlchemy (scope tenant siempre activo)
├── models/             → SQLAlchemy models
├── schemas/            → Pydantic v2 (extra='forbid')
├── core/               → Security, database, config
├── integrations/       → Moodle WS, N8N
└── workers/            → Cola asíncrona de comunicaciones

Frontend (React 18 + TypeScript + Vite)
└── src/features/       → Módulos feature-based
    ├── academico/      → Docente: calificaciones, atrasados, comunicaciones
    ├── coordinacion/   → Equipos, avisos, tareas, monitores
    ├── finanzas/       → Liquidaciones, facturas, grilla salarial
    └── admin/          → Estructura, usuarios, auditoría
```

## Documentación

- [Base de conocimiento](knowledge-base/) — qué hace el sistema (11 archivos)
- [Arquitectura](docs/ARQUITECTURA.md) — decisiones técnicas y patrones
- [Roadmap](CHANGES.md) — 24 módulos (C-01 a C-24)
- [Reporte académico](docs/REPORTE_PRESENTACION.md) — análisis completo del proyecto

## Metodología

El proyecto se desarrolló con **OPSX** (Open Spec-Driven Development): cada funcionalidad se especifica, diseña, implementa y archiva siguiendo un flujo de 4 pasos. Se utilizaron **39 skills de IA** para estandarizar la codificación, **Strict TDD** en toda la implementación, y **Engram** como memoria persistente del equipo.

Ver [AGENTS.md](AGENTS.md) para las reglas y flujo de trabajo completo.

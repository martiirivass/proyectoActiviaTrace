from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.core.observability import init_opentelemetry
from app.core.database import engine
from app.api.v1.routers import audit, auth, health
from app.api.v1.routers.padron import router as padron_router
from app.api.v1.routers.calificaciones import router as calificaciones_router
from app.api.v1.routers.admin_asignaciones import asignaciones_router
from app.api.v1.routers.equipos import equipos_router
from app.api.v1.routers.admin_estructura import (
    carreras_router,
    cohortes_router,
    dictados_router,
    materias_router,
)
from app.api.v1.routers.admin_usuarios import usuarios_router
from app.api.v1.routers.analisis import router as analisis_router
from app.api.v1.routers.comunicaciones import router as comunicaciones_router
from app.api.v1.routers.encuentros import router as encuentros_router
from app.api.v1.routers.guardias import router as guardias_router
from app.api.v1.routers.evaluaciones import router as evaluaciones_router
from app.api.v1.routers.avisos import router as avisos_router
from app.api.v1.routers.tareas import router as tareas_router
from app.api.v1.routers.programas import programas_router
from app.api.v1.routers.fechas_academicas import fechas_router
from app.api.v1.routers.grilla_salarial import router as grilla_salarial_router
from app.api.v1.routers.liquidaciones import router as liquidaciones_router
from app.api.v1.routers.facturas import router as facturas_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    init_opentelemetry(app)
    yield
    await engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="activia-trace API",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.include_router(health.router)
    app.include_router(auth.router, prefix="/api/v1/auth")
    app.include_router(audit.router, prefix="/api/v1/audit")

    app.include_router(carreras_router)
    app.include_router(cohortes_router)
    app.include_router(materias_router)
    app.include_router(dictados_router)

    app.include_router(usuarios_router)
    app.include_router(asignaciones_router)
    app.include_router(equipos_router)
    app.include_router(padron_router)
    app.include_router(calificaciones_router)
    app.include_router(analisis_router)
    app.include_router(comunicaciones_router)
    app.include_router(encuentros_router)
    app.include_router(guardias_router)
    app.include_router(evaluaciones_router)
    app.include_router(avisos_router)
    app.include_router(tareas_router)
    app.include_router(programas_router)
    app.include_router(fechas_router)
    app.include_router(grilla_salarial_router)
    app.include_router(liquidaciones_router)
    app.include_router(facturas_router)

    return app


app = create_app()
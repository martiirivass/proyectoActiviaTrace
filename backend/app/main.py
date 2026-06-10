from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.core.observability import init_opentelemetry
from app.core.database import engine
from app.api.v1.routers import audit, auth, health
from app.api.v1.routers.admin_asignaciones import asignaciones_router
from app.api.v1.routers.admin_estructura import (
    carreras_router,
    cohortes_router,
    dictados_router,
    materias_router,
)
from app.api.v1.routers.admin_usuarios import usuarios_router


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

    return app


app = create_app()
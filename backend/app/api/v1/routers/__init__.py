from app.api.v1.routers.avisos import router as avisos_router
from app.api.v1.routers.facturas import router as facturas_router
from app.api.v1.routers.grilla_salarial import router as grilla_salarial_router
from app.api.v1.routers.liquidaciones import router as liquidaciones_router

__all__ = [
    "avisos_router",
    "facturas_router",
    "grilla_salarial_router",
    "liquidaciones_router",
]

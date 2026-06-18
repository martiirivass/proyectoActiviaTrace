from app.repositories.encuentro_repository import (
    InstanciaEncuentroRepository,
    SlotEncuentroRepository,
)
from app.repositories.guardia_repository import GuardiaRepository
from app.repositories.evaluacion_repository import (
    EvaluacionRepository,
    DiaConvocatoriaRepository,
    EvaluacionAlumnoRepository,
)
from app.repositories.reserva_repository import ReservaRepository
from app.repositories.resultado_repository import ResultadoRepository
from app.repositories.aviso_repository import AvisoRepository
from app.repositories.acknowledgment_repository import AcknowledgmentRepository
from app.repositories.tarea_repository import TareaRepository
from app.repositories.comentario_repository import ComentarioTareaRepository
from app.repositories.programa_repository import ProgramaMateriaRepository
from app.repositories.fecha_academica_repository import FechaAcademicaRepository
from app.repositories.grilla_salarial_repository import (
    SalarioBaseRepository,
    SalarioPlusRepository,
)
from app.repositories.liquidacion_repository import LiquidacionRepository
from app.repositories.factura_repository import FacturaRepository

__all__ = [
    "SlotEncuentroRepository",
    "InstanciaEncuentroRepository",
    "GuardiaRepository",
    "EvaluacionRepository",
    "DiaConvocatoriaRepository",
    "EvaluacionAlumnoRepository",
    "ReservaRepository",
    "ResultadoRepository",
    "AvisoRepository",
    "AcknowledgmentRepository",
    "TareaRepository",
    "ComentarioTareaRepository",
    "ProgramaMateriaRepository",
    "FechaAcademicaRepository",
    "SalarioBaseRepository",
    "SalarioPlusRepository",
    "LiquidacionRepository",
    "FacturaRepository",
]

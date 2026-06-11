"""
Worker asíncrono de comunicaciones.
Polling a PostgreSQL cada WORKER_POLL_INTERVAL segundos.
Procesa comunicaciones en estado Pendiente:
  - Sin lote (individuales) → procesa directo
  - Con lote aprobado → procesa
Transición: Pendiente → Enviando → Enviado/Error
"""

import asyncio
import logging
import signal
from datetime import datetime, timezone

import aiosmtplib
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.models.comunicacion import Comunicacion, EstadoComunicacion
from app.models.lote_comunicacion import EstadoLote, LoteComunicacion

logger = logging.getLogger("activia-trace.worker")

_running = True


def _handle_sigterm(signum, frame):
    global _running
    logger.info("Received SIGTERM, shutting down gracefully...")
    _running = False


def _handle_sigint(signum, frame):
    global _running
    logger.info("Received SIGINT, shutting down gracefully...")
    _running = False


class ComunicacionWorker:
    def __init__(self, settings):
        self.settings = settings
        self.poll_interval = settings.worker_poll_interval
        self.batch_size = settings.worker_batch_size
        self.engine = create_async_engine(
            settings.database_url,
            echo=False,
            pool_pre_ping=True,
        )
        self.session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def run(self):
        logger.info(
            "Worker started: poll_interval=%ds, batch_size=%d",
            self.poll_interval,
            self.batch_size,
        )
        while _running:
            try:
                await self._process_batch()
            except Exception:
                logger.exception("Error in worker cycle")
            await asyncio.sleep(self.poll_interval)
        await self.engine.dispose()
        logger.info("Worker stopped")

    async def _process_batch(self):
        async with self.session_factory() as session:
            # Find pendientes procesables
            lote_aprobado_subq = (
                select(LoteComunicacion.id)
                .where(
                    LoteComunicacion.estado == EstadoLote.APROBADO,
                    LoteComunicacion.is_deleted == False,
                )
            ).subquery()

            stmt = (
                select(Comunicacion)
                .where(
                    Comunicacion.estado == EstadoComunicacion.PENDIENTE,
                    Comunicacion.is_deleted == False,
                    (
                        (Comunicacion.lote_id.is_(None))
                        | (Comunicacion.lote_id.in_(select(lote_aprobado_subq.c.id)))
                    ),
                )
                .limit(self.batch_size)
                .order_by(Comunicacion.created_at.asc())
            )
            result = await session.execute(stmt)
            comunicaciones = list(result.scalars().all())

            if not comunicaciones:
                logger.debug("No pendientes to process")
                return

            logger.info("Processing %d comunicaciones", len(comunicaciones))

            for comunicacion in comunicaciones:
                if not _running:
                    break
                await self._procesar_una(session, comunicacion)

            await session.commit()

    async def _procesar_una(self, session: AsyncSession, comunicacion: Comunicacion):
        """Process a single communication: Enviando → send → Enviado/Error."""
        # Mark as Enviando
        comunicacion.estado = EstadoComunicacion.ENVIANDO
        await session.flush()

        try:
            await self._enviar_email(comunicacion)
            comunicacion.estado = EstadoComunicacion.ENVIADO
            comunicacion.enviado_at = datetime.now(timezone.utc)
            logger.info(
                "Enviado OK: id=%s, destinatario=%s",
                comunicacion.id,
                self._mask_email(comunicacion.destinatario),
            )
        except Exception as e:
            comunicacion.estado = EstadoComunicacion.ERROR
            comunicacion.error_msg = str(e)[:1000]
            logger.error(
                "Error enviando: id=%s, error=%s",
                comunicacion.id,
                str(e),
            )

    async def _enviar_email(self, comunicacion: Comunicacion):
        """Send email via SMTP using aiosmtplib."""
        message = (
            f"From: {self.settings.smtp_from_address}\r\n"
            f"To: {comunicacion.destinatario}\r\n"
            f"Subject: {comunicacion.asunto}\r\n"
            f"MIME-Version: 1.0\r\n"
            f"Content-Type: text/plain; charset=\"utf-8\"\r\n"
            f"\r\n"
            f"{comunicacion.cuerpo}"
        )

        if self.settings.smtp_use_tls:
            await aiosmtplib.send(
                message,
                hostname=self.settings.smtp_host,
                port=self.settings.smtp_port,
                username=self.settings.smtp_user or None,
                password=self.settings.smtp_password or None,
                use_tls=True,
            )
        else:
            await aiosmtplib.send(
                message,
                hostname=self.settings.smtp_host,
                port=self.settings.smtp_port,
                username=self.settings.smtp_user or None,
                password=self.settings.smtp_password or None,
                starttls=False,
            )

    @staticmethod
    def _mask_email(email: str) -> str:
        if "@" not in email:
            return email
        local, dominio = email.split("@", 1)
        if len(local) <= 4:
            prefix = local[:1]
        else:
            prefix = local[:4]
        return f"{prefix}***@{dominio}"


async def main():
    signal.signal(signal.SIGTERM, _handle_sigterm)
    signal.signal(signal.SIGINT, _handle_sigint)

    settings = get_settings()
    worker = ComunicacionWorker(settings)
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())

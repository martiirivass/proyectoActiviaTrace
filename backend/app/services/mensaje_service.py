import uuid
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mensaje import Mensaje
from app.repositories.mensaje_repository import MensajeRepository
from app.schemas.mensajes import HiloResponse, MensajeResponse


class MensajeService:
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.repo = MensajeRepository(Mensaje, session, tenant_id)
        self.tenant_id = tenant_id

    async def send_message(
        self,
        remitente_id: UUID,
        destinatario_id: UUID,
        asunto: str,
        cuerpo: str,
    ) -> Mensaje:
        # Verify destinatario exists in same tenant and is not deleted
        destinatario = await self.repo.find_destinatario_en_tenant(destinatario_id)
        if destinatario is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Destinatario no encontrado",
            )

        # Generate new hilo_id for the thread
        hilo_id = uuid.uuid4()

        mensaje = await self.repo.create(
            hilo_id=hilo_id,
            remitente_id=remitente_id,
            destinatario_id=destinatario_id,
            asunto=asunto,
            cuerpo=cuerpo,
            leido=False,
        )
        return mensaje

    async def get_inbox(
        self, user_id: UUID, offset: int = 0, limit: int = 50
    ) -> list[HiloResponse]:
        hilos_data = await self.repo.find_hilos(user_id, offset=offset, limit=limit)

        result = []
        for hilo in hilos_data:
            msg = hilo["mensaje"]
            result.append(HiloResponse(
                hilo_id=msg.hilo_id,
                remitente_id=msg.remitente_id,
                remitente_nombre=hilo["remitente_nombre"],
                asunto=msg.asunto,
                ultimo_mensaje=msg.cuerpo[:200] if msg.cuerpo else "",
                ultima_fecha=msg.created_at,
                no_leidos=hilo["no_leidos"],
            ))
        return result

    async def get_hilo(self, hilo_id: UUID, user_id: UUID) -> list[Mensaje]:
        messages = await self.repo.find_mensajes_por_hilo(hilo_id, user_id)
        if not messages:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Hilo no encontrado",
            )

        # Mark all messages as read for this user
        await self.repo.marcar_hilo_leido(hilo_id, user_id)

        return messages

    async def respond_to_hilo(
        self, hilo_id: UUID, remitente_id: UUID, cuerpo: str
    ) -> Mensaje:
        # Verify access by checking if user is participant
        messages = await self.repo.find_mensajes_por_hilo(hilo_id, remitente_id)
        if not messages:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Hilo no encontrado",
            )

        # Find the latest message to determine recipient (auto-swap)
        last_msg = await self.repo.get_hilo_ultimo_mensaje(hilo_id)
        if last_msg is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Hilo no encontrado",
            )

        # Determine recipient: if user was the last recipient, swap roles
        if last_msg.destinatario_id == remitente_id:
            nuevo_destinatario = last_msg.remitente_id
        else:
            nuevo_destinatario = last_msg.destinatario_id

        # Get the asunto from the first message of the hilo
        asunto = messages[0].asunto

        reply = await self.repo.create(
            hilo_id=hilo_id,
            remitente_id=remitente_id,
            destinatario_id=nuevo_destinatario,
            asunto=asunto,
            cuerpo=cuerpo,
            leido=False,
        )
        return reply

    async def count_no_leidos(self, user_id: UUID) -> int:
        return await self.repo.count_no_leidos(user_id)

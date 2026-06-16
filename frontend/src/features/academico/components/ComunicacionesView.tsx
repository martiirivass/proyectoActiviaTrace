import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { Alert } from '@/shared/components/ui/Alert'
import { FormularioRedaccion } from './FormularioRedaccion'
import { PreviewModal } from './PreviewModal'
import { TrackingTable } from './TrackingTable'
import {
  usePreviewComunicacion,
  useEnviarIndividual,
  useEnviarLote,
} from '@/features/academico/hooks/useComunicaciones'
import { useAtrasados } from '@/features/academico/hooks/useAtrasados'

export function ComunicacionesView() {
  const { materiaId } = useParams<{ materiaId: string }>()
  const [selectedIds, setSelectedIds] = useState<string[]>([])
  const [showPreview, setShowPreview] = useState(false)
  const [lastFormData, setLastFormData] = useState<{
    asunto: string
    cuerpo: string
  } | null>(null)

  const { data: atrasados } = useAtrasados(materiaId ?? '')
  const previewMutation = usePreviewComunicacion()
  const enviarIndividualMutation = useEnviarIndividual()
  const enviarLoteMutation = useEnviarLote()

  const alumnos = atrasados?.map((a) => a.alumno) ?? []

  const handlePreview = (data: {
    asunto: string
    cuerpo: string
    destinatarios: string[]
  }) => {
    if (!materiaId) return
    setLastFormData({ asunto: data.asunto, cuerpo: data.cuerpo })
    previewMutation.mutate(
      {
        asunto: data.asunto,
        cuerpo: data.cuerpo,
        materia_id: materiaId,
        destinatarios: data.destinatarios,
      },
      { onSuccess: () => setShowPreview(true) },
    )
  }

  const handleSend = () => {
    if (!materiaId || !lastFormData) return
    const payload = {
      asunto: lastFormData.asunto,
      cuerpo: lastFormData.cuerpo,
      materia_id: materiaId,
      destinatarios: selectedIds,
    }

    const mutation =
      selectedIds.length === 1
        ? enviarIndividualMutation
        : enviarLoteMutation

    mutation.mutate(payload, {
      onSuccess: () => {
        setShowPreview(false)
        setLastFormData(null)
        setSelectedIds([])
        previewMutation.reset()
      },
    })
  }

  const isSending =
    enviarIndividualMutation.isPending || enviarLoteMutation.isPending

  const sendError =
    enviarIndividualMutation.error?.message ??
    enviarLoteMutation.error?.message ??
    previewMutation.error?.message ??
    null

  return (
    <div className="space-y-8">
      <div>
        <h3 className="mb-4 text-base font-semibold text-gray-900">
          Redactar comunicación
        </h3>
        <FormularioRedaccion
          alumnos={alumnos}
          selectedIds={selectedIds}
          onSelectionChange={setSelectedIds}
          onPreview={handlePreview}
          isLoading={previewMutation.isPending}
        />
      </div>

      <div>
        <h3 className="mb-4 text-base font-semibold text-gray-900">
          Tracking de comunicaciones
        </h3>
        <TrackingTable />
      </div>

      {enviarIndividualMutation.isSuccess && (
        <Alert
          variant="success"
          message="Comunicación enviada exitosamente."
        />
      )}
      {enviarLoteMutation.isSuccess && (
        <Alert
          variant="success"
          message={`Lote de comunicaciones enviado.`}
        />
      )}

      <PreviewModal
        preview={previewMutation.data ?? null}
        isOpen={showPreview}
        isSending={isSending}
        error={sendError}
        onClose={() => {
          setShowPreview(false)
          previewMutation.reset()
        }}
        onSend={handleSend}
      />
    </div>
  )
}

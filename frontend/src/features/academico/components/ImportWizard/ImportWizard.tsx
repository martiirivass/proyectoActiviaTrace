import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { Alert } from '@/shared/components/ui/Alert'
import { UploadStep } from './UploadStep'
import { PreviewStep } from './PreviewStep'
import { ConfirmStep } from './ConfirmStep'
import { useUploadPreview, useConfirmImport } from '@/features/academico/hooks/useCalificaciones'
import type { CalificacionPreview } from '@/features/academico/types'

type Step = 'upload' | 'preview' | 'confirm'

const STEP_LABELS: Record<Step, string> = {
  upload: 'Subir archivo',
  preview: 'Vista previa',
  confirm: 'Confirmar',
}

export function ImportWizard() {
  const { materiaId, cohorteId } = useParams<{
    materiaId: string
    cohorteId: string
  }>()
  const [step, setStep] = useState<Step>('upload')
  const [preview, setPreview] = useState<CalificacionPreview | null>(null)
  const [selectedActividades, setSelectedActividades] = useState<string[]>([])
  const [uploadError, setUploadError] = useState<string | null>(null)

  const uploadMutation = useUploadPreview()
  const confirmMutation = useConfirmImport()

  const handleFileSelected = (file: File) => {
    setUploadError(null)
    const ext = '.' + file.name.split('.').pop()?.toLowerCase()
    if (!['.xlsx', '.csv'].includes(ext)) {
      setUploadError('Formato no soportado. Use archivos .xlsx o .csv')
      return
    }
    if (!materiaId || !cohorteId) return

    uploadMutation.mutate(
      { file, materiaId, cohorteId },
      {
        onSuccess: (data) => {
          setPreview(data)
          setSelectedActividades(data.actividades_detectadas.map((a) => a.id))
          setStep('preview')
        },
        onError: () => {
          setUploadError('Error al procesar el archivo. Intente nuevamente.')
        },
      },
    )
  }

  const handleConfirm = () => {
    if (!materiaId || !cohorteId || !preview) return

    confirmMutation.mutate(
      {
        materia_id: materiaId,
        cohorte_id: cohorteId,
        actividades: selectedActividades,
        parse_data: preview,
      },
      {
        onSuccess: () => setStep('confirm'),
      },
    )
  }

  const handleReset = () => {
    setStep('upload')
    setPreview(null)
    setSelectedActividades([])
    setUploadError(null)
    uploadMutation.reset()
    confirmMutation.reset()
  }

  const stepIndex = ['upload', 'preview', 'confirm'].indexOf(step)
  const steps = Object.entries(STEP_LABELS).map(([key, label]) => ({
    key,
    label,
    current: key === step,
    complete: stepIndex > ['upload', 'preview', 'confirm'].indexOf(key),
  }))

  return (
    <div className="space-y-6">
      {/* Step indicator */}
      <div className="flex items-center gap-2">
        {steps.map((s, idx) => (
          <div key={s.key} className="flex items-center gap-2">
            <span
              className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-medium ${
                s.complete || s.current
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-500'
              }`}
            >
              {s.complete ? '✓' : idx + 1}
            </span>
            <span
              className={`text-sm ${
                s.current ? 'font-medium text-blue-700' : 'text-gray-500'
              }`}
            >
              {s.label}
            </span>
            {idx < steps.length - 1 && (
              <span className="text-gray-300">—</span>
            )}
          </div>
        ))}
      </div>

      {/* Step content */}
      {step === 'upload' && (
        <UploadStep
          onFileSelected={handleFileSelected}
          isLoading={uploadMutation.isPending}
          error={uploadError}
        />
      )}

      {step === 'preview' && preview && (
        <PreviewStep
          preview={preview}
          selectedActividades={selectedActividades}
          onSelectionChange={setSelectedActividades}
        />
      )}

      {step === 'preview' && selectedActividades.length === 0 && preview && (
        <Alert
          variant="warning"
          message="Seleccioná al menos una actividad para importar."
        />
      )}

      {step === 'confirm' && preview && (
        <ConfirmStep
          preview={preview}
          selectedActividades={selectedActividades}
          isConfirming={confirmMutation.isPending}
          result={confirmMutation.data ?? null}
          error={confirmMutation.error?.message ?? null}
          onConfirm={handleConfirm}
          onBack={() => setStep('preview')}
          onReset={handleReset}
        />
      )}

      {/* Back button for preview */}
      {step === 'preview' && (
        <button
          type="button"
          onClick={() => setStep('upload')}
          className="text-sm text-blue-600 hover:text-blue-800"
        >
          ← Volver a subir archivo
        </button>
      )}
    </div>
  )
}

import { Button } from '@/shared/components/ui/Button'
import { Alert } from '@/shared/components/ui/Alert'
import type { CalificacionPreview, ImportResult } from '@/features/academico/types'

interface ConfirmStepProps {
  preview: CalificacionPreview
  selectedActividades: string[]
  isConfirming: boolean
  result: ImportResult | null
  error: string | null
  onConfirm: () => void
  onBack: () => void
  onReset: () => void
}

export function ConfirmStep({
  preview,
  selectedActividades,
  isConfirming,
  result,
  error,
  onConfirm,
  onBack,
  onReset,
}: ConfirmStepProps) {
  if (result) {
    return (
      <div className="space-y-4">
        <Alert variant="success" message="Importación completada exitosamente.">
          <p className="mt-2 text-sm">
            Registros creados: {result.registros_creados}
          </p>
        </Alert>
        <Button variant="secondary" onClick={onReset}>
          Volver a calificaciones
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-gray-200 bg-white p-6">
        <h3 className="mb-4 text-lg font-semibold text-gray-900">
          Resumen de importación
        </h3>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-500">Actividades a importar:</span>
            <span className="ml-2 font-medium text-gray-900">
              {selectedActividades.length}
            </span>
          </div>
          <div>
            <span className="text-gray-500">Alumnos afectados:</span>
            <span className="ml-2 font-medium text-gray-900">
              {preview.alumnos.length}
            </span>
          </div>
        </div>
      </div>

      {error && (
        <Alert variant="error" message={error}>
          <Button
            variant="secondary"
            size="sm"
            onClick={onConfirm}
            className="mt-2"
          >
            Reintentar
          </Button>
        </Alert>
      )}

      <div className="flex gap-3">
        <Button variant="secondary" onClick={onBack} disabled={isConfirming}>
          Atrás
        </Button>
        <Button onClick={onConfirm} loading={isConfirming}>
          Confirmar importación
        </Button>
      </div>
    </div>
  )
}

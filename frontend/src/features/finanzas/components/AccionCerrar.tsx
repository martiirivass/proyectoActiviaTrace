import { useState } from 'react'
import { Button } from '@/shared/components/ui/Button'
import { Alert } from '@/shared/components/ui/Alert'

interface AccionCerrarProps {
  onConfirm: () => Promise<void>
  onCancel: () => void
}

export function AccionCerrar({ onConfirm, onCancel }: AccionCerrarProps) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleConfirm = async () => {
    setLoading(true)
    setError(null)
    try {
      await onConfirm()
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error al cerrar liquidación'
      if (message.includes('409') || message.includes('ya cerrada')) {
        setError('La liquidación ya está cerrada')
      } else {
        setError(message)
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
        <h3 className="text-lg font-semibold text-gray-900">Cerrar Liquidación</h3>
        <p className="mt-2 text-sm text-gray-600">
          ¿Estás seguro de cerrar esta liquidación? Esta acción es irreversible.
        </p>

        {error && (
          <div className="mt-3">
            <Alert variant="error" message={error} onDismiss={() => setError(null)} />
          </div>
        )}

        <div className="mt-6 flex justify-end gap-3">
          <Button variant="secondary" onClick={onCancel} disabled={loading}>
            Cancelar
          </Button>
          <Button variant="danger" onClick={handleConfirm} loading={loading}>
            Confirmar Cierre
          </Button>
        </div>
      </div>
    </div>
  )
}

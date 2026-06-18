import { Button } from '@/shared/components/ui/Button'
import { Alert } from '@/shared/components/ui/Alert'

interface ConfirmAbonarModalProps {
  onConfirm: () => void
  onCancel: () => void
  loading: boolean
  error: string | null
}

export function ConfirmAbonarModal({ onConfirm, onCancel, loading, error }: ConfirmAbonarModalProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="w-full max-w-sm rounded-lg bg-white p-6 shadow-xl">
        <h3 className="text-lg font-semibold text-gray-900">Abonar Factura</h3>
        <p className="mt-2 text-sm text-gray-600">
          ¿Estás seguro de abonar esta factura? Esta acción registrará la fecha de abono.
        </p>

        {error && (
          <div className="mt-3">
            <Alert variant="error" message={error} />
          </div>
        )}

        <div className="mt-6 flex justify-end gap-3">
          <Button variant="secondary" onClick={onCancel} disabled={loading}>
            Cancelar
          </Button>
          <Button onClick={onConfirm} loading={loading}>
            Confirmar Abono
          </Button>
        </div>
      </div>
    </div>
  )
}

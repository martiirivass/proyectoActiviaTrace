import { Button } from '@/shared/components/ui/Button'
import { Alert } from '@/shared/components/ui/Alert'
import type { ComunicacionPreview } from '@/features/academico/types'

interface PreviewModalProps {
  preview: ComunicacionPreview | null
  isOpen: boolean
  isSending: boolean
  error: string | null
  onClose: () => void
  onSend: () => void
}

export function PreviewModal({
  preview,
  isOpen,
  isSending,
  error,
  onClose,
  onSend,
}: PreviewModalProps) {
  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="mx-4 w-full max-w-lg rounded-lg bg-white shadow-xl">
        <div className="border-b border-gray-200 px-6 py-4">
          <h3 className="text-lg font-semibold text-gray-900">
            Previsualizar comunicación
          </h3>
        </div>

        <div className="space-y-4 px-6 py-4">
          {preview && (
            <>
              <div>
                <span className="text-sm font-medium text-gray-500">
                  Asunto:{' '}
                </span>
                <span className="text-sm text-gray-900">
                  {preview.preview_html}
                </span>
              </div>
              <div
                className="rounded-md border border-gray-200 p-4 text-sm text-gray-700"
                dangerouslySetInnerHTML={{
                  __html: preview.preview_html,
                }}
              />
              <div className="text-sm text-gray-600">
                <span className="font-medium">
                  {preview.cantidad_destinatarios}
                </span>{' '}
                destinatario(s)
              </div>
            </>
          )}

          {error && <Alert variant="error" message={error} />}
        </div>

        <div className="flex justify-end gap-3 border-t border-gray-200 px-6 py-4">
          <Button
            variant="secondary"
            onClick={onClose}
            disabled={isSending}
          >
            Cancelar
          </Button>
          <Button onClick={onSend} loading={isSending}>
            Enviar
          </Button>
        </div>
      </div>
    </div>
  )
}

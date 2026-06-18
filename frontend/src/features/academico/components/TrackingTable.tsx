import { useParams } from 'react-router-dom'
import { Spinner } from '@/shared/components/ui/Spinner'
import { Alert } from '@/shared/components/ui/Alert'
import { EstadoBadge } from './EstadoBadge'
import { useTrackingPorMateria } from '@/features/academico/hooks/useComunicaciones'
import type { TrackingDistribucion } from '@/features/academico/types'

function DistribucionSummary({
  distribucion,
}: {
  distribucion: TrackingDistribucion
}) {
  return (
    <div className="flex flex-wrap gap-3 text-sm">
      <span className="text-gray-500">
        Pendientes: <strong>{distribucion.pendiente}</strong>
      </span>
      <span className="text-blue-600">
        Enviando: <strong>{distribucion.enviando}</strong>
      </span>
      <span className="text-green-600">
        Enviados: <strong>{distribucion.enviado}</strong>
      </span>
      <span className="text-red-600">
        Errores: <strong>{distribucion.error}</strong>
      </span>
      <span className="text-orange-600">
        Cancelados: <strong>{distribucion.cancelado}</strong>
      </span>
    </div>
  )
}

export function TrackingTable() {
  const { materiaId } = useParams<{ materiaId: string }>()
  const { data, isLoading, isError, refetch } = useTrackingPorMateria(
    materiaId ?? '',
  )

  if (isLoading) {
    return (
      <div className="flex min-h-32 items-center justify-center">
        <Spinner size="md" />
      </div>
    )
  }

  if (isError) {
    return (
      <Alert variant="error" message="Error al cargar el tracking.">
        <button
          type="button"
          onClick={() => refetch()}
          className="mt-2 text-sm font-medium underline"
        >
          Reintentar
        </button>
      </Alert>
    )
  }

  if (!data || data.comunicaciones.length === 0) {
    return (
      <p className="py-8 text-center text-sm text-gray-500">
        No hay comunicaciones enviadas para esta comisión.
      </p>
    )
  }

  return (
    <div className="space-y-4">
      <DistribucionSummary distribucion={data.distribucion} />

      <div className="overflow-x-auto rounded-lg border border-gray-200">
        <table className="min-w-full divide-y divide-gray-200 text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left font-medium text-gray-600">
                Destinatario
              </th>
              <th className="px-4 py-3 text-left font-medium text-gray-600">
                Asunto
              </th>
              <th className="px-4 py-3 text-left font-medium text-gray-600">
                Estado
              </th>
              <th className="px-4 py-3 text-left font-medium text-gray-600">
                Fecha
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {data.comunicaciones.map((msg) => (
              <tr key={msg.id} className="hover:bg-gray-50">
                <td className="whitespace-nowrap px-4 py-3 text-gray-700">
                  {maskEmail(msg.destinatario)}
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-gray-900">
                  {msg.asunto}
                </td>
                <td className="whitespace-nowrap px-4 py-3">
                  <EstadoBadge estado={msg.estado} />
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-gray-500">
                  {msg.fecha_envio
                    ? new Date(msg.fecha_envio).toLocaleDateString('es-AR')
                    : '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function maskEmail(email: string): string {
  const [local, domain] = email.split('@')
  if (!domain) return email
  const masked = local.charAt(0) + '*'.repeat(local.length - 1)
  return `${masked}@${domain}`
}

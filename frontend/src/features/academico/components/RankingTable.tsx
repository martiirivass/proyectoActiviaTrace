import { useParams } from 'react-router-dom'
import { Spinner } from '@/shared/components/ui/Spinner'
import { Alert } from '@/shared/components/ui/Alert'
import { useRanking } from '@/features/academico/hooks/useRanking'

export function RankingTable() {
  const { materiaId } = useParams<{ materiaId: string }>()
  const { data: ranking, isLoading, isError, refetch } = useRanking(materiaId ?? '')

  if (isLoading) {
    return (
      <div className="flex min-h-64 items-center justify-center">
        <Spinner size="lg" />
      </div>
    )
  }

  if (isError) {
    return (
      <Alert variant="error" message="Error al cargar el ranking.">
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

  if (!ranking || ranking.length === 0) {
    return (
      <div className="flex min-h-48 items-center justify-center">
        <p className="text-gray-500">No hay datos de ranking disponibles.</p>
      </div>
    )
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200">
      <table className="min-w-full divide-y divide-gray-200 text-sm">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left font-medium text-gray-600">#</th>
            <th className="px-4 py-3 text-left font-medium text-gray-600">
              Nombre
            </th>
            <th className="px-4 py-3 text-left font-medium text-gray-600">
              Email
            </th>
            <th className="px-4 py-3 text-left font-medium text-gray-600">
              Aprobadas
            </th>
            <th className="px-4 py-3 text-left font-medium text-gray-600">
              Total
            </th>
            <th className="px-4 py-3 text-left font-medium text-gray-600">
              Porcentaje
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {ranking.map((entry) => (
            <tr key={entry.posicion} className="hover:bg-gray-50">
              <td className="whitespace-nowrap px-4 py-3 text-gray-500">
                {entry.posicion}
              </td>
              <td className="whitespace-nowrap px-4 py-3 font-medium text-gray-900">
                {entry.alumno.apellido}, {entry.alumno.nombre}
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-gray-600">
                {entry.email}
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-gray-700">
                {entry.aprobadas}
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-gray-700">
                {entry.total}
              </td>
              <td className="whitespace-nowrap px-4 py-3">
                <div className="flex items-center gap-2">
                  <div className="h-2 w-24 overflow-hidden rounded-full bg-gray-200">
                    <div
                      className="h-full rounded-full bg-blue-600"
                      style={{ width: `${entry.porcentaje}%` }}
                    />
                  </div>
                  <span className="text-xs text-gray-600">
                    {entry.porcentaje}%
                  </span>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

import { Spinner } from '@/shared/components/ui/Spinner'
import { Alert } from '@/shared/components/ui/Alert'
import type { MonitorEntry } from '@/features/academico/types'

interface MonitorTableProps {
  data: MonitorEntry[] | undefined
  isLoading: boolean
  isError: boolean
  onRefetch: () => void
}

function PorcentajeBar({ value }: { value: number }) {
  let color = 'bg-red-500'
  if (value >= 70) color = 'bg-green-500'
  else if (value >= 40) color = 'bg-yellow-500'

  return (
    <div className="flex items-center gap-2">
      <div className="h-2 w-24 overflow-hidden rounded-full bg-gray-200">
        <div
          className={`h-full rounded-full ${color}`}
          style={{ width: `${Math.min(value, 100)}%` }}
        />
      </div>
      <span className="text-xs text-gray-600">{value}%</span>
    </div>
  )
}

export function MonitorTable({
  data,
  isLoading,
  isError,
  onRefetch,
}: MonitorTableProps) {
  if (isLoading) {
    return (
      <div className="flex min-h-64 items-center justify-center">
        <Spinner size="lg" />
      </div>
    )
  }

  if (isError) {
    return (
      <Alert variant="error" message="Error al cargar los datos del monitor.">
        <button
          type="button"
          onClick={onRefetch}
          className="mt-2 text-sm font-medium underline"
        >
          Reintentar
        </button>
      </Alert>
    )
  }

  if (!data || data.length === 0) {
    return (
      <div className="flex min-h-48 items-center justify-center">
        <p className="text-gray-500">
          No hay alumnos asignados para seguimiento.
        </p>
      </div>
    )
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200">
      <table className="min-w-full divide-y divide-gray-200 text-sm">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left font-medium text-gray-600">
              Nombre
            </th>
            <th className="px-4 py-3 text-left font-medium text-gray-600">
              Email
            </th>
            <th className="px-4 py-3 text-left font-medium text-gray-600">
              Comisión
            </th>
            <th className="px-4 py-3 text-left font-medium text-gray-600">
              Regional
            </th>
            <th className="px-4 py-3 text-center font-medium text-gray-600">
              Total
            </th>
            <th className="px-4 py-3 text-center font-medium text-gray-600">
              Aprobadas
            </th>
            <th className="px-4 py-3 text-center font-medium text-gray-600">
              Desaprobadas
            </th>
            <th className="px-4 py-3 text-center font-medium text-gray-600">
              Pendientes
            </th>
            <th className="px-4 py-3 text-left font-medium text-gray-600">
              %
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {data.map((entry, idx) => (
            <tr key={idx} className="hover:bg-gray-50">
              <td className="whitespace-nowrap px-4 py-3 font-medium text-gray-900">
                {entry.alumno.apellido}, {entry.alumno.nombre}
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-gray-600">
                {entry.email}
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-gray-700">
                {entry.comision}
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-gray-700">
                {entry.regional}
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-center text-gray-700">
                {entry.total}
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-center text-green-600">
                {entry.aprobadas}
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-center text-red-600">
                {entry.desaprobadas}
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-center text-yellow-600">
                {entry.pendientes}
              </td>
              <td className="whitespace-nowrap px-4 py-3">
                <PorcentajeBar value={entry.porcentaje} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { Spinner } from '@/shared/components/ui/Spinner'
import { Alert } from '@/shared/components/ui/Alert'
import { useNotasFinales } from '@/features/academico/hooks/useNotasFinales'
import type { NotaFinalEntry } from '@/features/academico/types'

function FilaExpandible({ entry }: { entry: NotaFinalEntry }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <>
      <tr
        className="cursor-pointer hover:bg-gray-50"
        onClick={() => setExpanded(!expanded)}
      >
        <td className="whitespace-nowrap px-4 py-3 text-gray-500">
          {expanded ? '▼' : '▶'}
        </td>
        <td className="whitespace-nowrap px-4 py-3 font-medium text-gray-900">
          {entry.alumno.apellido}, {entry.alumno.nombre}
        </td>
        <td className="whitespace-nowrap px-4 py-3 text-gray-600">
          {entry.email}
        </td>
        <td className="whitespace-nowrap px-4 py-3 text-gray-700">
          {entry.actividades_consideradas}
        </td>
        <td className="whitespace-nowrap px-4 py-3 font-medium text-gray-900">
          {entry.nota_final !== null ? entry.nota_final : <span className="text-gray-400">&mdash;</span>}
        </td>
      </tr>
      {expanded && (
        <tr className="bg-gray-50">
          <td colSpan={5} className="px-8 py-3">
            <div className="text-sm text-gray-600">
              <h4 className="mb-2 font-medium text-gray-700">
                Detalle de actividades
              </h4>
              <div className="space-y-1">
                {entry.actividades.map((act, idx) => (
                  <div key={idx} className="flex justify-between">
                    <span>{act.nombre}</span>
                    <span className="font-medium">
                      {act.nota !== null ? String(act.nota) : <span className="text-gray-400">&mdash;</span>}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  )
}

export function NotasTable() {
  const { materiaId } = useParams<{ materiaId: string }>()
  const { data: notas, isLoading, isError, refetch } = useNotasFinales(materiaId ?? '')

  if (isLoading) {
    return (
      <div className="flex min-h-64 items-center justify-center">
        <Spinner size="lg" />
      </div>
    )
  }

  if (isError) {
    return (
      <Alert variant="error" message="Error al cargar las notas finales.">
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

  if (!notas || notas.length === 0) {
    return (
      <div className="flex min-h-48 items-center justify-center">
        <p className="text-gray-500">No hay notas finales disponibles.</p>
      </div>
    )
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200">
      <table className="min-w-full divide-y divide-gray-200 text-sm">
        <thead className="bg-gray-50">
          <tr>
            <th className="w-8 px-4 py-3" />
            <th className="px-4 py-3 text-left font-medium text-gray-600">
              Nombre
            </th>
            <th className="px-4 py-3 text-left font-medium text-gray-600">
              Email
            </th>
            <th className="px-4 py-3 text-left font-medium text-gray-600">
              Actividades
            </th>
            <th className="px-4 py-3 text-left font-medium text-gray-600">
              Nota Final
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {notas.map((entry, idx) => (
            <FilaExpandible key={idx} entry={entry} />
          ))}
        </tbody>
      </table>
    </div>
  )
}

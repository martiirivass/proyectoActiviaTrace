import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Spinner } from '@/shared/components/ui/Spinner'
import { Alert } from '@/shared/components/ui/Alert'
import { Button } from '@/shared/components/ui/Button'
import { FiltroBusqueda } from './FiltroBusqueda'
import { useAtrasados } from '@/features/academico/hooks/useAtrasados'
import type { CausaAtraso } from '@/features/academico/types'

const causaStyles: Record<CausaAtraso, string> = {
  nota_bajo_umbral: 'bg-red-100 text-red-800',
  actividad_faltante: 'bg-orange-100 text-orange-800',
}

const causaLabels: Record<CausaAtraso, string> = {
  nota_bajo_umbral: 'Nota bajo umbral',
  actividad_faltante: 'Actividad faltante',
}

export function AtrasadosTable() {
  const { materiaId } = useParams<{ materiaId: string }>()
  const navigate = useNavigate()
  const [busqueda, setBusqueda] = useState('')
  const { data: atrasados, isLoading, isError, refetch } = useAtrasados(
    materiaId ?? '',
    busqueda || undefined,
  )

  if (isLoading) {
    return (
      <div className="flex min-h-64 items-center justify-center">
        <Spinner size="lg" />
      </div>
    )
  }

  if (isError) {
    return (
      <Alert variant="error" message="Error al cargar los atrasados.">
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

  if (!atrasados || atrasados.length === 0) {
    return (
      <div className="flex min-h-48 items-center justify-center">
        <p className="text-gray-500">
          No hay alumnos atrasados en esta comisión.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-600">
          {atrasados.length} alumnos atrasados
        </p>
        <div className="w-72">
          <FiltroBusqueda
            value={busqueda}
            onChange={setBusqueda}
            placeholder="Buscar por nombre o apellido..."
          />
        </div>
      </div>

      <div className="overflow-x-auto rounded-lg border border-gray-200">
        <table className="min-w-full divide-y divide-gray-200 text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left font-medium text-gray-600">
                Alumno
              </th>
              <th className="px-4 py-3 text-left font-medium text-gray-600">
                Email
              </th>
              <th className="px-4 py-3 text-left font-medium text-gray-600">
                Actividad
              </th>
              <th className="px-4 py-3 text-left font-medium text-gray-600">
                Causa
              </th>
              <th className="px-4 py-3" />
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {atrasados.map((entry, idx) => (
              <tr key={idx} className="hover:bg-gray-50">
                <td className="whitespace-nowrap px-4 py-3 font-medium text-gray-900">
                  {entry.alumno.apellido}, {entry.alumno.nombre}
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-gray-600">
                  {entry.alumno.email}
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-gray-700">
                  {entry.actividad}
                </td>
                <td className="whitespace-nowrap px-4 py-3">
                  <span
                    className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${causaStyles[entry.causa]}`}
                  >
                    {causaLabels[entry.causa]}
                  </span>
                </td>
                <td className="whitespace-nowrap px-4 py-3">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() =>
                      navigate(
                        `../comunicaciones?alumno=${entry.alumno.id}`,
                      )
                    }
                  >
                    Comunicar
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

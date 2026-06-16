import { useState } from 'react'
import { Card } from '@/shared/components/ui/Card'
import { Button } from '@/shared/components/ui/Button'
import { Spinner } from '@/shared/components/ui/Spinner'
import { useMonitorGeneral } from '@/features/coordinacion/hooks/useMonitorCoordinacion'
import type { MonitorFiltrosCoordinacion } from '@/features/coordinacion/types'

export default function MonitorGeneralPage() {
  const [filtros, setFiltros] = useState<MonitorFiltrosCoordinacion>({})
  const { data: entries, isLoading, isFetching } = useMonitorGeneral(filtros)

  const updateFiltro = (key: keyof MonitorFiltrosCoordinacion, value: string | undefined) =>
    setFiltros((f) => ({ ...f, [key]: value || undefined }))

  const limpiar = () => setFiltros({})

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">Monitor General</h2>
        <div className="flex gap-2">
          <Button variant="secondary" size="sm" onClick={limpiar}>
            Limpiar Filtros
          </Button>
          <Button variant="secondary" size="sm">
            Exportar
          </Button>
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        <input
          type="text"
          placeholder="Buscar alumno..."
          className="rounded-md border border-gray-300 px-3 py-1.5 text-sm"
          value={filtros.busqueda ?? ''}
          onChange={(e) => updateFiltro('busqueda', e.target.value)}
        />
        <input
          type="text"
          placeholder="Materia"
          className="rounded-md border border-gray-300 px-3 py-1.5 text-sm"
          value={filtros.materia ?? ''}
          onChange={(e) => updateFiltro('materia', e.target.value)}
        />
        <input
          type="text"
          placeholder="Regional"
          className="rounded-md border border-gray-300 px-3 py-1.5 text-sm"
          value={filtros.regional ?? ''}
          onChange={(e) => updateFiltro('regional', e.target.value)}
        />
        <input
          type="text"
          placeholder="Comisión"
          className="rounded-md border border-gray-300 px-3 py-1.5 text-sm"
          value={filtros.comision ?? ''}
          onChange={(e) => updateFiltro('comision', e.target.value)}
        />
        <select
          className="rounded-md border border-gray-300 px-3 py-1.5 text-sm"
          value={filtros.estado ?? ''}
          onChange={(e) => updateFiltro('estado', e.target.value)}
        >
          <option value="">Todos los estados</option>
          <option value="activo">Activo</option>
          <option value="bajo_seguimiento">Bajo seguimiento</option>
          <option value="inactivo">Inactivo</option>
        </select>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-8">
          <Spinner />
        </div>
      ) : (
        <Card>
          {isFetching && (
            <div className="mb-2 flex items-center gap-2 text-xs text-gray-500">
              <Spinner size="sm" /> Actualizando...
            </div>
          )}
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-gray-200 text-gray-600">
                <th className="pb-2 pr-4 font-medium">Alumno</th>
                <th className="pb-2 pr-4 font-medium">Materia</th>
                <th className="pb-2 pr-4 font-medium">Regional</th>
                <th className="pb-2 pr-4 font-medium">Comisión</th>
                <th className="pb-2 pr-4 font-medium">Estado</th>
                <th className="pb-2 pr-4 font-medium">Criterio</th>
                <th className="pb-2 font-medium">Actividades</th>
              </tr>
            </thead>
            <tbody>
              {entries?.map((e) => (
                <tr key={e.id} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="py-2 pr-4">{e.apellido}, {e.nombre}</td>
                  <td className="py-2 pr-4">{e.materia_nombre}</td>
                  <td className="py-2 pr-4">{e.regional}</td>
                  <td className="py-2 pr-4">{e.comision}</td>
                  <td className="py-2 pr-4">{e.estado_actividad}</td>
                  <td className="py-2 pr-4">{e.criterio_clasificacion}</td>
                  <td className="py-2">
                    {e.aprobadas}/{e.total_actividades}
                  </td>
                </tr>
              ))}
              {(!entries || entries.length === 0) && (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-gray-500">
                    No se encontraron registros
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  )
}

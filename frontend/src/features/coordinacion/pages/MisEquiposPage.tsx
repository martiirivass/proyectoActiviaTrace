import { useState } from 'react'
import { Card } from '@/shared/components/ui/Card'
import { Spinner } from '@/shared/components/ui/Spinner'
import { useMisEquipos } from '@/features/coordinacion/hooks/useEquipos'
import { ExportarEquipo } from '@/features/coordinacion/components/ExportarEquipo'
import type { MisEquiposFiltros } from '@/features/coordinacion/types'

export function MisEquiposPage() {
  const [filtros, setFiltros] = useState<MisEquiposFiltros>({})
  const { data: equipos, isLoading } = useMisEquipos(filtros)

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-base font-medium text-gray-800">Mis Equipos</h3>
        <ExportarEquipo />
      </div>

      <div className="flex flex-wrap gap-2">
        <select
          className="rounded-md border border-gray-300 px-3 py-1.5 text-sm"
          value={filtros.estado ?? ''}
          onChange={(e) => setFiltros((f) => ({ ...f, estado: e.target.value || undefined }))}
        >
          <option value="">Todos los estados</option>
          <option value="activo">Activo</option>
          <option value="inactivo">Inactivo</option>
          <option value="finalizado">Finalizado</option>
        </select>
        <select
          className="rounded-md border border-gray-300 px-3 py-1.5 text-sm"
          value={filtros.rol ?? ''}
          onChange={(e) => setFiltros((f) => ({ ...f, rol: e.target.value || undefined }))}
        >
          <option value="">Todos los roles</option>
          <option value="PROFESOR">Profesor</option>
          <option value="TUTOR">Tutor</option>
          <option value="COORDINADOR">Coordinador</option>
        </select>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-8">
          <Spinner />
        </div>
      ) : (
        <Card>
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-gray-200 text-gray-600">
                <th className="pb-2 pr-4 font-medium">Materia</th>
                <th className="pb-2 pr-4 font-medium">Carrera</th>
                <th className="pb-2 pr-4 font-medium">Cohorte</th>
                <th className="pb-2 pr-4 font-medium">Rol</th>
                <th className="pb-2 pr-4 font-medium">Vigencia</th>
                <th className="pb-2 font-medium">Estado</th>
              </tr>
            </thead>
            <tbody>
              {equipos?.map((eq) => (
                <tr key={eq.id} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="py-2 pr-4">{eq.materia_nombre}</td>
                  <td className="py-2 pr-4">{eq.carrera_nombre}</td>
                  <td className="py-2 pr-4">{eq.cohorte_nombre}</td>
                  <td className="py-2 pr-4">{eq.rol}</td>
                  <td className="py-2 pr-4">
                    {eq.vigencia_desde} — {eq.vigencia_hasta}
                  </td>
                  <td className="py-2">
                    <span
                      className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${
                        eq.estado === 'activo'
                          ? 'bg-green-100 text-green-700'
                          : eq.estado === 'inactivo'
                            ? 'bg-yellow-100 text-yellow-700'
                            : 'bg-gray-100 text-gray-600'
                      }`}
                    >
                      {eq.estado}
                    </span>
                  </td>
                </tr>
              ))}
              {(!equipos || equipos.length === 0) && (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-gray-500">
                    No se encontraron equipos
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

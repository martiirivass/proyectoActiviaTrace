import { useState } from 'react'
import { Card } from '@/shared/components/ui/Card'
import { Spinner } from '@/shared/components/ui/Spinner'
import { useAsignaciones } from '@/features/coordinacion/hooks/useEquipos'
import { ExportarEquipo } from '@/features/coordinacion/components/ExportarEquipo'
import type { AsignacionesFiltros } from '@/features/coordinacion/types'

export function AsignacionesPage() {
  const [filtros, setFiltros] = useState<AsignacionesFiltros>({})
  const { data: asignaciones, isLoading } = useAsignaciones(filtros)

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-base font-medium text-gray-800">Asignaciones Globales</h3>
        <ExportarEquipo />
      </div>

      <div className="flex flex-wrap gap-2">
        <input
          type="text"
          placeholder="Buscar por usuario..."
          className="rounded-md border border-gray-300 px-3 py-1.5 text-sm"
          value={filtros.usuario ?? ''}
          onChange={(e) => setFiltros((f) => ({ ...f, usuario: e.target.value || undefined }))}
        />
        <select
          className="rounded-md border border-gray-300 px-3 py-1.5 text-sm"
          value={filtros.role ?? ''}
          onChange={(e) => setFiltros((f) => ({ ...f, role: e.target.value || undefined }))}
        >
          <option value="">Todos los roles</option>
          <option value="PROFESOR">Profesor</option>
          <option value="TUTOR">Tutor</option>
          <option value="COORDINADOR">Coordinador</option>
          <option value="NEXO">Nexo</option>
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
                <th className="pb-2 pr-4 font-medium">Docente</th>
                <th className="pb-2 pr-4 font-medium">Materia</th>
                <th className="pb-2 pr-4 font-medium">Carrera</th>
                <th className="pb-2 pr-4 font-medium">Cohorte</th>
                <th className="pb-2 pr-4 font-medium">Rol</th>
                <th className="pb-2 pr-4 font-medium">Vigencia</th>
                <th className="pb-2 font-medium">Estado</th>
              </tr>
            </thead>
            <tbody>
              {asignaciones?.map((a) => (
                <tr key={a.id} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="py-2 pr-4">{a.docente_apellido}, {a.docente_nombre}</td>
                  <td className="py-2 pr-4">{a.materia_nombre}</td>
                  <td className="py-2 pr-4">{a.carrera_nombre}</td>
                  <td className="py-2 pr-4">{a.cohorte_nombre}</td>
                  <td className="py-2 pr-4">{a.rol}</td>
                  <td className="py-2 pr-4">
                    {a.vigencia_desde} — {a.vigencia_hasta}
                  </td>
                  <td className="py-2">
                    <span
                      className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${
                        a.estado === 'activo'
                          ? 'bg-green-100 text-green-700'
                          : a.estado === 'inactivo'
                            ? 'bg-yellow-100 text-yellow-700'
                            : 'bg-gray-100 text-gray-600'
                      }`}
                    >
                      {a.estado}
                    </span>
                  </td>
                </tr>
              ))}
              {(!asignaciones || asignaciones.length === 0) && (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-gray-500">
                    No se encontraron asignaciones
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

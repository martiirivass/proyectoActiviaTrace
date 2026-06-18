import { useState } from 'react'
import { Card } from '@/shared/components/ui/Card'
import { Spinner } from '@/shared/components/ui/Spinner'
import { useEncuentrosAdmin } from '@/features/coordinacion/hooks/useEncuentros'
import type { EncuentrosAdminFiltros } from '@/features/coordinacion/types'

export default function EncuentrosAdminPage() {
  const [filtros, setFiltros] = useState<EncuentrosAdminFiltros>({})
  const { data: encuentros, isLoading } = useEncuentrosAdmin(filtros)

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-gray-900">Encuentros — Vista Admin</h2>

      <div className="flex flex-wrap gap-2">
        <input
          type="text"
          placeholder="Materia"
          className="rounded-md border border-gray-300 px-3 py-1.5 text-sm"
          value={filtros.materia ?? ''}
          onChange={(e) => setFiltros((f) => ({ ...f, materia: e.target.value || undefined }))}
        />
        <input
          type="text"
          placeholder="Docente"
          className="rounded-md border border-gray-300 px-3 py-1.5 text-sm"
          value={filtros.docente ?? ''}
          onChange={(e) => setFiltros((f) => ({ ...f, docente: e.target.value || undefined }))}
        />
        <input
          type="date"
          className="rounded-md border border-gray-300 px-3 py-1.5 text-sm"
          value={filtros.fecha_desde ?? ''}
          onChange={(e) => setFiltros((f) => ({ ...f, fecha_desde: e.target.value || undefined }))}
        />
        <input
          type="date"
          className="rounded-md border border-gray-300 px-3 py-1.5 text-sm"
          value={filtros.fecha_hasta ?? ''}
          onChange={(e) => setFiltros((f) => ({ ...f, fecha_hasta: e.target.value || undefined }))}
        />
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
                <th className="pb-2 pr-4 font-medium">Cohorte</th>
                <th className="pb-2 pr-4 font-medium">Docente</th>
                <th className="pb-2 pr-4 font-medium">Fecha</th>
                <th className="pb-2 pr-4 font-medium">Tema</th>
                <th className="pb-2 font-medium">Asistentes</th>
              </tr>
            </thead>
            <tbody>
              {encuentros?.map((e) => (
                <tr key={e.id} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="py-2 pr-4">{e.materia_nombre}</td>
                  <td className="py-2 pr-4">{e.cohorte_nombre}</td>
                  <td className="py-2 pr-4">{e.docente_nombre}</td>
                  <td className="py-2 pr-4">{e.fecha}</td>
                  <td className="py-2 pr-4 text-gray-600">{e.tema}</td>
                  <td className="py-2">{e.asistentes_count}</td>
                </tr>
              ))}
              {(!encuentros || encuentros.length === 0) && (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-gray-500">
                    No se encontraron encuentros
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

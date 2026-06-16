import { useState } from 'react'
import type { InteraccionesPorDocenteMateria } from '@/features/admin/types'

interface Props {
  data: InteraccionesPorDocenteMateria[]
}

export function InteraccionesPorDocenteMateriaTable({ data }: Props) {
  const [expanded, setExpanded] = useState<number | null>(null)

  if (data.length === 0) {
    return <p className="py-4 text-center text-sm text-gray-500">Sin datos para este período</p>
  }

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold text-gray-700">Interacciones por Docente+Materia</h3>
      <div className="overflow-x-auto rounded-lg border border-gray-200">
        <table className="min-w-full divide-y divide-gray-200 text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-3 py-2 text-left font-medium text-gray-600">Docente</th>
              <th className="px-3 py-2 text-left font-medium text-gray-600">Materia</th>
              <th className="px-3 py-2 text-right font-medium text-gray-600">Total Acciones</th>
              <th className="px-3 py-2 text-center font-medium text-gray-600" />
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {data.map((row, i) => (
              <>
                <tr key={i} className="cursor-pointer hover:bg-gray-50" onClick={() => setExpanded(expanded === i ? null : i)}>
                  <td className="px-3 py-2">{row.docente}</td>
                  <td className="px-3 py-2">{row.materia}</td>
                  <td className="px-3 py-2 text-right font-medium">{row.total_acciones}</td>
                  <td className="px-3 py-2 text-center text-xs text-gray-400">
                    {expanded === i ? '▲' : '▼'}
                  </td>
                </tr>
                {expanded === i && row.desglose && (
                  <tr key={`${i}-detail`}>
                    <td colSpan={4} className="bg-gray-50 px-6 py-2">
                      <div className="flex flex-wrap gap-4">
                        {Object.entries(row.desglose).map(([accion, count]) => (
                          <span key={accion} className="rounded bg-white px-2 py-1 text-xs shadow-sm">
                            {accion}: <strong>{count}</strong>
                          </span>
                        ))}
                      </div>
                    </td>
                  </tr>
                )}
              </>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

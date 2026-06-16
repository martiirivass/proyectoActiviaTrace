import type { ComunicacionesPorDocente } from '@/features/admin/types'

interface ComunicacionesPorDocenteTableProps {
  data: ComunicacionesPorDocente[]
}

export function ComunicacionesPorDocenteTable({ data }: ComunicacionesPorDocenteTableProps) {
  if (data.length === 0) {
    return <p className="py-4 text-center text-sm text-gray-500">Sin datos para este período</p>
  }

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold text-gray-700">Comunicaciones por Docente</h3>
      <div className="overflow-x-auto rounded-lg border border-gray-200">
        <table className="min-w-full divide-y divide-gray-200 text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-3 py-2 text-left font-medium text-gray-600">Docente</th>
              <th className="px-3 py-2 text-right font-medium text-gray-600">Pendientes</th>
              <th className="px-3 py-2 text-right font-medium text-gray-600">Enviando</th>
              <th className="px-3 py-2 text-right font-medium text-gray-600">Enviados</th>
              <th className="px-3 py-2 text-right font-medium text-gray-600">Error</th>
              <th className="px-3 py-2 text-right font-medium text-gray-600">Cancelados</th>
              <th className="px-3 py-2 text-right font-medium text-gray-600">Total</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {data.map((row, i) => (
              <tr key={i} className="hover:bg-gray-50">
                <td className="px-3 py-2">{row.docente}</td>
                <td className="px-3 py-2 text-right">{row.pendientes}</td>
                <td className="px-3 py-2 text-right">{row.enviando}</td>
                <td className="px-3 py-2 text-right text-green-600">{row.enviados}</td>
                <td className="px-3 py-2 text-right text-red-600">{row.error}</td>
                <td className="px-3 py-2 text-right">{row.cancelados}</td>
                <td className="px-3 py-2 text-right font-medium">{row.total}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

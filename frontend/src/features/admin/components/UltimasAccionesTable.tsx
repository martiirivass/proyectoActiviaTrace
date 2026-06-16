import type { AuditLogEntry } from '@/features/admin/types'

interface UltimasAccionesTableProps {
  data: AuditLogEntry[]
}

export function UltimasAccionesTable({ data }: UltimasAccionesTableProps) {
  if (data.length === 0) {
    return <p className="py-4 text-center text-sm text-gray-500">Sin datos para este período</p>
  }

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold text-gray-700">Últimas Acciones</h3>
      <div className="overflow-x-auto rounded-lg border border-gray-200">
        <table className="min-w-full divide-y divide-gray-200 text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-3 py-2 text-left font-medium text-gray-600">Fecha/Hora</th>
              <th className="px-3 py-2 text-left font-medium text-gray-600">Actor</th>
              <th className="px-3 py-2 text-left font-medium text-gray-600">Acción</th>
              <th className="px-3 py-2 text-left font-medium text-gray-600">Materia</th>
              <th className="px-3 py-2 text-left font-medium text-gray-600">Detalle</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {data.map((entry) => (
              <tr key={entry.id} className="hover:bg-gray-50">
                <td className="whitespace-nowrap px-3 py-2 text-xs">
                  {new Date(entry.fecha_hora).toLocaleString()}
                </td>
                <td className="px-3 py-2">{entry.actor}</td>
                <td className="px-3 py-2">
                  <span className="rounded bg-gray-100 px-1.5 py-0.5 text-xs font-mono">
                    {entry.accion}
                  </span>
                </td>
                <td className="px-3 py-2">{entry.materia ?? '—'}</td>
                <td className="max-w-xs truncate px-3 py-2 text-xs text-gray-500">
                  {entry.detalle}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

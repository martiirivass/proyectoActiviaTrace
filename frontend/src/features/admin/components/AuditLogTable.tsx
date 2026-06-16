import { useState } from 'react'
import type { AuditLogResponse } from '@/features/admin/types'
import { Button } from '@/shared/components/ui/Button'

interface AuditLogTableProps {
  data: AuditLogResponse | undefined
  onPageChange: (filtros: { offset?: number; limit?: number }) => void
  currentFiltros: { offset?: number; limit?: number }
}

export function AuditLogTable({ data, onPageChange, currentFiltros }: AuditLogTableProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const limit = currentFiltros.limit ?? 50

  if (!data || data.items.length === 0) {
    return (
      <p className="py-8 text-center text-gray-500">
        No se encontraron registros de auditoría para los filtros seleccionados
      </p>
    )
  }

  const totalPages = Math.ceil(data.total / limit)
  const currentPage = data.page || 1

  return (
    <div className="space-y-4">
      <div className="overflow-x-auto rounded-lg border border-gray-200">
        <table className="min-w-full divide-y divide-gray-200 text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-3 py-2 text-left font-medium text-gray-600">Fecha/Hora</th>
              <th className="px-3 py-2 text-left font-medium text-gray-600">Actor</th>
              <th className="px-3 py-2 text-left font-medium text-gray-600">Acción</th>
              <th className="px-3 py-2 text-left font-medium text-gray-600">Materia</th>
              <th className="px-3 py-2 text-left font-medium text-gray-600">Detalle</th>
              <th className="px-3 py-2 text-left font-medium text-gray-600">IP</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {data.items.map((entry) => (
              <>
                <tr
                  key={entry.id}
                  className="cursor-pointer hover:bg-gray-50"
                  onClick={() => setExpandedId(expandedId === entry.id ? null : entry.id)}
                >
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
                  <td className="px-3 py-2 text-xs text-gray-400">{entry.ip ?? '—'}</td>
                </tr>
                {expandedId === entry.id && (
                  <tr key={`${entry.id}-detail`}>
                    <td colSpan={6} className="bg-gray-50 px-6 py-3">
                      <div className="space-y-1 text-xs">
                        <p><strong>ID:</strong> {entry.id}</p>
                        <p><strong>Actor ID:</strong> {entry.actor_id}</p>
                        <p><strong>Detalle completo:</strong> {entry.detalle}</p>
                        {entry.metadata && (
                          <p><strong>Metadata:</strong> {JSON.stringify(entry.metadata)}</p>
                        )}
                      </div>
                    </td>
                  </tr>
                )}
              </>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-500">
            Página {currentPage} de {totalPages} ({data.total} registros)
          </p>
          <div className="flex gap-2">
            <Button
              variant="secondary"
              size="sm"
              disabled={currentPage <= 1}
              onClick={() => onPageChange({ offset: (currentPage - 2) * limit, limit })}
            >
              Anterior
            </Button>
            <Button
              variant="secondary"
              size="sm"
              disabled={currentPage >= totalPages}
              onClick={() => onPageChange({ offset: currentPage * limit, limit })}
            >
              Siguiente
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}

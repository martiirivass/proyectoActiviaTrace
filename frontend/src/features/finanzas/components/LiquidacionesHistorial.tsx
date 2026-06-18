import { useState } from 'react'
import { useLiquidacionesHistorial } from '@/features/finanzas/hooks/useLiquidaciones'
import { Spinner } from '@/shared/components/ui/Spinner'
import { Alert } from '@/shared/components/ui/Alert'
import { Button } from '@/shared/components/ui/Button'

export function LiquidacionesHistorial() {
  const [page, setPage] = useState(1)
  const { data, isLoading, error } = useLiquidacionesHistorial(page)

  return (
    <div className="space-y-3">
      <h3 className="text-lg font-semibold text-gray-800">Historial de Ejecuciones</h3>

      {isLoading && (
        <div className="flex justify-center py-4">
          <Spinner />
        </div>
      )}

      {error && <Alert variant="error" message="Error al cargar historial" />}

      {data && data.items.length === 0 && (
        <p className="py-4 text-center text-gray-500">No hay ejecuciones registradas</p>
      )}

      {data && data.items.length > 0 && (
        <>
          <div className="overflow-x-auto rounded-lg border border-gray-200">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left font-medium text-gray-600">Fecha</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-600">Usuario</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-600">Cohorte</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-600">Período</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {data.items.map((entry) => (
                  <tr key={entry.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">{new Date(entry.fecha).toLocaleString()}</td>
                    <td className="px-4 py-3">{entry.usuario}</td>
                    <td className="px-4 py-3">{entry.cohorte}</td>
                    <td className="px-4 py-3">{entry.periodo}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-500">
              Página {data.page} de {data.total_pages} ({data.total} registros)
            </p>
            <div className="flex gap-2">
              <Button
                variant="secondary"
                size="sm"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
              >
                Anterior
              </Button>
              <Button
                variant="secondary"
                size="sm"
                disabled={page >= data.total_pages}
                onClick={() => setPage((p) => p + 1)}
              >
                Siguiente
              </Button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

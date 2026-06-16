import type { Liquidacion } from '@/features/finanzas/types'
import type { TabSegmento } from './TabsSegmentacion'
import { Spinner } from '@/shared/components/ui/Spinner'
import { Alert } from '@/shared/components/ui/Alert'
import { Button } from '@/shared/components/ui/Button'

interface LiquidacionesTableProps {
  items: Liquidacion[]
  loading: boolean
  error: string | null
  segmento: TabSegmento
  onCerrar: (id: string) => void
  cerrandoId: string | null
}

function filterItems(items: Liquidacion[], segmento: TabSegmento): Liquidacion[] {
  switch (segmento) {
    case 'nexo':
      return items.filter((i) => i.es_nexo)
    case 'factura':
      return items.filter((i) => i.excluido_por_factura)
    default:
      return items
  }
}

export function LiquidacionesTable({ items, loading, error, segmento, onCerrar, cerrandoId }: LiquidacionesTableProps) {
  if (loading) {
    return (
      <div className="flex justify-center py-8">
        <Spinner />
      </div>
    )
  }

  if (error) {
    return <Alert variant="error" message={error} />
  }

  const filtered = filterItems(items, segmento)

  if (filtered.length === 0) {
    return (
      <p className="py-8 text-center text-gray-500">
        No hay liquidaciones para este período
      </p>
    )
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200">
      <table className="min-w-full divide-y divide-gray-200 text-sm">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left font-medium text-gray-600">Docente</th>
            <th className="px-4 py-3 text-left font-medium text-gray-600">Rol</th>
            <th className="px-4 py-3 text-right font-medium text-gray-600">Monto Base</th>
            <th className="px-4 py-3 text-right font-medium text-gray-600">Monto Plus</th>
            <th className="px-4 py-3 text-right font-medium text-gray-600">Total</th>
            <th className="px-4 py-3 text-center font-medium text-gray-600">Estado</th>
            <th className="px-4 py-3 text-center font-medium text-gray-600" />
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {filtered.map((liq) => (
            <tr key={liq.id} className="hover:bg-gray-50">
              <td className="px-4 py-3">{liq.docente_apellido}, {liq.docente_nombre}</td>
              <td className="px-4 py-3">{liq.rol}</td>
              <td className="px-4 py-3 text-right">${liq.monto_base.toLocaleString()}</td>
              <td className="px-4 py-3 text-right">${liq.monto_plus.toLocaleString()}</td>
              <td className="px-4 py-3 text-right font-medium">${liq.total.toLocaleString()}</td>
              <td className="px-4 py-3 text-center">
                <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${
                  liq.estado === 'Cerrada' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
                }`}>
                  {liq.estado}
                </span>
              </td>
              <td className="px-4 py-3 text-center">
                {liq.estado === 'Abierta' && (
                  <Button
                    variant="danger"
                    size="sm"
                    onClick={() => onCerrar(liq.id)}
                    loading={cerrandoId === liq.id}
                  >
                    Cerrar
                  </Button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

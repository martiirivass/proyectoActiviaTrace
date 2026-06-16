import type { Factura } from '@/features/finanzas/types'
import { Button } from '@/shared/components/ui/Button'

interface FacturasTableProps {
  items: Factura[]
  onAbonar: (id: string) => void
  onDelete: (id: string) => void
  onEdit: (item: Factura) => void
  abonandoId: string | null
}

export function FacturasTable({ items, onAbonar, onDelete, onEdit, abonandoId }: FacturasTableProps) {
  if (items.length === 0) {
    return (
      <p className="py-8 text-center text-gray-500">
        No hay facturas para los filtros seleccionados
      </p>
    )
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200">
      <table className="min-w-full divide-y divide-gray-200 text-sm">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left font-medium text-gray-600">Docente</th>
            <th className="px-4 py-3 text-left font-medium text-gray-600">Período</th>
            <th className="px-4 py-3 text-left font-medium text-gray-600">Detalle</th>
            <th className="px-4 py-3 text-right font-medium text-gray-600">Monto</th>
            <th className="px-4 py-3 text-center font-medium text-gray-600">Estado</th>
            <th className="px-4 py-3 text-left font-medium text-gray-600">Fecha Carga</th>
            <th className="px-4 py-3 text-center font-medium text-gray-600" />
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {items.map((fac) => (
            <tr key={fac.id} className="hover:bg-gray-50">
              <td className="px-4 py-3">{fac.docente_apellido}, {fac.docente_nombre}</td>
              <td className="px-4 py-3">{fac.periodo}</td>
              <td className="max-w-xs truncate px-4 py-3">{fac.detalle}</td>
              <td className="px-4 py-3 text-right">${fac.monto.toLocaleString()}</td>
              <td className="px-4 py-3 text-center">
                <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${
                  fac.estado === 'Abonada' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
                }`}>
                  {fac.estado}
                </span>
              </td>
              <td className="px-4 py-3">{new Date(fac.created_at).toLocaleDateString()}</td>
              <td className="px-4 py-3 text-center">
                <div className="flex justify-center gap-1">
                  <Button variant="ghost" size="sm" onClick={() => onEdit(fac)}>Editar</Button>
                  {fac.estado === 'Pendiente' && (
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={() => onAbonar(fac.id)}
                      loading={abonandoId === fac.id}
                    >
                      Abonar
                    </Button>
                  )}
                  <Button variant="ghost" size="sm" onClick={() => onDelete(fac.id)}>Eliminar</Button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

import type { LiquidacionKPI } from '@/features/finanzas/types'
import { Card } from '@/shared/components/ui/Card'

interface KPILiquidacionesProps {
  kpis: LiquidacionKPI | null
}

export function KPILiquidaciones({ kpis }: KPILiquidacionesProps) {
  if (!kpis) return null

  const items = [
    { label: 'Total Facturante', value: `$${kpis.total_facturante.toLocaleString()}`, color: 'text-green-700' },
    { label: 'Total No Facturante', value: `$${kpis.total_no_facturante.toLocaleString()}`, color: 'text-blue-700' },
    { label: 'Cantidad Facturante', value: kpis.cantidad_facturante.toString(), color: 'text-green-600' },
    { label: 'Cantidad No Facturante', value: kpis.cantidad_no_facturante.toString(), color: 'text-blue-600' },
  ]

  return (
    <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
      {items.map((item) => (
        <Card key={item.label}>
          <div className="text-center">
            <p className="text-sm text-gray-500">{item.label}</p>
            <p className={`mt-1 text-2xl font-bold ${item.color}`}>{item.value}</p>
          </div>
        </Card>
      ))}
    </div>
  )
}

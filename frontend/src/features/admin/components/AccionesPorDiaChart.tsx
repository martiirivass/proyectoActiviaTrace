import type { AccionesPorDia } from '@/features/admin/types'

interface AccionesPorDiaChartProps {
  data: AccionesPorDia[]
}

export function AccionesPorDiaChart({ data }: AccionesPorDiaChartProps) {
  if (data.length === 0) {
    return <p className="py-4 text-center text-sm text-gray-500">Sin datos para este período</p>
  }

  const maxValor = Math.max(...data.map((d) => d.total), 1)

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold text-gray-700">Acciones por Día</h3>
      <div className="flex items-end gap-1" style={{ height: 120 }}>
        {data.map((item) => {
          const altura = (item.total / maxValor) * 100
          return (
            <div
              key={item.fecha}
              className="group relative flex flex-1 flex-col items-center"
              style={{ height: '100%', justifyContent: 'flex-end' }}
            >
              <div
                className="w-full rounded-t bg-blue-500 transition-all hover:bg-blue-600"
                style={{ height: `${altura}%` }}
                title={`${item.fecha}: ${item.total} acciones`}
              />
              <span className="mt-1 text-[10px] text-gray-400">
                {item.fecha.slice(5)}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

import type { ReporteRapido } from '@/features/academico/types'

interface MetricasConsolidadasProps {
  reporte: ReporteRapido
}

export function MetricasConsolidadas({ reporte }: MetricasConsolidadasProps) {
  const metricas = [
    { label: 'Total alumnos', value: reporte.alumnos_total },
    { label: 'Total actividades', value: reporte.actividades_total },
    {
      label: 'Promedio general',
      value: reporte.promedio_general !== null ? reporte.promedio_general.toFixed(1) : '—',
    },
    { label: 'Aprobados', value: reporte.aprobados, variant: 'success' as const },
    { label: 'Desaprobados', value: reporte.desaprobados, variant: 'danger' as const },
    {
      label: '% Aprobación',
      value: reporte.pct_aprobacion !== null ? `${reporte.pct_aprobacion}%` : '—',
    },
  ]

  return (
    <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-6">
      {metricas.map((m) => (
        <div
          key={m.label}
          className="rounded-lg border border-gray-200 bg-white p-4 text-center shadow-sm"
        >
          <p
            className={`text-2xl font-bold ${
              m.variant === 'success'
                ? 'text-green-600'
                : m.variant === 'danger'
                  ? 'text-red-600'
                  : 'text-gray-900'
            }`}
          >
            {m.value}
          </p>
          <p className="mt-1 text-sm text-gray-500">{m.label}</p>
        </div>
      ))}
    </div>
  )
}

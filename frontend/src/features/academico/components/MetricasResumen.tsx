interface MetricaResumen {
  label: string
  value: number
  variant?: 'default' | 'success' | 'danger' | 'warning'
}

interface MetricasResumenProps {
  metricas: MetricaResumen[]
}

const variantStyles: Record<string, string> = {
  default: 'text-gray-900',
  success: 'text-green-600',
  danger: 'text-red-600',
  warning: 'text-yellow-600',
}

export function MetricasResumen({ metricas }: MetricasResumenProps) {
  return (
    <div className="grid grid-cols-2 gap-4 md:grid-cols-4 lg:grid-cols-6">
      {metricas.map((m) => (
        <div
          key={m.label}
          className="rounded-lg border border-gray-200 bg-white p-4 text-center shadow-sm"
        >
          <p
            className={`text-3xl font-bold ${variantStyles[m.variant ?? 'default']}`}
          >
            {m.value}
          </p>
          <p className="mt-1 text-sm text-gray-500">{m.label}</p>
        </div>
      ))}
    </div>
  )
}

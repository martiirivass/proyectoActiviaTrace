import type { AuditDashboard } from '@/features/admin/types'
import { Card } from '@/shared/components/ui/Card'

interface KPIAuditoriaProps {
  data: AuditDashboard | undefined
}

export function KPIAuditoria({ data }: KPIAuditoriaProps) {
  if (!data) return null

  const totalAcciones = data.acciones_por_dia.reduce((sum, d) => sum + d.total, 0)
  const totalComunicaciones = data.comunicaciones_por_docente.reduce((sum, d) => sum + d.total, 0)
  const totalInteracciones = data.interacciones_por_docente_materia.reduce((sum, d) => sum + d.total_acciones, 0)

  const items = [
    { label: 'Total Acciones', value: totalAcciones.toLocaleString(), color: 'text-blue-700' },
    { label: 'Total Comunicaciones', value: totalComunicaciones.toLocaleString(), color: 'text-green-700' },
    { label: 'Interacciones D/M', value: totalInteracciones.toLocaleString(), color: 'text-purple-700' },
    { label: 'Últimas Acciones', value: data.ultimas_acciones.length.toString(), color: 'text-gray-700' },
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

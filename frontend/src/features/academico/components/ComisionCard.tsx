import { useNavigate } from 'react-router-dom'
import { Card } from '@/shared/components/ui/Card'
import type { Comision } from '@/features/academico/types'

interface ComisionCardProps {
  comision: Comision
}

export function ComisionCard({ comision }: ComisionCardProps) {
  const navigate = useNavigate()

  return (
    <button
      type="button"
      className="w-full text-left transition-transform hover:scale-[1.02]"
      onClick={() =>
        navigate(`/comision/${comision.materia_id}/${comision.cohorte_id}`)
      }
    >
      <Card className="h-full cursor-pointer">
        <CardHeader>
          <h3 className="text-lg font-semibold text-gray-900">
            {comision.materia_nombre}
          </h3>
          <p className="text-sm text-gray-500">
            Cohorte: {comision.cohorte_nombre}
          </p>
        </CardHeader>
        <div className="grid grid-cols-3 gap-4">
          <Metrica label="Alumnos" value={comision.alumnos_count} />
          <Metrica
            label="Atrasados"
            value={comision.atrasados_count}
            variant={comision.atrasados_count > 0 ? 'danger' : 'default'}
          />
          <Metrica label="Pendientes" value={comision.pendientes_count} />
        </div>
      </Card>
    </button>
  )
}

function CardHeader({ children }: { children: React.ReactNode }) {
  return <div className="mb-3">{children}</div>
}

function Metrica({
  label,
  value,
  variant = 'default',
}: {
  label: string
  value: number
  variant?: 'default' | 'danger'
}) {
  return (
    <div className="text-center">
      <p
        className={`text-2xl font-bold ${
          variant === 'danger' ? 'text-red-600' : 'text-gray-900'
        }`}
      >
        {value}
      </p>
      <p className="text-xs text-gray-500">{label}</p>
    </div>
  )
}

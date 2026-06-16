import type { EstadoComunicacion } from '@/features/academico/types'

interface EstadoBadgeProps {
  estado: EstadoComunicacion
}

const estadoStyles: Record<EstadoComunicacion, string> = {
  pendiente: 'bg-gray-100 text-gray-700',
  enviando: 'bg-blue-100 text-blue-700',
  enviado: 'bg-green-100 text-green-700',
  error: 'bg-red-100 text-red-700',
  cancelado: 'bg-orange-100 text-orange-700',
}

const estadoLabels: Record<EstadoComunicacion, string> = {
  pendiente: 'Pendiente',
  enviando: 'Enviando',
  enviado: 'Enviado',
  error: 'Error',
  cancelado: 'Cancelado',
}

export function EstadoBadge({ estado }: EstadoBadgeProps) {
  return (
    <span
      className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${estadoStyles[estado]}`}
    >
      {estadoLabels[estado]}
    </span>
  )
}

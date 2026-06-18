import { Spinner } from '@/shared/components/ui/Spinner'
import { useAckStats } from '@/features/coordinacion/hooks/useAvisos'

interface AckStatsDisplayProps {
  avisoId: string
}

export function AckStatsDisplay({ avisoId }: AckStatsDisplayProps) {
  const { data: stats, isLoading } = useAckStats(avisoId)

  if (isLoading) return <Spinner size="sm" />

  if (!stats) return <span className="text-sm text-gray-400">—</span>

  return (
    <div className="flex items-center gap-3 text-sm">
      <span className="text-gray-600">Total: {stats.total_destinatarios}</span>
      <span className="text-gray-600">ACKs: {stats.acknowledgments_count}</span>
      <span
        className={`font-medium ${
          stats.acknowledgment_rate >= 0.8
            ? 'text-green-600'
            : stats.acknowledgment_rate >= 0.5
              ? 'text-yellow-600'
              : 'text-red-600'
        }`}
      >
        {Math.round(stats.acknowledgment_rate * 100)}%
      </span>
    </div>
  )
}

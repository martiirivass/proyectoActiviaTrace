import { RankingTable } from '@/features/academico/components/RankingTable'

export default function RankingPage() {
  return (
    <div>
      <h2 className="mb-4 text-lg font-semibold text-gray-900">
        Ranking de actividades
      </h2>
      <RankingTable />
    </div>
  )
}

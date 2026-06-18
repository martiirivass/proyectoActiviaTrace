import { useState } from 'react'
import { FiltrosPanel } from './FiltrosPanel'
import { MonitorTable } from './MonitorTable'
import { useMonitor } from '@/features/academico/hooks/useMonitor'
import type { MonitorFiltros } from '@/features/academico/types'

export function MonitorView() {
  const [filtros, setFiltros] = useState<MonitorFiltros>({})
  const { data, isLoading, isError, refetch } = useMonitor(filtros)

  return (
    <div className="space-y-4">
      <FiltrosPanel onFiltrosChange={setFiltros} />
      <MonitorTable
        data={data}
        isLoading={isLoading}
        isError={isError}
        onRefetch={() => refetch()}
      />
    </div>
  )
}

import { useState, useCallback } from 'react'
import { FiltrosLog } from './FiltrosLog'
import { AuditLogTable } from './AuditLogTable'
import { useAuditLog } from '@/features/admin/hooks/useAuditoria'
import type { AuditLogFiltros } from '@/features/admin/types'
import { Spinner } from '@/shared/components/ui/Spinner'
import { Alert } from '@/shared/components/ui/Alert'

export function AuditLogView() {
  const [filtros, setFiltros] = useState<AuditLogFiltros>({ limit: 50 })
  const { data, isLoading, error } = useAuditLog(filtros)

  const handleFilter = useCallback((f: AuditLogFiltros) => {
    setFiltros(f)
  }, [])

  const handlePageChange = useCallback((pf: { offset?: number; limit?: number }) => {
    setFiltros((prev) => ({ ...prev, offset: pf.offset, limit: pf.limit ?? 50 }))
  }, [])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Log de Auditoría</h1>
      </div>

      <FiltrosLog onFilter={handleFilter} />

      {isLoading && <div className="flex justify-center py-8"><Spinner /></div>}
      {error && <Alert variant="error" message="Error al cargar el log de auditoría" />}

      {!isLoading && !error && (
        <AuditLogTable
          data={data}
          onPageChange={handlePageChange}
          currentFiltros={filtros}
        />
      )}
    </div>
  )
}

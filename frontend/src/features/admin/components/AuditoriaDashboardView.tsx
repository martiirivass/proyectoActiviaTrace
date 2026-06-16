import { useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { FiltrosAuditoria } from './FiltrosAuditoria'
import { KPIAuditoria } from './KPIAuditoria'
import { AccionesPorDiaChart } from './AccionesPorDiaChart'
import { ComunicacionesPorDocenteTable } from './ComunicacionesPorDocenteTable'
import { InteraccionesPorDocenteMateriaTable } from './InteraccionesPorDocenteMateriaTable'
import { UltimasAccionesTable } from './UltimasAccionesTable'
import { useAuditDashboard } from '@/features/admin/hooks/useAuditoria'
import type { AuditoriaFiltros } from '@/features/admin/types'
import { Spinner } from '@/shared/components/ui/Spinner'
import { Alert } from '@/shared/components/ui/Alert'
import { Button } from '@/shared/components/ui/Button'

export function AuditoriaDashboardView() {
  const [filtros, setFiltros] = useState<AuditoriaFiltros>({})
  const { data, isLoading, error, refetch } = useAuditDashboard(filtros)

  const handleFilter = useCallback((f: AuditoriaFiltros) => {
    setFiltros(f)
  }, [])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Panel de Auditoría</h1>
        <Link to="/admin/auditoria/log">
          <Button variant="secondary">Ver Log Completo</Button>
        </Link>
      </div>

      <FiltrosAuditoria onFilter={handleFilter} />

      {isLoading && <div className="flex justify-center py-8"><Spinner /></div>}

      {error && (
        <Alert variant="error" message="Error al cargar datos de auditoría">
          <Button variant="ghost" size="sm" onClick={() => refetch()}>Reintentar</Button>
        </Alert>
      )}

      {!isLoading && !error && (
        <>
          <KPIAuditoria data={data} />

          <div className="rounded-lg border border-gray-200 bg-white p-4">
            <AccionesPorDiaChart data={data?.acciones_por_dia ?? []} />
          </div>

          <div className="rounded-lg border border-gray-200 bg-white p-4">
            <ComunicacionesPorDocenteTable data={data?.comunicaciones_por_docente ?? []} />
          </div>

          <div className="rounded-lg border border-gray-200 bg-white p-4">
            <InteraccionesPorDocenteMateriaTable data={data?.interacciones_por_docente_materia ?? []} />
          </div>

          <div className="rounded-lg border border-gray-200 bg-white p-4">
            <UltimasAccionesTable data={data?.ultimas_acciones ?? []} />
          </div>
        </>
      )}
    </div>
  )
}

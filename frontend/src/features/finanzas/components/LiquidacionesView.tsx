import { useState, useCallback } from 'react'
import { FiltrosLiquidaciones } from './FiltrosLiquidaciones'
import { KPILiquidaciones } from './KPILiquidaciones'
import { TabsSegmentacion } from './TabsSegmentacion'
import type { TabSegmento } from './TabsSegmentacion'
import { LiquidacionesTable } from './LiquidacionesTable'
import { LiquidacionesHistorial } from './LiquidacionesHistorial'
import { ExportarButton } from './ExportarButton'
import { AccionCerrar } from './AccionCerrar'
import { useLiquidaciones, useCalcularLiquidacion, useCerrarLiquidacion, useExportarLiquidaciones } from '@/features/finanzas/hooks/useLiquidaciones'

export function LiquidacionesView() {
  const [cohorteId, setCohorteId] = useState('')
  const [periodo, setPeriodo] = useState('')
  const [segmento, setSegmento] = useState<TabSegmento>('general')
  const [cerrandoId, setCerrandoId] = useState<string | null>(null)

  const { data, isLoading, error } = useLiquidaciones(cohorteId, periodo)
  const calcularMutation = useCalcularLiquidacion()
  const cerrarMutation = useCerrarLiquidacion()
  const exportarMutation = useExportarLiquidaciones()

  const handleCalcular = useCallback((cid: string, per: string) => {
    setCohorteId(cid)
    setPeriodo(per)
    calcularMutation.mutate({ cohorteId: cid, periodo: per })
  }, [calcularMutation])

  const handleCargar = useCallback((cid: string, per: string) => {
    setCohorteId(cid)
    setPeriodo(per)
  }, [])

  const handleCerrar = useCallback((id: string) => {
    setCerrandoId(id)
  }, [])

  const handleConfirmCerrar = useCallback(async () => {
    if (!cerrandoId) return
    await cerrarMutation.mutateAsync(cerrandoId)
    setCerrandoId(null)
  }, [cerrandoId, cerrarMutation])

  const handleExportar = useCallback(() => {
    if (!cohorteId || !periodo) return
    exportarMutation.mutate(
      { cohorteId, periodo },
      {
        onSuccess: (blob) => {
          const url = window.URL.createObjectURL(blob)
          const a = document.createElement('a')
          a.href = url
          a.download = `liquidaciones-${periodo}.csv`
          a.click()
          window.URL.revokeObjectURL(url)
        },
      },
    )
  }, [cohorteId, periodo, exportarMutation])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Liquidaciones</h1>
        {cohorteId && periodo && (
          <ExportarButton onExport={handleExportar} loading={exportarMutation.isPending} />
        )}
      </div>

      <FiltrosLiquidaciones
        onCalcular={handleCalcular}
        onCargar={handleCargar}
        loading={calcularMutation.isPending}
      />

      <KPILiquidaciones kpis={data?.kpis ?? null} />

      {data && (
        <>
          <TabsSegmentacion activeTab={segmento} onChange={setSegmento} />
          <LiquidacionesTable
            items={data.items}
            loading={isLoading}
            error={error ? (error as Error).message : null}
            segmento={segmento}
            onCerrar={handleCerrar}
            cerrandoId={null}
          />
        </>
      )}

      <LiquidacionesHistorial />

      {cerrandoId && (
        <AccionCerrar
          onConfirm={handleConfirmCerrar}
          onCancel={() => setCerrandoId(null)}
        />
      )}
    </div>
  )
}

import { useState } from 'react'
import { Button } from '@/shared/components/ui/Button'
import { Input } from '@/shared/components/ui/Input'
import type { FacturaFiltros, EstadoFactura } from '@/features/finanzas/types'

interface FiltrosFacturasProps {
  onFilter: (filtros: FacturaFiltros) => void
}

export function FiltrosFacturas({ onFilter }: FiltrosFacturasProps) {
  const [periodo, setPeriodo] = useState('')
  const [estado, setEstado] = useState<EstadoFactura | ''>('')
  const [usuarioId, setUsuarioId] = useState('')

  const handleFilter = () => {
    const filtros: FacturaFiltros = {}
    if (periodo) filtros.periodo = periodo
    if (estado) filtros.estado = estado as EstadoFactura
    if (usuarioId) filtros.usuario_id = usuarioId
    onFilter(filtros)
  }

  return (
    <div className="flex flex-wrap items-end gap-4 rounded-lg border border-gray-200 bg-white p-4">
      <Input
        label="Período (AAAA-MM)"
        placeholder="2026-06"
        value={periodo}
        onChange={(e) => setPeriodo(e.target.value)}
      />
      <div className="flex flex-col gap-1.5">
        <label className="text-sm font-medium text-gray-700">Estado</label>
        <select
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-base transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
          value={estado}
          onChange={(e) => setEstado(e.target.value as EstadoFactura | '')}
        >
          <option value="">Todos</option>
          <option value="Pendiente">Pendiente</option>
          <option value="Abonada">Abonada</option>
        </select>
      </div>
      <Input
        label="ID Usuario"
        placeholder="Filtrar por usuario"
        value={usuarioId}
        onChange={(e) => setUsuarioId(e.target.value)}
      />
      <Button onClick={handleFilter}>Filtrar</Button>
    </div>
  )
}

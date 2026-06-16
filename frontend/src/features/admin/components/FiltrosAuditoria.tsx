import { useState } from 'react'
import { Button } from '@/shared/components/ui/Button'
import { Input } from '@/shared/components/ui/Input'
import type { AuditoriaFiltros } from '@/features/admin/types'

interface FiltrosAuditoriaProps {
  onFilter: (filtros: AuditoriaFiltros) => void
}

export function FiltrosAuditoria({ onFilter }: FiltrosAuditoriaProps) {
  const [desde, setDesde] = useState('')
  const [hasta, setHasta] = useState('')
  const [materiaId, setMateriaId] = useState('')

  const handleFilter = () => {
    const f: AuditoriaFiltros = {}
    if (desde) f.desde = desde
    if (hasta) f.hasta = hasta
    if (materiaId) f.materia_id = materiaId
    onFilter(f)
  }

  return (
    <div className="flex flex-wrap items-end gap-4 rounded-lg border border-gray-200 bg-white p-4">
      <Input label="Desde" type="date" value={desde} onChange={(e) => setDesde(e.target.value)} />
      <Input label="Hasta" type="date" value={hasta} onChange={(e) => setHasta(e.target.value)} />
      <Input label="ID Materia" placeholder="Filtrar por materia" value={materiaId} onChange={(e) => setMateriaId(e.target.value)} />
      <Button onClick={handleFilter}>Filtrar</Button>
    </div>
  )
}
